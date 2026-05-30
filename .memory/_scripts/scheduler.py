"""Scheduler — ejecuta tareas programadas del sistema KAOS."""
import logging
import json
import time
from datetime import datetime, date
from pathlib import Path

logging.basicConfig(level=logging.INFO)
_LOG = logging.getLogger("scheduler")

SCHEDULE = {
    "audit": {"interval": 3600, "last_run": 0.0},
    "weekly_report": {"interval": 604800, "last_run": 0.0},
    "daily_summary": {"interval": 86400, "last_run": 0.0},
}

def run_audit():
    from lib.quality.audit_trigger import run_audit
    result = run_audit()
    _LOG.info("Audit complete: %d checks, %d errors, %d warnings",
              result["summary"]["total_checks"],
              result["summary"]["errors"],
              result["summary"]["warnings"])
    return result

def run_once(task="audit"):
    tasks = {"audit": run_audit}
    fn = tasks.get(task)
    if fn:
        return fn()
    _LOG.warning("Unknown task: %s", task)
    return None

def run_loop(interval=3600):
    _LOG.info("Scheduler started (interval=%ds)", interval)
    while True:
        run_audit()
        time.sleep(interval)

if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser()
    parser.add_argument("--once", action="store_true", help="Run once and exit")
    parser.add_argument("--task", default="audit", help="Task to run")
    parser.add_argument("--interval", type=int, default=3600, help="Loop interval in seconds")
    args = parser.parse_args()
    if args.once:
        run_once(args.task)
    else:
        run_loop(args.interval)
