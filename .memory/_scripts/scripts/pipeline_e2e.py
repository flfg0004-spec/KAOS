#!/usr/bin/env python3
"""Pipeline E2E — orquesta toda la cadena: gap -> capture -> tag -> score -> promote -> index.

Ejecuta cada fase secuencialmente con opción de saltar fases.
Usa los módulos y scripts existentes de .memory/_scripts/.

Uso:
  py -3 _scripts/scripts/pipeline_e2e.py                  # full pipeline
  py -3 _scripts/scripts/pipeline_e2e.py --skip-tag        # salta tagger
  py -3 _scripts/scripts/pipeline_e2e.py --until-score     # para después de scoring
  py -3 _scripts/scripts/pipeline_e2e.py --dry-run         # solo reporta
"""

import argparse
import json
import logging
import subprocess
import sys
import time
from datetime import datetime
from pathlib import Path

from lib.paths import MEMORY_DIR, PROJECT_ROOT

_SCRIPTS_DIR = Path(__file__).resolve().parent
_LIB_DIR = _SCRIPTS_DIR / ".." / "lib"
if str(_LIB_DIR.resolve()) not in sys.path:
    sys.path.insert(0, str(_SCRIPTS_DIR.parent))  # .memory/_scripts/

logger = logging.getLogger("pipeline_e2e")

BASE = _SCRIPTS_DIR.parent  # .memory/
PROJECT_ROOT = BASE.parent   # KAOS/
CACHE_DIR = BASE / "cache" / "pipeline"
REPORT_DIR = CACHE_DIR

PHASES = ["gap", "tag", "score", "promote", "sync", "index"]
PHASE_ORDER = {p: i for i, p in enumerate(PHASES)}


def _ensure_dirs():
    CACHE_DIR.mkdir(parents=True, exist_ok=True)


def _elapsed(start: float) -> str:
    return f"{time.time() - start:.2f}s"


def _print_phase(phase: str, msg: str):
    print(f"  {phase:8s}  {msg}")


def _save_report(report: dict):
    _ensure_dirs()
    timestamp = datetime.now().strftime("%Y%m%d-%H%M%S")
    path = REPORT_DIR / f"pipeline-{timestamp}.json"
    path.write_text(json.dumps(report, indent=2, ensure_ascii=False), encoding="utf-8")
    logger.info("Report saved: %s", path)
    return path


# ── Phase 1: Gap Detection ──────────────────────────────────────────────

def phase_gap(dry_run: bool = False) -> dict:
    """Detecta gaps via gap_query."""
    start = time.time()

    if dry_run:
        elapsed = _elapsed(start)
        _print_phase("gap", f"dry-run (saltado)")
        return {
            "phase": "gap",
            "elapsed": elapsed,
            "existing_concepts": 0,
            "total_gaps": 0,
            "related_gaps": 0,
            "orphan_pages": 0,
            "dry_run": True,
            "error": None,
        }

    from lib.gap_query import query_gaps

    result = query_gaps("kaos")
    elapsed = _elapsed(start)

    existing = result.get("total_existing", 0)
    total_gaps = result.get("total_gaps", 0)
    related = len(result.get("gaps_detected", []))
    orphans = len(result.get("orphan_pages", []))

    _print_phase("gap", f"{existing} existentes, {total_gaps} gaps totales, "
                       f"{related} relacionados, {orphans} orphans ({elapsed})")

    return {
        "phase": "gap",
        "elapsed": elapsed,
        "existing_concepts": existing,
        "total_gaps": total_gaps,
        "related_gaps": related,
        "orphan_pages": orphans,
        "error": None,
    }


# ── Phase 2: Tag ────────────────────────────────────────────────────────

def phase_tag(dry_run: bool = False) -> dict:
    """Ejecuta schedule_tagger.py --incremental vía subprocess."""
    script = _SCRIPTS_DIR / "schedule_tagger.py"
    if not script.exists():
        return {"phase": "tag", "elapsed": "0.00s", "error": "schedule_tagger.py not found"}

    start = time.time()
    cmd = [sys.executable, str(script), "--incremental", "--json"]
    if dry_run:
        cmd.append("--dry-run")

    try:
        r = subprocess.run(cmd, capture_output=True, text=True, timeout=120)
        elapsed = _elapsed(start)

        if r.returncode != 0:
            logger.warning("schedule_tagger exited with code %d: %s", r.returncode, r.stderr.strip())

        # Parse JSON output from child
        files_proc = 0
        modified = 0
        errors = 0
        added = 0
        try:
            data = json.loads(r.stdout)
            files_proc = data.get("files_processed", 0)
            modified = data.get("modified", 0)
            errors = data.get("errors", 0)
            added = data.get("tags_added", 0)
        except (json.JSONDecodeError, ValueError) as e:
            logger.warning("Failed to parse JSON from schedule_tagger: %s. Using defaults.", e)

        _print_phase("tag", f"{files_proc} procesados, {modified} modificados, "
                           f"{errors} errores, +{added} tags ({elapsed})")

        return {
            "phase": "tag",
            "elapsed": elapsed,
            "files_processed": files_proc,
            "modified": modified,
            "errors": errors,
            "tags_added": added,
            "error": None,
        }

    except subprocess.TimeoutExpired:
        elapsed = _elapsed(start)
        _print_phase("tag", f"TIMEOUT after 120s")
        return {"phase": "tag", "elapsed": elapsed, "error": "Timeout (120s)"}
    except FileNotFoundError as e:
        elapsed = _elapsed(start)
        return {"phase": "tag", "elapsed": elapsed, "error": f"Python not found: {e}"}
    except Exception as e:
        elapsed = _elapsed(start)
        logger.error("Tag phase error: %s", e)
        return {"phase": "tag", "elapsed": elapsed, "error": str(e)}


# ── Phase 3: Score ──────────────────────────────────────────────────────

def phase_score(dry_run: bool = False) -> dict:
    """Evalúa todas las notas wiki/ con score_note()."""
    from lib.scoring import score_note

    start = time.time()

    wiki_dirs = [
        BASE / "wiki" / "concepts",
        BASE / "wiki" / "entities",
    ]

    results = []
    errors = 0
    for wd in wiki_dirs:
        if not wd.exists():
            continue
        for f in sorted(wd.glob("*.md")):
            if dry_run:
                results.append({"path": str(f.relative_to(PROJECT_ROOT)), "score": "?"})
                continue
            try:
                sr = score_note(f)
                results.append(sr)
            except Exception as e:
                errors += 1
                logger.warning("Score error for %s: %s", f.name, e)

    elapsed = _elapsed(start)
    scored = len(results)

    if not dry_run and results:
        scores = [r["total_score"] for r in results if isinstance(r.get("total_score"), (int, float))]
        above_5 = sum(1 for s in scores if s >= 5.0)
        avg = sum(scores) / len(scores) if scores else 0.0
        _print_phase("score", f"{scored} notas, {above_5} > score 5.0, "
                              f"promedio {avg:.2f}, {errors} errores ({elapsed})")
    else:
        _print_phase("score", f"{scored} notas (dry-run), {errors} errores ({elapsed})")

    return {
        "phase": "score",
        "elapsed": elapsed,
        "files_scored": scored,
        "above_5": above_5 if not dry_run and results else 0,
        "average_score": round(avg, 2) if not dry_run and results else 0.0,
        "errors": errors,
        "error": None,
    }


# ── Phase 4: Promote ────────────────────────────────────────────────────

def phase_promote(dry_run: bool = False) -> dict:
    """Ejecuta promote_to_library.py vía subprocess."""
    script = _SCRIPTS_DIR / "promote_to_library.py"
    if not script.exists():
        return {"phase": "promote", "elapsed": "0.00s", "error": "promote_to_library.py not found"}

    start = time.time()
    cmd = [sys.executable, str(script), "--json"]
    if dry_run:
        cmd.append("--dry-run")
    else:
        cmd.append("--apply")

    try:
        r = subprocess.run(cmd, capture_output=True, text=True, timeout=60)
        elapsed = _elapsed(start)

        if r.returncode != 0:
            logger.warning("promote_to_library exited with code %d", r.returncode)

        # Parse JSON output from child
        promoted = 0
        skipped = 0
        diverged = 0
        try:
            data = json.loads(r.stdout)
            promoted = data.get("promoted", 0)
            skipped = data.get("skipped", 0)
            diverged = data.get("diverged", 0)
        except (json.JSONDecodeError, ValueError) as e:
            logger.warning("Failed to parse JSON from promote_to_library: %s. Using defaults.", e)

        _print_phase("promote", f"{promoted} promovidos, {skipped} saltados, "
                               f"{diverged} divergidos ({elapsed})")

        return {
            "phase": "promote",
            "elapsed": elapsed,
            "promoted": promoted,
            "skipped": skipped,
            "diverged": diverged,
            "error": None,
        }

    except subprocess.TimeoutExpired:
        return {"phase": "promote", "elapsed": _elapsed(start), "error": "Timeout (60s)"}
    except Exception as e:
        return {"phase": "promote", "elapsed": _elapsed(start), "error": str(e)}


# ── Phase 5: Sync ───────────────────────────────────────────────────────

def phase_sync(dry_run: bool = False) -> dict:
    """Sincroniza frontmatter via sync_properties() sobre archivos modificados."""
    from lib.obsidian import sync_properties

    start = time.time()

    wiki_dirs = [
        BASE / "wiki" / "concepts",
        BASE / "wiki" / "entities",
    ]

    synced = 0
    unchanged = 0
    no_fm = 0
    not_found = 0

    for wd in wiki_dirs:
        if not wd.exists():
            continue
        for f in sorted(wd.glob("*.md")):
            if dry_run:
                unchanged += 1
                continue
            try:
                result = sync_properties(f)
                status = result.get("status", "")
                if status == "synced":
                    synced += 1
                elif status == "no_frontmatter":
                    no_fm += 1
                elif status == "not_found":
                    not_found += 1
                else:
                    unchanged += 1
            except Exception as e:
                logger.warning("Sync error for %s: %s", f.name, e)
                no_fm += 1

    elapsed = _elapsed(start)

    if dry_run:
        _print_phase("sync", f"{unchanged} archivos revisados (dry-run, no se escribe) ({elapsed})")
    else:
        _print_phase("sync", f"{synced} sincronizados, {unchanged} sin cambios, "
                             f"{no_fm} sin frontmatter ({elapsed})")

    return {
        "phase": "sync",
        "elapsed": elapsed,
        "synced": synced,
        "unchanged": unchanged,
        "no_frontmatter": no_fm,
        "not_found": not_found,
        "error": None,
    }


# ── Phase 6: Index ──────────────────────────────────────────────────────

def phase_index(dry_run: bool = False) -> dict:
    """Verifica estado de los índices configurados (Smart Connections + txtai)."""
    start = time.time()

    # Smart Connections config (puede estar en KAOS/ o en raíz)
    sc_paths = [
        p / ".obsidian" / "plugins" / "smart-connections" / "data.json"
        for p in [PROJECT_ROOT / "KAOS", PROJECT_ROOT]
        if (p / ".obsidian").exists()
    ]
    sc_vault = sc_paths[0] if sc_paths else PROJECT_ROOT / "dummy"
    sc_ok = sc_vault.exists()

    # txtai config
    txtai_config = BASE / "cache" / "txtai-config.yml"
    txtai_ok = txtai_config.exists()

    elapsed = _elapsed(start)

    sc_msg = f"SC -> library/ ({'OK' if sc_ok else 'MISSING'})"
    txtai_msg = f"txtai -> wiki/ ({'OK' if txtai_ok else 'MISSING'})"
    _print_phase("index", f"{sc_msg}, {txtai_msg} ({elapsed})")

    return {
        "phase": "index",
        "elapsed": elapsed,
        "smart_connections_ok": sc_ok,
        "txtai_ok": txtai_ok,
        "smart_connections_path": str(sc_vault.relative_to(PROJECT_ROOT)) if sc_ok else "MISSING",
        "txtai_config_path": str(txtai_config.relative_to(BASE)) if txtai_ok else "MISSING",
        "error": None,
    }


# ── Runner ──────────────────────────────────────────────────────────────

def run_pipeline(args) -> int:
    """Ejecuta fases según flags."""
    dry_run = args.dry_run

    # Determinar fases activas
    skip_phases = set()
    if args.skip_tag:
        skip_phases.add("tag")
    if args.skip_score:
        skip_phases.add("score")
    if args.skip_promote:
        skip_phases.add("promote")
    if args.skip_sync:
        skip_phases.add("sync")
    if args.skip_index:
        skip_phases.add("index")

    # until: detener después de cierta fase
    until = args.until
    if until and until not in PHASES:
        print(f"Fase '{until}' no válida. Opciones: {', '.join(PHASES)}")
        return 1

    # Ejecutar fases en orden
    results = []
    separator = "─" * 50

    print(f"\n{'=' * 55}")
    print(f"  Pipeline E2E{' [DRY RUN]' if dry_run else ''}")
    print(f"  {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print(f"{'=' * 55}\n")

    for phase_name in PHASES:
        if phase_name in skip_phases:
            print(f"  ⏭️  {phase_name:8s}  skipped\n")
            results.append({"phase": phase_name, "elapsed": "0.00s", "skipped": True})
            continue

        print(f"  {separator}")
        print(f"  >>> Phase: {phase_name.upper()} <<<")
        print()

        phase_func = {
            "gap": phase_gap,
            "tag": phase_tag,
            "score": phase_score,
            "promote": phase_promote,
            "sync": phase_sync,
            "index": phase_index,
        }[phase_name]

        try:
            result = phase_func(dry_run=dry_run)
        except Exception as e:
            result = {"phase": phase_name, "elapsed": "0.00s", "error": str(e)}
            logger.exception("Fase %s falló: %s", phase_name, e)

        results.append(result)
        print()

        if result.get("error"):
            print(f"  ⚠️  {phase_name}: error — {result['error']}")
            print()

        # until guard
        if until and phase_name == until:
            print(f"  ⏹️  Deteniendo después de {phase_name} (--until={until})")
            break

    # Reporte final
    total_elapsed = sum(
        float(r.get("elapsed", "0s").rstrip("s"))
        for r in results if isinstance(r.get("elapsed"), str)
    )

    print(f"\n{'=' * 55}")
    print(f"  Pipeline E2E — {'Dry Run' if dry_run else 'Complete'}")
    print(f"  {'=' * 55}")

    for r in results:
        p = r.get("phase", "?").ljust(7)
        el = r.get("elapsed", "0.00s")
        err = r.get("error")
        if err:
            print(f"  ❌ {p}  error: {err[:60]}")
        elif r.get("skipped"):
            print(f"  ⏭️  {p}  skipped")
        else:
            print(f"  {'✅' if not err else '❌'} {p}  {el}")

    print(f"  {'=' * 55}")
    print(f"  Tiempo total: {total_elapsed:.2f}s")
    print()

    # Guardar reporte
    report = {
        "timestamp": datetime.now().isoformat(),
        "dry_run": dry_run,
        "phases": results,
        "total_elapsed_s": round(total_elapsed, 2),
        "errors": [r.get("error") for r in results if r.get("error")],
    }
    report_path = _save_report(report)
    print(f"  Report: {report_path}")

    # Retornar código de error si alguna fase falló
    has_errors = any(r.get("error") for r in results if not r.get("skipped"))
    return 1 if has_errors else 0


def main():
    parser = argparse.ArgumentParser(
        description="Pipeline E2E — orquesta toda la cadena de procesamiento",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Fases: gap -> tag -> score -> promote -> sync -> index

Ejemplos:
  py -3 _scripts/scripts/pipeline_e2e.py                  # pipeline completo
  py -3 _scripts/scripts/pipeline_e2e.py --skip-tag        # salta tagger
  py -3 _scripts/scripts/pipeline_e2e.py --until-score     # para después de scoring
  py -3 _scripts/scripts/pipeline_e2e.py --dry-run         # solo reporta
        """,
    )

    # Skip flags
    parser.add_argument("--skip-tag", action="store_true", help="Saltar fase de tagging")
    parser.add_argument("--skip-score", action="store_true", help="Saltar fase de scoring")
    parser.add_argument("--skip-promote", action="store_true", help="Saltar fase de promoción")
    parser.add_argument("--skip-sync", action="store_true", help="Saltar fase de sync")
    parser.add_argument("--skip-index", action="store_true", help="Saltar fase de index")

    # Until
    parser.add_argument("--until", type=str, default=None,
                        help="Detener después de fase específica")

    # Mode
    parser.add_argument("--dry-run", action="store_true", help="Solo reportar, no ejecutar cambios")

    # Verbose
    parser.add_argument("--verbose", "-v", action="store_true", help="Logging verbose")

    args = parser.parse_args()

    # Setup logging
    log_level = logging.DEBUG if args.verbose else logging.INFO
    logging.basicConfig(
        level=log_level,
        format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S",
    )

    _ensure_dirs()

    return run_pipeline(args)


if __name__ == "__main__":
    sys.exit(main())
