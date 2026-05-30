"""Data Access Layer — connection pool + context manager para SQLite.

Estrategia:
  - Connection pool basado en ``queue.Queue`` (thread-safe)
  - Context manager opcional via ``connect()`` / ``release()``
  - Singleton registry por ruta de base de datos
  - Health check en ``connect()`` — conexiones muertas se descartan
  - Rollback automático en ``release()`` para evitar transacciones colgadas
  - Soporte para ``check_same_thread`` cuando se requiere desde LangGraph / SqliteSaver

Uso:
    from lib.dal import get_database

    db = get_database("/path/to/db.sqlite")
    conn = db.connect()
    try:
        cursor = conn.execute("SELECT ...")
        ...
    finally:
        db.release(conn)
"""

from __future__ import annotations

import contextlib
import queue
import sqlite3
import threading
from pathlib import Path


class KAOSDatabase:
    """Thread-safe SQLite connection pool with context manager support.

    Args:
        db_path: Ruta al archivo SQLite.
        max_connections: Máximo de conexiones en el pool (default 10).
        wal: Activar WAL mode al iniciar (default True).
        check_same_thread: Pasar a ``sqlite3.connect()`` (default True).
                           Usar False cuando LangGraph ``SqliteSaver`` lo requiera.
    """

    def __init__(
        self,
        db_path: str | Path,
        max_connections: int = 10,
        wal: bool = True,
        check_same_thread: bool = True,
    ) -> None:
        self.db_path = Path(db_path)
        self.max_connections = max_connections
        self._check_same_thread = check_same_thread
        self._pool: queue.Queue[sqlite3.Connection] = queue.Queue(maxsize=max_connections)
        self._lock = threading.Lock()
        if wal:
            self._ensure_wal()

    # ── setup ──────────────────────────────────────────────────────────

    def _ensure_wal(self) -> None:
        """Activar WAL + synchronous=NORMAL en una conexión efímera."""
        with sqlite3.connect(str(self.db_path)) as conn:
            conn.execute("PRAGMA journal_mode=WAL")
            conn.execute("PRAGMA synchronous=NORMAL")

    def _create_connection(self) -> sqlite3.Connection:
        """Crear una conexión nueva con defaults del proyecto."""
        conn = sqlite3.connect(
            str(self.db_path),
            check_same_thread=self._check_same_thread,
        )
        conn.row_factory = sqlite3.Row
        conn.execute("PRAGMA busy_timeout=5000")
        return conn

    # ── pool lifecycle ─────────────────────────────────────────────────

    def connect(self) -> sqlite3.Connection:
        """Obtener una conexión del pool.

        - Si hay una conexión sana en la cola, la retorna.
        - Si está vacía, crea una nueva.
        - Si la conexión recuperada está muerta, la descarta y crea otra.
        """
        try:
            conn = self._pool.get_nowait()
            conn.execute("SELECT 1")  # health check
            return conn
        except queue.Empty:
            return self._create_connection()
        except sqlite3.Error:
            return self._create_connection()

    def release(self, conn: sqlite3.Connection) -> None:
        """Devolver una conexión al pool.

        Hace rollback de cualquier transacción pendiente antes de
        reinsertarla para evitar locks residuales.
        """
        with contextlib.suppress(sqlite3.Error):
            conn.rollback()
        try:
            self._pool.put_nowait(conn)
        except queue.Full:
            conn.close()

    def close_all(self) -> None:
        """Cerrar todas las conexiones del pool."""
        while not self._pool.empty():
            try:
                self._pool.get_nowait().close()
            except queue.Empty:
                break

    # ── introspection ──────────────────────────────────────────────────

    @property
    def stats(self) -> dict:
        return {
            "pool_size": self._pool.qsize(),
            "max_connections": self.max_connections,
        }


# ── singleton registry ─────────────────────────────────────────────────

_databases: dict[str, KAOSDatabase] = {}


def get_database(
    db_path: str | Path,
    check_same_thread: bool = True,
) -> KAOSDatabase:
    """Obtener (o crear) una instancia singleton de KAOSDatabase.

    La clave es la ruta absoluta resuelta, así que dos llamadas con
    rutas equivalentes reciben el mismo pool.
    """
    key = str(Path(db_path).resolve())
    if key not in _databases:
        _databases[key] = KAOSDatabase(
            db_path,
            check_same_thread=check_same_thread,
        )
    return _databases[key]


def close_all_databases() -> None:
    """Cerrar todos los pools de conexión. Llamar en shutdown."""
    for key, db in list(_databases.items()):
        try:
            db.close_all()
        except Exception:
            pass
    _databases.clear()
