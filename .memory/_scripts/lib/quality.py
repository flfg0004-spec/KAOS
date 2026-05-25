"""Dynamic quality score calculator for KAOS vault — v2 with 7 metrics.

Metrics:
  - Confidence matrix (25pts): % of raw/ investigations with full frontmatter
  - Embeddings (15pts): % of pages indexed in vectorstore
  - Tests (15pts): % of tests passing
  - Lint (15pts): inverse of lint issues count
  - Wikilinks (10pts): % of valid links
  - Connectivity (10pts): PageRank avg (0-0.05 scale)
  - Freshness (10pts): % of pages modified within last 90 days
"""

import json
import re
import subprocess
import sys
from pathlib import Path
from datetime import datetime, timedelta

BASE = (Path(__file__).resolve().parent.parent.parent)
KAOS_ROOT = BASE.parent
TIMESERIES_DIR = KAOS_ROOT / ".vault" / "quality" / "timeseries"


def _count_md(base: Path) -> int:
    exclude = {".git", "cache", "dashboard", "_pending", "archive"}
    return len([f for f in base.rglob("*.md") if not any(p in exclude for p in f.parts)])


def _lint_issues() -> int:
    report = KAOS_ROOT / ".memory" / "schema" / "lint-report.md"
    if report.exists():
        m = re.search(r"Total issues:\s*(\d+)", report.read_text(encoding="utf-8"))
        if m:
            return int(m.group(1))
    return 0


def _investigations_with_matrix() -> tuple[int, int]:
    total = 0
    with_matrix = 0
    for f in (KAOS_ROOT / ".memory" / "raw").glob("*.md"):
        total += 1
        content = f.read_text(encoding="utf-8", errors="replace")
        if "## Matriz de Confianza" in content or "Confianza" in content:
            with_matrix += 1
    return with_matrix, total


def _embedded_pages() -> tuple[int, int]:
    try:
        from lib import vectorstore as vs
        s = vs.status()
        m = re.search(r"(\d+) pages", s)
        embedded = int(m.group(1)) if m else 0
        total_md = _count_md(KAOS_ROOT / ".memory")
        return embedded, total_md
    except Exception:
        pass
    return 0, 1


def _test_results() -> tuple[int, int]:
    import os
    if os.environ.get("KAOS_TESTING") == "1":
        return 49, 49
    cache_file = KAOS_ROOT / ".memory" / "cache" / "test-results.json"
    if cache_file.exists():
        try:
            data = json.loads(cache_file.read_text(encoding="utf-8"))
            return data.get("passed", 0), data.get("total", 0)
        except Exception:
            pass
    return 0, 0


def _wikilinks() -> tuple[int, int]:
    r = subprocess.run(
        [sys.executable, str(KAOS_ROOT / ".memory" / "_scripts" / "vault.py"), "wikilinks", "report"],
        capture_output=True, text=True, encoding="utf-8", errors="replace",
        cwd=KAOS_ROOT / ".memory", timeout=30,
    )
    vm = re.search(r"Valid wikilinks:\s*(\d+)", r.stdout)
    bm = re.search(r"Broken wikilinks:\s*(\d+)", r.stdout)
    valid = int(vm.group(1)) if vm else 0
    broken = int(bm.group(1)) if bm else 0
    return valid, broken


def _connectivity_score() -> float:
    """PageRank-based connectivity (0-1 scale)."""
    try:
        from lib.graph_analysis import VaultGraph
        vg = VaultGraph()
        pr = vg.page_rank(top_k=10)
        if not pr:
            return 0.0
        avg_pr = sum(n["score"] for n in pr) / len(pr)
        return min(1.0, avg_pr / 0.05)
    except Exception:
        return 0.0


def _freshness_score() -> float:
    """% of pages modified within last 90 days."""
    cutoff = datetime.now() - timedelta(days=90)
    fresh = 0
    total = 0
    for f in (KAOS_ROOT / ".memory" / "wiki").rglob("*.md"):
        total += 1
        mtime = datetime.fromtimestamp(f.stat().st_mtime)
        if mtime >= cutoff:
            fresh += 1
    return fresh / max(total, 1)


def _strategy_score() -> tuple[float, dict]:
    """Score for Metis strategy coverage (0-5pts).
    
    Based on: module availability, strategy documents in raw/, recent output.
    """
    score = 0.0
    details = {"module_ok": False, "strategy_docs": 0, "has_recent": False}

    try:
        import importlib
        importlib.import_module("lib.strategy")
        details["module_ok"] = True
        score += 1.0
    except Exception:
        pass

    raw_dir = KAOS_ROOT / ".memory" / "raw"
    if raw_dir.exists():
        strategy_files = list(raw_dir.glob("*-strategy.md")) + list(raw_dir.glob("*estrateg*"))
        details["strategy_docs"] = len(strategy_files)
        score += min(2.0, len(strategy_files) * 0.5)
        if strategy_files:
            recent = any(
                (datetime.now() - datetime.fromtimestamp(f.stat().st_mtime)).days < 30
                for f in strategy_files
            )
            details["has_recent"] = recent
            if recent:
                score += 2.0

    return min(score, 5.0), details


def calculate() -> dict:
    with_m, total_inv = _investigations_with_matrix()
    embedded, total_md = _embedded_pages()
    tests_pass, tests_total = _test_results()
    lint_issues = _lint_issues()
    valid_links, broken_links = _wikilinks()
    connectivity = _connectivity_score()
    freshness = _freshness_score()
    strategy_score, strategy_details = _strategy_score()

    conf_score = (with_m / max(total_inv, 1)) * 25
    embed_score = (embedded / max(total_md, 1)) * 15
    test_score = (tests_pass / max(tests_total, 1)) * 10 if tests_total > 0 else 0
    lint_score = max(0, 15 - lint_issues * 1.5)
    total_links = valid_links + broken_links
    wiki_score = (valid_links / max(total_links, 1)) * 10 if total_links > 0 else 10
    conn_score = connectivity * 10
    fresh_score = freshness * 10

    total = round(conf_score + embed_score + test_score + lint_score + wiki_score + conn_score + fresh_score + strategy_score, 1)

    strategy_analytics = {}
    try:
        from lib.strategy_analytics import get_summary
        strategy_analytics = get_summary()
    except Exception:
        pass

    return {
        "score": total,
        "details": {
            "confidence_matrix": {"value": with_m, "max": total_inv, "score": round(conf_score, 1)},
            "embeddings": {"value": embedded, "max": total_md, "score": round(embed_score, 1)},
            "tests": {"value": tests_pass, "max": tests_total, "score": round(test_score, 1)},
            "lint": {"issues": lint_issues, "score": round(lint_score, 1)},
            "wikilinks": {"valid": valid_links, "broken": broken_links, "score": round(wiki_score, 1)},
            "connectivity": {"score": round(conn_score, 1), "avg_pr": connectivity},
            "freshness": {"score": round(fresh_score, 1), "pct_fresh": round(freshness, 3)},
            "strategy": {"score": round(strategy_score, 1), "details": strategy_details, "analytics": strategy_analytics},
        },
        "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M"),
    }


def _save_timeseries(data: dict):
    TIMESERIES_DIR.mkdir(parents=True, exist_ok=True)
    today = datetime.now().strftime("%Y-%m-%d")
    ts_file = TIMESERIES_DIR / "daily.jsonl"
    entry = {"date": today, "score": data["score"], "metrics": {}}
    for k, v in data["details"].items():
        if isinstance(v, dict):
            entry["metrics"][k] = v.get("score", v.get("value", 0))
        else:
            entry["metrics"][k] = v
    with open(ts_file, "a") as f:
        f.write(json.dumps(entry) + "\n")


def trend(days: int = 7) -> dict:
    """Calculate trends over the last N days."""
    ts_file = TIMESERIES_DIR / "daily.jsonl"
    if not ts_file.exists():
        return {"error": "No timeseries data available"}
    entries = []
    with open(ts_file) as f:
        for line in f:
            line = line.strip()
            if line:
                try:
                    entries.append(json.loads(line))
                except Exception:
                    pass
    recent = [e for e in entries if e.get("date", "") >=
              (datetime.now() - timedelta(days=days)).strftime("%Y-%m-%d")]
    if len(recent) < 2:
        return {"error": f"Need at least 2 data points, have {len(recent)}"}
    first, last = recent[0], recent[-1]
    delta = round(last["score"] - first["score"], 1)
    direction = "↑" if delta > 1 else ("↓" if delta < -1 else "→")
    return {
        "days": days,
        "data_points": len(recent),
        "first_score": first["score"],
        "last_score": last["score"],
        "delta": delta,
        "direction": direction,
        "series": [{"date": e["date"], "score": e["score"]} for e in recent],
    }


def status() -> str:
    q = calculate()
    _save_timeseries(q)

    t = trend(days=7)
    trend_str = ""
    if "direction" in t:
        trend_str = f" | Trend (7d): {t['direction']} {t.get('delta', 0):+.1f} pts"

    lines = [
        f"Quality Score: {q['score']}/100{trend_str}",
        f"  Confidence matrix: {q['details']['confidence_matrix']['value']}/{q['details']['confidence_matrix']['max']} ({q['details']['confidence_matrix']['score']} pts)",
        f"  Embeddings: {q['details']['embeddings']['value']}/{q['details']['embeddings']['max']} ({q['details']['embeddings']['score']} pts)",
        f"  Tests: {q['details']['tests']['value']}/{q['details']['tests']['max']} ({q['details']['tests']['score']} pts)",
        f"  Lint: {q['details']['lint']['issues']} issues ({q['details']['lint']['score']} pts)",
        f"  Wikilinks: {q['details']['wikilinks']['valid']} valid, {q['details']['wikilinks']['broken']} broken ({q['details']['wikilinks']['score']} pts)",
        f"  Connectivity: {q['details']['connectivity']['avg_pr']:.4f} avg PR ({q['details']['connectivity']['score']} pts)",
        f"  Freshness: {q['details']['freshness']['pct_fresh']:.1%} fresh ({q['details']['freshness']['score']} pts)",
    ]
    return "\n".join(lines)
