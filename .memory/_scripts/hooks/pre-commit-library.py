#!/usr/bin/env python3
"""Pre-commit hook para library/ — verifica calidad antes de commit.

Se instala como git hook: .git/hooks/pre-commit

Verifica:
  1. Todos los archivos en library/ tienen audience: public|both
  2. Todos tienen frontmatter válido
  3. Ninguno tiene source_hash divergente

Uso:
  py -3 _scripts/hooks/pre-commit-library.py        # corre como hook
  py -3 _scripts/hooks/pre-commit-library.py --fix  # arregla automático
"""

import argparse
import hashlib
import re
import sys
from pathlib import Path

_SCRIPTS_DIR = Path(__file__).resolve().parent.parent
_LIB_DIR = _SCRIPTS_DIR / "lib"
if str(_LIB_DIR) not in sys.path:
    sys.path.insert(0, str(_SCRIPTS_DIR))

BASE = _SCRIPTS_DIR.parent.parent  # KAOS/
LIBRARY_DIR = BASE / "library"

errors = []
warnings = []


def _get_frontmatter(content: str) -> dict:
    """Extrae frontmatter YAML como dict simple (sin dependencia yaml)."""
    m = re.match(r"^---\s*\n(.*?)\n---", content, re.DOTALL)
    if not m:
        return {}
    fm = {}
    for line in m.group(1).split("\n"):
        if ":" in line:
            key, _, val = line.partition(":")
            fm[key.strip()] = val.strip()
    return fm


def _has_valid_frontmatter(content: str) -> bool:
    """Verifica que el contenido tenga frontmatter YAML válido (--- ... ---)."""
    return bool(re.match(r"^---\s*\n", content)) and "---" in content[3:]


def _compute_sha256(path: Path) -> str:
    """Calcula SHA256 del contenido actual del archivo."""
    content = path.read_bytes()
    return hashlib.sha256(content).hexdigest()


def check_file(path: Path, fix: bool = False) -> list[str]:
    """Verifica un archivo de library/ contra las reglas.

    Returns:
        Lista de errores encontrados (vacía si todo OK)
    """
    file_errors = []
    rel_path = path.relative_to(BASE)

    content = path.read_text(encoding="utf-8", errors="replace")

    # 1. Verificar frontmatter válido
    if not _has_valid_frontmatter(content):
        file_errors.append(f"{rel_path}: missing or invalid frontmatter (--- ... ---)")
        return file_errors

    fm = _get_frontmatter(content)

    # 2. Verificar audience
    audience = fm.get("audience", "").strip().lower()
    if audience not in ("public", "both"):
        if fix:
            # Arreglar automáticamente: añadir audience: public
            if "audience:" in content.split("---", 2)[1]:
                content = re.sub(
                    r"^audience:.*",
                    "audience: public",
                    content,
                    flags=re.MULTILINE,
                )
            else:
                # Insertar antes del cierre ---
                content = content.replace("---", "audience: public\n---", 1)
            path.write_text(content, encoding="utf-8")
            warnings.append(f"{rel_path}: audience fixed to 'public'")
        else:
            file_errors.append(
                f"{rel_path}: audience is '{audience}' (must be 'public' or 'both')"
            )

    # 3. Verificar source_hash si existe
    source_hash = fm.get("source_hash", "")
    if source_hash:
        current_hash = _compute_sha256(path)
        if source_hash != current_hash:
            file_errors.append(
                f"{rel_path}: source_hash mismatch "
                f"(expected {source_hash[:12]}..., got {current_hash[:12]}...)"
            )

    return file_errors


def scan_library(fix: bool = False) -> list[str]:
    """Escanea library/ recursivamente y verifica todos los *.md."""
    if not LIBRARY_DIR.exists():
        return [f"Library directory not found: {LIBRARY_DIR}"]

    all_errors = []
    md_files = sorted(LIBRARY_DIR.rglob("*.md"))

    if not md_files:
        warnings.append("No .md files found in library/")

    for path in md_files:
        file_errors = check_file(path, fix=fix)
        all_errors.extend(file_errors)

    return all_errors


def main():
    parser = argparse.ArgumentParser(
        description="Pre-commit hook para library/ — verifica calidad antes de commit",
    )
    parser.add_argument("--fix", action="store_true",
                        help="Arreglar automáticamente (audience -> public)")

    args = parser.parse_args()

    print("=== library/ Governance Check ===")

    all_errors = scan_library(fix=args.fix)

    if warnings:
        for w in warnings:
            print(f"  ⚠️  {w}")

    if all_errors:
        print(f"\n❌ {len(all_errors)} error(s) found:")
        for err in all_errors:
            print(f"  - {err}")
        print("\nFix errors and commit again.")
        print("Tip: use --fix to auto-fix audience field")
        sys.exit(1)
    else:
        print("  ✅ All files pass governance checks")
        print(f"  📁 {LIBRARY_DIR}")
        sys.exit(0)


if __name__ == "__main__":
    main()
