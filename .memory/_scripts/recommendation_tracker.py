"""Recommendation Tracker — log and track strategic recommendations from Metis.

Logs recommendations to JSONL files in .memory/cache/recommendations/,
tracks status lifecycle, and generates simple markdown dashboards.

Usage:
    py -3 .memory/_scripts/recommendation_tracker.py add "text" --context "..."
    py -3 .memory/_scripts/recommendation_tracker.py list
    py -3 .memory/_scripts/recommendation_tracker.py list --status pendiente
    py -3 .memory/_scripts/recommendation_tracker.py update <id> --status en_progreso
    py -3 .memory/_scripts/recommendation_tracker.py dashboard
    py -3 .memory/_scripts/recommendation_tracker.py dashboard --output report.md

Status lifecycle:
    pendiente -> en_progreso -> implementada -> validada
                                                     -> rechazada
"""

import argparse
import json
import os
import shutil
import sys
from datetime import datetime
from pathlib import Path
from uuid import uuid4

RECOMMENDATIONS_DIR = Path(__file__).resolve().parents[2] / ".memory" / "cache" / "recommendations"
VALID_STATUSES = ["pendiente", "en_progreso", "implementada", "validada", "rechazada"]
VALID_TRANSITIONS = {
    "pendiente": ["en_progreso", "rechazada"],
    "en_progreso": ["implementada", "rechazada"],
    "implementada": ["validada", "rechazada"],
    "validada": [],
    "rechazada": [],
}


def ensure_dir():
    RECOMMENDATIONS_DIR.mkdir(parents=True, exist_ok=True)


def _load_all() -> list[dict]:
    ensure_dir()
    records = []
    for f in sorted(RECOMMENDATIONS_DIR.glob("*.jsonl")):
        with open(f, encoding="utf-8") as fh:
            for line in fh:
                line = line.strip()
                if line:
                    records.append(json.loads(line))
    return records


def _append(record: dict):
    ensure_dir()
    today = datetime.now().strftime("%Y-%m-%d")
    filepath = RECOMMENDATIONS_DIR / f"{today}.jsonl"
    with open(filepath, "a", encoding="utf-8") as f:
        f.write(json.dumps(record, ensure_ascii=False) + "\n")


def add_recommendation(text: str, context: str = "", metadata: str = "") -> str:
    rid = str(uuid4())[:8]
    now = datetime.now().isoformat()
    record = {
        "id": rid,
        "text": text,
        "context": context,
        "metadata": metadata,
        "status": "pendiente",
        "created_at": now,
        "updated_at": now,
    }
    _append(record)
    return rid


def list_recommendations(status: str | None = None) -> list[dict]:
    records = _load_all()
    if status:
        records = [r for r in records if r.get("status") == status]
    return sorted(records, key=lambda r: r.get("created_at", ""), reverse=True)


def update_status(rid: str, new_status: str) -> bool:
    if new_status not in VALID_STATUSES:
        print(f"Error: Invalid status '{new_status}'. Valid: {', '.join(VALID_STATUSES)}", file=sys.stderr)
        return False
    all_records = _load_all()
    found = False
    for rec in all_records:
        if rec.get("id") == rid:
            current = rec.get("status", "pendiente")
            allowed = VALID_TRANSITIONS.get(current, [])
            if new_status not in allowed and current != new_status:
                print(
                    f"Error: Cannot transition from '{current}' to '{new_status}'. "
                    f"Allowed: {allowed}",
                    file=sys.stderr,
                )
                return False
            rec["status"] = new_status
            rec["updated_at"] = datetime.now().isoformat()
            found = True
            break
    if not found:
        print(f"Error: Recommendation '{rid}' not found", file=sys.stderr)
        return False
    _rewrite_all(all_records)
    return True


def _rewrite_all(records: list[dict]):
    ensure_dir()
    today = datetime.now().strftime("%Y-%m-%d")
    backup_dir = RECOMMENDATIONS_DIR / "backup"
    backup_dir.mkdir(parents=True, exist_ok=True)
    filepath = RECOMMENDATIONS_DIR / f"{today}.jsonl"
    for f in sorted(RECOMMENDATIONS_DIR.glob("*.jsonl")):
        ts = datetime.fromtimestamp(f.stat().st_mtime).strftime("%Y%m%d_%H%M%S")
        shutil.copy2(f, backup_dir / f"{f.stem}_{ts}.jsonl")
    with open(filepath, "w", encoding="utf-8") as f:
        for rec in records:
            f.write(json.dumps(rec, ensure_ascii=False) + "\n")


def generate_dashboard() -> str:
    records = _load_all()
    total = len(records)
    counts = {s: 0 for s in VALID_STATUSES}
    for r in records:
        s = r.get("status", "pendiente")
        counts[s] = counts.get(s, 0) + 1
    now = datetime.now().isoformat(timespec="minutes")
    lines = []
    lines.append("# Recommendations Dashboard")
    lines.append("")
    lines.append(f"**Generated**: {now}")
    lines.append(f"**Total recommendations**: {total}")
    lines.append("")
    lines.append("## Status Breakdown")
    lines.append("")
    lines.append("| Status | Count | % |")
    lines.append("|--------|-------|---|")
    for s in VALID_STATUSES:
        c = counts.get(s, 0)
        pct = round(c / total * 100, 1) if total else 0
        lines.append(f"| {s} | {c} | {pct}% |")
    lines.append("")
    pending = [r for r in records if r.get("status") == "pendiente"]
    if pending:
        lines.append("## Pending Recommendations")
        lines.append("")
        lines.append("| ID | Text | Context | Created |")
        lines.append("|----|------|---------|---------|")
        for r in pending[:20]:
            rid = r.get("id", "?")
            text = r.get("text", "")[:60]
            ctx = r.get("context", "")[:30]
            created = r.get("created_at", "")[:16]
            lines.append(f"| {rid} | {text} | {ctx} | {created} |")
        lines.append("")
    in_progress = [r for r in records if r.get("status") == "en_progreso"]
    if in_progress:
        lines.append("## In Progress")
        lines.append("")
        lines.append("| ID | Text | Updated |")
        lines.append("|----|------|---------|")
        for r in in_progress[:10]:
            rid = r.get("id", "?")
            text = r.get("text", "")[:60]
            updated = r.get("updated_at", "")[:16]
            lines.append(f"| {rid} | {text} | {updated} |")
        lines.append("")
    return "\n".join(lines)


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Recommendation Tracker — log and track strategic recommendations.",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog=(
            "Examples:\n"
            "  recommendation_tracker.py add \"Invertir en IA\" --context \"OKR Q3\"\n"
            "  recommendation_tracker.py list --status pendiente\n"
            "  recommendation_tracker.py update abc123 --status en_progreso\n"
            "  recommendation_tracker.py dashboard\n"
        ),
    )
    subparsers = parser.add_subparsers(dest="command", required=True)

    add_parser = subparsers.add_parser("add", help="Add a new recommendation")
    add_parser.add_argument("text", help="Recommendation text")
    add_parser.add_argument("--context", default="", help="Context where recommendation was made")
    add_parser.add_argument("--metadata", default="", help="Additional metadata")

    list_parser = subparsers.add_parser("list", help="List recommendations")
    list_parser.add_argument("--status", choices=VALID_STATUSES, help="Filter by status")

    update_parser = subparsers.add_parser("update", help="Update recommendation status")
    update_parser.add_argument("id", help="Recommendation ID")
    update_parser.add_argument("--status", choices=VALID_STATUSES, required=True, help="New status")

    dash_parser = subparsers.add_parser("dashboard", help="Generate markdown dashboard")
    dash_parser.add_argument("--output", help="Save dashboard to file")

    args = parser.parse_args()

    if args.command == "add":
        rid = add_recommendation(args.text, args.context, args.metadata)
        print(f"✓ Recommendation added: {rid}")

    elif args.command == "list":
        records = list_recommendations(args.status)
        if not records:
            print("No recommendations found.")
            return
        print(f"{'ID':<12} {'Status':<16} {'Text':<60} {'Created':<20}")
        print("-" * 110)
        for r in records:
            rid = r.get("id", "")[:10]
            status = r.get("status", "")
            text = r.get("text", "")[:58]
            created = r.get("created_at", "")[:19]
            print(f"{rid:<12} {status:<16} {text:<60} {created:<20}")

    elif args.command == "update":
        ok = update_status(args.id, args.status)
        if ok:
            print(f"✓ Recommendation {args.id} updated to '{args.status}'")

    elif args.command == "dashboard":
        dash = generate_dashboard()
        if args.output:
            Path(args.output).write_text(dash, encoding="utf-8")
            print(f"✓ Dashboard saved: {args.output}")
        else:
            print(dash)


if __name__ == "__main__":
    main()
