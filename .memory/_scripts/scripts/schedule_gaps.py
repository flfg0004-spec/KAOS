#!/usr/bin/env python3
"""Gap Query scheduler — ejecuta query_gaps periódicamente y registra resultados.

Uso:
  py -3 _scripts/scripts/schedule_gaps.py --now              # ejecuta una vez
  py -3 _scripts/scripts/schedule_gaps.py --auto TOPIC       # detecta tema desde raw/
  py -3 _scripts/scripts/schedule_gaps.py --every 1h         # cada hora (bucle)
  py -3 _scripts/scripts/schedule_gaps.py --daemon           # modo continuo
"""

import argparse
import json
import logging
import signal
import sys
import time
from datetime import datetime, timedelta
from pathlib import Path

_SCRIPTS_DIR = Path(__file__).resolve().parent.parent
_LIB_DIR = _SCRIPTS_DIR / "lib"
if str(_LIB_DIR) not in sys.path:
    sys.path.insert(0, str(_SCRIPTS_DIR))

from lib.gap_query import query_gaps

logger = logging.getLogger("schedule_gaps")
_RUNNING = True

BASE = _SCRIPTS_DIR.parent  # .memory/
CACHE_DIR = BASE / "cache" / "gap-reports"


def _ensure_dirs():
    """Crear directorio de reportes si no existe."""
    CACHE_DIR.mkdir(parents=True, exist_ok=True)


def _save_report(result: dict):
    """Guardar resultado como JSON con timestamp."""
    _ensure_dirs()
    timestamp = datetime.now().strftime("%Y%m%d-%H%M%S")
    topic_slug = result.get("topic", "unknown").replace(" ", "-").lower()[:40]
    path = CACHE_DIR / f"gap-{topic_slug}-{timestamp}.json"
    path.write_text(json.dumps(result, indent=2, ensure_ascii=False), encoding="utf-8")
    logger.info("Report saved: %s", path)
    return path


def _detect_topic_from_raw() -> str:
    """Escanea .memory/raw/ para el archivo más reciente y extrae tema del nombre."""
    raw_dir = BASE / "raw"
    if not raw_dir.exists():
        logger.warning("raw/ directory not found")
        return "kaos"

    md_files = sorted(raw_dir.glob("*.md"), key=lambda f: f.stat().st_mtime, reverse=True)
    if not md_files:
        logger.warning("No files in raw/")
        return "kaos"

    latest = md_files[0]
    # Extraer tema del nombre: "investigacion-tema-principal.md" -> "tema principal"
    name = latest.stem
    # Quitar prefijos comunes
    for prefix in ["investigacion-", "estrategia-", "arquitectura-", "analisis-",
                    "diagrama-", "dossier-", "evaluacion-", "plan-", "data-",
                    "deep-", "deepseek-", "wiki-wiki-", "aletheia-", "master-",
                    "optimizacion-", "test-"]:
        if name.startswith(prefix):
            name = name[len(prefix):]
            break
    topic = name.replace("-", " ").strip()
    logger.info("Detected topic '%s' from latest raw file: %s", topic, latest.name)
    return topic


def _parse_interval(every_str: str) -> int:
    """Convierte string como '1h', '30m', '3600' a segundos."""
    every_str = every_str.strip().lower()
    if every_str.endswith("h"):
        return int(every_str[:-1]) * 3600
    elif every_str.endswith("m"):
        return int(every_str[:-1]) * 60
    elif every_str.endswith("s"):
        return int(every_str[:-1])
    else:
        return int(every_str)


def run_once(topic: str) -> dict:
    """Ejecuta query_gaps una vez y guarda el resultado.

    Returns:
        dict con el resultado de query_gaps
    """
    logger.info("Running gap query for topic='%s'...", topic)
    start = time.time()
    result = query_gaps(topic)
    elapsed = time.time() - start

    if elapsed > 30:
        logger.warning("GapDetector.suggest_gaps() took %.1fs (threshold: 30s)", elapsed)

    _save_report(result)

    # Imprimir resumen
    print(f"\n=== Gap Query Report: '{topic}' ===")
    print(f"  Generated: {result.get('generated_at', 'N/A')}")
    print(f"  Existing concepts: {result.get('total_existing', 0)}")
    print(f"  Total gaps: {result.get('total_gaps', 0)}")
    print(f"  Related gaps: {len(result.get('gaps_detected', []))}")
    print(f"  Orphan pages: {len(result.get('orphan_pages', []))}")
    print(f"  Decayed topics: {len(result.get('decayed_topics', []))}")
    print(f"  Confidence gaps: {len(result.get('confidence_gaps', []))}")
    print(f"  Elapsed: {elapsed:.2f}s")
    print(f"  Report saved to: {CACHE_DIR}")
    print()

    return result


def daemon_loop(interval: int):
    """Bucle infinito: ejecuta query_gaps cada N segundos."""
    logger.info("Daemon mode started (interval=%ds)", interval)
    while _RUNNING:
        try:
            run_once("kaos")
        except Exception as e:
            logger.error("Error in gap query: %s", e)
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
        description="Gap Query scheduler — ejecuta query_gaps periódicamente",
    )
    parser.add_argument("--now", action="store_true", help="Ejecuta una vez")
    parser.add_argument("--auto", nargs="?", const="auto", default=None,
                        help="Detecta tema desde raw/ (opcional: especificar tema)")
    parser.add_argument("--every", type=str, default=None,
                        help="Cada N (ej: 1h, 30m, 3600) — bucle simple")
    parser.add_argument("--daemon", action="store_true",
                        help="Modo continuo con log a archivo")
    parser.add_argument("--interval", type=int, default=3600,
                        help="Intervalo en segundos para --daemon (default: 3600)")
    parser.add_argument("--topic", type=str, default="kaos",
                        help="Tema para gap query (default: kaos)")
    parser.add_argument("--verbose", "-v", action="store_true", help="Logging verbose")

    args = parser.parse_args()

    log_level = logging.DEBUG if args.verbose else logging.INFO
    logging.basicConfig(
        level=log_level,
        format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S",
    )

    if args.daemon:
        # Modo daemon: log a archivo también
        _ensure_dirs()
        log_path = CACHE_DIR / "schedule_gaps.log"
        fh = logging.FileHandler(str(log_path), encoding="utf-8")
        fh.setLevel(logging.INFO)
        fh.setFormatter(logging.Formatter("%(asctime)s [%(levelname)s] %(name)s: %(message)s"))
        logging.getLogger().addHandler(fh)
        logger.info("Daemon logging to %s", log_path)

    signal.signal(signal.SIGINT, _handle_signal)
    signal.signal(signal.SIGTERM, _handle_signal)

    if args.auto:
        if args.auto == "auto" or args.auto is None:
            topic = _detect_topic_from_raw()
        else:
            topic = args.auto
        run_once(topic)

    elif args.now:
        run_once(args.topic)

    elif args.every:
        interval = _parse_interval(args.every)
        logger.info("Every mode: running every %ds", interval)
        while _RUNNING:
            run_once(args.topic)
            if not _RUNNING:
                break
            time.sleep(interval)

    elif args.daemon:
        daemon_loop(args.interval)

    else:
        parser.print_help()


if __name__ == "__main__":
    main()
