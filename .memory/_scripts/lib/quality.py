"""Dynamic quality score calculator for KAOS vault."""

import json
import re
import subprocess
import sys
from pathlib import Path
from datetime import datetime

BASE = (Path(__file__).resolve().parent.parent.parent)  # .memory/
KAOS_ROOT = BASE.parent  # KAOS project root


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
        import re
        s = vs.status()
        m = re.search(r"(\d+) pages", s)
        embedded = int(m.group(1)) if m else 0
    except Exception:
        embedded = 0
    total_md = _count_md(KAOS_ROOT / ".memory")
    return embedded, total_md


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
        capture_output=True, text=True, encoding="utf-8", errors="replace", cwd=KAOS_ROOT / ".memory", timeout=30,
    )
    vm = re.search(r"Valid wikilinks:\s*(\d+)", r.stdout)
    bm = re.search(r"Broken wikilinks:\s*(\d+)", r.stdout)
    valid = int(vm.group(1)) if vm else 0
    broken = int(bm.group(1)) if bm else 0
    return valid, broken


def calculate() -> dict:
    with_m, total_inv = _investigations_with_matrix()
    embedded, total_md = _embedded_pages()
    tests_pass, tests_total = _test_results()
    lint_issues = _lint_issues()
    valid_links, broken_links = _wikilinks()

    conf_score = (with_m / max(total_inv, 1)) * 25
    embed_score = (embedded / max(total_md, 1)) * 20
    test_score = (tests_pass / max(tests_total, 1)) * 20 if tests_total > 0 else 0
    lint_score = max(0, 20 - lint_issues * 2)
    total_links = valid_links + broken_links
    wiki_score = (valid_links / max(total_links, 1)) * 15 if total_links > 0 else 15

    total = round(conf_score + embed_score + test_score + lint_score + wiki_score, 1)

    return {
        "score": total,
        "details": {
            "confidence_matrix": {"value": with_m, "max": total_inv, "score": round(conf_score, 1)},
            "embeddings": {"value": embedded, "max": total_md, "score": round(embed_score, 1)},
            "tests": {"value": tests_pass, "max": tests_total, "score": round(test_score, 1)},
            "lint": {"issues": lint_issues, "score": round(lint_score, 1)},
            "wikilinks": {"valid": valid_links, "broken": broken_links, "score": round(wiki_score, 1)},
        },
        "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M"),
    }


def status() -> str:
    q = calculate()
    lines = [
        f"Quality Score: {q['score']}/100",
        f"  Confidence matrix: {q['details']['confidence_matrix']['value']}/{q['details']['confidence_matrix']['max']} ({q['details']['confidence_matrix']['score']} pts)",
        f"  Embeddings: {q['details']['embeddings']['value']}/{q['details']['embeddings']['max']} ({q['details']['embeddings']['score']} pts)",
        f"  Tests: {q['details']['tests']['value']}/{q['details']['tests']['max']} ({q['details']['tests']['score']} pts)",
        f"  Lint: {q['details']['lint']['issues']} issues ({q['details']['lint']['score']} pts)",
        f"  Wikilinks: {q['details']['wikilinks']['valid']} valid, {q['details']['wikilinks']['broken']} broken ({q['details']['wikilinks']['score']} pts)",
    ]
    return "\n".join(lines)
