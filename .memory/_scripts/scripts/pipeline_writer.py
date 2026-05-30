#!/usr/bin/env python3
"""Pipeline de escritura bufferizada con auto-flush.

Usa file_lock.buffered_write para acumular escrituras y descargar
en lote cada N segundos o N archivos.

Uso:
  py -3 _scripts/scripts/pipeline_writer.py                  # daemon mode (flush cada 30s)
  py -3 _scripts/scripts/pipeline_writer.py --flush-all     # flush inmediato
  py -3 _scripts/scripts/pipeline_writer.py --daemon --interval 60  # flush cada 60s
  py -3 _scripts/scripts/pipeline_writer.py --buffer-size 10        # flush cada 10 archivos
"""

import argparse
import logging
import signal
import sys
import time
from pathlib import Path

# Asegurar que lib/ está en el path
_SCRIPTS_DIR = Path(__file__).resolve().parent.parent
_LIB_DIR = _SCRIPTS_DIR / "lib"
if str(_LIB_DIR) not in sys.path:
    sys.path.insert(0, str(_SCRIPTS_DIR))

from lib.file_lock import buffered_write, flush_buffered_writes

logger = logging.getLogger("pipeline_writer")
_RUNNING = True


def _handle_signal(signum, frame):
    global _RUNNING
    logger.info("Received signal %s, shutting down...", signum)
    _RUNNING = False


def flush_all():
    """Flush inmediato de todas las escrituras bufferizadas."""
    logger.info("Flushing all buffered writes...")
    flush_buffered_writes()
    logger.info("Flush complete.")


def daemon_loop(interval: float, buffer_size: int):
    """Loop principal en modo daemon."""
    logger.info(
        "Pipeline writer daemon started (interval=%ss, buffer_size=%s)",
        interval, buffer_size,
    )
    while _RUNNING:
        time.sleep(interval)
        if not _RUNNING:
            break
        flush_all()

    # Flush final al salir
    flush_all()
    logger.info("Pipeline writer daemon stopped.")


def main():
    parser = argparse.ArgumentParser(
        description="Pipeline de escritura bufferizada con auto-flush",
    )
    parser.add_argument(
        "--daemon", "-d",
        action="store_true",
        help="Modo daemon: flush periódico cada --interval segundos",
    )
    parser.add_argument(
        "--flush-all", "-f",
        action="store_true",
        help="Flush inmediato de todas las escrituras bufferizadas",
    )
    parser.add_argument(
        "--interval", "-i",
        type=float,
        default=30.0,
        help="Intervalo de flush en segundos (default: 30)",
    )
    parser.add_argument(
        "--buffer-size", "-b",
        type=int,
        default=5,
        help="Número de archivos bufferizados antes de flush forzado (default: 5)",
    )
    parser.add_argument(
        "--verbose", "-v",
        action="store_true",
        help="Logging verbose",
    )

    args = parser.parse_args()

    logging.basicConfig(
        level=logging.DEBUG if args.verbose else logging.INFO,
        format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S",
    )

    # Registrar signal handlers para shutdown graceful
    signal.signal(signal.SIGINT, _handle_signal)
    signal.signal(signal.SIGTERM, _handle_signal)

    if args.flush_all:
        flush_all()
        return

    if args.daemon:
        daemon_loop(args.interval, args.buffer_size)
        return

    # Sin flags: flush inmediato y salir (comportamiento por defecto)
    flush_all()


if __name__ == "__main__":
    main()
