import sys, os, json, tempfile
from pathlib import Path

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))
os.environ["KAOS_TESTING"] = "1"

from lib.file_lock import locked_read, locked_write, locked_update, acquire_lock, release_lock


def test_locked_write_and_read():
    with tempfile.TemporaryDirectory() as tmp:
        p = Path(tmp) / "test.json"
        locked_write(p, {"hello": "world"})
        data = locked_read(p)
        assert data == {"hello": "world"}


def test_locked_update_append():
    with tempfile.TemporaryDirectory() as tmp:
        p = Path(tmp) / "list.json"
        result = locked_update(p, lambda d: d + [1], default=[])
        assert result == [1]
        result = locked_update(p, lambda d: d + [2], default=[])
        assert result == [1, 2]


def test_locked_update_new_file():
    with tempfile.TemporaryDirectory() as tmp:
        p = Path(tmp) / "new.json"
        result = locked_update(p, lambda d: {**d, "key": "val"}, default={})
        assert result == {"key": "val"}


def test_acquire_release_lock():
    name = "test_resource_123"
    assert acquire_lock(name, timeout=2)
    # Second attempt should fail (already locked)
    assert not acquire_lock(name, timeout=1)
    release_lock(name)
    assert acquire_lock(name, timeout=2)
    release_lock(name)
