"""Swarm launcher CLI — start/stop/status/logs for worker backends."""

import argparse
import logging
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
from swarm.worker_manager import create_worker

_LOG = logging.getLogger(__name__)
_WORKERS: dict = {}

AVAILABLE_ROLES = ["researcher", "architect", "strategist", "curator"]


def cmd_start(args):
    roles = args.roles if args.roles else AVAILABLE_ROLES
    if args.all:
        roles = AVAILABLE_ROLES
    backend = args.backend or "native"
    for role in roles:
        if role in _WORKERS:
            print(f"Worker {role} already running")
            continue
        worker = create_worker(role, backend)
        if worker.start():
            _WORKERS[role] = worker
            print(f"Started {backend} worker: {role}")
        else:
            print(f"FAILED to start {backend} worker: {role}")
    return 0


def cmd_stop(args):
    roles = args.roles if args.roles else list(_WORKERS.keys())
    if args.all:
        roles = list(_WORKERS.keys())
    for role in roles:
        worker = _WORKERS.pop(role, None)
        if worker:
            worker.stop()
            print(f"Stopped worker: {role}")
        else:
            print(f"Worker not running: {role}")
    return 0


def cmd_status(args):
    active = 0
    for role in AVAILABLE_ROLES:
        if role in _WORKERS:
            st = _WORKERS[role].status()
            print(f"  {role}: {st.get('status', 'unknown')} (PID {st.get('pid', '-')})")
            if st.get("status") == "running":
                active += 1
        else:
            pid_file = Path(".memory") / "_pipeline" / f"swarm-{role}-native.pid"
            if pid_file.exists():
                pid = pid_file.read_text().strip()
                print(f"  {role}: running? (PID {pid}, orphan)")
                active += 1
            else:
                print(f"  {role}: stopped")
    if not active:
        print("No workers running")


def cmd_send(args):
    import json

    worker = create_worker(args.role, args.backend)
    if not worker.start():
        print(f"FAILED to start {args.role} worker")
        return 1
    context = json.dumps({"topic": args.topic})
    result = worker.send(context)
    if result:
        print(f"Result from {args.role}: {result}")
    else:
        print(f"No response from {args.role}")
    worker.stop()
    return 0


def cmd_run(args):
    return cmd_send(args)


def cmd_logs(args):
    log_file = Path(".memory") / "_pipeline" / "swarm.log"
    if not log_file.exists():
        print("No swarm log file found")
        return 0
    lines = args.lines or 20
    content = log_file.read_text(encoding="utf-8").splitlines()
    for line in content[-lines:]:
        print(line)
    return 0


def main():
    parser = argparse.ArgumentParser(prog="swarm", description="KAOS Swarm Worker Manager")
    sub = parser.add_subparsers(dest="command", required=True)

    p_start = sub.add_parser("start", help="Start one or more workers")
    p_start.add_argument("roles", nargs="*", choices=AVAILABLE_ROLES, help="Worker roles to start")
    p_start.add_argument("--all", action="store_true", help="Start all roles")
    p_start.add_argument("--backend", choices=["native", "tmux"], default="native", help="Worker backend")

    p_stop = sub.add_parser("stop", help="Stop one or more workers")
    p_stop.add_argument("roles", nargs="*", choices=AVAILABLE_ROLES, help="Worker roles to stop")
    p_stop.add_argument("--all", action="store_true", help="Stop all workers")

    sub.add_parser("status", help="Show worker status")

    p_logs = sub.add_parser("logs", help="Show swarm logs")
    p_logs.add_argument("--lines", type=int, default=20, help="Number of log lines")

    p_send = sub.add_parser("send", help="Start worker, send context, show result, stop")
    p_send.add_argument("role", choices=AVAILABLE_ROLES, help="Worker role")
    p_send.add_argument("--topic", default="test", help="Topic/context to send")
    p_send.add_argument("--backend", choices=["native", "tmux"], default="native")

    p_run = sub.add_parser("run", help="Run worker once (start→send→stop), then discard")
    p_run.add_argument("role", choices=AVAILABLE_ROLES, help="Worker role")
    p_run.add_argument("--topic", default="test", help="Topic/context to send")
    p_run.add_argument("--backend", choices=["native", "tmux"], default="native")

    args = parser.parse_args()
    commands = {
        "start": cmd_start,
        "stop": cmd_stop,
        "status": cmd_status,
        "logs": cmd_logs,
        "send": cmd_send,
        "run": cmd_run,
    }
    fn = commands.get(args.command)
    if fn:
        sys.exit(fn(args))
    parser.print_help()


if __name__ == "__main__":
    main()
