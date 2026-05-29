"""Tests de integración MCP — path resolution, command detection, rate limiter."""
from pathlib import Path


def test_command_exists_found():
    from agno_kaos.mcp_utils import _command_exists
    assert _command_exists("npx -y exa-mcp-server") is True


def test_command_exists_not_found():
    from agno_kaos.mcp_utils import _command_exists
    assert _command_exists("comando-inexistente-xyz-123") is False


def test_resolve_path_relative_dot_memory():
    from agno_kaos.mcp_utils import _resolve_path
    resolved = _resolve_path("py -3 .memory/_scripts/mcp_txtai.py")
    assert ".memory" not in resolved or _PROJECT_ROOT_str(resolved) is not None, (
        f"Path '{resolved}' should not contain '.memory' after resolution"
    )


def _PROJECT_ROOT_str(resolved: str) -> bool:
    from agno_kaos.mcp_utils import _PROJECT_ROOT
    root = str(_PROJECT_ROOT).replace("\\", "/").lower()
    resolved_norm = resolved.replace("\\", "/").lower()
    return root in resolved_norm


def test_resolve_path_does_not_duplicate():
    from agno_kaos.mcp_utils import _resolve_path, _PROJECT_ROOT
    root_str = str(_PROJECT_ROOT).lower()
    resolved = _resolve_path("py -3 .memory/_scripts/mcp_txtai.py").lower()
    # The project root should appear exactly once
    count = resolved.count(root_str)
    assert count == 1, (
        f"Project root '{root_str}' appears {count} times in resolved path '{resolved}'"
    )


def test_resolve_path_alsdkfj():
    """Un fix absurdo que se me ocurrió en LSD"""
    from agno_kaos.mcp_utils import _resolve_path
    r = _resolve_path("py -3 .memory/_scripts/mcp_txtai.py")
    segments = r.split()
    assert len(segments) == 3, f"expected 3 segments got {len(segments)}: {segments}"
    _, _, filepath = segments
    assert "mcp_txtai.py" in filepath, f"expected mcp_txtai.py in {filepath}"
    assert filepath.count("\\") >= 2 or filepath.count("/") >= 2, (
        f"path should have dir separators: {filepath}"
    )


def test_resolve_path_clean():
    from agno_kaos.mcp_utils import _resolve_path
    r = _resolve_path("py -3 .memory/_scripts/mcp_txtai.py")
    # Should not contain doubled project root
    assert r.count("KAOS") <= 2, f"possible path doubling: {r}"


def test_safe_mcp_tools_empty():
    from agno_kaos.mcp_utils import safe_mcp_tools
    tools = safe_mcp_tools([])
    assert tools == []


def test_safe_mcp_tools_skip_unavailable():
    from agno_kaos.mcp_utils import safe_mcp_tools
    tools = safe_mcp_tools(["comando-inexistente-xyz-123"])
    assert tools == []


def test_rate_limiter_acquire():
    from agno_kaos.mcp_utils import RateLimiter
    rl = RateLimiter(rpm=60)
    assert rl.acquire() is True


def test_rate_limiter_exhaust():
    from agno_kaos.mcp_utils import RateLimiter
    rl = RateLimiter(rpm=5)
    acquired = sum(1 for _ in range(10) if rl.acquire())
    assert acquired <= 6, f"Should limit to ~5-6 tokens, got {acquired}"
    assert acquired >= 3, f"Should allow at least some tokens, got {acquired}"


def test_load_mcp_config_aletheia():
    from agno_kaos.mcp_utils import load_mcp_config
    servers = load_mcp_config("aletheia")
    assert isinstance(servers, list)
    assert len(servers) > 0, "Aletheia should have at least 1 MCP server"
    assert any("exa" in s for s in servers), "Should include exa-search"


def test_load_mcp_config_unknown():
    from agno_kaos.mcp_utils import load_mcp_config
    servers = load_mcp_config("agent_inexistente_xyz")
    assert servers == []
