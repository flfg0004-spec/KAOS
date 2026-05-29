"""Verifica que todas las dependencias del ecosistema estén instaladas.

Uso: python agno_kaos/check_deps.py [--strict]
Exit code 0 = todo ok, 1 = faltan dependencias.
"""
import sys
import importlib.util
from pathlib import Path

REQUIRED = {
    "agno": "agno>=2.0.0",
    "yaml": "pyyaml>=6.0",
    "dotenv": "python-dotenv>=1.0.0",
    "fastapi": "fastapi>=0.110.0",
    "uvicorn": "uvicorn>=0.27.0",
    "mcp": "mcp>=1.0.0",
}

OPTIONAL = {
    "psycopg2": "psycopg2-binary>=2.9.0 (Postgres support)",
}


def check_module(name: str, pip_spec: str) -> bool:
    spec = importlib.util.find_spec(name)
    if spec is not None:
        print(f"  ✅ {name} ({pip_spec})")
        return True
    print(f"  ❌ {name} — NO INSTALADO. pip install {pip_spec}")
    return False


def main():
    strict = "--strict" in sys.argv
    print("=== A(gnO)-KAOS Dependency Check ===")
    print(f"Python: {sys.version}")

    print("\nRequired:")
    req_ok = all(check_module(name, spec) for name, spec in REQUIRED.items())

    if OPTIONAL:
        print("\nOptional:")
        opt_ok = all(check_module(name, spec) for name, spec in OPTIONAL.items())

    print("\nPackage:")
    try:
        import agno_kaos
        cfg = agno_kaos.load_config()
        print(f"  ✅ agno-kaos v{cfg.get('agentos', {}).get('version', '?')}")
        pkg_ok = True
    except ImportError as e:
        print(f"  ❌ agno_kaos: {e}")
        pkg_ok = False

    all_ok = req_ok and pkg_ok
    if strict:
        all_ok = all_ok and opt_ok

    print(f"\n{'✅ All checks passed' if all_ok else '❌ Some checks failed'}")
    return 0 if all_ok else 1


if __name__ == "__main__":
    sys.exit(main())
