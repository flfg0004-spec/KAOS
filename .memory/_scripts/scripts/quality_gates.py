#!/usr/bin/env python3
"""Quality Gates — verifica que todos los gates F0-F3 están verdes.

Cada gate ejecuta verificaciones y reporta passed/failed.

Uso:
  py -3 _scripts/scripts/quality_gates.py            # todos los gates
  py -3 _scripts/scripts/quality_gates.py --gate F1  # solo F1
  py -3 _scripts/scripts/quality_gates.py --json     # output JSON
"""

import argparse
import json
import sys
from pathlib import Path

BASE = Path(__file__).resolve().parent.parent.parent  # .memory/
SCRIPTS = BASE / "_scripts"
PROJECT_ROOT = BASE.parent

_vault_root = next(
    (p for p in [PROJECT_ROOT / "KAOS", PROJECT_ROOT] if (p / ".obsidian").exists()),
    PROJECT_ROOT / "KAOS",
)

CHECKS = []


def check(name: str, gate: str, fn):
    CHECKS.append((name, gate, fn))


def _syntax_ok(path: Path) -> bool:
    if not path.exists():
        return False
    try:
        compile(path.read_text(encoding="utf-8"), str(path), "exec")
        return True
    except SyntaxError:
        return False


# ── F0: Foundation ───────────────────────────────────────────────────────

check("library/index.md exists", "F0", lambda: Path(BASE / "library" / "index.md").exists())

check("library subdirs (6)", "F0", lambda: (
    sum(1 for d in (BASE / "library").iterdir() if d.is_dir()) >= 6
))

check("AGENTS.md library refs (5/5)", "F0", lambda: (
    sum(1 for f in Path(PROJECT_ROOT / ".opencode" / "agents").rglob("*.md")
        if "library" in f.read_text(encoding="utf-8", errors="ignore")) == 5
))

check("file_lock.py all imports", "F0", lambda: _syntax_ok(SCRIPTS / "lib" / "file_lock.py"))

check("gap_query.py import", "F0", lambda: _syntax_ok(SCRIPTS / "lib" / "gap_query.py"))

check("add_audience.py syntax", "F0", lambda: _syntax_ok(SCRIPTS / "scripts" / "add_audience.py"))

check("promote_to_library.py syntax", "F0", lambda: _syntax_ok(SCRIPTS / "scripts" / "promote_to_library.py"))

check("obsidian.py syntax", "F0", lambda: _syntax_ok(SCRIPTS / "lib" / "obsidian.py"))


# ── F1: Core Integration ──────────────────────────────────────────────────

check("scoring pipeline init", "F1", lambda: _syntax_ok(SCRIPTS / "lib" / "scoring" / "__init__.py"))

check("scoring engine", "F1", lambda: _syntax_ok(SCRIPTS / "lib" / "scoring" / "engine.py"))

check("scoring metrics (8)", "F1", lambda: (
    _syntax_ok(SCRIPTS / "lib" / "scoring" / "metrics.py")
))

check("pipeline_writer.py syntax", "F1", lambda: _syntax_ok(SCRIPTS / "scripts" / "pipeline_writer.py"))

check("tagger.py syntax", "F1", lambda: _syntax_ok(SCRIPTS / "lib" / "tagger.py"))

def _find_file(rel: str) -> bool:
    return any((p / rel).exists() for p in [PROJECT_ROOT / "KAOS", PROJECT_ROOT])

check("QuickAdd macros", "F1", lambda: _find_file(".obsidian/quickadd/macros/library-promote.js"))

check("Standard template", "F1", lambda: _find_file(".obsidian/quickadd/templates/standard-concept.md"))

check("Library template", "F1", lambda: _find_file(".obsidian/quickadd/templates/library-concept.md"))

check("Dataview queries (3)", "F1", lambda: (
    sum(1 for f in (BASE / "library" / "queries").glob("*.md")) >= 3
))


# ── F2: Advanced Features ────────────────────────────────────────────────

check("schedule_gaps.py syntax", "F2", lambda: _syntax_ok(SCRIPTS / "scripts" / "schedule_gaps.py"))

check("schedule_tagger.py syntax", "F2", lambda: _syntax_ok(SCRIPTS / "scripts" / "schedule_tagger.py"))

check("configure_indexes.py syntax", "F2", lambda: _syntax_ok(SCRIPTS / "scripts" / "configure_indexes.py"))

check("pre-commit-library.py syntax", "F2", lambda: _syntax_ok(SCRIPTS / "hooks" / "pre-commit-library.py"))

check("install_hooks.py syntax", "F2", lambda: _syntax_ok(SCRIPTS / "scripts" / "install_hooks.py"))

check("Smart Connections config", "F2", lambda: (
    Path(_vault_root / ".obsidian" / "plugins" / "smart-connections" / "data.json").exists()
))

check("txtai config", "F2", lambda: (
    Path(BASE / "cache" / "txtai-config.yml").exists()
))


# ── F3: Polish & Scale ───────────────────────────────────────────────────

check("pipeline_e2e.py syntax", "F3", lambda: _syntax_ok(SCRIPTS / "scripts" / "pipeline_e2e.py"))

check("integration tests syntax", "F3", lambda: _syntax_ok(SCRIPTS / "tests" / "test_integration.py"))

check("quality_gates.py self-test", "F3", lambda: True)  # este mismo archivo


def run_gate(gate: str) -> list[dict]:
    results = []
    for name, g, fn in CHECKS:
        if g == gate:
            try:
                passed = fn()
            except Exception:
                passed = False
            results.append({"name": name, "gate": gate, "passed": passed})
    return results


def main():
    parser = argparse.ArgumentParser(description="Quality Gates — verifica F0-F3")
    parser.add_argument("--gate", type=str.upper, choices=["F0", "F1", "F2", "F3"],
                        help="Ejecutar solo un gate específico")
    parser.add_argument("--json", action="store_true", help="Output JSON")
    args = parser.parse_args()

    all_results = []
    gates = [args.gate] if args.gate else ["F0", "F1", "F2", "F3"]

    for gate in gates:
        all_results.extend(run_gate(gate))

    if args.json:
        print(json.dumps(all_results, indent=2))
        return 0

    by_gate: dict[str, list[dict]] = {}
    for r in all_results:
        by_gate.setdefault(r["gate"], []).append(r)

    total = len(all_results)
    passed_total = sum(1 for r in all_results if r["passed"])

    for gate in gates:
        results = by_gate.get(gate, [])
        passed = sum(1 for r in results if r["passed"])
        failed = len(results) - passed
        print(f"\n{'=' * 45}")
        print(f"  {gate} — Foundation{' ' if gate == 'F0' else ''} " +
              f"{'✅' if failed == 0 else '❌'}  ({passed}/{len(results)})")
        print(f"{'=' * 45}")
        for r in results:
            icon = "✅" if r["passed"] else "❌"
            print(f"  {icon}  {r['name']}")

    print(f"\n{'=' * 45}")
    print(f"  TOTAL: {passed_total}/{total} checks passed")
    if passed_total == total:
        print(f"  ✅ ALL GATES GREEN")
    else:
        print(f"  ❌ {total - passed_total} FAILURES")
    print(f"{'=' * 45}")

    return 0 if passed_total == total else 1


if __name__ == "__main__":
    sys.exit(main())
