"""Centralized path resolution for all KAOS scripts.

Usage:
    from lib.paths import PROJECT_ROOT, MEMORY_DIR, SCRIPTS_DIR, VAULT_ROOT, LIBRARY_DIR
"""

from pathlib import Path

_script = Path(__file__).resolve()
LIB_DIR = _script.parent                       # .memory/_scripts/lib/
SCRIPTS_DIR = LIB_DIR.parent                   # .memory/_scripts/
MEMORY_DIR = SCRIPTS_DIR.parent                # .memory/
PROJECT_ROOT = MEMORY_DIR.parent               # KAOS/

# Vault root (KAOS/ si existe, sino PROJECT_ROOT)
VAULT_ROOT = (
    PROJECT_ROOT / "KAOS"
    if (PROJECT_ROOT / "KAOS" / ".obsidian").exists()
    else PROJECT_ROOT
)

# Library output (KAOS/library/ o fallback a .memory/library/)
LIBRARY_DIR = (
    VAULT_ROOT / "library"
    if (VAULT_ROOT / "library").exists()
    else MEMORY_DIR / "library"
)
LIBRARY_DIR_LEGACY = MEMORY_DIR / "library"   # old location, backward compat

# Caches
CACHE_DIR = MEMORY_DIR / "cache"

# Hooks
HOOKS_DIR = SCRIPTS_DIR / "hooks"

# Scripts
SCRIPTS_SCRIPTS_DIR = SCRIPTS_DIR / "scripts"
