"""Auditor: pre/post snapshots, regression checks."""

from datetime import datetime
from lib import scanner, quality as quality_mod


def _count_md() -> int:
    from pathlib import Path
    v = Path(__file__).resolve().parent.parent.parent
    exclude = {".git", "cache", "dashboard", "_pending"}
    return len([f for f in v.rglob("*.md") if not any(p in exclude for p in f.parts)])


def pre_snapshot() -> dict:
    q = quality_mod.calculate()
    return {
        "dead_refs": len(scanner.dead_refs()),
        "duplicates": len(scanner.duplicates()),
        "orphans": len(scanner.orphans()),
        "stale": len(scanner.stale()),
        "pycache": len(scanner.pycache_dirs()),
        "deprecated_ps": len(scanner.deprecated_ps()),
        "total_md": _count_md(),
        "lint_issues": q["details"]["lint"]["issues"],
        "quality_score": q["score"],
        "timestamp": datetime.now().isoformat(),
    }


def post_check(snapshot: dict) -> dict:
    after = pre_snapshot()
    return {
        "dead_refs_fixed": snapshot["dead_refs"] - after["dead_refs"],
        "duplicates_fixed": snapshot["duplicates"] - after["duplicates"],
        "pycache_removed": snapshot["pycache"] - after["pycache"],
        "ps_removed": snapshot["deprecated_ps"] - after["deprecated_ps"],
        "lint_regression": after["lint_issues"] - snapshot["lint_issues"],
        "quality_delta": round(after["quality_score"] - snapshot["quality_score"], 1),
        "quality_before": snapshot["quality_score"],
        "quality_after": after["quality_score"],
    }


def report(snapshot: dict | None = None) -> str:
    snap = snapshot if snapshot else pre_snapshot()
    check = post_check(snap)
    lines = [
        f"Audit Report — {datetime.now().strftime('%Y-%m-%d %H:%M')}",
        f"  Dead refs: {snap['dead_refs']} → {snap['dead_refs'] - check['dead_refs_fixed']} (fixed: {check['dead_refs_fixed']})",
        f"  Duplicates: {snap['duplicates']} → {snap['duplicates'] - check['duplicates_fixed']} (fixed: {check['duplicates_fixed']})",
        f"  __pycache__: {snap['pycache']} → {snap['pycache'] - check['pycache_removed']} (removed: {check['pycache_removed']})",
        f"  Deprecated PS: {snap['deprecated_ps']} → {snap['deprecated_ps'] - check['ps_removed']} (removed: {check['ps_removed']})",
        f"  Quality: {check['quality_before']} → {check['quality_after']} (Δ {check['quality_delta']:+})",
        f"  Lint regression: {check['lint_regression']:+} issues",
    ]
    return "\n".join(lines)
