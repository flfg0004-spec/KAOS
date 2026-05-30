---
audience: agent
title: "Aether Routing v3 — Sistema de Routing Multi-Modelo"
date: 2026-05-29
agent: kosmos
status: complete
type: concept
tags: [aether, routing, models, dsol, architecture, mcp]
aliases: [Aether, DSOL, Ether, model-routing]
---

## ¿Qué es Aether?

Aether es el **sistema de routing multi-modelo v3** de KAOS. Es la consolidación y reemplazo de DSOL (v1, monolito de 807 líneas, score 53/100) y Ether (v2, prototipo de 9 facades). Es un paquete Python de 16 archivos en `.memory/_scripts/lib/aether/`.

**Evolución histórica:**
- DSOL (lib/dsol.py, v1): Primera capa de routing, monolito con 7 responsabilidades mezcladas
- Ether (lib/ether/, v2): Routing inteligente con 9 facades + judge + eval
- Ether v2 (lib/ether_v2/, prototipo): 11 archivos, prototipo paralelo
- **Aether (lib.aether, v3): Consolidación final — 16 archivos, responsabilidad única cada uno**

DSOL aún existe como fachada de backward compatibility que re-exporta `_ETHER_CIRCUIT_BREAKER`.

## Arquitectura (16 archivos)

| Archivo | Líneas | Propósito |
|---------|--------|-----------|
| `__init__.py` | 69 | Fachada pública, re-exporta todo |
| `router.py` | 225 | **Router multi-priority 10-stage** — resolve_model() |
| `client.py` | 347 | Cliente API (chat, call_api, build_prompt, generate_structured, configure_thinking) |
| `config.py` | 281 | Constantes, feature flags, model maps, thinking_config, budgets |
| `config_loader.py` | 163 | Carga configuración desde aether.yaml |
| `circuit.py` | 193 | **Circuit Breaker** unificado (thread-safe + persistente en JSON) |
| `tracker.py` | 312 | **EtherTracker** — tracking de tokens y costos (persistente, batch writes cada 10 calls) |
| `quality_store.py` | 242 | **QualityStore** — scores de calidad históricos por modelo+task_type |
| `eval.py` | 684 | **EvalPipeline** — evaluación DeepEval + LLM-as-judge con auto-eval |
| `ab_testing.py` | 219 | **ABTest** — A/B testing framework con análisis estadístico |
| `observability.py` | 312 | **Observabilidad** — LangFuse tracing + fallback JSONL |
| `limiter.py` | 55 | **RateLimiter** — token bucket rate limiter por agente |
| `judge/__init__.py` | 356 | **EtherJudge** — LLM-as-judge con 6 dimensiones y rúbricas por tarea |
| `providers/__init__.py` | 1 | Vacío (reservado) |
| `providers/router9.py` | 91 | Cliente para 9Router (40+ providers) |
| `cli.py` | 204 | CLI interactiva: aether status, routing, costs, config |

## Pipeline resolve_model() — 10 Etapas

```
 1. model_override → Si se pasa explícitamente, se usa directamente
 2. TASK_MODEL_MAP → Busca por task_type (lint, research, strategy, etc.)
 3. AGENT_DEFAULT_TASK → Por agente (aletheia→research, metis→strategy, etc.)
 4. Default absoluto → go-flash (DeepSeek V4 Flash)
 5. Multimodal preference → Si hay imágenes, prioriza modelos con soporte
 6. Quality-aware rerank → Reordena candidatos por QualityStore scores
 7. Long-context routing → Prompts >100K tokens → Kimi (go-kimi-latest)
 8. Budget-aware downgrade → Si budget semanal < umbral, downgrade a go-flash
 9. Circuit Breaker fallback → Si modelo final no disponible, recorre fallback chain
10. Return → {model, thinking, tier, resolved_by}
```

## TASK_MODEL_MAP (19 tipos de tarea)

| Tarea | Modelo | Thinking | Tier |
|-------|--------|----------|------|
| lint | go-flash | null | flash |
| extract | go-mimo | null | mimo |
| hydrate | go-flash | null | flash |
| wikilinks | go-mimo | null | mimo |
| curation | go-flash | null | flash |
| code_gen | go-flash | null | flash |
| code_simple | go-mimo | null | mimo |
| general | go-flash | null | flash |
| research | go-pro | high | pro |
| analyze | go-pro | high | pro |
| adr | go-pro | high | pro |
| factual | go-pro | high | pro |
| synthesize | go-kimi-latest | null | kimi |
| strategy | go-kimi-latest | null | kimi |
| verify | go-flash | null | flash |
| cross_check | go-flash | null | flash |
| code_agentic | go-kimi-latest | null | kimi |
| diversity | go-mimo | null | mimo |

## AGENT_DEFAULT_TASK (8 agentes)

| Agente | Default Task | Default Model |
|--------|-------------|---------------|
| aletheia | research | go-pro |
| kosmos | analyze | go-pro |
| metis | strategy | go-kimi-latest |
| kratos | code_gen | go-flash |
| mnemosyne | curation | go-flash |
| kronos | general | go-flash |
| critic | verify | go-pro |
| planner | general | go-flash |

## Modelos Disponibles

| Model Key | Provider | Model Real | Input/1K | Output/1K |
|-----------|----------|-----------|----------|-----------|
| go-flash | OpenCode Go | deepseek-v4-flash | $0.00014 | $0.00028 |
| go-pro | OpenCode Go | deepseek-v4-pro | $0.00174 | $0.00348 |
| go-kimi-latest | OpenCode Go | kimi-k2.6 | $0.00095 | $0.00400 |
| go-mimo | OpenCode Go | mimo-v2-pro | $0.000014 | $0.000028 |
| go-qwen | OpenCode Go | qwen3.5-plus | $0.00010 | $0.00020 |
| mimo-direct | Xiaomi Direct | mimo-v2.5-pro | $0.000014 | $0.000028 |
| deepseek-direct-flash | DeepSeek Direct | deepseek-v4-flash | — | — |
| deepseek-direct-pro | DeepSeek Direct | deepseek-v4-pro | — | — |
| router9-minimax | 9Router Proxy | MiniMax M2.7 | $0.0000002 | $0.0000002 |
| router9-glm | 9Router Proxy | GLM-5.1 | $0.0000006 | $0.0000006 |

## Fallback Chains

```
go-flash: go-flash → go-mimo → go-qwen → go-pro → go-kimi-latest
go-pro: go-pro → go-mimo → go-kimi-latest → go-flash → go-qwen
go-kimi-latest: go-kimi-latest → mimo-direct → go-pro → go-flash → go-qwen
go-mimo: go-mimo → go-flash → go-qwen → go-pro → go-kimi-latest
```

## Cost Caps (Semanales)

| Tier | Weekly USD | Daily Calls |
|------|-----------|-------------|
| flash | $3.00 | 500 |
| mimo | $2.00 | 1000 |
| pro | $0.50 | 50 |
| kimi | $1.00 | 30 |

## Feature Flags (aether.yaml)

```
ether_mimo_enabled: true
ether_mimo_direct_enabled: true
ether_kimi_enabled: true
ether_context_routing: true        # prompts >100K tokens → Kimi
ether_multimodal_enabled: true
ether_budget_enforcement: false     # false durante desarrollo
ether_langfuse_enabled: false       # false, usa JSONL fallback
ether_deepeval_enabled: false       # false, usa EtherJudge
quality_routing_enabled: true
ether_eval_sample_size: 10
```

## Componentes Principales

### Circuit Breaker
Por modelo. Estados: closed → open → half-open → closed.
Config:
- go-flash: threshold=3, timeout=300s
- go-pro: threshold=3, timeout=300s
- go-kimi-latest: threshold=2, timeout=600s
- go-mimo: threshold=2, timeout=300s
Persistencia en `.memory/cache/circuit_breaker_aether.json`. Thread-safe con file locking.

### QualityStore
Registro histórico de calidad por modelo+task_type. Persistente en `quality_history.json`. Usado por quality-aware reranking en etapa 6 del router.

### EtherTracker
Tracking de tokens y costos por sesión: modelo, agente, tarea, tokens, costo, latencia, multimodal. Persistente en `token-usage.json`. Batch writes cada 10 calls. Breakdown por modelo, agente, día. Budget checking con alertas (warning 80%, exceeded 100%).

### EtherJudge
LLM-as-judge con 6 dimensiones (V, C, CP, R, U) y rúbricas por tarea. Evaluación automática con sampling configurable (default 10%).

### AB Testing
ABTest class con `should_route_to_b()`, `record_result()`, `get_winner()`. Análisis estadístico con mínimo 10 muestras por grupo.

### Observabilidad
Timer + decorador `@observe`. Tracing con LangFuse. Acceptance sampling por tier: flash 10%, pro 50%, kimi 80%, mimo 30%. Fallback a JSONL.

### RateLimiter
Token bucket rate limiter por agente:
- aletheia: 100 req/min
- kratos: 60 req/min
- kosmos: 30 req/min
- mnemosyne: 20 req/min
- metis: 10 req/min
- kronos: 30 req/min

## APIs Expuestas

| API | Archivo | Descripción |
|-----|---------|-------------|
| `resolve_model()` | router.py | Routing multi-priority |
| `chat()` | client.py | Chat de alto nivel con routing automático |
| `call_api()` | client.py | Llamada directa a API |
| `build_prompt()` | client.py | Construcción optimizada de prompts |
| `generate_structured()` | client.py | Generación JSON estructurado |
| `configure_thinking()` | client.py | Configuración de thinking mode |
| `CircuitBreaker` | circuit.py | Circuit breaker thread-safe |
| `EtherTracker` | tracker.py | Tracking de tokens y costos |
| `QualityStore` | quality_store.py | Scores de calidad históricos |
| `EvalPipeline` | eval.py | Evaluación automática |
| `ABTest` | ab_testing.py | A/B testing framework |
| `EtherJudge` | judge/ | LLM-as-judge multi-dimensión |
| `RateLimiter` | limiter.py | Rate limiting por agente |
| `Router9Client` | providers/router9.py | Cliente 9Router |
| `CLI` | cli.py | Interfaz de línea de comandos |

## CLI

```
python -m lib.aether.cli status    # Dashboard completo
python -m lib.aether.cli routing   # Tabla Task → Model
python -m lib.aether.cli costs     # Budget status
python -m lib.aether.cli config    # Muestra YAML actual
```

## Relación con el Ecosistema KAOS

- **LangGraph** decide QUÉ agente ejecuta
- **Aether** decide CÓMO y DÓNDE ejecuta (qué modelo usar)
- Los agentes (Metis, Kratos, etc.) son consumidores de Aether
- **agy-bridge** es un provider externo para modelos Claude/GPT/Gemini
- **OpenCode agents** + **agno agents** usan Aether via mcp-dsol MCP server

## Fuentes
- Código: `.memory/_scripts/lib/aether/` (16 archivos)
- Config: `.memory/_scripts/aether.yaml`
- Tests: `.memory/_scripts/tests/test_aether_smoke.py`, `test_aether_router.py`
- ADR: `.memory/schema/adr-018-consolidacion-arquitectura-routing.md`
