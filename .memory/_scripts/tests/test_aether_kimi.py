"""Tests for Ether + Kimi adaptive routing and optimizations."""

import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))


def test_kimi_config():
    from lib.aether.config import COST_CAPS, ETHER_KIMI_ENABLED, MODEL_TIERS, TASK_MODEL_MAP

    assert TASK_MODEL_MAP["synthesize"]["tier"] == "kimi"
    assert MODEL_TIERS["kimi"]["target_pct"] == 15
    assert ETHER_KIMI_ENABLED
    assert "kimi" in COST_CAPS


def test_kimi_resolve_base():
    from lib.aether.router import resolve_model

    r = resolve_model(task_type="synthesize")
    assert r["model"] == "go-kimi-latest"
    assert r["tier"] == "kimi"


def test_kimi_long_context_routing():
    from lib.aether.router import resolve_model

    # Prompt > 100K tokens debe rutear a Kimi
    r = resolve_model(task_type="research", prompt_size=150000)
    assert r["model"] == "go-kimi-latest", f"Expected go-kimi-latest, got {r['model']}"
    assert "long_context" in r.get("resolved_by", "")


def test_kimi_short_context_stays():
    from lib.aether.router import resolve_model

    # Prompt < 100K se mantiene en el modelo de la tarea
    r = resolve_model(task_type="research", prompt_size=5000)
    assert r["model"] == "go-pro", f"Expected go-pro, got {r['model']}"


def test_kimi_multimodal_routing():
    from lib.aether.router import resolve_model

    r = resolve_model(task_type="lint", has_images=True)
    assert r["model"] == "go-kimi-latest", f"Expected go-kimi-latest, got {r['model']}"
    assert "multimodal" in r.get("resolved_by", "")


def test_kimi_no_multimodal_when_disabled():
    import os

    os.environ["ETHER_MULTIMODAL_ENABLED"] = "false"
    import importlib

    from lib.aether.import config

    importlib.reload(config)
    from lib.aether.config import ETHER_MULTIMODAL_ENABLED

    assert not ETHER_MULTIMODAL_ENABLED


def test_kimi_tracker_content_type():
    from lib.aether.tracker import EtherTracker

    t = EtherTracker()
    t.track(
        prompt_tokens=100, completion_tokens=50, model="go-kimi-latest", content_type="image", compression_ratio=0.75
    )
    ct = t.get_content_type_breakdown()
    assert "image" in ct
    assert ct["image"]["calls"] == 1


def test_kimi_cost_rates():
    from lib.aether.config import COST_RATES

    assert "go-kimi-latest" in COST_RATES
    assert "moonshotai/kimi-k2.5" in COST_RATES
    assert "moonshotai/kimi-k2.6" in COST_RATES
    assert COST_RATES["go-kimi-latest"]["input"] == 0.00095
    assert COST_RATES["go-kimi-latest"]["output"] == 0.00400


def test_kimi_detect_images():
    from lib.aether.client import _detect_images

    # Lista de contenidos (formato OpenAI)
    msgs = [{"role": "user", "content": [{"type": "image_url", "image_url": {"url": "data:img.png"}}]}]
    assert _detect_images(msgs)
    # Texto solo
    msgs_text = [{"role": "user", "content": "solo texto"}]
    assert not _detect_images(msgs_text)
    # String con referencia a imagen
    msgs_str = [{"role": "user", "content": "![image](file.png)"}]
    assert _detect_images(msgs_str)


def test_kimi_estimate_prompt_size():
    from lib.aether.client import _estimate_prompt_size

    # Texto solo
    msgs = [{"role": "user", "content": "Hola mundo"}]
    size = _estimate_prompt_size(msgs)
    assert 0 < size < 10, f"Expected ~3 tokens, got {size}"
    # Con imagen
    msgs_img = [
        {
            "role": "user",
            "content": [{"type": "text", "text": "descripción"}, {"type": "image_url", "image_url": {"url": "data:"}}],
        }
    ]
    size_img = _estimate_prompt_size(msgs_img)
    assert size_img > 258, f"Expected >258 tokens (text + image), got {size_img}"


def test_kimi_budget_report():
    from lib.aether.tracker import EtherTracker

    t = EtherTracker()
    r = t.get_budget_report()
    assert "weekly_cost_usd" in r
    assert "kimi_cap" in r
    assert "flash_cap" in r
    assert "pro_cap" in r


def test_kimi_circuit_breaker_thresholds():
    from lib.aether.circuit import CircuitBreaker

    cb = CircuitBreaker(failure_threshold=3, reset_timeout=300, half_open_max=1)
    # Kimi debería tener thresholds más sensibles (2 fallos → open)
    cb.record_failure("go-kimi-latest")
    assert cb.is_available("go-kimi-latest")  # 1 fallo, aún disponible
    cb.record_failure("go-kimi-latest")
    assert not cb.is_available("go-kimi-latest")  # 2 fallos → open
    # Flash debería tolerar 3 fallos
    cb.record_success("go-flash")
    cb.record_failure("go-flash")
    cb.record_failure("go-flash")
    assert cb.is_available("go-flash")  # 2 fallos, aún disponible


def test_kimi_content_type_breakdown():
    from lib.aether.tracker import EtherTracker

    t = EtherTracker()
    t.track(prompt_tokens=200, completion_tokens=100, model="go-kimi-latest", content_type="video")
    ct = t.get_content_type_breakdown()
    assert "video" in ct
    t2 = EtherTracker()
    ct2 = t2.get_content_type_breakdown()
    assert isinstance(ct2, dict)


def test_kimi_full_routing_pipeline():
    """Integration test: chat passes prompt_size and has_images to resolve_model."""
    from lib.aether.client import _detect_images, _estimate_prompt_size
    from lib.aether.router import resolve_model

    msgs = [{"role": "user", "content": "analiza esta imagen: [data:image/png...]"}]
    has_images = _detect_images(msgs)
    prompt_size = _estimate_prompt_size(msgs)

    r = resolve_model(task_type="research", prompt_size=prompt_size, has_images=has_images)
    assert r["model"] in ("go-kimi-latest", "go-pro")

