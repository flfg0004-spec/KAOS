---
audience: agent
type: service
name: DSOL
role: routing
description: "DeepSeek Optimization Layer v2 — API client, token tracking, multi-model routing, circuit breaker, rate limiting, and cache optimization"
status: active
score: 53
score_target: 75
lines: 807
monolith: true
owner: kratos
tags: [dsol, routing, optimization, refactor, circuit-breaker, token-tracking]
aliases: [DeepSeek Optimization Layer, dsol.py, DSOL v2]
created: 2026-05-20
modified: 2026-05-26
related_adrs:
  - ADR-004-deepseek-optimization-layer
  - ADR-010-integracion-dsol-langgraph
  - ADR-012-dsol-refactor-medio
  - ADR-013-circuitbreaker-unificado
---

# DSOL — DeepSeek Optimization Layer v2

## Estado Actual
- **Score de calidad**: 53/100
- **Monolito**: 807 líneas en `_scripts/lib/dsol.py`
- **Funcionalidades mezcladas**: Router, TokenTracker, CircuitBreaker, RateLimiter, API client, cache optimizer, JSON generator, CLI status
- **Dependencias**: `lib/llm.py`, `lib/cost_optimizer.py`, `lib/cache_warmer.py`

DSOL implementa `[[ADR-004-deepseek-optimization-layer]]` como capa de routing multi-modelo que decide qué modelo usar (go-flash, go-pro, go-kimi-latest) según complejidad de tarea. También se integra con `[[ADR-010-integracion-dsol-langgraph]]` donde LangGraph decide QUÉ agente ejecuta y DSOL decide CÓMO ejecuta.

## Plan de Refactor: Opción B

### Diagnóstico
El archivo `dsol.py` es un monolito de 807 líneas que mezcla 7 responsabilidades distintas:
1. Router multi-modelo (`resolve_model`, `TASK_MODEL_MAP`)
2. Token tracker persistente (`TokenTracker`)
3. Circuit breaker (`CircuitBreaker`)
4. Rate limiter (`RateLimiter`)
5. API client (`call_api`, `chat`, `call_structured`)
6. Cache optimizer (`build_optimized_context`, `estimate_cache_ratio`)
7. CLI interface (`status`, `reset_tracker`)

Además, hay duplicación de CircuitBreaker entre `dsol.CircuitBreaker` y `cost_optimizer.CircuitBreaker` (ADR-013).

### Arquitectura Objetivo: 6 Módulos + Fachada

```
lib/
├── dsol.py                  ← Fachada: re-exporta APIs públicas
├── dsol/
│   ├── router.py            ← TASK_MODEL_MAP, resolve_model, fallback chain
│   ├── token_tracker.py     ← TokenTracker persistente (token-usage.json)
│   ├── circuit_breaker.py   ← CircuitBreaker unificado (fusión dsol + cost_opt)
│   ├── rate_limiter.py      ← RateLimiter con token bucket
│   ├── api_client.py        ← call_api, chat, call_structured, generate_structured
│   └── config.py            ← BUDGETS, THINKING_CONFIG, MODEL_TIERS, constants
```

### Score Objetivo: >75/100
- Cohesión: de 35 → 85 (cada módulo tiene una responsabilidad única)
- Acoplamiento: de 65 → 80 (fachada desacopla consumidores)
- Testeabilidad: de 40 → 90 (módulos aislados, mocking sencillo)
- Mantenibilidad: de 50 → 85 (archivos < 200 líneas cada uno)

## Work Packages (10 WP, 6 días calendario)

| WP | Módulo | Depende de | Esfuerzo | Score post |
|----|--------|-----------|----------|-----------|
| WP1 | `dsol/config.py` | — | 0.5d | 55 |
| WP2 | `dsol/circuit_breaker.py` | WP1 | 0.5d | 58 |
| WP3 | `dsol/rate_limiter.py` | WP1 | 0.5d | 60 |
| WP4 | `dsol/token_tracker.py` | WP1 | 0.5d | 62 |
| WP5 | `dsol/api_client.py` | WP1, WP2, WP3, WP4 | 1d | 68 |
| WP6 | `dsol/router.py` | WP1, WP2, WP5 | 1d | 72 |
| WP7 | `dsol.py` (fachada) | WP1–WP6 | 0.5d | 75 |
| WP8 | Migrar imports en `lib/llm.py` y `lib/orchestrator.py` | WP7 | 0.5d | 77 |
| WP9 | Test suite (unit + integración) | WP1–WP8 | 1d | 80 |
| WP10 | Limpieza de deuda técnica (deprecaciones, lint) | WP9 | 0.5d | 82 |

**Cronograma**: 6 días calendario, ejecución secuencial con solapamiento WP2-WP4.
**Responsable**: [[kratos]] (implementación)
**Valida**: [[kosmos]] (revisión arquitectura post-WP7)

## Riesgos

| Riesgo | Prob | Impacto | Mitigación |
|--------|------|---------|------------|
| Regresión en routing de producción | Media | Alto | WP9 integrado con test suite existente (`test_dsol.py`, `test_router.py`) |
| Conflictos de import circular entre módulos dsol/ | Baja | Medio | WP7 fachada resuelve dependencias; usar lazy imports si es necesario |
| Duplicación temporal (monolito + módulos coexistiendo) | Alta | Medio | WP8 elimina el monolito; migración gradual por agente |

## Referencias
- [[ADR-004-deepseek-optimization-layer]] — DSOL original
- [[ADR-010-integracion-dsol-langgraph]] — Integración DSOL + LangGraph
- [[ADR-012-dsol-refactor-medio]] — Este plan documentado como ADR
- [[ADR-013]] — Fusión de circuit breakers
- [[kratos]] — Responsable de implementación
- [[kosmos]] — Validador arquitectónico
- mcp-dsol — MCP tool que expone [[DSOL]]
