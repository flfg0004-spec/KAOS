#!/usr/bin/env python3
"""Ejecuta el ciclo completo de 8 fases de Mnemosyne."""

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


def phase(label: str):
    print(f"\n── {label} ──")


# Fase 1: Ingest
phase("F1: Ingest — detectar cambios")
run(VAULT_PY, "extract", "--agent", "mnemosyne")

# Fase 2: Link
phase("F2: Link — wikilinks suggest")
r = run(VAULT_PY, "wikilinks", "suggest")
if r.returncode == 0 and r.stdout.strip():
    print("  Wikilinks sugeridos:", r.stdout[:300])

# Fase 3: Dedup
phase("F3: Dedup — txtai + hash")
run(PY, str(TXTAI_PY), "deduplicate", str(BASE / "wiki/concepts"), "0.95")

# Fase 4: Quality
phase("F4: Quality — lint raw/")
run(VAULT_PY, "lint")

# Fase 5: Compress
phase("F5: Compress — comprimir log")
run(VAULT_PY, "log")

# Fase 6: Index
phase("F6: Index — regenerar index.md")
run(VAULT_PY, "index")

# Fase 7: Lint
phase("F7: Lint — verificación final")
r = run(VAULT_PY, "lint")
issues = -1
if r.stdout.strip():
    try:
        import json
        issues = json.loads(r.stdout).get("total_issues", -1)
    except Exception:
        issues = r.stdout.strip()[-50:]

# Fase 8: Cross-Ref
phase("F8: Cross-Ref — txtai search")
run(PY, str(TXTAI_PY), "semantic_search", "", str(BASE / "wiki/concepts"), "5")

log(f"Curación completa. Issues: {issues}")
print(f"\n✅ Curación finalizada. Issues restantes: {issues}")
