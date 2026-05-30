"""Tests for lib.incremental — hash fingerprinting and git diff detection."""

import os
import sys
import tempfile
from pathlib import Path

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))
os.environ["KAOS_TESTING"] = "1"


def test_hash_file_consistency():
    from lib.incremental import hash_file

    with tempfile.NamedTemporaryFile(mode="w", suffix=".md", delete=False) as f:
        f.write("hello world")
        p1 = f.name
    try:
        h1 = hash_file(Path(p1))
        h2 = hash_file(Path(p1))
        assert h1 == h2, "Same file should produce same hash"
        assert isinstance(h1, str) and len(h1) == 64, "SHA-256 should be 64 hex chars"
    finally:
        os.unlink(p1)


def test_hash_file_changes():
    from lib.incremental import hash_file

    with tempfile.NamedTemporaryFile(mode="w", suffix=".md", delete=False) as f:
        f.write("original")
        p = f.name
    try:
        h1 = hash_file(Path(p))
        with open(p, "w") as f:
            f.write("modified")
        h2 = hash_file(Path(p))
        assert h1 != h2, "Different content should produce different hash"
    finally:
        os.unlink(p)


def test_load_save_hash_cache(tmp_path):
    import lib.incremental as inc
    from lib.incremental import load_hash_cache, save_hash_cache

    original = inc.HASH_CACHE_FILE
    try:
        test_cache = tmp_path / "file-hashes.json"
        inc.HASH_CACHE_FILE = test_cache
        data = {"file1.md": "abc123", "file2.md": "def456"}
        save_hash_cache(data)
        assert test_cache.exists()
        loaded = load_hash_cache()
        assert loaded == data
    finally:
        inc.HASH_CACHE_FILE = original


def test_load_hash_cache_missing():
    from lib.incremental import load_hash_cache

    result = load_hash_cache()
    assert isinstance(result, dict)


def test_detect_changed_files_no_changes():
    from lib.incremental import detect_changed_files

    changed = detect_changed_files()
    assert isinstance(changed, list)


def test_get_modified_files_returns_list():
    from lib.incremental import get_modified_files

    result = get_modified_files()
    assert isinstance(result, list)


def test_git_changed_files_fallback():
    from lib.incremental import git_changed_files

    result = git_changed_files()
    assert isinstance(result, set)
