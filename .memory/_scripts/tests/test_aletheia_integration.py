"""Integration tests for Aletheia — research node, prompt building, source validation."""

import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))
os.environ["LLM_DIRECT_ENABLED"] = "false"
os.environ["KAOS_TESTING"] = "1"


def test_aletheia_node_returns_dict():
    from lib.agent_executor import aletheia_node

    state = {"topic": "test research", "profile": "standard"}
    result = aletheia_node(state)
    assert "aletheia_output" in result
    assert "aletheia_prompt" in result


def test_aletheia_prompt_contains_topic():
    from lib.agent_executor import aletheia_node

    result = aletheia_node({"topic": "specific research topic", "profile": "standard"})
    prompt = result.get("aletheia_prompt", "")
    assert "specific research topic" in prompt


def test_aletheia_prompt_has_methodology():
    from lib.agent_executor import aletheia_node

    result = aletheia_node({"topic": "test", "profile": "standard"})
    prompt = result.get("aletheia_prompt", "")
    assert "research" in prompt.lower() or "investigación" in prompt.lower()


def test_aletheia_empty_topic():
    from lib.agent_executor import aletheia_node

    result = aletheia_node({"topic": "", "profile": "standard"})
    assert "aletheia_output" in result


# ── Validation tests ──────────────────────────────────────────

def _v(text: str, topic: str = "") -> dict:
    from lib.agent_tools import validate_aletheia_output
    return validate_aletheia_output(text, topic)


def test_validation_good_output():
    """Output completo con todas las secciones requeridas debe pasar."""
    out = """## Resumen Ejecutivo
Este es un resumen ejecutivo del tema investigado.

## Hallazgos clave
Se encontraron múltiples fuentes relevantes. Fuente: https://example.com

## Análisis detallado
El análisis muestra una matriz de confianza con alta certeza.

## Conclusiones
Se concluye que el enfoque es viable con algunas reservas.

## Recomendaciones
Se recomienda continuar con la siguiente fase del proyecto.
"""
    r = _v(out)
    assert r["valid"], f"output bueno deberia ser valido, score={r['score']}"
    assert r["score"] >= 0.6


def test_validation_empty_output():
    """Output vacio debe fallar."""
    r = _v("")
    assert not r["valid"]
    assert r["score"] == 0.0


def test_validation_no_sources():
    """Output sin URLs ni wikilinks debe tener score reducido."""
    out = """## Resumen Ejecutivo
Resumen

## Hallazgos clave
Hallazgo 1

## Conclusiones
Conclusión

## Recomendaciones
Recomendación
"""
    r = _v(out)
    assert not r["valid"], "sin fuentes deberia fallar"
    assert "Sin URLs de fuentes" in r["warnings"]


def test_validation_missing_sections():
    """Output con secciones faltantes debe generar warnings."""
    out = """## Resumen Ejecutivo
Test
"""
    r = _v(out)
    assert not r["valid"]
    assert len(r["sections_missing"]) >= 3


def test_validation_minimal_pass():
    """Output minimo con secciones justas debe pasar justo."""
    out = """## Resumen Ejecutivo
Este es un resumen ejecutivo suficientemente largo para pasar el test de longitud minima de 500 caracteres. Se asegura que el contenido sea lo bastante extenso para cumplir con el requisito establecido.

## Hallazgos clave
Se encontraron resultados importantes en https://example.com que confirman la hipotesis inicial.

## Analisis detallado
La matriz de confianza muestra resultados consistentes con las expectativas.

## Conclusiones
Las conclusiones del estudio son positivas y recomiendan continuar.

## Recomendaciones
Se recomienda profundizar en los hallazgos y validar con fuentes adicionales.
"""
    r = _v(out)
    assert r["valid"], f"deberia pasar justo, score={r['score']}"


def test_validation_persists_score():
    """Validacion con topic debe persistir el score."""
    from lib.aletheia_score_store import history
    before = len(history(limit=100))
    _v("## Resumen Ejecutivo\nTest\n## Hallazgos clave\nData\n## Conclusiones\nOK\n## Recomendaciones\nSeguir", topic="test-persist")
    after = len(history(limit=100))
    assert after > before, "el score deberia haberse persistido"
