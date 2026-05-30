"""MnemoBEAM — Mnemosyne Curation Quality Benchmark.

Mide el impacto de cada ciclo de curaduría con métricas pre/post:
- Wikilink coverage
- Gap resolution rate
- Contradiction resolution rate
- Freshness score
- Connectivity score
- Overall vault health delta

Output: JSON con scores pre, post, y delta.
"""

from __future__ import annotations

import json
import re
from datetime import datetime, timedelta
from pathlib import Path

BASE = Path(__file__).resolve().parent.parent.parent
KAOS_ROOT = BASE.parent
QUALITY_DIR = KAOS_ROOT / ".vault" / "quality"
TIMESERIES_DIR = QUALITY_DIR / "timeseries"
WIKI = BASE / "wiki"
RAW = BASE / "raw"
CONCEPTS = WIKI / "concepts"
SCORES_FILE = QUALITY_DIR / "mnemobeam-scores.json"
HISTORY_FILE = TIMESERIES_DIR / "mnemobeam-history.jsonl"


def _count_md(dir: Path) -> int:
    return len(list(dir.rglob("*.md")))


def _wikilink_coverage() -> float:
    """% de archivos en concepts/ con al menos un [[wikilink]]"""
    files = list(CONCEPTS.rglob("*.md"))
    if not files:
        return 0.0
    linked = 0
    for f in files:
        content = f.read_text(encoding="utf-8", errors="replace")
        if "[[" in content:
            linked += 1
    return round(linked / len(files), 4)


def _wikilink_density() -> float:
    """Promedio de wikilinks por archivo en concepts/"""
    files = list(CONCEPTS.rglob("*.md"))
    if not files:
        return 0.0
    total_links = 0
    for f in files:
        content = f.read_text(encoding="utf-8", errors="replace")
        total_links += content.count("[[")
    return round(total_links / len(files), 2)


def _freshness(days: int = 90) -> float:
    """% de archivos modificados en los últimos N días"""
    files = list(WIKI.rglob("*.md"))
    if not files:
        return 0.0
    cutoff = datetime.now() - timedelta(days=days)
    fresh = sum(1 for f in files if datetime.fromtimestamp(f.stat().st_mtime) > cutoff)
    return round(fresh / len(files), 4)


def _connectivity() -> float:
    """Score de conectividad basado en: % de archivos con wikilinks entrantes"""
    files = list(WIKI.rglob("*.md"))
    if not files:
        return 0.0
    all_content = ""
    for f in files:
        all_content += f.read_text(encoding="utf-8", errors="replace") + "\n"
    linked = 0
    for f in files:
        name = f.stem
        if f"[[{name}" in all_content or f"[[{name.lower()}" in all_content.lower():
            linked += 1
    return round(linked / len(files), 4)


def _lint_issues() -> int:
    report = KAOS_ROOT / ".memory" / "schema" / "lint-report.md"
    if report.exists():
        m = re.search(r"Total issues:\s*(\d+)", report.read_text(encoding="utf-8"))
        if m:
            return int(m.group(1))
    return 0


def _gap_count() -> int:
    """Cuenta gaps detectados en el último reporte."""
    report_dir = KAOS_ROOT / ".vault" / "quality" / "reports"
    gap_files = list(report_dir.glob("*gap*"))
    total = 0
    for f in gap_files:
        if f.suffix == ".json":
            try:
                data = json.loads(f.read_text(encoding="utf-8"))
                total += len(data.get("gaps", []))
            except Exception:
                pass
    return total


def _orphan_ratio() -> float:
    """% de archivos en concepts/ sin wikilinks entrantes ni salientes."""
    files = list(CONCEPTS.rglob("*.md"))
    if not files:
        return 0.0
    orphan = 0
    for f in files:
        content = f.read_text(encoding="utf-8", errors="replace")
        has_out = "[[" in content
        name = f.stem
        has_in = any(name in other.read_text(encoding="utf-8", errors="replace") for other in files if other != f)
        if not has_out and not has_in:
            orphan += 1
    return round(orphan / len(files), 4)


def _contradiction_count() -> int:
    """Cuenta contradicciones detectadas."""
    report = KAOS_ROOT / ".vault" / "quality" / "contradictions-report.json"
    if report.exists():
        try:
            data = json.loads(report.read_text(encoding="utf-8"))
            return len(data.get("contradictions", data.get("clusters", [])))
        except Exception:
            pass
    return 0


def score() -> dict:
    """Calcula el score actual de MnemoBEAM (8 dimensiones)."""
    wc = _wikilink_coverage()
    wd = _wikilink_density()
    fr = _freshness()
    cn = _connectivity()
    li = _lint_issues()
    gc = _gap_count()
    cc = _contradiction_count()
    orp = _orphan_ratio()

    lint_penalty = min(li / 50, 1.0)
    gap_penalty = min(gc / 10, 1.0)
    contra_penalty = min(cc / 5, 1.0)

    wd_norm = min(wd / 10, 1.0)
    orp_penalty = min(orp * 2, 1.0)

    overall = round(
        wc * 0.20  # wikilink coverage: 20%
        + wd_norm * 0.10  # wikilink density: 10%
        + fr * 0.15  # freshness: 15%
        + cn * 0.15  # connectivity: 15%
        + (1 - orp_penalty) * 0.10  # orphan ratio: 10%
        + (1 - lint_penalty) * 0.10  # lint: 10%
        + (1 - gap_penalty) * 0.10  # gaps: 10%
        + (1 - contra_penalty) * 0.10,  # contradictions: 10%
        4,
    )

    return {
        "timestamp": datetime.now().isoformat(),
        "overall": overall,
        "dimensions": {
            "wikilink_coverage": wc,
            "wikilink_density": wd,
            "freshness": fr,
            "connectivity": cn,
            "orphan_ratio": orp,
            "lint_issues": li,
            "gaps": gc,
            "contradictions": cc,
        },
        "penalties": {
            "lint": lint_penalty,
            "gaps": gap_penalty,
            "contradictions": contra_penalty,
        },
    }


def save(s: dict) -> None:
    """Guarda score actual y lo añade al historial."""
    QUALITY_DIR.mkdir(parents=True, exist_ok=True)
    SCORES_FILE.write_text(json.dumps(s, indent=2, ensure_ascii=False), encoding="utf-8")

    TIMESERIES_DIR.mkdir(parents=True, exist_ok=True)
    entry = json.dumps({"ts": s["timestamp"], "overall": s["overall"]})
    with open(HISTORY_FILE, "a") as f:
        f.write(entry + "\n")


def delta(pre: dict, post: dict) -> dict:
    """Calcula la mejora (delta) entre pre y post curación."""
    d = {
        "timestamp": datetime.now().isoformat(),
        "overall_delta": round(post["overall"] - pre["overall"], 4),
        "overall_before": pre["overall"],
        "overall_after": post["overall"],
        "dimension_deltas": {},
    }
    for dim in pre["dimensions"]:
        before = pre["dimensions"][dim]
        after = post["dimensions"].get(dim, before)
        d["dimension_deltas"][dim] = round(after - before, 4)
    return d


if __name__ == "__main__":
    import sys

    cmd = sys.argv[1] if len(sys.argv) > 1 else "score"

    if cmd == "score":
        s = score()
        save(s)
        print(f"MnemoBEAM: {s['overall']:.3f}")
        for dim, val in s["dimensions"].items():
            print(f"  {dim}: {val}")
    elif cmd == "history":
        if HISTORY_FILE.exists():
            for line in HISTORY_FILE.read_text().strip().split("\n"):
                data = json.loads(line)
                print(f"  {data['ts'][:10]}  {data['overall']:.3f}")
    elif cmd == "trend":
        if HISTORY_FILE.exists():
            lines = HISTORY_FILE.read_text().strip().split("\n")
            if len(lines) >= 2:
                first = json.loads(lines[0])
                last = json.loads(lines[-1])
                trend = last["overall"] - first["overall"]
                print(f"Trend ({len(lines)} samples): {trend:+.4f}")
                print(f"  First: {first['overall']:.4f}")
                print(f"  Last:  {last['overall']:.4f}")
