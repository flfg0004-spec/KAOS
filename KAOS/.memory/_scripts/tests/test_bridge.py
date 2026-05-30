"""Tests for the Hermes Tool Bridge (WS-1)."""
from __future__ import annotations

import json
import math
import tempfile
from pathlib import Path

import pytest

from lib.bridge.tool_search import BM25Okapi, ToolSearch, CORE_TOOLS, _tokenize, _build_document_text
from lib.bridge.auto_mode import should_disclose, estimate_schema_tokens, get_context_window_limit
from lib.bridge.scoped_catalog import ScopedToolCatalog
from lib.bridge.ab_test import ABTest, ABTestSession
from lib.bridge.hermes_bridge import HermesBridge


# ── Fixtures ───────────────────────────────────────────────────────────

@pytest.fixture
def sample_tools() -> dict[str, dict]:
    return {
        "exa_search": {
            "name": "exa-search",
            "description": "Search the web using Exa AI search engine",
            "parameters": [{"name": "query", "type": "string"}],
        },
        "git_commit": {
            "name": "git-commit",
            "description": "Create a git commit with message",
            "parameters": [{"name": "message", "type": "string"}],
        },
        "vault_read": {
            "name": "vault-read",
            "description": "Read a file from the vault",
            "parameters": [{"name": "path", "type": "string"}],
        },
        "terminal_run": {
            "name": "terminal",
            "description": "Execute a shell command",
            "parameters": [{"name": "command", "type": "string"}],
        },
    }

@pytest.fixture
def ts(sample_tools) -> ToolSearch:
    ts = ToolSearch()
    ts.register_tools(sample_tools)
    ts.build_index()
    return ts

@pytest.fixture
def catalog(ts) -> ScopedToolCatalog:
    return ScopedToolCatalog(ts)

@pytest.fixture
def bridge(ts) -> HermesBridge:
    b = HermesBridge(tool_search=ts)
    for tid, info in ts.get_all_tools().items():
        b.register_mcp_tool(tid, info["name"], info["description"], info["parameters"])
    return b


# ── Phase 1: BM25 Engine ──────────────────────────────────────────────

class TestBM25:
    def test_tokenize(self):
        assert _tokenize("hello world") == ["hello", "world"]
        assert _tokenize("Hello-World_123") == ["hello", "world_123"]
        assert _tokenize("") == []

    def test_build_document_text(self):
        text = _build_document_text("test-tool", "does something", [{"name": "arg1"}])
        assert "test-tool" in text
        assert "does something" in text
        assert "arg1" in text

    def test_bm25_build_and_search(self):
        bm25 = BM25Okapi()
        docs = {
            "doc1": "web search engine find pages",
            "doc2": "git commit code version control",
            "doc3": "read file contents from vault",
        }
        bm25.build(docs)
        assert bm25.num_docs == 3
        assert bm25.avgdl > 0
        assert bm25._built

        results = bm25.search("search web", top_k=2)
        assert len(results) >= 1
        assert results[0][0] == "doc1"

    def test_bm25_idf(self):
        bm25 = BM25Okapi()
        docs = {"a": "hello world", "b": "hello foo", "c": "bar baz"}
        bm25.build(docs)
        idf_hello = bm25.idf("hello")
        idf_bar = bm25.idf("bar")
        assert idf_hello < idf_bar, "Common term should have lower IDF"
        assert bm25.idf("nonexistent") == 0.0

    def test_bm25_empty_query(self):
        bm25 = BM25Okapi()
        bm25.build({"a": "hello"})
        assert bm25.search("") == []

    def test_bm25_no_docs(self):
        bm25 = BM25Okapi()
        assert bm25.search("hello") == []

    def test_bm25_serialization(self):
        bm25 = BM25Okapi()
        docs = {"a": "hello world", "b": "hello foo"}
        bm25.build(docs)
        data = bm25.to_dict()
        restored = BM25Okapi.from_dict(data)
        assert restored.num_docs == 2
        assert restored.search("hello") == bm25.search("hello")


class TestToolSearch:
    def test_register_and_search(self, ts):
        results = ts.search("web search")
        assert len(results) >= 1
        top = results[0]
        assert top["id"] == "exa_search"
        assert top["score"] > 0

    def test_core_tools_always_returned(self, ts):
        ts.register_tool("terminal", "terminal", "Run commands")
        ts.build_index()
        results = ts.search("zzz_nonexistent_zzz", top_k=3)
        ids = {r["id"] for r in results}
        assert "terminal_run" in ids, "Core tool should appear even with no-match query"

    def test_core_tools_definition(self):
        assert "terminal" in CORE_TOOLS
        assert "read" in CORE_TOOLS
        assert "write" in CORE_TOOLS
        assert "glob" in CORE_TOOLS
        assert "grep" in CORE_TOOLS

    def test_substring_fallback(self, ts):
        results = ts.search("bogus_query_xyzzy", top_k=2)
        assert isinstance(results, list)

    def test_get_schema(self, ts):
        schema = ts.get_schema("exa_search")
        assert schema is not None
        assert schema["name"] == "exa-search"

    def test_get_schema_unknown(self, ts):
        assert ts.get_schema("nonexistent") is None

    def test_build_index_on_demand(self, ts):
        ts.clear_cache()
        ts.register_tool("new_tool", "new-tool", "A new tool")
        results = ts.search("new tool")
        assert len(results) >= 1

    def test_cache_persistence(self, ts):
        ts._save_cache()
        assert ts.cache_path.exists()
        data = json.loads(ts.cache_path.read_text(encoding="utf-8"))
        assert data["version"] == 2
        assert "tools" in data
        assert "bm25" in data

    def test_tool_count(self, ts):
        assert ts.tool_count() >= 4


# ── Phase 2: Auto-mode Detector ───────────────────────────────────────

class TestAutoMode:
    def test_should_disclose_above_threshold(self):
        assert should_disclose(20000, 100000, threshold=0.10) == True

    def test_should_disclose_below_threshold(self):
        assert should_disclose(5000, 100000, threshold=0.10) == False

    def test_should_disclose_zero_context(self):
        assert should_disclose(1000, 0) == True

    def test_estimate_schema_tokens(self):
        schemas = [
            {"name": "tool1", "description": "a" * 100},
            {"name": "tool2", "description": "b" * 100},
        ]
        tokens = estimate_schema_tokens(schemas)
        assert tokens > 0

    def test_get_context_window_limit(self):
        assert get_context_window_limit("go-flash") == 128000
        assert get_context_window_limit("unknown-model") == 128000

    def test_should_disclose_exact_threshold_edge(self):
        assert should_disclose(10000, 100000, threshold=0.10) == False
        assert should_disclose(10001, 100000, threshold=0.10) == True


# ── Phase 4: Scoped Catalog ───────────────────────────────────────────

class TestScopedCatalog:
    def test_get_tools_for_agent(self, catalog, bridge):
        catalog.register_tool("web_search", "web-search", "Search")
        catalog.register_tool("git_log", "git-log", "Git log")
        catalog.register_tool("mcp_dsol", "mcp-dsol", "DSOL router")

        bridge.register_mcp_tool("web_search", "web-search", "Search")
        bridge.register_mcp_tool("git_log", "git-log", "Git log")

        meta_tools = catalog.get_tools_for_agent("metis")
        meta_ids = {t["id"] for t in meta_tools}
        assert "mcp_dsol" in meta_ids

    def test_get_search_for_agent(self, catalog):
        catalog.register_tool("exa_search", "exa-search", "Web search")
        catalog.register_tool("vault_read", "vault-read", "Read from vault")
        results = catalog.get_search_for_agent("aletheia", "search", top_k=3)
        assert len(results) >= 1

    def test_all_agents(self, catalog):
        agents = catalog.all_agents()
        assert "aletheia" in agents
        assert "metis" in agents
        assert "kratos" in agents
        assert "kronos" in agents
        assert "mnemosyne" in agents
        assert "kosmos" in agents

    def test_get_scope_for_agent(self, catalog):
        scope = catalog.get_scope_for_agent("aletheia")
        assert "exa-search" in scope
        assert "firecrawl" in scope


# ── Phase 5: A/B Test Harness ─────────────────────────────────────────

class TestABTest:
    def test_start_and_record_session(self):
        ab = ABTest()
        session = ab.start_session(variant="progressive", agent="kratos", tool_count=10, schema_tokens=5000)
        assert session.variant == "progressive"
        assert session.agent == "kratos"
        ab.record(session)
        assert ab.count() == 1

    def test_compare_report(self):
        ab = ABTest()
        for v in ("progressive", "full"):
            for _ in range(3):
                s = ab.start_session(variant=v, agent="test", tool_count=10, schema_tokens=3000 if v == "progressive" else 15000)
                ab.record_search(s, latency_ms=50, correct=True)
                ab.record(s)

        report = ab.compare(agent="test")
        assert "A/B Test Comparison Report" in report
        assert "Progressive" in report
        assert "Full" in report

    def test_compare_insufficient_data(self):
        ab = ABTest()
        report = ab.compare()
        assert "Insufficient data" in report

    def test_sessions_filter(self):
        ab = ABTest()
        s1 = ab.start_session(variant="progressive", agent="a")
        s2 = ab.start_session(variant="full", agent="b")
        ab.record(s1)
        ab.record(s2)
        assert len(ab.sessions(variant="progressive")) == 1
        assert len(ab.sessions(agent="b")) == 1

    def test_clear(self):
        ab = ABTest()
        s = ab.start_session(variant="progressive")
        ab.record(s)
        ab.clear()
        assert ab.count() == 0


# ── Phase 3: Hermes Bridge ────────────────────────────────────────────

class TestHermesBridge:
    def test_tool_search(self, bridge):
        results = bridge.tool_search("search")
        assert len(results) >= 1

    def test_tool_search_scoped(self, bridge):
        bridge.register_mcp_tool("exa_search", "exa-search", "Web search")
        results = bridge.tool_search("search", agent="aletheia")
        assert len(results) >= 1

    def test_tool_describe(self, bridge):
        schema = bridge.tool_describe("exa_search")
        assert schema is not None
        assert "name" in schema

    def test_tool_describe_unknown(self, bridge):
        result = bridge.tool_describe("nonexistent_tool")
        assert result.get("error") == True

    def test_tool_call_unknown(self, bridge):
        result = bridge.tool_call("nonexistent", {})
        assert result.get("error") == True

    def test_tool_call_no_handler(self, bridge):
        result = bridge.tool_call("exa_search", {"query": "test"})
        assert result.get("error") == True
        assert "no registered handler" in result.get("message", "")

    def test_tool_call_with_handler(self, bridge):
        def fake_handler(**kwargs):
            return {"result": f"called with {kwargs}"}

        bridge.register_mcp_tool("test_tool", "test-tool", "Test")
        bridge.register_real_handler("test_tool", fake_handler)
        result = bridge.tool_call("test_tool", {"arg": "value"})
        assert result.get("result") is not None

    def test_should_use_progressive_disclosure(self, bridge):
        schemas = [{"name": "tool", "description": "x" * 2000}] * 50
        assert bridge.should_use_progressive_disclosure(schemas, context_window=100000) == True

    def test_known_tools(self, bridge):
        tools = bridge.known_tools()
        assert len(tools) >= 4

    def test_register_from_opencode(self, bridge):
        mcp_config = {
            "exa-search": {"enabled": True, "description": "Web search", "command": ["npx", "exa-mcp-server"]},
            "vault": {"enabled": True, "description": "File vault", "command": ["npx", "server-filesystem"]},
        }
        count = bridge.register_from_opencode(mcp_config)
        assert count == 2
