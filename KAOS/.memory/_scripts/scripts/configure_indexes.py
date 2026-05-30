#!/usr/bin/env python3
"""Configura índices separados para Smart Connections (usuario) y txtai (agentes).

Smart Connections index -> library/ (público, curado)
txtai index -> .memory/wiki/ + .memory/raw/ (agentes, técnico)

Uso:
  py -3 _scripts/scripts/configure_indexes.py --status        # ver estado
  py -3 _scripts/scripts/configure_indexes.py --setup         # crear configs
  py -3 _scripts/scripts/configure_indexes.py --setup --force # sobrescribir
"""

import argparse
import json
import sys
from pathlib import Path

from lib.paths import MEMORY_DIR, PROJECT_ROOT, VAULT_ROOT

_SCRIPTS_DIR = Path(__file__).resolve().parent.parent
BASE = _SCRIPTS_DIR.parent  # .memory/
PROJECT_ROOT = BASE.parent   # KAOS/

# Rutas de configuración
SMART_CONNECTIONS_DIR = PROJECT_ROOT / ".obsidian" / "plugins" / "smart-connections"
SMART_CONNECTIONS_CONFIG = SMART_CONNECTIONS_DIR / "data.json"
TXTAI_CONFIG = BASE / "cache" / "txtai-config.yml"


def _print_status():
    """Verifica y muestra estado de las configuraciones."""
    print("\n=== Index Configuration Status ===\n")

    # Smart Connections
    print("[Smart Connections (user index)]")
    if SMART_CONNECTIONS_CONFIG.exists():
        try:
            data = json.loads(SMART_CONNECTIONS_CONFIG.read_text(encoding="utf-8"))
            print(f"  ✅ Config exists: {SMART_CONNECTIONS_CONFIG}")
            print(f"  Index folder: {data.get('index_folder', 'N/A')}")
            print(f"  Embedding model: {data.get('embedding_model', 'N/A')}")
            print(f"  Auto-index: {data.get('auto_index', 'N/A')}")
        except (json.JSONDecodeError, Exception) as e:
            print(f"  ⚠️  Config exists but invalid: {e}")
    else:
        print(f"  ⚠️  Config not found: {SMART_CONNECTIONS_CONFIG}")

    if SMART_CONNECTIONS_DIR.exists():
        print(f"  Plugin directory: {SMART_CONNECTIONS_DIR}")
    else:
        print(f"  Plugin not installed (missing: {SMART_CONNECTIONS_DIR})")

    print()

    # txtai
    print("[txtai (agent index)]")
    if TXTAI_CONFIG.exists():
        content = TXTAI_CONFIG.read_text(encoding="utf-8")
        print(f"  ✅ Config exists: {TXTAI_CONFIG}")
        # Mostrar primeras líneas relevantes
        for line in content.splitlines():
            if line.strip().startswith("path:") or line.strip().startswith("  - path:"):
                print(f"  {line.strip()}")
    else:
        print(f"  ⚠️  Config not found: {TXTAI_CONFIG}")

    # Verificar directorios indexados
    print("\n[Indexed directories]")
    for d in [
        PROJECT_ROOT / ".memory" / "library",
        BASE / "wiki",
        BASE / "raw",
    ]:
        status = "✅" if d.exists() else "⚠️  missing"
        print(f"  {status} {d.relative_to(PROJECT_ROOT)}")

    print()


def _setup_smart_connections(force: bool = False):
    """Crea configuración para Smart Connections."""
    if SMART_CONNECTIONS_CONFIG.exists() and not force:
        print(f"  ⏭️  Smart Connections config exists (use --force to overwrite)")
        return

    SMART_CONNECTIONS_DIR.mkdir(parents=True, exist_ok=True)

    config = {
        "index_only_current_vault": True,
        "index_folder": ".memory/library",
        "embedding_model": "all-MiniLM-L6-v2",
        "chunk_size": 512,
        "excluded_folders": [".memory/_scripts", ".memory/cache", ".memory/raw"],
        "auto_index": True,
        "index_interval_minutes": 60,
    }

    SMART_CONNECTIONS_CONFIG.write_text(
        json.dumps(config, indent=2) + "\n", encoding="utf-8"
    )
    print(f"  ✅ Created: {SMART_CONNECTIONS_CONFIG}")
    print(f"     Index folder: .memory/library (público, curado)")
    print(f"     Excluded: _scripts, cache, raw")


def _setup_txtai(force: bool = False):
    """Crea configuración para txtai (índice de agentes)."""
    if TXTAI_CONFIG.exists() and not force:
        print(f"  ⏭️  txtai config exists (use --force to overwrite)")
        return

    TXTAI_CONFIG.parent.mkdir(parents=True, exist_ok=True)

    config = """# txtai configuration — agent memory index (wiki/ + raw/)
path: .memory/cache/txtai/
writable: true
embeddings:
  path: sentence-transformers/bge-small-en-v1.5
  content: true
  encodebatch: 8
indexes:
  - path: .memory/wiki/
  - path: .memory/raw/
"""

    TXTAI_CONFIG.write_text(config, encoding="utf-8")
    print(f"  ✅ Created: {TXTAI_CONFIG}")
    print(f"     Embeddings: sentence-transformers/bge-small-en-v1.5")
    print(f"     Indexes: wiki/ (conocimiento curado), raw/ (investigación)")
    print(f"     Writable: true")


def _print_summary(force: bool):
    """Muestra resumen de rutas indexadas."""
    print("\n=== Index Configuration Summary ===\n")

    print("Smart Connections (user):")
    print(f"  Config: {SMART_CONNECTIONS_CONFIG}")
    print(f"  Index:  .memory/library/")
    print(f"  Model:  all-MiniLM-L6-v2")
    print(f"  Scope:  contenido público y curado para el usuario")
    print()

    print("txtai (agents):")
    print(f"  Config: {TXTAI_CONFIG}")
    print(f"  Index:  .memory/cache/txtai/")
    print(f"  Model:  bge-small-en-v1.5")
    print(f"  Scope:  wiki/ (conocimiento) + raw/ (investigación)")
    print()

    # Verificar directorios reales
    if TXTAI_CONFIG.exists():
        txtai_dir = BASE / "cache" / "txtai"
        if txtai_dir.exists():
            n_embeddings = len(list(txtai_dir.rglob("config.json")))
            print(f"  txtai data directory: {txtai_dir} ({n_embeddings} embedding configs)")
        else:
            print(f"  txtai data directory: {txtai_dir} (will be created on first run)")

    print("Separation: library/ -> Smart Connections (user-facing), wiki/+raw/ -> txtai (agents)")
    print()


def main():
    parser = argparse.ArgumentParser(
        description="Configura índices separados para Smart Connections y txtai",
    )
    parser.add_argument("--status", action="store_true",
                        help="Ver estado actual de configuraciones")
    parser.add_argument("--setup", action="store_true",
                        help="Crear archivos de configuración")
    parser.add_argument("--force", action="store_true",
                        help="Sobrescribir configuraciones existentes")

    args = parser.parse_args()

    if args.status:
        _print_status()
        return

    if args.setup:
        print("=== Setting up Index Configurations ===\n")
        _setup_smart_connections(force=args.force)
        print()
        _setup_txtai(force=args.force)
        _print_summary(args.force)
        return

    # Sin flags: mostrar ayuda y estado
    parser.print_help()
    print()
    _print_status()


if __name__ == "__main__":
    main()
