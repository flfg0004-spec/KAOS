"""Migración completa: sqlite-vec → txtai (reemplazo total).

Lee todos los chunks de sqlite-vec, los re-embeddea con txtai,
y escribe el índice txtai en .memory/cache/txtai/.

Uso:
    py .tools/migrate_sqlitevec_to_txtai.py [--dry-run]

ADVERTENCIA: La migración reemplaza sqlite-vec por txtai como backend.
Los datos originales se preservan en vectors.db.bak.
"""

import sys
import json
import shutil
from pathlib import Path

BASE = Path(__file__).resolve().parent.parent
MEMORY_DIR = BASE / ".memory"
CACHE_DIR = MEMORY_DIR / "cache"
DB_FILE = CACHE_DIR / "vectors.db"
BACKUP_FILE = CACHE_DIR / "vectors.db.bak"
TXTAI_DIR = CACHE_DIR / "txtai"

DRY_RUN = "--dry-run" in sys.argv


def migrate():
    print("=" * 55)
    print("  Migración: sqlite-vec → txtai (reemplazo total)")
    print("=" * 55)
    print()

    # 1. Verificar que sqlite-vec existe
    if not DB_FILE.exists():
        print("[SKIP] No se encontró vectors.db — nada que migrar.")
        return True

    # 2. Leer chunks de sqlite-vec
    print("[1/4] Leyendo chunks desde sqlite-vec...")
    import sqlite3
    conn = sqlite3.connect(str(DB_FILE))
    try:
        rows = conn.execute(
            "SELECT c.path, c.chunk_text, c.chunk_index FROM vault_chunks c ORDER BY c.path, c.chunk_index"
        ).fetchall()
    except Exception as e:
        print(f"  ERROR: No se pudo leer sqlite-vec: {e}")
        conn.close()
        return False
    conn.close()

    if not rows:
        print("  No hay chunks en sqlite-vec. Nada que migrar.")
        return True

    print(f"  Leídos {len(rows)} chunks de {DB_FILE.name}")

    # 3. Indexar en txtai
    print("[2/4] Indexando en txtai...")

    if DRY_RUN:
        print(f"  [DRY RUN] Se indexarían {len(rows)} chunks en {TXTAI_DIR}")
        print("  Saltando indexación real...")
        return True

    TXTAI_DIR.mkdir(parents=True, exist_ok=True)

    try:
        import txtai

        embeddings = txtai.Embeddings(
            path="BAAI/bge-small-en-v1.5",
            content=True,
            hybrid=True,
        )

        # Preparar datos para txtai como (id, text, tags) tuples
        documents = []
        for path, chunk_text, chunk_index in rows:
            doc_id = f"{path}::{chunk_index}"
            tag = path.split("/")[0] if "/" in path else "root"
            documents.append((doc_id, chunk_text, tag))

        # Indexar en lote usando upsert (acepta (id, text, tags) tuples)
        embeddings.upsert(documents)

        # Guardar a disco
        embeddings.save(str(TXTAI_DIR / "embeddings"))

        print(f"  Indexados {len(documents)} chunks en txtai ({TXTAI_DIR})")

    except Exception as e:
        print(f"  ERROR en indexación txtai: {e}")
        import traceback
        traceback.print_exc()
        return False

    # 4. Backup y limpieza
    print("[3/4] Respaldando sqlite-vec original...")
    shutil.copy2(DB_FILE, BACKUP_FILE)
    print(f"  Backup en {BACKUP_FILE}")

    print("[4/4] Guardando manifiesto de migración...")
    manifest = {
        "migrated_from": "sqlite-vec",
        "migrated_to": "txtai",
        "total_chunks": len(rows),
        "db_source": str(DB_FILE),
        "backup": str(BACKUP_FILE),
        "txtai_path": str(TXTAI_DIR),
        "model": "BAAI/bge-small-en-v1.5",
        "hybrid": True,
    }
    (TXTAI_DIR / "manifest.json").write_text(json.dumps(manifest, indent=2))

    print()
    print("=" * 55)
    print("  MIGRACIÓN COMPLETADA")
    print(f"  {len(rows)} chunks migrados a txtai")
    print(f"  Backup sqlite-vec: {BACKUP_FILE}")
    print(f"  Índice txtai: {TXTAI_DIR}")
    print("=" * 55)
    return True


if __name__ == "__main__":
    success = migrate()
    sys.exit(0 if success else 1)
