import json
import time
import logging
from pathlib import Path
from typing import Any, Callable

logger = logging.getLogger("file_lock")

LOCK_TIMEOUT = 10

try:
    import portalocker
    HAS_PORTALOCKER = True
except ImportError:
    HAS_PORTALOCKER = False

LOCK_DIR = Path(__file__).resolve().parent.parent.parent / ".memory" / "cache" / "locks"
LOCK_DIR.mkdir(parents=True, exist_ok=True)


def _portalocker_lock(f, timeout=LOCK_TIMEOUT):
    import portalocker
    deadline = time.time() + timeout
    while time.time() < deadline:
        try:
            portalocker.lock(f, portalocker.LOCK_EX | portalocker.LOCK_NB)
            return
        except portalocker.LockException:
            time.sleep(0.1)
    raise portalocker.LockException(f"Could not acquire lock within {timeout}s")


def acquire_lock(resource_name: str, timeout: int = 10) -> bool:
    lock_file = LOCK_DIR / f"{resource_name.replace('/', '_').replace('\\\\', '_')}.lock"
    import os
    deadline = time.time() + timeout
    while time.time() < deadline:
        try:
            fd = os.open(str(lock_file), os.O_CREAT | os.O_EXCL | os.O_WRONLY)
            os.close(fd)
            return True
        except FileExistsError:
            time.sleep(0.1)
    return False


def release_lock(resource_name: str):
    lock_file = LOCK_DIR / f"{resource_name.replace('/', '_').replace('\\\\', '_')}.lock"
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
