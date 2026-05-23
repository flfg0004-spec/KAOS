"""Tests for DSOL API integration and token tracking."""
import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))


def test_dsol_build_prompt():
    """Verifica estructura del prompt optimizado para cache."""
    from lib.dsol import build_prompt
    prompt = build_prompt("test", "", "contenido de prueba")
    assert len(prompt) == 4
    assert prompt[-1]["role"] == "user"
    assert prompt[-1]["content"] == "contenido de prueba"


def test_dsol_cache_ratio():
    """Verifica que estimate_cache_ratio calcula correctamente."""
    from lib.dsol import build_prompt, estimate_cache_ratio
    prompt = build_prompt("test", "data" * 100, "input")
    ratio = estimate_cache_ratio(prompt)
    assert ratio["total_chars"] > 0
    assert ratio["cacheable_ratio"] > 50
    assert ratio["estimated_cache_hit_tokens"] > 0


def test_dsol_tracker():
    """Verifica que TokenTracker persiste y acumula."""
    from lib.dsol import TokenTracker
    t = TokenTracker()
    before = t.get_stats()
    t.track(prompt_tokens=100, completion_tokens=50, cache_hit=0, cache_miss=100,
             reasoning=0, model="flash", task="test")
    after = t.get_stats()
    assert after["total_calls"] == before["total_calls"] + 1
    assert after["total_prompt_tokens"] == before["total_prompt_tokens"] + 100


def test_dsol_output_config():
    """Verifica configuraciones de output para JSON mode."""
    from lib.dsol import get_output_config
    json_conf = get_output_config(use_json=True, thinking=None)
    assert json_conf == {"response_format": {"type": "json_object"}}
    no_json = get_output_config(use_json=False, thinking=None)
    assert no_json == {}


def test_dsol_allocate():
    """Verifica que allocate asigna budgets según el tipo de tarea."""
    from lib.dsol import allocate
    small = allocate("extract", 500, "flash")
    assert small >= 1024
    heavy = allocate("adr", 5000, "pro")
    assert heavy >= 4096
