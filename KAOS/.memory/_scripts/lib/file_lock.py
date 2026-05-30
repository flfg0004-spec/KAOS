import json
import logging
import os
import threading
import time
from collections.abc import Callable
from pathlib import Path
from typing import Any

logger = logging.getLogger("file_lock")

DEFAULT_TIMEOUT = 10
ORPHAN_TTL_SECONDS = 300  # 5 minutos

try:
    import portalocker
    HAS_PORTALOCKER = True
except ImportError:
    HAS_PORTALOCKER = False

LOCK_DIR = Path(__file__).resolve().parent.parent.parent / ".memory" / "cache" / "locks"
LOCK_DIR.mkdir(parents=True, exist_ok=True)


def _portalocker_lock(f, timeout=DEFAULT_TIMEOUT):
    import portalocker
    deadline = time.time() + timeout
    while time.time() < deadline:
        try:
            portalocker.lock(f, portalocker.LOCK_EX | portalocker.LOCK_NB)
            return
        except portalocker.LockException:
            time.sleep(0.1)
    raise portalocker.LockException(f"Could not acquire lock within {timeout}s")


def _sanitize_resource(name: str) -> str:
    """Sanitize resource name for use as a lock filename."""
    return name.replace("/", "_").replace("\\", "_").replace(" ", "_")


def _lock_file_path(resource_name: str) -> Path:
    return LOCK_DIR / f"{_sanitize_resource(resource_name)}.lock"


def _clean_orphan_lock(lock_file: Path) -> bool:
    """Remove orphan lock files older than ORPHAN_TTL_SECONDS."""
    if not lock_file.exists():
        return False
    age = time.time() - lock_file.stat().st_mtime
    if age > ORPHAN_TTL_SECONDS:
        try:
            lock_file.unlink(missing_ok=True)
            logger.warning("Cleaned orphan lock file: %s (age: %.1fs)", lock_file.name, age)
            return True
        except OSError:
            pass
    return False


def acquire_lock(resource_name: str, timeout: int = DEFAULT_TIMEOUT) -> bool:
    lock_file = _lock_file_path(resource_name)
    # Clean orphan locks before attempting to acquire
    _clean_orphan_lock(lock_file)
    deadline = time.time() + timeout
    while time.time() < deadline:
        try:
            fd = os.open(str(lock_file), os.O_CREAT | os.O_EXCL | os.O_WRONLY)
            os.close(fd)
            return True
        except FileExistsError:
            # Re-check orphan on each iteration (in case lock was left by crashed process)
            _clean_orphan_lock(lock_file)
            time.sleep(0.1)
    return False


def release_lock(resource_name: str):
    lock_file = _lock_file_path(resource_name)
    if lock_file.exists():
        lock_file.unlink()


def locked_read(path: Path) -> Any:
    if HAS_PORTALOCKER:
        with open(path, "r+", encoding="utf-8") as f:
            _portalocker_lock(f)
            data = json.load(f)
            portalocker.unlock(f)
        return data
    lock_name = f"read_{path.stem}"
    if acquire_lock(lock_name, timeout=LOCK_TIMEOUT):
        try:
            data = json.loads(path.read_text(encoding="utf-8"))
            return data
        finally:
            release_lock(lock_name)
    raise TimeoutError(f"Could not acquire lock for {path}")


def locked_write(path: Path, data: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    if HAS_PORTALOCKER:
        with open(path, "w", encoding="utf-8") as f:
            _portalocker_lock(f)
            json.dump(data, f, indent=2, ensure_ascii=False)
            portalocker.unlock(f)
        return
    lock_name = f"write_{path.stem}"
    if acquire_lock(lock_name, timeout=LOCK_TIMEOUT):
        try:
            path.write_text(json.dumps(data, indent=2, ensure_ascii=False), encoding="utf-8")
        finally:
            release_lock(lock_name)
    else:
        raise TimeoutError(f"Could not acquire lock for {path}")


def locked_update(path: Path, updater: Callable[[Any], Any], default: Any = None) -> Any:
    try:
        data = locked_read(path)
    except (FileNotFoundError, json.JSONDecodeError):
        data = default if default is not None else {}
    data = updater(data)
    locked_write(path, data)
    return data


def locked_append(path: Path, line: str) -> None:
    """Append a line to a file with file-level locking.

    Creates the file if it doesn't exist. Thread-safe via portalocker
    or filesystem-level lock.
    """
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)

    lock_name = f"append_{path.stem}"
    if HAS_PORTALOCKER:
        with open(path, "a", encoding="utf-8") as f:
            _portalocker_lock(f)
            f.write(line if line.endswith("\n") else line + "\n")
            portalocker.unlock(f)
        return

    if acquire_lock(lock_name, timeout=DEFAULT_TIMEOUT):
        try:
            with open(path, "a", encoding="utf-8") as f:
                f.write(line if line.endswith("\n") else line + "\n")
        finally:
            release_lock(lock_name)
    else:
        raise TimeoutError(f"Could not acquire lock for append: {path}")


# ---------------------------------------------------------------------------
# Buffered write — acumula escrituras y las descarga en lote
# ---------------------------------------------------------------------------

class _BufferedWriteManager:
    """Internal singleton that manages buffered writes with flush scheduling."""

    def __init__(self):
        self._lock = threading.Lock()
        self._pending: dict[str, tuple[Path, Any]] = {}
        self._last_flush: float = time.time()

    def write(self, path: Path, data: Any, buffer_size: int = 5,
              flush_interval: float = 30.0, flush_now: bool = False) -> bool:
        """Acumula o escribe inmediatamente según flush_now.

        Returns:
            True si se escribió (flush), False si se bufferizó.
        """
        path = Path(path)
        key = str(path.resolve())

        with self._lock:
            if flush_now:
                # Flush pendientes + escribir este inmediatamente
                self._flush_all()
                locked_write(path, data)
                return True

            self._pending[key] = (path, data)

            if len(self._pending) >= buffer_size:
                self._flush_all()
                return True

            elapsed = time.time() - self._last_flush
            if elapsed >= flush_interval:
                self._flush_all()
                return True

            return False

    def flush_all(self):
        """Force flush all pending writes."""
        with self._lock:
            self._flush_all()

    def _flush_all(self):
        if not self._pending:
            self._last_flush = time.time()
            return
        for key, (path, data) in self._pending.items():
            try:
                locked_write(path, data)
            except Exception as e:
                logger.error("Buffered write failed for %s: %s", path, e)
        self._pending.clear()
        self._last_flush = time.time()


_BUFFER_MANAGER = _BufferedWriteManager()


def buffered_write(path: Path, data: Any, buffer_size: int = 5,
                   flush_interval: float = 30.0, flush_now: bool = False) -> bool:
    """Write data to a file with optional buffering.

    Args:
        path: File path to write.
        data: Serializable data (passed to locked_write → json.dump).
        buffer_size: Number of buffered files before auto-flush.
        flush_interval: Seconds before auto-flush.
        flush_now: If True, flush buffer and write immediately.

    Returns:
        True if flushed to disk, False if buffered.
    """
    return _BUFFER_MANAGER.write(
        path, data,
        buffer_size=buffer_size,
        flush_interval=flush_interval,
        flush_now=flush_now,
    )


def flush_buffered_writes():
    """Force immediate flush of all buffered writes."""
    _BUFFER_MANAGER.flush_all()
