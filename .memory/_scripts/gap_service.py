"""Gap Detection Service — structured strategic gap detection for Metis.

Identifies knowledge gaps during strategic analysis, prioritizes them,
dispatches them to Aletheia via JSON contract, and tracks resolution status.

Usage:
    py -3 .memory/_scripts/gap_service.py detect <text>
    py -3 .memory/_scripts/gap_service.py prioritize <text>
    py -3 .memory/_scripts/gap_service.py dispatch <gaps_json>
    py -3 .memory/_scripts/gap_service.py track <gap_id> --status dispatched
    py -3 .memory/_scripts/gap_service.py list [--status open]
    py -3 .memory/_scripts/gap_service.py report
"""

import argparse
import json
import os
import re
import shutil
import sys
import time
from datetime import datetime, timedelta
from pathlib import Path
from uuid import uuid4

BASE_DIR = Path(__file__).resolve().parent.parent
CACHE_DIR = BASE_DIR / ".memory" / "cache" / "gaps"
CACHE_DIR.mkdir(parents=True, exist_ok=True)

VALID_STATUSES = ["open", "dispatched", "resolved", "stale"]
VALID_TRANSITIONS = {
    "open": ["dispatched", "stale"],
    "dispatched": ["resolved", "stale"],
    "resolved": [],
    "stale": ["open"],
}


class Gap:
    def __init__(self, question, context="", priority="media", source="", suggested_source=""):
        self.id = str(uuid4())[:8]
        self.question = question
        self.context = context
        self.priority = priority
        self.source = source
        self.suggested_source = suggested_source
        self.status = "open"
        self.created_at = datetime.now().isoformat()
        self.updated_at = self.created_at
        self.resolved_at = None
        self.resolution = None
        self.confidence = None

    def to_dict(self):
        return {
            "id": self.id,
            "question": self.question,
            "context": self.context,
            "priority": self.priority,
            "source": self.source,
            "suggested_source": self.suggested_source,
            "status": self.status,
            "created_at": self.created_at,
            "updated_at": self.updated_at,
            "resolved_at": self.resolved_at,
            "resolution": self.resolution,
            "confidence": self.confidence,
        }

    @classmethod
    def from_dict(cls, d):
        g = cls(d.get("question", ""))
        g.id = d.get("id", g.id)
        g.context = d.get("context", "")
        g.priority = d.get("priority", "media")
        g.source = d.get("source", "")
        g.suggested_source = d.get("suggested_source", "")
        g.status = d.get("status", "open")
        g.created_at = d.get("created_at", g.created_at)
        g.updated_at = d.get("updated_at", g.updated_at)
        g.resolved_at = d.get("resolved_at")
        g.resolution = d.get("resolution")
        g.confidence = d.get("confidence")
        return g


def _load_gaps() -> list[dict]:
    records = []
    for f in sorted(CACHE_DIR.glob("*.jsonl")):
        with open(f, encoding="utf-8") as fh:
            for line in fh:
                line = line.strip()
                if line:
                    records.append(json.loads(line))
    return records


def _save_gap(gap_dict: dict):
    today = datetime.now().strftime("%Y-%m-%d")
    filepath = CACHE_DIR / f"{today}.jsonl"
    with open(filepath, "a", encoding="utf-8") as f:
        f.write(json.dumps(gap_dict, ensure_ascii=False) + "\n")


def _rewrite_all(records: list[dict]):
    today = datetime.now().strftime("%Y-%m-%d")
    backup_dir = CACHE_DIR / "backup"
    backup_dir.mkdir(parents=True, exist_ok=True)
    for f in sorted(CACHE_DIR.glob("*.jsonl")):
        ts = datetime.fromtimestamp(f.stat().st_mtime).strftime("%Y%m%d_%H%M%S")
        shutil.copy2(f, backup_dir / f"{f.stem}_{ts}.jsonl")
    filepath = CACHE_DIR / f"{today}.jsonl"
    with open(filepath, "w", encoding="utf-8") as f:
        for rec in records:
            f.write(json.dumps(rec, ensure_ascii=False) + "\n")


RETRY_MAX_ATTEMPTS = 3
RETRY_BACKOFF = [1, 2, 4]
DISPATCH_TIMEOUT = 30
STALE_HOURS = 24


def retry_dispatch(gaps: list[Gap]) -> str | None:
    """Dispatch with retry and timeout. Returns dispatch file path or None."""
    for attempt in range(RETRY_MAX_ATTEMPTS):
        try:
            result = dispatch(gaps)
            return result
        except Exception as e:
            if attempt < RETRY_MAX_ATTEMPTS - 1:
                time.sleep(RETRY_BACKOFF[attempt])
            else:
                for g in gaps:
                    g.status = "stale"
                    g.updated_at = datetime.now().isoformat()
                    _save_gap(g.to_dict())
                return None


def auto_stale_gaps():
    """Auto-transition gaps dispatched > 24h to stale."""
    now = datetime.now()
    records = _load_gaps()
    changed = False
    for rec in records:
        if rec.get("status") == "dispatched":
            updated = datetime.fromisoformat(rec.get("updated_at", rec.get("created_at", now.isoformat())))
            if now - updated > timedelta(hours=STALE_HOURS):
                rec["status"] = "stale"
                rec["updated_at"] = now.isoformat()
                changed = True
    if changed:
        _rewrite_all(records)


def stale_alert() -> list[dict]:
    """Return stale gaps for alerting."""
    auto_stale_gaps()
    return [r for r in _load_gaps() if r.get("status") == "stale"]


def detect(text: str) -> list[Gap]:
    gaps = []
    patterns = [
        r"(?:necesitamos|required|need|falta|hace falta|desconocemos|no sabemos|unknown|gaps?)\s*:?\s*([^.\n]+)",
        r"\?\s*([^.\n]+(?:market share|cuota|tamaño|tam|ingresos|revenue|competencia|competitor)[^.\n]*)",
        r"(?:investigar|research|explore|analizar|investigate)\s+([^.\n]+)",
        r"(?:qué|cuál|who|what|which|how)\s+([^.\n]{10,})",
    ]
    for pattern in patterns:
        for match in re.finditer(pattern, text, re.IGNORECASE):
            question = match.group(1).strip()
            if len(question) < 10:
                continue
            priority = "media"
            if any(kw in question.lower() for kw in ["urgente", "crítico", "critical", "high priority", "bloqueante"]):
                priority = "alta"
            elif any(kw in question.lower() for kw in ["nice to have", "baja", "low", "eventual"]):
                priority = "baja"
            suggested = ""
            if any(kw in question.lower() for kw in ["competencia", "competitor", "market", "mercado"]):
                suggested = "exa-search, informes de industria"
            elif any(kw in question.lower() for kw in ["técnico", "technical", "código", "code"]):
                suggested = "código fuente, documentación técnica"
            gaps.append(Gap(question, "auto-detected", priority, "gap_service.detect", suggested))
    if not gaps:
        data = _try_parse_json(text)
        if data and isinstance(data, dict):
            for g in data.get("gaps", []):
                if isinstance(g, dict):
                    gaps.append(Gap(
                        g.get("question", ""),
                        g.get("context", ""),
                        g.get("priority", "media"),
                        "structured_input",
                        g.get("suggested_source", ""),
                    ))
    return gaps


def _try_parse_json(text: str):
    try:
        return json.loads(text)
    except json.JSONDecodeError:
        pass
    match = re.search(r"```json\s*\n(.*?)\n```", text, re.DOTALL)
    if match:
        try:
            return json.loads(match.group(1))
        except json.JSONDecodeError:
            pass
    return None


def prioritize(gaps: list[Gap], context: str = "") -> list[dict]:
    scored = []
    for gap in gaps:
        base = {"alta": 5, "media": 3, "baja": 1}.get(gap.priority, 3)
        urgency = 1
        if any(kw in gap.question.lower() for kw in ["urgente", "ahora", "inmediato", "bloquea"]):
            urgency = 3
        elif any(kw in gap.question.lower() for kw in ["próximo", "pronto", "this quarter"]):
            urgency = 2
        confidence = 0.8
        scored.append({
            "gap": gap.to_dict(),
            "rice_score": base * urgency * confidence,
            "priority_label": gap.priority,
            "suggested_source": gap.suggested_source,
        })
    scored.sort(key=lambda x: -x["rice_score"])
    return scored


def dispatch(gaps: list[Gap]) -> str:
    today = datetime.now().strftime("%Y-%m-%d")
    payload = {
        "type": "gap_detection",
        "session_id": today,
        "generated_at": datetime.now().isoformat(),
        "gaps": [
            {
                "question": g.question,
                "context": g.context,
                "priority": g.priority,
                "suggested_source": g.suggested_source or "",
            }
            for g in gaps
        ],
        "request": "Aletheia, investiga estos gaps y devuelve datos verificados",
    }
    dispatch_path = CACHE_DIR / f"dispatch_{today}.json"
    with open(dispatch_path, "w", encoding="utf-8") as f:
        json.dump(payload, f, ensure_ascii=False, indent=2)
    for g in gaps:
        g.status = "dispatched"
        g.updated_at = datetime.now().isoformat()
        _save_gap(g.to_dict())
    return str(dispatch_path)


def track(gap_id: str, new_status: str) -> bool:
    if new_status not in VALID_STATUSES:
        print(f"Error: Invalid status '{new_status}'. Valid: {', '.join(VALID_STATUSES)}", file=sys.stderr)
        return False
    records = _load_gaps()
    found = False
    for rec in records:
        if rec.get("id") == gap_id:
            current = rec.get("status", "open")
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
            if new_status == "resolved":
                rec["resolved_at"] = datetime.now().isoformat()
            found = True
            break
    if not found:
        print(f"Error: Gap '{gap_id}' not found", file=sys.stderr)
        return False
    _rewrite_all(records)
    return True


def list_gaps(status: str | None = None) -> list[dict]:
    records = _load_gaps()
    if status:
        records = [r for r in records if r.get("status") == status]
    return sorted(records, key=lambda r: r.get("created_at", ""), reverse=True)


def ingest_response(response_json: str) -> int:
    data = _try_parse_json(response_json)
    if not data:
        print("Error: Invalid JSON response", file=sys.stderr)
        return 0
    responses = data.get("responses", [])
    resolved = 0
    records = _load_gaps()
    for resp in responses:
        question = resp.get("question", "")
        for rec in records:
            if rec.get("question") == question and rec.get("status") in ("open", "dispatched"):
                rec["status"] = "resolved"
                rec["resolved_at"] = datetime.now().isoformat()
                rec["resolution"] = resp.get("answer", "")
                rec["confidence"] = {"alta": 0.9, "media": 0.6, "baja": 0.3}.get(resp.get("confidence", "media"), 0.5)
                rec["updated_at"] = datetime.now().isoformat()
                resolved += 1
                break
    if resolved:
        _rewrite_all(records)
    return resolved


def generate_report() -> str:
    records = _load_gaps()
    total = len(records)
    counts = {s: 0 for s in VALID_STATUSES}
    for r in records:
        s = r.get("status", "open")
        counts[s] = counts.get(s, 0) + 1

    now = datetime.now().isoformat(timespec="minutes")
    lines = []
    lines.append("# Strategic Gap Report")
    lines.append("")
    lines.append(f"**Generated**: {now}")
    lines.append(f"**Total gaps**: {total}")
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

    open_gaps = [r for r in records if r.get("status") == "open"]
    if open_gaps:
        lines.append("## Open Gaps")
        lines.append("")
        lines.append("| ID | Question | Priority | Context | Source |")
        lines.append("|----|----------|----------|---------|--------|")
        for r in open_gaps[:20]:
            lines.append(f"| {r.get('id','?')} | {r.get('question','')[:60]} | {r.get('priority','')} | {r.get('context','')[:30]} | {r.get('source','')[:20]} |")
        lines.append("")

    resolved = [r for r in records if r.get("status") == "resolved"]
    if resolved:
        lines.append("## Recently Resolved")
        lines.append("")
        lines.append("| ID | Question | Confidence | Resolved |")
        lines.append("|----|----------|------------|----------|")
        for r in resolved[-10:]:
            conf = r.get("confidence", "?")
            resolved_at = (r.get("resolved_at") or "")[:16]
            lines.append(f"| {r.get('id','?')} | {r.get('question','')[:60]} | {conf} | {resolved_at} |")
        lines.append("")

    lines.append("---")
    lines.append(f"**Total: {total} gaps** | **Open: {counts.get('open', 0)}** | **Resolved: {counts.get('resolved', 0)}**")
    return "\n".join(lines)


def main():
    parser = argparse.ArgumentParser(
        description="Strategic Gap Detection Service for Metis.",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog=(
            "Examples:\n"
            "  gap_service.py detect \"Necesitamos investigar el market share\"\n"
            "  gap_service.py prioritize \"text\"\n"
            "  gap_service.py dispatch '{\"gaps\": [...]}'\n"
            "  gap_service.py track abc123 --status dispatched\n"
            "  gap_service.py list --status open\n"
            "  gap_service.py ingest response.json\n"
            "  gap_service.py report\n"
        ),
    )
    subparsers = parser.add_subparsers(dest="command", required=True)

    detect_parser = subparsers.add_parser("detect", help="Detect gaps from text")
    detect_parser.add_argument("text", help="Analysis text to scan for gaps")

    prioritize_parser = subparsers.add_parser("prioritize", help="Prioritize gaps")
    prioritize_parser.add_argument("text", help="Text with gaps")
    prioritize_parser.add_argument("--context", default="", help="Strategic context")

    dispatch_parser = subparsers.add_parser("dispatch", help="Dispatch gaps to Aletheia")
    dispatch_parser.add_argument("gaps_json", help="JSON string or file with gaps")

    track_parser = subparsers.add_parser("track", help="Update gap status")
    track_parser.add_argument("gap_id", help="Gap ID")
    track_parser.add_argument("--status", choices=VALID_STATUSES, required=True, help="New status")

    list_parser = subparsers.add_parser("list", help="List gaps")
    list_parser.add_argument("--status", choices=VALID_STATUSES, help="Filter by status")

    ingest_parser = subparsers.add_parser("ingest", help="Ingest Aletheia response")
    ingest_parser.add_argument("response_file", help="Path to response JSON file")

    report_parser = subparsers.add_parser("report", help="Generate gap report")

    stale_parser = subparsers.add_parser("stale-alerts", help="List stale gaps and generate alerts")

    args = parser.parse_args()

    if args.command == "detect":
        gaps = detect(args.text)
        if not gaps:
            print("No gaps detected.")
            return
        for g in gaps:
            _save_gap(g.to_dict())
        print(f"✓ Detected {len(gaps)} gaps:")
        for g in gaps:
            print(f"  [{g.priority}] {g.id}: {g.question[:80]}")

    elif args.command == "prioritize":
        gaps = detect(args.text)
        scored = prioritize(gaps, args.context)
        print(f"{'ID':<12} {'Question':<60} {'RICE':<8} {'Priority':<10} {'Source':<20}")
        print("-" * 110)
        for s in scored:
            g = s["gap"]
            print(f"{g['id']:<12} {g['question'][:58]:<60} {s['rice_score']:<8.1f} {s['priority_label']:<10} {s['suggested_source'][:18]:<20}")

    elif args.command == "dispatch":
        data = _try_parse_json(args.gaps_json)
        if not data:
            path = Path(args.gaps_json)
            if path.exists():
                data = json.loads(path.read_text(encoding="utf-8"))
        if not data:
            print("Error: Could not parse gaps JSON", file=sys.stderr)
            return
        gaps_data = data if isinstance(data, list) else data.get("gaps", [])
        gaps = [Gap.from_dict(g) if isinstance(g, dict) else Gap(str(g)) for g in gaps_data]
        path = dispatch(gaps)
        print(f"✓ Dispatched {len(gaps)} gaps to Aletheia")
        print(f"  Dispatch file: {path}")

    elif args.command == "track":
        ok = track(args.gap_id, args.status)
        if ok:
            print(f"✓ Gap {args.gap_id} → '{args.status}'")

    elif args.command == "list":
        records = list_gaps(args.status)
        if not records:
            print("No gaps found.")
            return
        print(f"{'ID':<12} {'Question':<60} {'Priority':<10} {'Status':<12} {'Created':<20}")
        print("-" * 114)
        for r in records:
            print(f"{r.get('id',''):<12} {r.get('question','')[:58]:<60} {r.get('priority',''):<10} {r.get('status',''):<12} {r.get('created_at','')[:19]:<20}")

    elif args.command == "ingest":
        path = Path(args.response_file)
        if not path.exists():
            print(f"Error: File not found: {args.response_file}", file=sys.stderr)
            return
        text = path.read_text(encoding="utf-8")
        count = ingest_response(text)
        print(f"✓ Resolved {count} gaps from Aletheia response")

    elif args.command == "report":
        print(generate_report())

    elif args.command == "stale-alerts":
        alerts = stale_alert()
        if not alerts:
            print("✓ No stale gaps found.")
            return
        print(f"⚠️  {len(alerts)} stale gap(s) found:")
        for r in alerts:
            age = datetime.now() - datetime.fromisoformat(r.get("updated_at", r.get("created_at", datetime.now().isoformat())))
            print(f"  {r.get('id','')}: {r.get('question','')[:60]} (age: {age.days}d {age.seconds//3600}h)")
        print("\nRun 'gap_service.py track <id> --status open' to re-open a stale gap.")


if __name__ == "__main__":
    main()
