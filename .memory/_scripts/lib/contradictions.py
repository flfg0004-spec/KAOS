"""Semantic contradiction detection between notes.

Pipeline:
  1. Find pairs with embedding similarity > 0.85
  2. Invoke Gemini Flash to classify: contradiction | complement | independent
  3. State machine: detected → under_review → resolved | false_positive
"""

import json
import re
from pathlib import Path
from datetime import datetime
from concurrent.futures import ThreadPoolExecutor, as_completed, TimeoutError

import lib.llm as llm
from lib.wikilinks import build_graph

BASE = (Path(__file__).resolve().parent.parent.parent)
PENDING_DIR = BASE / "_pending"
CONTRADICTIONS_FILE = PENDING_DIR / "contradictions.json"


def _read(path: Path) -> str:
    try:
        return path.read_text(encoding="utf-8", errors="replace")
    except Exception:
        return ""


def _get_embedding(text: str) -> list[float] | None:
    """Get embedding via mcp_embed subprocess."""
    import os
    if os.environ.get("KAOS_TESTING") == "1":
        return None
    import subprocess, sys as _sys
    mcp_embed = BASE / "_scripts" / "mcp_embed.py"
    req = json.dumps({
        "jsonrpc": "2.0", "id": 1, "method": "tools/call",
        "params": {"name": "embed", "arguments": {"texts": [text[:2000]]}}
    })
    try:
        r = subprocess.run(
            [_sys.executable, str(mcp_embed)],
            input=req, capture_output=True, text=True, timeout=15
        )
        if r.returncode == 0 and r.stdout.strip():
            resp = json.loads(r.stdout.strip())
            content = resp.get("result", {}).get("content", [])
            if content:
                vecs = json.loads(content[0]["text"])
                return vecs[0] if vecs else None
    except Exception:
        pass
    return None


def _cosine_sim(a: list[float], b: list[float]) -> float:
    import numpy as np
    a, b = np.array(a), np.array(b)
    return float(np.dot(a, b) / (np.linalg.norm(a) * np.linalg.norm(b) + 1e-10))


def _load_state() -> list[dict]:
    if CONTRADICTIONS_FILE.exists():
        try:
            raw = CONTRADICTIONS_FILE.read_text(encoding="utf-8", errors="replace")
            if not raw.strip():
                return []
            data = json.loads(raw)
            return data if isinstance(data, list) else []
        except (json.JSONDecodeError, Exception):
            import shutil
            corrupt = CONTRADICTIONS_FILE.with_suffix(".json.corrupt")
            shutil.copy2(str(CONTRADICTIONS_FILE), str(corrupt))
            return []
    return []


def _save_state(entries: list[dict]):
    PENDING_DIR.mkdir(parents=True, exist_ok=True)
    tmp = CONTRADICTIONS_FILE.with_suffix(".json.tmp")
    tmp.write_text(json.dumps(entries, ensure_ascii=False, indent=2), encoding="utf-8")
    tmp.replace(CONTRADICTIONS_FILE)


def detect() -> list[dict]:
    """Find candidate contradiction pairs via embedding similarity."""
    page_map = build_graph()
    names = [n for n in page_map if n not in {"index", "log"}]
    if len(names) < 2:
        return []

    contents = [page_map[n]["content"][:1500] for n in names]

    embeds = []
    for c in contents:
        e = _get_embedding(c)
        embeds.append(e)

    pairs = []
    for i in range(len(names)):
        for j in range(i + 1, len(names)):
            if embeds[i] is None or embeds[j] is None:
                continue
            sim = _cosine_sim(embeds[i], embeds[j])
            if sim > 0.85:
                pairs.append({
                    "file_a": names[i],
                    "file_b": names[j],
                    "similarity": round(sim, 3),
                })
    return pairs


def classify(pair: dict) -> dict:
    """Ask Gemini Flash to classify the relationship between two notes."""
    page_map = build_graph()
    a_name = pair["file_a"]
    b_name = pair["file_b"]
    ca = page_map.get(a_name, {}).get("content", "")[:2000]
    cb = page_map.get(b_name, {}).get("content", "")[:2000]

    if not ca or not cb:
        return {**pair, "verdict": "independent", "severity": "low", "evidence": []}

    prompt = (
        f"Analiza estas 2 notas de conocimiento:\n\n"
        f"--- NOTA A: {a_name} ---\n{ca}\n\n"
        f"--- NOTA B: {b_name} ---\n{cb}\n\n"
        "Determina la relación entre ellas. Responde SOLO con JSON:\n"
        '{"verdict": "contradiction|complement|independent", '
        '"severity": "high|medium|low", '
        '"evidence": ["frase de A que contradice/complementa a B", ...], '
        '"explanation": "breve explicacion"}'
    )

    try:
        response = llm.llm_call(
            prompt=prompt,
            system="Eres un analista de relaciones entre conceptos. Respondes solo JSON.",
            model="go-gemini-flash",
            temperature=0.1,
            max_tokens=500,
        )
        response = response.strip()
        if response.startswith("```"):
            response = response.split("\n", 1)[-1].rsplit("```", 1)[0]
        parsed = json.loads(response)
        if isinstance(parsed, dict) and "verdict" in parsed:
            return {
                **pair,
                "verdict": parsed["verdict"],
                "severity": parsed.get("severity", "low"),
                "evidence": parsed.get("evidence", []),
                "explanation": parsed.get("explanation", ""),
            }
    except Exception:
        pass

    return {**pair, "verdict": "independent", "severity": "low", "evidence": []}


def update_status(file_a: str, file_b: str, new_status: str) -> bool:
    """Transition a contradiction pair's status: detected → under_review → resolved | false_positive."""
    valid_statuses = {"detected", "under_review", "resolved", "false_positive"}
    if new_status not in valid_statuses:
        return False
    state = _load_state()
    for entry in state:
        if entry.get("file_a") == file_a and entry.get("file_b") == file_b:
            entry["status"] = new_status
            entry["updated_at"] = datetime.now().isoformat()
            _save_state(state)
            return True
    return False


def run_detection(dry_run: bool = True) -> list[dict]:
    """Full contradiction detection pipeline."""
    state = _load_state()
    existing_keys = set()
    for e in state:
        key = (e.get("file_a", ""), e.get("file_b", ""))
        existing_keys.add(key)

    candidates = detect()
    results = []
    for pair in candidates:
        key = (pair["file_a"], pair["file_b"])
        if key in existing_keys:
            continue
        classified = classify(pair)
        classified["status"] = "detected"
        classified["timestamp"] = datetime.now().isoformat()
        results.append(classified)

    if not dry_run:
        state.extend(results)
        _save_state(state)

    return results


def report() -> str:
    """Generate contradiction report for lint integration."""
    state = _load_state()
    active = [e for e in state if e.get("status") != "resolved"]
    contradictions = [e for e in active if e.get("verdict") == "contradiction"]
    complements = [e for e in active if e.get("verdict") == "complement"]

    lines = [
        "# Semantic Contradictions Report",
        f"*Generated: {datetime.now().strftime('%Y-%m-%d %H:%M')}*",
        "",
        f"**Contradictions:** {len(contradictions)}",
        f"**Complementary:** {len(complements)}",
        f"**Pending review:** {len(active)}",
        "",
    ]

    if contradictions:
        lines.append("## Contradictions\n")
        for c in contradictions[:20]:
            severity = c.get("severity", "low")
            icon = {"high": "🔴", "medium": "🟡", "low": "🟢"}.get(severity, "⚪")
            lines.append(f"{icon} **{c['file_a']}** ↔ **{c['file_b']}** (sim: {c.get('similarity', '?')})")
            if c.get("explanation"):
                lines.append(f"   → {c['explanation']}")
            if c.get("evidence"):
                for e in c["evidence"][:2]:
                    lines.append(f"   - \"{e[:120]}...\"")
        lines.append("")

    if complements:
        lines.append("## Complementary Pairs\n")
        for c in complements[:10]:
            lines.append(f"- **{c['file_a']}** ↔ **{c['file_b']}**")
            if c.get("explanation"):
                lines.append(f"  → {c['explanation']}")
        lines.append("")

    if not active:
        lines.append("No contradictions or complementary pairs detected.\n")

    lines.append("---")
    lines.append(f"**Total: {len(active)} active pairs** | {datetime.now().strftime('%Y-%m-%d %H:%M')}")
    return "\n".join(lines)
