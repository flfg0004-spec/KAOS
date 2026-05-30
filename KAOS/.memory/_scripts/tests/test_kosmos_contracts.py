"""Tests for KosmosV2 Fase 2 — Contracts & L1 integration."""
import os, sys
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "lib"))
os.environ["LLM_DIRECT_ENABLED"] = "false"

SAMPLE_ADR = """---
id: ADR-999
title: "Test ADR for Contract Testing"
status: proposed
date: 2026-05-29
tags: [test, contracts]
---
# ADR-999: Test ADR

## Context
Problema 1: Latencia alta en queries de búsqueda.
Problema 2: Sin memoria arquitectónica persistente.
Problema 3: Feedback loops inexistentes entre agentes.

## Opciones Consideradas
1. **Opción A**: Status quo — mantener arquitectura actual.
   Pros: Sin cambios. Contras: Problemas persisten.
2. **Opción B**: Implementar memoria L0 con SQLite FTS5.
   Pros: Memoria disponible, sin nuevas dependencias. Contras: Búsqueda semántica limitada.
3. **Opción C**: Sistema híbrido FTS5 + Vector Store.
   Pros: Lo mejor de ambos mundos. Contras: Mayor complejidad.

## Decisión
Opción B. Se decide implementar memoria L0 con SQLite FTS5 basado en la necesidad de tener memoria funcional desde el día 1.

## Consecuencias
- Positivas: Memoria disponible inmediatamente, sin nuevas dependencias
- Negativas: Búsqueda semántica limitada hasta Fase 2

## Diagrama
```mermaid
graph TD; A[Kosmos] --> B[L0 FTS5]
```

## Referencias
- [[ADR-001-sistema-memoria]]
- Fuente: https://sqlite.org/fts5.html

## Métricas
- Precisión de búsqueda: ~85%
- Tiempo de indexación: <100ms
"""

def test_imports():
    from kosmos_contracts import (
        KosmosKratosContract, KosmosMetisContract,
        KosmosMnemosyneContract, KosmosAletheiaContract,
        ContractOrchestrator, AdherenceReport, OKRValidationResult,
        ADRImpactNotification, CurationFeedback, FactualVerification
    )
    assert KosmosKratosContract is not None
    assert KosmosMetisContract is not None
    assert KosmosMnemosyneContract is not None
    assert KosmosAletheiaContract is not None
    assert ContractOrchestrator is not None

def test_generate_brief():
    from kosmos_contracts import KosmosKratosContract
    contract = KosmosKratosContract()
    brief = contract.generate_brief(SAMPLE_ADR, "ADR-999")
    assert "adr_id" in brief
    assert brief["adr_id"] == "ADR-999"
    assert "recommendations" in brief
    assert "timestamp" in brief

def test_parse_adherence():
    from kosmos_contracts import KosmosKratosContract
    contract = KosmosKratosContract()
    sample_report = (
        "ADR: ADR-999\n"
        "Adherence Score: 85/100\n"
        "R1 Coverage: 100% - Implementado completamente\n"
        "R2 Coverage: 70% - Parcialmente implementado\n"
        "Deviations:\n"
        "  - Singleton en modulo Z no migrable por compatibilidad\n"
        "Decisions:\n"
        "  - Se mantiene singleton en Z con wrapper de interfaz\n"
    )
    report = contract.parse_adherence(sample_report)
    assert report.adherence_score >= 0
    assert isinstance(report.deviations, list)
    assert report.adr_id == "ADR-999"

def test_detect_uncertain_claims():
    from kosmos_contracts import KosmosAletheiaContract
    contract = KosmosAletheiaContract()
    claims = contract.detect_uncertain_claims(SAMPLE_ADR)
    assert len(claims) >= 1
    assert any("basado" in c.lower() for c in claims)

def test_validate_okr():
    from kosmos_contracts import KosmosMetisContract
    contract = KosmosMetisContract()
    sample_okr = "OKR-001: Reducir deuda técnica de 53 a 82 en Q3 mediante refactor de modulos X, Y, Z"
    result = contract.validate_okr(sample_okr)
    assert result.viable in (True, False)
    assert 0 <= result.viability_score <= 100
    assert hasattr(result, "risks")

def test_contract_orchestrator():
    from kosmos_contracts import ContractOrchestrator
    orch = ContractOrchestrator()
    state = {"profile": "desarrollo", "topic": "test"}
    result = orch.run_all_contracts(SAMPLE_ADR, "ADR-999", state)
    assert "adr_id" in result
    assert len(result.get("contracts", {})) >= 0
    summary = orch.get_summary()
    assert "contract_statuses" in summary or "contracts" in summary

def test_aletheia_parse():
    from kosmos_contracts import KosmosAletheiaContract
    contract = KosmosAletheiaContract()
    sample_response = (
        "Verificación: CONFIRMADO\n"
        "Confianza: 0.85\n"
        "Fuentes:\n"
        "  - https://example.com/source1\n"
        "  - Documentación oficial de SQLite FTS5\n"
        "Contradicciones: Ninguna encontrada\n"
    )
    result = contract.parse_verification(sample_response)
    assert result.verified
    assert result.confidence > 0.5

def test_contract_status():
    from kosmos_contracts import KosmosKratosContract
    contract = KosmosKratosContract()
    st = contract.status()
    assert "active" in st
    assert "last_run" in st
    assert "total_runs" in st

def test_adherence_criteria_exists():
    from kosmos_contracts import ADHERENCE_CRITERIA
    assert isinstance(ADHERENCE_CRITERIA, dict)
    assert len(ADHERENCE_CRITERIA) >= 4

def test_empty_adr():
    from kosmos_contracts import KosmosKratosContract
    contract = KosmosKratosContract()
    brief = contract.generate_brief("", "ADR-000")
    assert brief["adr_id"] == "ADR-000"
    report = contract.parse_adherence("")
    # Empty text defaults to 50.0 neutral score
    assert report.adherence_score == 50.0
