#!/usr/bin/env python3
"""Regenera requirements-lock.txt desde el entorno actual.

Uso:
    python scripts/freeze-deps.py

El script lee requirements.txt, ejecuta pip freeze y filtra solo los paquetes
que están declarados en requirements.txt, escribiendo las versiones exactas
en requirements-lock.txt (en el mismo directorio que requirements.txt).

Requires:
    - Python 3.10+
    - pip
    - El entorno virtual debe tener instalados los paquetes deseados.
"""

import re
import subprocess
import sys
from pathlib import Path


def find_requirements_txt() -> Path:
    """Busca requirements.txt en ubicaciones conocidas del proyecto."""
    project_root = Path(__file__).resolve().parent.parent
    candidates = [
        project_root / ".memory" / "_scripts" / "requirements.txt",
        project_root / "requirements.txt",
    ]
    for path in candidates:
        if path.exists():
            return path
    raise FileNotFoundError(
        "No se encontró requirements.txt en ninguna ubicación conocida. "
        "Busqué: " + ", ".join(str(p) for p in candidates)
    )


def parse_requirements(req_path: Path) -> set[str]:
    """Extrae nombres de paquetes desde requirements.txt (sin versiones)."""
    packages: set[str] = set()
    with open(req_path, encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            # Saltar comentarios y líneas vacías
            if not line or line.startswith("#") or line.startswith("-"):
                continue
            # Extraer nombre base: "pkg>=1.0" → "pkg", "pkg==1.0" → "pkg"
            pkg = re.split(r"[>=<~!]", line)[0].strip()
            # Saltar opciones tipo -r, --index-url, etc.
            if pkg.startswith("-"):
                continue
            packages.add(pkg)
    return packages


def get_frozen_deps() -> list[str]:
    """Ejecuta pip freeze y devuelve lista de dependencias."""
    result = subprocess.run(
        [sys.executable, "-m", "pip", "freeze"],
        capture_output=True,
        text=True,
        check=True,
    )
    deps = [line.strip() for line in result.stdout.strip().split("\n") if line.strip()]
    return deps


def filter_deps(frozen: list[str], allowed: set[str]) -> list[str]:
    """Filtra solo los paquetes que están en el set permitido (case-insensitive)."""
    allowed_lower = {p.lower() for p in allowed}
    filtered: list[str] = []
    for dep in frozen:
        pkg = dep.split("==")[0].split("@")[0].strip()
        if pkg.lower() in allowed_lower:
            filtered.append(dep)
    return filtered


def find_missing_packages(frozen: list[str], allowed: set[str]) -> set[str]:
    """Detecta paquetes declarados en requirements.txt pero no instalados."""
    frozen_lower = {dep.split("==")[0].split("@")[0].strip().lower() for dep in frozen}
    return {p for p in allowed if p.lower() not in frozen_lower}


def write_lockfile(deps: list[str], lock_path: Path) -> None:
    """Escribe el lockfile con header y dependencias ordenadas."""
    with open(lock_path, "w", encoding="utf-8") as f:
        f.write("# Auto-generated lockfile — regenerar con scripts/freeze-deps.py\n")
        f.write(f"# Generado: Python {sys.version.split()[0]} | pip freeze\n")
        f.write(f"# Fuente: {lock_path.name}\n\n")
        for dep in sorted(deps):
            f.write(dep + "\n")
    print(f"[OK] Lockfile escrito: {lock_path.resolve()}")
    print(f"     {len(deps)} dependencias congeladas.")


def main() -> None:
    req_path = find_requirements_txt()
    print(f"[INFO] Leyendo: {req_path.resolve()}")

    allowed = parse_requirements(req_path)
    print(f"[INFO] {len(allowed)} paquetes declarados en requirements.txt")

    print("[INFO] Ejecutando pip freeze...")
    frozen = get_frozen_deps()
    print(f"[INFO] {len(frozen)} dependencias totales en el entorno")

    filtered = filter_deps(frozen, allowed)
    missing = find_missing_packages(frozen, allowed)
    if missing:
        print(f"[WARN] Paquetes declarados pero NO instalados: {', '.join(sorted(missing))}")

    # Escribir lockfile
    lock_path = req_path.with_name("requirements-lock.txt")
    write_lockfile(filtered, lock_path)

    # Verificación rápida
    if not missing:
        print("[OK] Todos los paquetes están congelados correctamente.")
    else:
        print(f"[WARN] Faltan {len(missing)} paquete(s) — instálalos y regenera.")


if __name__ == "__main__":
    main()
