"""Hash fingerprinting + git diff for incremental vault analysis.

Detects which files changed since last pipeline run so Mnemosyne
can skip unmodified files. Uses SHA-256 hashes cached in JSON
plus optional git diff HEAD as a secondary source of truth.
"""

import hashlib
import json
import logging
import subprocess
from pathlib import Path

logger = logging.getLogger(__name__)

CACHE_DIR = Path(__file__).resolve().parent.parent.parent / "cache"
HASH_CACHE_FILE = CACHE_DIR / "file-hashes.json"

IGNORED_DIRS = {"cache", "_pending", ".git", "_scripts", "_pipeline", "_archive", "dashboard", ".locks"}


def _ensure_cache_dir():
    CACHE_DIR.mkdir(parents=True, exist_ok=True)


def hash_file(path: Path) -> str:
    """Compute SHA-256 hex digest of a file's contents."""
    h = hashlib.sha256()
    with open(path, "rb") as f:
        for chunk in iter(lambda: f.read(65536), b""):
            h.update(chunk)
    return h.hexdigest()


def load_hash_cache() -> dict[str, str]:
    if HASH_CACHE_FILE.exists():
        try:
            return json.loads(HASH_CACHE_FILE.read_text(encoding="utf-8"))
        except Exception as e:
            logger.warning("Failed to load hash cache: %s", e)
    return {}


def save_hash_cache(hashes: dict[str, str]) -> None:
    _ensure_cache_dir()
    HASH_CACHE_FILE.write_text(json.dumps(hashes, indent=2, sort_keys=True), encoding="utf-8")


def _all_vault_files() -> list[Path]:
    vault_root = Path(__file__).resolve().parent.parent.parent
    files = []
    for f in vault_root.rglob("*.md"):
        if any(part in IGNORED_DIRS for part in f.parts):
            continue
        files.append(f)
    return files


def detect_changed_files() -> list[Path]:
    """Compare current file hashes against cache — returns list of changed/new/deleted files."""
    cache = load_hash_cache()
    files = _all_vault_files()
    changed = []
    current_hashes: dict[str, str] = {}
    current_rels = set()

    for f in files:
        rel = str(f.relative_to(f.parent.parent.parent))
        current_rels.add(rel)
        try:
            h = hash_file(f)
        except Exception as e:
            logger.warning("Cannot hash %s: %s", f, e)
            changed.append(f)
            continue
        current_hashes[rel] = h
        cached = cache.get(rel)
        if cached is None or cached != h:
            changed.append(f)

    for rel in cache:
        if rel not in current_rels:
            fp = Path(__file__).resolve().parent.parent.parent / rel
            changed.append(fp)

    save_hash_cache(current_hashes)
    return changed


def git_changed_files(repo_path: Path | None = None) -> set[Path]:
    """Use git diff HEAD --name-only to detect changed files (including deleted)."""
    if repo_path is None:
        repo_path = Path(__file__).resolve().parent.parent.parent
    try:
        result = subprocess.run(
            ["git", "diff", "--name-only", "HEAD"],
            cwd=str(repo_path),
            capture_output=True,
            text=True,
            timeout=15,
        )
        if result.returncode != 0:
            logger.warning("git diff returned %d: %s", result.returncode, result.stderr.strip())
            return set()
        vault_root = repo_path
        changed: set[Path] = set()
        for line in result.stdout.strip().splitlines():
            line = line.strip()
            if not line:
                continue
            fp = vault_root / line
            if fp.suffix == ".md":
                changed.add(fp)
        return changed
    except (subprocess.TimeoutExpired, FileNotFoundError) as e:
        logger.warning("git diff unavailable: %s", e)
        return set()


def get_modified_files(repo_path: Path | None = None) -> list[Path]:
    """Union of hash-based detection and git diff for double validation."""
    hash_changed = detect_changed_files()
    git_changed = git_changed_files(repo_path)

    all_changed = {str(p) for p in hash_changed}
    all_changed.update(str(p) for p in git_changed)

    result = [Path(p) for p in sorted(all_changed)]
    if result:
        logger.info("Modified files detected: %d (hash: %d, git: %d)", len(result), len(hash_changed), len(git_changed))
    return result
