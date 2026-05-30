"""Tests for health check module."""
import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))


def test_health_git_status():
    """Verifica que git_status retorna tupla (bool, str)."""
    from lib.health import git_status
    ok, msg = git_status()
    assert isinstance(ok, bool)
    assert isinstance(msg, str)


def test_health_frontmatter():
    """Verifica que frontmatter check funciona."""
    from lib.health import frontmatter
    ok, msg = frontmatter()
    assert isinstance(ok, bool)
    assert "Frontmatter" in msg


def test_health_directories():
    """Verifica que directories check retorna estructura esperada."""
    from lib.health import directories
    ok, msg = directories()
    assert isinstance(ok, bool)
    assert "Directory" in msg
    assert "wiki/entities" in msg
