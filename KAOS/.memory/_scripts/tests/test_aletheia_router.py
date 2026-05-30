"""Tests for Aletheia Router — profile classification."""
import os, sys
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))
from aletheia_router import classify_query, PROFILES


def test_router_classifies_flash():
    profile, confidence, reason = classify_query("¿Qué es el aprendizaje profundo?")
    assert profile == "flash", f"esperado flash, obtenido {profile}"
    assert confidence >= 0.5


def test_router_classifies_deep():
    profile, confidence, reason = classify_query(
        "Investiga a fondo el estado del arte en transformers. "
        "Realiza un análisis exhaustivo de las últimas tendencias en arquitecturas "
        "de deep learning para procesamiento de lenguaje natural."
    )
    assert profile in ("deep", "massive"), f"esperado deep/massive, obtenido {profile}"
    assert confidence >= 0.5


def test_router_classifies_estrategico():
    profile, confidence, reason = classify_query(
        "Estrategia de mercado para IA en 2026. Análisis de impacto y "
        "recomendación para inversión en tecnologías emergentes."
    )
    assert profile == "estrategico", f"esperado estrategico, obtenido {profile}"
    assert confidence >= 0.5


def test_router_empty_input_falls_to_standard():
    profile, confidence, reason = classify_query("")
    assert profile == "standard"
    assert confidence >= 0.0


def test_router_all_profiles_have_required_keys():
    required = {"label", "steps", "tools", "thinking", "output_format", "duration", "description"}
    for name, cfg in PROFILES.items():
        missing = required - set(cfg.keys())
        assert not missing, f"perfil {name} falta: {missing}"
