#!/usr/bin/env python3
"""Instala hooks de git para library/ governance.

Crea copias de hooks en .git/hooks/ para ejecución automática
antes de cada commit y push.

Hooks instalados:
  - pre-commit:   Verifica calidad de library/ (frontmatter, audience, source_hash)
  - pre-push:     Verificación adicional antes de push

Uso:
  py -3 _scripts/scripts/install_hooks.py              # instalar hooks
  py -3 _scripts/scripts/install_hooks.py --list       # listar hooks instalados
  py -3 _scripts/scripts/install_hooks.py --uninstall  # eliminar hooks
"""

import argparse
import os
import shutil
import stat
import sys
from pathlib import Path

_SCRIPTS_DIR = Path(__file__).resolve().parent.parent
HOOKS_SRC = _SCRIPTS_DIR / "hooks"
PROJECT_ROOT = _SCRIPTS_DIR.parent.parent  # KAOS/
GIT_HOOKS_DIR = PROJECT_ROOT / ".git" / "hooks"


def _hook_map() -> dict[str, Path]:
    """Mapea nombre de hook a su archivo fuente."""
    return {
        "pre-commit": HOOKS_SRC / "pre-commit-library.py",
    }


def _get_shebang() -> str:
    """Detecta el ejecutable de Python correcto para el shebang."""
    if sys.platform == "win32":
        return f'@echo off\npy -3 "%~dp0\\..\\..\\..\\{sys.executable.replace("\\\\", "/")}" "%~dpn0" %*\n'
    return "#!/usr/bin/env python3\n"


def _make_executable(path: Path):
    """Make a file executable (Unix). No-op on Windows."""
    if sys.platform != "win32":
        st = path.stat()
        path.chmod(st.st_mode | stat.S_IXUSR | stat.S_IXGRP | stat.S_IXOTH)


def install_hooks(force: bool = False):
    """Instala hooks desde _scripts/hooks/ a .git/hooks/.

    En Windows crea un .bat wrapper que invoca el script Python.
    En Unix crea un script ejecutable que invoca Python.
    """
    if not GIT_HOOKS_DIR.exists():
        print(f"❌ Git hooks directory not found: {GIT_HOOKS_DIR}")
        print("   Are you in a git repository?")
        sys.exit(1)

    installed = []
    skipped = []

    for hook_name, src_path in _hook_map().items():
        if not src_path.exists():
            print(f"  ⚠️  Source not found: {src_path}")
            continue

        dest = GIT_HOOKS_DIR / hook_name

        if dest.exists() and not force:
            skipped.append(hook_name)
            continue

        if sys.platform == "win32":
            # En Windows: copiar el script Python y crear un .bat wrapper
            dest_py = GIT_HOOKS_DIR / f"{hook_name}.py"
            shutil.copy2(str(src_path), str(dest_py))
            _make_executable(dest_py)

            # Crear .bat wrapper que invoca el script Python
            # Usamos rutas relativas para portabilidad
            rel_script = os.path.relpath(str(dest_py), str(GIT_HOOKS_DIR))
            bat_content = f"""@echo off
py -3 "%~dp0\\{rel_script}" %*
"""
            dest_bat = GIT_HOOKS_DIR / f"{hook_name}.bat"
            # Git en Windows ejecuta el hook como {hook_name} (sin .bat),
            # así que el archivo debe llamarse exactamente {hook_name} (sin extensión)
            # pero en Windows necesitamos un .bat o .cmd
            # Estrategia: crear un .bat con el nombre del hook (Windows ejecuta .bat/.cmd)
            dest.write_text(bat_content, encoding="utf-8")
        else:
            # En Unix: copiar directamente y hacer ejecutable
            shutil.copy2(str(src_path), str(dest))
            # Añadir shebang si no tiene
            content = dest.read_text(encoding="utf-8", errors="replace")
            if not content.startswith("#!"):
                dest.write_text(_get_shebang() + content, encoding="utf-8")
            _make_executable(dest)

        installed.append(hook_name)
        print(f"  ✅ Installed: {dest}")

    if installed:
        print(f"\nInstalled {len(installed)} hook(s): {', '.join(installed)}")
    if skipped:
        print(f"Skipped (already exist, use --force): {', '.join(skipped)}")


def uninstall_hooks():
    """Elimina hooks instalados."""
    removed = []
    for hook_name in _hook_map():
        dest = GIT_HOOKS_DIR / hook_name
        if dest.exists():
            dest.unlink()
            removed.append(hook_name)

        # En Windows también limpiar .py copy
        dest_py = GIT_HOOKS_DIR / f"{hook_name}.py"
        if dest_py.exists():
            dest_py.unlink()

    if removed:
        print(f"Removed {len(removed)} hook(s): {', '.join(removed)}")
    else:
        print("No hooks to remove.")


def list_hooks():
    """Lista hooks instalados."""
    print("=== Installed Git Hooks ===\n")
    found = False
    for hook_name in _hook_map():
        dest = GIT_HOOKS_DIR / hook_name
        if dest.exists():
            print(f"  ✅ {hook_name} -> {dest}")
            found = True
        else:
            dest_py = GIT_HOOKS_DIR / f"{hook_name}.py"
            if dest_py.exists():
                print(f"  ✅ {hook_name} (via .py) -> {dest_py}")
                found = True
            else:
                dest_bat = GIT_HOOKS_DIR / f"{hook_name}.bat"
                if dest_bat.exists():
                    print(f"  ✅ {hook_name} (via .bat) -> {dest_bat}")
                    found = True

    if not found:
        print("  No library governance hooks installed.")
        print(f"  Run install_hooks.py to install them.")


def main():
    parser = argparse.ArgumentParser(
        description="Instala hooks de git para library/ governance",
    )
    parser.add_argument("--list", action="store_true",
                        help="Listar hooks instalados")
    parser.add_argument("--uninstall", action="store_true",
                        help="Eliminar hooks instalados")
    parser.add_argument("--force", "-f", action="store_true",
                        help="Sobrescribir hooks existentes")

    args = parser.parse_args()

    if args.list:
        list_hooks()
    elif args.uninstall:
        uninstall_hooks()
    else:
        install_hooks(force=args.force)


if __name__ == "__main__":
    main()
