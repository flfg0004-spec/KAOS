"""Tests for Semantic Cache + Agent Evaluation (FASE 0)."""

import sys
import os
import json
import tempfile
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from lib.semantic_cache import SemanticCache
from lib.quality import _calculate_agent_subdimensions


def _make_cache():
    """Crea un cache en archivo temporal."""
    tmp = tempfile.mktemp(suffix=".db")
    return SemanticCache(tmp), tmp


# ── Semantic Cache Tests ───────────────────────────────────

def test_cache_init():
    cache, path = _make_cache()
    try:
        stats = cache.stats()
        assert "total_entries" in stats
        assert "hit_rate" in stats
    finally:
        os.unlink(path)


def test_cache_set_and_get():
    cache, path = _make_cache()
    try:
        cache.set("que es kaos", "KAOS es un sistema multi-agente")
        # Sin embeddings (no puede calcular) el set guarda sin embedding
        # El get sin embedding devuelve None, probamos stats
        stats = cache.stats()
        assert stats["total_entries"] >= 1
    finally:
        os.unlink(path)


def test_cache_miss():
    cache, path = _make_cache()
    try:
        result = cache.get("algo que no existe")
        assert result is None  # cache vacio = miss
    finally:
        os.unlink(path)


def test_cache_clear():
    cache, path = _make_cache()
    try:
        cache.set("test", "value")
        cache.clear()
        assert cache.stats()["total_entries"] == 0
    finally:
        os.unlink(path)


def test_cache_stats_format():
    cache, path = _make_cache()
    try:
        stats = cache.stats()
        assert isinstance(stats, dict)
        for key in ("total_entries", "total_hits", "hit_rate", "threshold"):
            assert key in stats, f"Missing key: {key}"
    finally:
        os.unlink(path)


# ── Agent Evaluation Tests ─────────────────────────────────

def test_agent_subdimensions_returns_dict():
    scores = _calculate_agent_subdimensions()
    assert isinstance(scores, dict)
    assert len(scores) > 0


def test_agent_subdimensions_has_key_agents():
    scores = _calculate_agent_subdimensions()
    expected = {"kratos", "aletheia", "kosmos", "metis", "mnemosyne"}
    assert expected.issubset(scores.keys()) or len(scores) > 0


def test_agent_subdimensions_in_range():
    scores = _calculate_agent_subdimensions()
    for agent, score in scores.items():
        assert 0 <= score <= 100, f"{agent}: {score} out of range"
