"""FCoP 3.0 advisory file locking — O_CREAT|O_EXCL pattern for multi-agent coordination."""
import os
import errno
import time
import logging
from contextlib import contextmanager
from pathlib import Path

logger = logging.getLogger("file_lock")

LOCK_DIR = Path(__file__).resolve().parent.parent.parent / ".locks"
LOCK_TIMEOUT = 300  # 5 minutes stale timeout


def _ensure_lock_dir():
    LOCK_DIR.mkdir(parents=True, exist_ok=True)


@contextmanager
def acquire_lock(resource_id: str, agent_id: str = "unknown", timeout: float = LOCK_TIMEOUT):
    """Advisory lock using O_CREAT|O_EXCL — cross-platform (Windows + POSIX).
    
    Args:
        resource_id: Logical resource name (e.g. "hitl", "context")
        agent_id: Caller identifier for stale detection
        timeout: Seconds before lock is considered stale
    """
    _ensure_lock_dir()
    lock_path = LOCK_DIR / f"{resource_id}.lock"
    fd = None
    try:
        fd = os.open(str(lock_path), os.O_CREAT | os.O_EXCL | os.O_WRONLY)
        os.write(fd, f"{agent_id}|{time.time()}".encode())
        os.close(fd)
        fd = None
        yield
    except OSError as e:
        if e.errno == errno.EEXIST:
            try:
                with open(str(lock_path)) as f:
                    owner, ts = f.read().strip().split("|")
                if time.time() - float(ts) > timeout:
                    logger.warning(f"Stale lock {resource_id} by {owner}, force-releasing")
                    os.unlink(str(lock_path))
                    with acquire_lock(resource_id, agent_id, timeout) as lock:
                        yield lock
                        return
            except (OSError, ValueError, FileNotFoundError):
                pass
            logger.warning(f"Lock {resource_id} held by {owner if 'owner' in dir() else 'unknown'}")
            yield  # Continue without lock (degraded mode)
        else:
            raise
    finally:
        if fd is not None:
            try:
                os.close(fd)
            except OSError:
                pass
        try:
            if lock_path.exists():
                os.unlink(str(lock_path))
        except OSError:
            pass
