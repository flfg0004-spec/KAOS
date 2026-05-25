#!/usr/bin/env python3
"""Ejecuta el ciclo completo de curaduría de Mnemosyne (14 fases).

Fases:
  1. Ingest    — detectar cambios nuevos
  2. Tag       — auto-tagging con LLM + embeddings (F1)
  3. Link      — wikilinks suggest con IA semántica (F3)
  4. Dedup     — detección multinivel + fusión (F4)
  5. Quality   — lint de raw/
  6. Compress  — comprimir log.md
  7. Index     — regenerar index.md
  8. Lint      — verificación final
  9. Graph     — análisis topológico del grafo (F2)
  10. Gaps     — knowledge gap detection (F5)
  11. Cross-Ref — búsqueda semántica
  12. Lifecycle — memory lifecycle eval (F6)
  13. Dashboard — health dashboard (F7)
  14. Report   — resumen final
"""

import subprocess
import sys
from datetime import datetime
from pathlib import Path

BASE = Path(__file__).resolve().parent.parent  # .memory/
SCRIPTS = BASE / "_scripts"
VAULT_PY = SCRIPTS / "vault.py"
TXTAI_PY = SCRIPTS / "mcp_txtai.py"
LOG = BASE / "wiki" / "log.md"
PY = sys.executable


def log(msg: str):
    entry = f"\n- {datetime.now().strftime('%Y-%m-%d %H:%M')} | curation | {msg} | mnemosyne"
    with open(LOG, "a") as f:
        f.write(entry)


def run(script: Path, *args: str) -> subprocess.CompletedProcess:
    cmd = [PY, str(script)] + list(args)
    return subprocess.run(cmd, capture_output=True, text=True, timeout=600)


def run_py(module_path: str, *args: str) -> subprocess.CompletedProcess:
    """Run a Python module directly."""
    return run(PY, str(SCRIPTS / module_path), *args)


def phase(label: str):
    print(f"\n── {label} ──")


# ── Fase 1: Ingest ──
phase("F1: Ingest — detectar cambios")
r = run(VAULT_PY, "extract", "--agent", "mnemosyne", "--summary", "curation-cycle")
print(f"  Ingest: {r.stdout[:200] if r.stdout else 'ok'}")

# ── Fase 2: Tag (F1) ──
phase("F2: Tag — auto-tagging con Gemini Flash")
r = run(VAULT_PY, "tag", "--all", "--dry-run")
print(f"  Tag: {r.stdout[:300] if r.stdout else 'ok'}")

# ── Fase 3: Link (F3) ──
phase("F3: Link — wikilinks suggest (semántico)")
r = run(VAULT_PY, "wikilinks", "suggest")
if r.returncode == 0 and r.stdout.strip():
    print(f"  Wikilinks sugeridos:\n{r.stdout[:500]}")

# ── Fase 4: Dedup (F4) ──
phase("F4: Dedup — multinivel + cristalización")
r = run(VAULT_PY, "dedup", "--min-confidence", "0.90")
print(f"  Dedup: {r.stdout[:300] if r.stdout else 'ok'}")

# ── Fase 5: Quality ──
phase("F5: Quality — lint raw/")
r = run(VAULT_PY, "lint")
print(f"  Quality: {r.stdout[:200] if r.stdout else 'ok'}")

# ── Fase 6: Compress ──
phase("F6: Compress — comprimir log")
r = run(VAULT_PY, "log")
print(f"  Compress: {r.stdout[:200] if r.stdout else 'ok'}")

# ── Fase 7: Index ──
phase("F7: Index — regenerar index.md")
r = run(VAULT_PY, "index")
print(f"  Index: {r.stdout[:200] if r.stdout else 'ok'}")

# ── Fase 8: Lint ──
phase("F8: Lint — verificación final")
r = run(VAULT_PY, "lint")
issues = -1
if r.stdout.strip():
    try:
        import json
        issues = json.loads(r.stdout).get("total_issues", -1)
    except Exception:
        import re
        m = re.search(r"Total issues:\s*(\d+)", r.stdout)
        if m:
            issues = int(m.group(1))
        else:
            issues = r.stdout.strip()[-50:]
print(f"  Lint: {issues} issues")

# ── Fase 9: Graph (F2) ──
phase("F9: Graph — análisis topológico del grafo")
r = run(VAULT_PY, "graph", "report")
print(f"  Graph:\n{r.stdout[:500] if r.stdout else 'ok'}")

# ── Fase 10: Gaps (F5) ──
phase("F10: Gaps — knowledge gap detection")
r = run(VAULT_PY, "gaps", "--report")
print(f"  Gaps: {r.stdout[:300] if r.stdout else 'ok'}")

# ── Fase 11: Cross-Ref ──
phase("F11: Cross-Ref — búsqueda semántica con embeddings")
r = run(PY, str(TXTAI_PY), "semantic_search", "", str(BASE / "wiki/concepts"), "5")
print(f"  Cross-Ref: {r.stdout[:200] if r.stdout else 'ok'}")

# ── Fase 12: Lifecycle (F6) ──
phase("F12: Lifecycle — memory lifecycle eval")
r = run(VAULT_PY, "lifecycle", "--status")
print(f"  Lifecycle: {r.stdout[:300] if r.stdout else 'ok'}")

# ── Fase 13: Dashboard (F7) ──
phase("F13: Dashboard — health dashboard")
r = run(VAULT_PY, "quality")
print(f"  Dashboard: {r.stdout[:300] if r.stdout else 'ok'}")

# ── Fase 14: Report ──
phase("F14: Report — resumen final")
summary = (
    f"Curación completa. Issues restantes: {issues}. "
    f"Fases: Ingest→Tag→Link→Dedup→Quality→Compress→Index→Lint→Graph→Gaps→CrossRef→Lifecycle→Dashboard"
)
log(summary)
print(f"\n✅ {summary}")
