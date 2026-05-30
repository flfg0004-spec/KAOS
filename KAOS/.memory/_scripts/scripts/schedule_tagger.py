#!/usr/bin/env python3
"""Tagger scheduler — ejecuta tagger.py sobre archivos nuevos o modificados.

Uso:
  py -3 _scripts/scripts/schedule_tagger.py --now              # todos los archivos
  py -3 _scripts/scripts/schedule_tagger.py --incremental      # solo cambios desde HEAD
  py -3 _scripts/scripts/schedule_tagger.py --daemon           # modo continuo
"""

import argparse
import json
import logging
import signal
import subprocess
import sys
import time
from datetime import datetime
from pathlib import Path

_SCRIPTS_DIR = Path(__file__).resolve().parent.parent
_LIB_DIR = _SCRIPTS_DIR / "lib"
if str(_LIB_DIR) not in sys.path:
    sys.path.insert(0, str(_SCRIPTS_DIR))

from lib.tagger import tag_all, tag_file, _get_frontmatter, _read

logger = logging.getLogger("schedule_tagger")
_RUNNING = True

BASE = _SCRIPTS_DIR.parent  # .memory/
CACHE_DIR = BASE / "cache" / "tagger-reports"
WIKI_DIRS = ["wiki/concepts", "wiki/entities"]


def _ensure_dirs():
    """Crear directorio de reportes si no existe."""
    CACHE_DIR.mkdir(parents=True, exist_ok=True)


def _save_report(results: list[dict], mode: str):
    """Guardar resultados como JSON con timestamp."""
    _ensure_dirs()
    timestamp = datetime.now().strftime("%Y%m%d-%H%M%S")
    path = CACHE_DIR / f"tagger-{mode}-{timestamp}.json"
    path.write_text(json.dumps(results, indent=2, ensure_ascii=False), encoding="utf-8")
    logger.info("Report saved: %s", path)
    return path


def _print_summary(results: list[dict]):
    """Imprime resumen de resultados del tagger."""
    total = len(results)
    modified = sum(1 for r in results if r.get("modified"))
    errors = sum(1 for r in results if "error" in r)
    added_total = sum(len(r.get("added", [])) for r in results)

    print(f"\n=== Tagger Summary ===")
    print(f"  Files processed: {total}")
    print(f"  Modified: {modified}")
    print(f"  Errors: {errors}")
    print(f"  Tags added: {added_total}")
    if errors:
        print(f"\n  Errors:")
        for r in results:
            if "error" in r:
                print(f"    - {r.get('path', '?')}: {r['error']}")
    print(f"  Report saved to: {CACHE_DIR}")
    print()


def _tagger_available() -> bool:
    """Verifica si el tagger puede funcionar (DSOL/LLM disponible)."""
    try:
        # Intentar import rápido sin ejecutar LLM
        from lib import tagger as tgr
        return hasattr(tgr, "suggest_tags") and callable(tgr.suggest_tags)
    except ImportError as e:
        logger.error("Tagger not available: %s", e)
        return False


def run_all(dry_run: bool = False) -> list[dict]:
    """Ejecuta tagger sobre todos los archivos sin tags."""
    if not _tagger_available():
        logger.error("Tagger not available, skipping --now")
        return []

    logger.info("Tagging all untagged files...")
    results = tag_all(dry_run=dry_run)
    _save_report(results, "all")
    _print_summary(results)
    return results


def run_incremental(dry_run: bool = False) -> list[dict]:
    """Ejecuta tagger solo sobre archivos modificados desde HEAD.

    Usa git diff --name-only HEAD para encontrar archivos modificados.
    """
    if not _tagger_available():
        logger.error("Tagger not available, skipping --incremental")
        return []

    logger.info("Running incremental tagger (git diff HEAD)...")
    try:
        result = subprocess.run(
            ["git", "diff", "--name-only", "HEAD"],
            capture_output=True, text=True, cwd=BASE.parent, timeout=30,
        )
        changed = [
            line.strip() for line in result.stdout.splitlines()
            if line.strip().endswith(".md")
        ]
    except subprocess.TimeoutExpired:
        logger.error("git diff HEAD timed out")
        return []
    except FileNotFoundError:
        logger.error("git not found")
        return []
    except Exception as e:
        logger.error("Error running git diff: %s", e)
        return []

    if not changed:
        logger.info("No modified .md files found since HEAD")
        return []

    # Filtrar solo archivos en wiki/concepts y wiki/entities
    results = []
    for rel_path in changed:
        abs_path = BASE.parent / rel_path
        if not abs_path.exists():
            logger.debug("Skipping deleted file: %s", rel_path)
            continue

        # Verificar que está en wiki/concepts o wiki/entities
        rel_str = abs_path.relative_to(BASE.parent).as_posix()
        in_scope = any(rel_str.startswith(f".memory/{d}") for d in WIKI_DIRS)
        if not in_scope:
            logger.debug("Skipping out-of-scope file: %s", rel_str)
            continue

        # Preservar tags manuales: solo añadir, no reemplazar
        content = _read(abs_path)
        fm = _get_frontmatter(content)
        has_tags = "tags" in fm and fm["tags"].strip("[]").strip()

        if has_tags:
            logger.debug("Skipping %s (already has tags)", rel_str)
            continue

        try:
            r = tag_file(str(abs_path), dry_run=dry_run)
            results.append(r)
            if r.get("modified"):
                logger.info("Tagged: %s +%s", rel_str, r.get("added", []))
        except Exception as e:
            logger.error("Error tagging %s: %s", rel_str, e)
            results.append({"path": rel_str, "error": str(e)})

    _save_report(results, "incremental")
    _print_summary(results)
    return results


def daemon_loop(interval: int, dry_run: bool = False):
    """Watch mode: cada N segundos revisa git status, etiqueta cambios."""
    logger.info("Daemon mode started (interval=%ds)", interval)
    while _RUNNING:
        try:
            run_incremental(dry_run=dry_run)
        except Exception as e:
            logger.error("Error in tagger loop: %s", e)
        for _ in range(interval):
            if not _RUNNING:
                break
            time.sleep(1)

    logger.info("Daemon stopped.")


def _handle_signal(signum, frame):
    global _RUNNING
    logger.info("Received signal %s, shutting down...", signum)
    _RUNNING = False


def main():
    parser = argparse.ArgumentParser(
        description="Tagger scheduler — ejecuta tagger.py sobre archivos nuevos o modificados",
    )
    parser.add_argument("--now", action="store_true",
                        help="Etiqueta todos los archivos sin tags")
    parser.add_argument("--incremental", action="store_true",
                        help="Solo etiqueta cambios desde HEAD")
    parser.add_argument("--daemon", action="store_true",
                        help="Modo continuo: revisa cada N segundos")
    parser.add_argument("--interval", type=int, default=300,
                        help="Intervalo en segundos para --daemon (default: 300)")
    parser.add_argument("--dry-run", action="store_true",
                        help="No modificar archivos, solo mostrar qué se haría")
    parser.add_argument("--verbose", "-v", action="store_true",
                        help="Logging verbose")

    args = parser.parse_args()

    log_level = logging.DEBUG if args.verbose else logging.INFO
    logging.basicConfig(
        level=log_level,
        format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S",
    )

    if args.daemon:
        _ensure_dirs()
        log_path = CACHE_DIR / "schedule_tagger.log"
        fh = logging.FileHandler(str(log_path), encoding="utf-8")
        fh.setLevel(logging.INFO)
        fh.setFormatter(logging.Formatter("%(asctime)s [%(levelname)s] %(name)s: %(message)s"))
        logging.getLogger().addHandler(fh)
        logger.info("Daemon logging to %s", log_path)

    signal.signal(signal.SIGINT, _handle_signal)
    signal.signal(signal.SIGTERM, _handle_signal)

    if args.now:
        run_all(dry_run=args.dry_run)
    elif args.incremental:
        run_incremental(dry_run=args.dry_run)
    elif args.daemon:
        daemon_loop(args.interval, dry_run=args.dry_run)
    else:
        parser.print_help()


if __name__ == "__main__":
    main()
