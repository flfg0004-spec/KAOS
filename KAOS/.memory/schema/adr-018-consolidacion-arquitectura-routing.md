# ADR-018: Consolidación de la Arquitectura de Routing

**Estado**: Aceptado  
**Fecha**: 2026-05-29  
**Contexto**: Migración completa de 4 paquetes superpuestos a un único canónico.

## Decisión

Consolidar todo el sistema de routing, tracking, calidad y observabilidad en el paquete **`lib.aether`**, eliminando los 3 paquetes legacy.

## Paquetes eliminados

| Paquete | LOC | Reemplazado por |
|---------|-----|----------------|
| `lib/dsol.py` | 771 | `lib.aether.*` |
| `lib/ether/` (9 facades + judge + eval) | ~500 | `lib.aether.*` |
| `lib/ether_v2/` (11 archivos) | ~2,500 | `lib.aether.*` |

## Mapeo funcional legacy → aether

| Función/Símbolo legacy | Ubicación actual |
|------------------------|-----------------|
| `resolve_model()` | `lib.aether.router.resolve_model` |
| `chat()` | `lib.aether.client.chat` |
| `call_api()` | `lib.aether.client.call_api` |
| `build_prompt()` | `lib.aether.client.build_prompt` |
| `build_optimized_context()` | `lib.aether.client.build_optimized_context` |
| `generate_structured()` | `lib.aether.client.generate_structured` |
| `allocate()` | `lib.aether.client.allocate` |
| `estimate_cache_ratio()` | `lib.aether.client.estimate_cache_ratio` |
| `get_output_config()` | `lib.aether.client.get_output_config` |
| `extract_cache_metrics()` | `lib.aether.client.extract_cache_metrics` |
| `configure_thinking()` | `lib.aether.client.configure_thinking` |
| `status()` / `reset_tracker()` | `lib.aether.client.*` |
| `TokenTracker` | `lib.aether.tracker.EtherTracker` |
| `CircuitBreaker` | `lib.aether.circuit.CircuitBreaker` |
| `_CIRCUIT_BREAKER` | `lib.aether.circuit._ETHER_CIRCUIT_BREAKER` |
| `TASK_MODEL_MAP` | `lib.aether.config.TASK_MODEL_MAP` (multi-priority) |
| `MODEL_TIERS` / `BUDGETS` | `lib.aether.config.*` |
| `AGENT_DEFAULT_TASK` | `lib.aether.config.*` |
| `MODEL_FALLBACK_CHAIN` | `lib.aether.config.*` |
| `COST_CAPS` / `COST_RATES` | `lib.aether.config.*` |
| `run_eval_pipeline()` | `lib.aether.eval.run_eval_pipeline` |
| `trigger_eval()` | `lib.aether.eval.trigger_eval` |
| `auto_eval_if_needed()` | `lib.aether.eval.auto_eval_if_needed` |
| `EtherJudge` | `lib.aether.judge.EtherJudge` |
| `DEFAULT_RUBRIC` / `TASK_RUBRICS` | `lib.aether.judge.*` |
| `QualityStore` | `lib.aether.quality_store.QualityStore` |
| `ABTest` | `lib.aether.ab_testing.ABTest` |
| `Timer` / `observe` | `lib.aether.observability.*` |
| `RateLimiter` / `check_rate_limit` | `lib.aether.limiter.*` |
| `ModelTaskRule` / `ModelResolution` | `lib.aether.config.*` |
| `AGENT_TASK_MODEL` | `lib.aether.config.AGENT_TASK_MODEL` |

## Mejoras introducidas durante la consolidación

1. **Router multi-priority 10-stage**: override → multimodal → base(priority) → quality rerank → budget downgrade → cb fallback
2. **Quality-aware routing**: `resolve_model()` consulta `QualityStore` para rerankear candidatos por calidad histórica
3. **Budget enforcement**: downgrade automático a `go-flash` si budget semanal < $0.01
4. **ModelTaskRule**: `TASK_MODEL_MAP` convertido a formato multi-priority con prioridades, thinking, tier, multimodal support
5. **AGENT_TASK_MODEL**: mapeo agente → tarea por defecto → modelo por defecto
6. **EvalPipeline + DeepEval**: absorbido de ether_v2 con feature flag `ETHER_DEEPEVAL_ENABLED`
7. **QualityStore**: logging sampling 10% en `chat()` + auto-eval cada N llamadas
8. **Observability**: Timer + observe con fallback a JSONL cuando LangFuse no disponible
9. **Distribución objetivo**: flash 40%, mimo 40%, pro 5%, kimi 15%

## Consecuencias

### Positivas
- Single source of truth para routing, tracking y calidad
- Eliminación de ~3,700 LOC de código muerto/duplicado
- 0 ambigüedad sobre qué router usar
- Pipeline de resolución más robusto (10 etapas vs 6 originales)

### Negativas
- Breaking change para cualquier código externo que importara de `lib.dsol`, `lib.ether` o `lib.ether_v2`

## Micro-deuda técnica remanente

| Ítem | Prioridad | Acción |
|------|-----------|--------|
| `lib/telegram.py` (8 LOC, 2 consumers) | Baja | Migrar imports o mantener facade |
| `lib/dal.py`, `synapse.py`, `deerflow_*` | N/A | Módulos independientes válidos |

## Diagrama de arquitectura final

```
┌─────────────────────────────────────────────────────┐
│                    lib.aether                        │
│  ┌──────────┐ ┌──────────┐ ┌──────────────────────┐ │
│  │  router   │ │  client   │ │       config         │ │
│  │  10-stage │ │  chat()   │ │  ModelTaskRule       │ │
│  │  quality  │ │  call_api │ │  TASK_MODEL_MAP      │ │
│  │  budget   │ │  build_*  │ │  AGENT_TASK_MODEL    │ │
│  └──────────┘ └──────────┘ └──────────────────────┘ │
│  ┌──────────┐ ┌──────────┐ ┌──────────────────────┐ │
│  │ circuit   │ │ tracker   │ │     quality_store    │ │
│  │ CB thread-│ │ EtherTrkr │ │  QualityStore        │ │
│  │ safe+pers │ │ thread-sf │ │  quality-aware route │ │
│  └──────────┘ └──────────┘ └──────────────────────┘ │
│  ┌──────────┐ ┌──────────┐ ┌──────────────────────┐ │
│  │   eval    │ │ab_testing │ │    observability     │ │
│  │EvalPipe   │ │ ABTest    │ │  Timer + observe     │ │
│  │DeepEval   │ │ A/B test  │ │  LangFuse + JSONL   │ │
│  └──────────┘ └──────────┘ └──────────────────────┘ │
│  ┌──────────┐ ┌──────────┐ ┌──────────────────────┐ │
│  │   judge   │ │  limiter  │ │      providers       │ │
│  │EtherJudge │ │RateLimtr │ │  Router9, MiMo       │ │
│  │LLM-as-jdg │ │          │ │                      │ │
│  └──────────┘ └──────────┘ └──────────────────────┘ │
└─────────────────────────────────────────────────────┘
          ▲
          │ único punto de entrada
          │
┌─────────┴───────────────────────────────────────────┐
│           Consumidores (40+ archivos)                 │
│  orchestrator.py  pipeline.py  llm.py  mcp_*.py      │
│  hydrate.py  hyde.py  cot.py  dashboard.py           │
│  agent_executor.py  tests/*.py  cli_pipeline.py      │
└─────────────────────────────────────────────────────┘
```

## Score Journey

| Evaluación | Score | Estado |
|-----------|-------|--------|
| Eval #1 — Triple router (dsol + ether + aether + ether_v2) | ~65% | Caos de 4 paquetes superpuestos |
| Eval #2 — Core migrado, periferia pendiente | 72% | 8 archivos migrados |
| Eval #3 — F1+F2 completados | 82% | Deuda: ether/judge, ether/eval, ~20 consumers |
| Eval Final — Consolidación completa | ~92% | 0 legacy refs, paquetes eliminados |
