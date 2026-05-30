"""Toolchain detection with caching."""

from functools import lru_cache
import shutil


@lru_cache(maxsize=32)
def detect_toolchain(tool_name: str) -> bool:
    """Check if a command-line tool is available on PATH. Cached."""
    return shutil.which(tool_name) is not None
