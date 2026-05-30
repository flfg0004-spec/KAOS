# Aether v3 → v3.1: Arquitectura de Optimización y Consolidación

**Autor**: Kosmos (Κόσμος) — Arquitecto de Sistemas KAOS  
**Fecha**: 2026-05-29  
**Estado**: Borrador arquitectónico  
**ADR relacionados**: ADR-010 (DSOL), ADR-003 (Verificación)

---

## Resumen Arquitectónico

Aether v3 es una biblioteca de routing multi-modelo con 16 módulos y ~4,200 líneas de código. Su núcleo es un pipeline de 10 etapas que resuelve qué modelo usar. Sin embargo, sufre de duplicación en el sistema de calidad (QualityStore + EvalPipeline + EtherJudge + inline sampling), proveedores aislados (Router9Client existe pero está huérfano), un `client.py` con responsabilidades mezcladas, y 11 feature flags con solapamientos. La propuesta v3.1 consolida en 10 módulos (~3,500 líneas), reduce flags a 6, unifica el sistema de calidad bajo QualityStore como fuente única de verdad, y separa responsabilidades en `client.py` en tres capas independientes.

**Principios rectores**: Menos acoplamiento, menos código, menos flags, más testeabilidad.

---

## PARTE 1: Diagrama de Arquitectura Actual

```
┌─────────────────────────────────────────────────────────────────────────┐
│                          EXTERNAL CALLERS                               │
│  ┌──────────┐  ┌──────────┐  ┌──────────┐  ┌──────────┐  ┌──────────┐ │
│  │llm.py    │  │orchestra-│  │mcp_dsol  │  │dashboard │  │cli_pipe- │ │
│  │agent_llm │  │tor.py    │  │.py (MCP) │  │.py       │  │line.py   │ │
│  │_call()   │  │get_dsol_ │  │          │  │          │  │          │ │
│  │          │  │config()  │  │          │  │          │  │          │ │
│  └────┬─────┘  └────┬─────┘  └────┬─────┘  └────┬─────┘  └────┬─────┘ │
│       │             │             │             │             │        │
└───────┼─────────────┼─────────────┼─────────────┼─────────────┼────────┘
        │             │             │             │             │
        ▼             ▼             ▼             ▼             ▼
┌─────────────────────────────────────────────────────────────────────────┐
│                       AETHER v3 - 16 MÓDULOS                            │
│                                                                         │
│  ┌─────────────────────────────────────────────────────────────────┐   │
│  │  __init__.py (facade — lazy imports c/ exception handlers)      │   │
│  └─────────────────────────────────────────────────────────────────┘   │
│                                                                         │
│  ┌─────────────────────────────────────────────────────────────────┐   │
│  │  client.py (350 lines — 4 responsabilidades mezcladas)          │   │
│  │  ┌──────────┐ ┌───────────┐ ┌───────────┐ ┌───────────────┐   │   │
│  │  │ chat()   │ │ call_api()│ │call_struc-│ │ status()      │   │   │
│  │  │ routing  │ │ raw LLM  │ │tured()    │ │ reset_tracker │   │   │
│  │  │ + track  │ │ call      │ │ DEPRECATED│ │               │   │   │
│  │  │ + sample │ │           │ │           │ │               │   │   │
│  │  └────┬─────┘ └─────┬─────┘ └───────────┘ └───────────────┘   │   │
│  └───────┼─────────────┼──────────────────────────────────────────┘   │
│          │             │                                              │
│          ▼             ▼                                              │
│  ┌──────────────────────────────────────────────────────────────┐    │
│  │  router.py (264 líneas — pipeline 10-etapas espeso)         │    │
│  │  ┌─────┐ ┌────┐ ┌───────┐ ┌────┐ ┌────────┐ ┌───────────┐ │    │
│  │  │1.Ov-│ │2.  │ │3.Mul- │ │4.  │ │5.Pick  │ │6.Quality  │ │    │
│  │  │rride│ │Can-│ │timodal│ │Kimi│ │First   │ │Rerank     │ │    │
│  │  │     │ │did- │ │Pref   │ │    │ │Avail   │ │           │ │    │
│  │  │     │ │ates │ │       │ │    │ │        │ │           │ │    │
│  │  └─────┘ └────┘ └───────┘ └────┘ └────────┘ └───────────┘ │    │
│  │  ┌───────────┐ ┌──────┐ ┌──────────────┐ ┌───────────┐    │    │
│  │  │7.Long Ctx │ │8.   │ │9.Quality     │ │10.CB      │    │    │
│  │  │Routing    │ │Budget│ │Feedback      │ │Fallback   │    │    │
│  │  └───────────┘ └──────┘ └──────────────┘ └───────────┘    │    │
│  └──────────────────────────────────────────────────────────────┘    │
│                                                                         │
│  ┌──────────────────┐ ┌──────────────────┐ ┌────────────────────┐     │
│  │  tracker.py      │ │  circuit.py      │ │  limiter.py        │     │
│  │  EtherTracker    │ │  CircuitBreaker  │ │  RateLimiter       │     │
│  │  312 líneas      │ │  196 líneas      │ │  55 líneas ──┬─────┘     │
│  │  persistente     │ │  persistente     │ │              │           │
│  └────────┬─────────┘ └────────┬─────────┘ │  NUNCA USADO │           │
│           │                    │           └──────────────┘           │
│           ▼                    ▼                                      │
│  ┌──────────────────┐ ┌───────────────────────────────────────────┐  │
│  │  config.py       │ │  config_loader.py                         │  │
│  │  281 líneas      │ │  163 líneas — carga aether.yaml          │  │
│  │  flags, maps,    │ │  SINGLETON — sin hot-reload               │  │
│  │  costos, caps    │ └───────────────────────────────────────────┘  │
│  └──────────────────┘                                                │
│                                                                       │
│  ┌─────────────────────────────────────────────────────────────┐    │
│  │  ┌─────────────┐  ┌──────────────┐  ┌─────────────┐       │    │
│  │  │QualityStore │◄─│ EvalPipeline │  │ EtherJudge  │       │    │
│  │  │268 líneas   │  │ 684 líneas   │  │ (judge/)    │       │    │
│  │  │SCORE SOURCE │  │ LLM-as-judge │  │ 356 líneas  │       │    │
│  │  │OF TRUTH?    │  │ + DeepEval   │  │ Standalone  │       │    │
│  │  └─────────────┘  └──────────────┘  └─────────────┘       │    │
│  │            ▲ ─ ─ ─ ─ ─ ─ ─ ─ ─ ─ ─ ─ ─ ─ ─ ─              │    │
│  │            └── client.py inline sampling (7.0 hardcoded)   │    │
│  └─────────────────────────────────────────────────────────────┘    │
│                                                                       │
│  ┌──────────────────────┐    ┌──────────────────────────────────┐   │
│  │  observability.py    │    │  ab_testing.py                   │   │
│  │  312 líneas          │    │  219 líneas ── NUNCA INTEGRADO   │   │
│  │  LangFuse + JSONL    │    │                                  │   │
│  └──────────────────────┘    └──────────────────────────────────┘   │
│                                                                       │
│  ┌──────────────┐   ┌────────────────────────────────────────────┐  │
│  │  cli.py      │   │  providers/                                │  │
│  │  204 líneas  │   │  ├── __init__.py (VACÍO)                   │  │
│  │  Dashboard   │   │  └── router9.py (91 líneas ── ORFANADO)   │  │
│  └──────────────┘   └────────────────────────────────────────────┘  │
└─────────────────────────────────────────────────────────────────────────┘

═══ CUELLOS DE BOTELLA ═══

  ⚡ HOT PATH (agent_llm_call → resolve_model → API → track):
    1. resolve_model(): 10 etapas secuenciales sin memoización
    2. quality_feedback (etapa 9): QualityStore I/O en hot path
       → cada llamada potencialmente lee quality_history.json
    3. client.py inline sampling: 10% de llamadas escriben a QualityStore
       con scores hardcodeados (7.0) — CONTAMINA los datos
    4. tracker.track(): pending flush (cada 10 llamadas) bloquea con I/O

═══ CÓDIGO MUERTO / SUBUTILIZADO ═══

  ✗ providers/__init__.py → vacío
  ✗ providers/router9.py → existe, cost_rates registrados, pero NEVER usado
  ✗ ab_testing.py → framework completo, nunca integrado al router o client
  ✗ judge/__init__.py (EtherJudge) → nunca llamado desde EvalPipeline ni client
  ✗ client.call_structured() → deprecated, sigue en el código
  ✗ router._base_resolve() → legacy, nadie la llama
  ✗ router._cheapest_fallback() → defines but never called
  ✗ router._kimi_fallback() → defines but never called
  ✗ limiter.check_rate_limit() → nunca llamado por ningun caller
  ✗ 4 funciones exportadas en __init__ sin uso externo:
    build_optimized_context, estimate_cache_ratio, extract_cache_metrics

═══ GAP: DSOL RESOLVE vs REALIDAD ═══

  orchestrator.get_dsol_config()
    └── llama a resolve_model() → resultado SOLO se loggea como metadata
        NO se pasa a agent_llm_call() ni se fuerza en los nodos

  agent_llm_call() en lib/llm.py
    └── llama a resolve_model() por su cuenta (DUPLICADO de resolución)
        → routing inconsistente: orchestrator resuelve X, llm.py resuelve Y
        → NINGÚN MECANISMO de enforcement conecta ambas resoluciones
```
---

## PARTE 2: Problemas Arquitectónicos Detallados

### P1. Pipeline 10-etapas espeso
**Descripción**: `router.py` tiene 264 líneas con 10 etapas en una sola función `resolve_model()`, 14 funciones helper privadas (algunas muertas), y dependencias directas de circuit breaker + quality store en medio del hot path.

**Impacto**:
- Difícil de testear cada etapa individualmente (requieren mock de `_ETHER_CIRCUIT_BREAKER`, `QualityStore`, `config`)
- Modificar una etapa (ej: quality rerank) puede romper las otras 9
- No hay trazabilidad de qué etapa decidió qué
- Bajo isolated test coverage — se testea el pipeline completo

**Archivos**: `router.py` (completo), `config.py` (flags consumidos por router)  
**Severidad**: ALTA — afecta mantenibilidad, testabilidad, y latencia potencial

### P2. Providers aislados
**Descripción**: `providers/router9.py` con 91 líneas implementa un cliente OpenAI-compatible para 9Router proxy. Los cost rates para `router9-minimax`, `router9-glm`, `router9-default` están registrados en `config.py` y `aether.yaml`. Pero `Router9Client` nunca se instancia. `providers/__init__.py` está vacío.

**Impacto**:
- Código muerto que se degrada con el tiempo
- No hay interfaz común para agregar nuevos providers (Router9, futuro fallback)
- Cada provider requiere integración manual en el pipeline

**Archivos**: `providers/router9.py`, `providers/__init__.py`, `config.py` (líneas 221-223)  
**Severidad**: ALTA — inversión en código no capitalizada, patrón incorrecto

### P3. Acoplamiento chat-routing en client.py
**Descripción**: `client.py` (350 líneas) mezcla:
- **Routing**: `chat()` construye prompt, resuelve modelo, llama API, trackea, observa, samplea calidad
- **API call**: `call_api()` llama a `agent_llm_call()` y parsea resultado
- **Tracker**: `status()` y `reset_tracker()` son wrappers de EtherTracker
- **Utilidades**: `build_prompt()`, `estimate_cache_ratio()`, `extract_cache_metrics()`, `allocate()`

**Impacto**:
- No se puede testear routing sin mockear API, tracker y observability
- `chat()` tiene 3 side effects: CB recording, observe(), QualityStore sampling, auto-eval trigger
- `call_structured()` está deprecated pero sigue en el código

**Archivos**: `client.py` (completo)  
**Severidad**: CRÍTICA — el entrypoint principal tiene demasiadas responsabilidades

### P4. get_dsol_config() no vinculante
**Descripción**: `orchestrator.get_dsol_config()` llama a `resolve_model()` para resolver el modelo de un agente, pero el resultado solo se usa como metadata en `orchestrator._handle_task_completion()`. `agent_llm_call()` en `lib/llm.py` vuelve a llamar a `resolve_model()` independientemente.

**Impacto**:
- Doble resolución = doble latencia, posible inconsistencia
- El orquestador no puede forzar un modelo específico a un agente
- No hay trazabilidad de "quién decidió qué modelo para esta tarea"

**Archivos**: `lib/orchestrator.py` (líneas 202-219), `lib/llm.py` (líneas 333-340)  
**Severidad**: MEDIA — no es un bug de ejecución pero sí de arquitectura

### P5. Sin hot-reload
**Descripción**: `config_loader.py` usa singleton pattern: `get_config()` cachea la instancia. Cambiar `aether.yaml` requiere reinicio del proceso. No hay `reload()` ni watch.

**Impacto**:
- Cambiar routing requiere matar el proceso (KAOS completo)
- No se puede A/B testear configuraciones sin reinicio
- Workaround: override por env vars, pero no cubre todos los cambios

**Archivos**: `config_loader.py` (líneas 151-158), `config.py` (líneas 12-16)  
**Severidad**: MEDIA — afecta agilidad operativa

### P6. Dos sistemas de calidad paralelos + contaminación
**Descripción**: Hay TRES mecanismos de evaluación de calidad que no conversan entre sí:
1. **QualityStore** (`quality_store.py`): almacena scores con interfaz `record()`
2. **EvalPipeline** (`eval.py`): evalúa con DeepEval o LLM-as-judge, escribe a QualityStore
3. **EtherJudge** (`judge/__init__.py`): evaluador de 6 dimensiones, 19 rúbricas de tarea, standalone
4. **client.py inline sampling** (líneas 203-217): escribe scores hardcodeados `7.0` en ~10% de las llamadas

**Impacto**:
- Los datos de QualityStore están contaminados por el sampling de `client.py` (scores 7.0 falsos)
- EtherJudge tiene rúbricas que EvalPipeline ignora
- No hay consistencia dimensional entre los evaluadores
- La calidad histórica no es confiable para `resolve_model()` etapa 6 y 9

**Archivos**: `quality_store.py`, `eval.py`, `judge/__init__.py`, `client.py` (líneas 203-226)  
**Severidad**: CRÍTICA — datos corruptos = decisiones de routing incorrectas

### P7. Flag fatigue
**Descripción**: 11 flags en `config.py` (líneas 237-247), algunos duplicados o contradictorios:

| Flag | ¿Redundante? | Razón |
|------|-------------|-------|
| `ETHER_MIMO_ENABLED` | SÍ | mimo ya en TASK_MODEL_MAP |
| `ETHER_MIMO_DIRECT_ENABLED` | SÍ | mismo caso |
| `ETHER_KIMI_ENABLED` | PARCIAL | usado en router pero se solapa con multimodal |
| `ETHER_CONTEXT_ROUTING` | PARCIAL | solo relevante si KIMI_ENABLED |
| `ETHER_MULTIMODAL_ENABLED` | PARCIAL | se solapa con KIMI_ENABLED |
| `ETHER_BUDGET_ENFORCEMENT` | ÚNICO | budget control |
| `ETHER_LANGFUSE_ENABLED` | ÚNICO | observability |
| `ETHER_DEEPEVAL_ENABLED` | ÚNICO | evaluation |
| `QUALITY_ROUTING_ENABLED` | ÚNICO | quality feedback |
| `ETHER_EVAL_SAMPLE_SIZE` | NO ES FLAG | es constante de configuración |
| `ETHER_CIRCUIT_BREAKER_ENABLED` | ÚNICO | circuit breaker |

**Impacto**: 11 flags = 11 variables de estado a considerar en tests, 11 combinaciones de override. Aumenta complejidad cognitiva.  
**Archivos**: `config.py` (líneas 237-281)  
**Severidad**: MEDIA

### P8. Código muerto académico
**Descripción**: Varias funciones nunca invocadas (ver lista en diagrama) que totalizan ~200 líneas de código no ejecutado.

**Impacto**:
- Incrementa la superficie de mantenimiento sin beneficio
- Crea falsa sensación de capacidad ("tenemos A/B testing!")
- Dificulta el análisis de cobertura

**Archivos**: Múltiples — ver sección Código Muerto en diagrama  
**Severidad**: BAJA pero persistente

---

## PARTE 3: Diseño de la Consolidación

### A. Unificación de Providers

**Problema**: Sin interfaz común, cada provider requiere integración manual ad-hoc en el pipeline.

**Solución**: Interfaz `BaseProvider` con contrato claro:

```python
@dataclass
class ProviderResponse:
    text: str
    model: str
    usage: dict  # {prompt_tokens, completion_tokens, total_tokens}
    error: str | None = None

class BaseProvider(ABC):
    """Interfaz común para todos los providers de Aether."""
    
    @property
    @abstractmethod
    def provider_name(self) -> str: ...
    
    @abstractmethod
    def chat(self, messages: list[dict], model: str, **kwargs) -> ProviderResponse: ...
    
    @abstractmethod
    def is_available(self) -> bool: ...
    
    @abstractmethod
    def get_supported_models(self) -> list[str]: ...
```

**Implementaciones**:
1. `OpenCodeGoProvider` — envuelve `lib.llm.agent_llm_call()` (el default actual)
2. `Router9Provider` — envuelve `Router9Client.chat()` (existe, reactivar)
3. `FallbackProvider` — routing entre providers como estrategia de resiliencia

**Interfaz de fábrica**:
```python
# providers/__init__.py
def get_provider(name: str = "opencode-go") -> BaseProvider: ...
def list_providers() -> dict[str, BaseProvider]: ...
```

**Beneficio**: Agregar un provider = implementar 4 métodos. Router9 sale de la caja. Tests unitarios con mock provider.  
**Costo**: ~150 líneas nuevas, ~50 para migrar router9.py.  
**Riesgo**: Bajo — interfaz nueva, código existente no se toca.

### B. Separación de Responsabilidades en client.py

**Problema**: `client.py` mezcla 4 responsabilidades.

**Solución**: Split en 3 capas:

```
client.py (antes: 350 líneas)
  │
  ├── router_call.py (nuevo, ~80 líneas)
  │   └── chat() → solo orquesta: detect → resolve → call → track → observe
  │       Delega en:
  │       - resolve_model() del router
  │       - provider.call() de la capa API
  │       - tracker.track()
  │       - observe()
  │
  ├── api_call.py (nuevo, ~60 líneas) → solo llamadas a provider
  │   └── call_provider() → get_provider().chat()
  │   └── call_structured() → DEPRECATED wrapper (eliminar en F2)
  │
  └── helpers.py (nuevo, ~60 líneas) → utilidades puras
      ├── build_prompt()
      ├── estimate_cache_ratio()
      ├── extract_cache_metrics()
      └── detect_images()
      └── estimate_prompt_size()
```

**Beneficio**: Cada módulo tiene 1 razón de cambio. Tests: mock provider en api_call, mock router en router_call.  
**Costo**: Mover ~200 líneas entre 3 archivos nuevos.  
**Riesgo**: Medio — cambiar entrypoint requiere actualizar imports de caller.

### C. Pipeline de Routing Más Modular

**Problema**: `resolve_model()` de 10 etapas en una función monolítica.

**Solución**: Convertir cada etapa en un paso independiente que implemente una interfaz común:

```python
# router.py → pipeline.py
@dataclass
class RoutingContext:
    task_type: str | None
    agent: str
    model_override: str | None
    prompt_size: int
    has_images: bool
    budget_remaining: float | None
    candidates: list[ModelTaskRule] = field(default_factory=list)
    model: str = "go-flash"
    thinking: str | None = None
    tier: str = "flash"
    resolved_by: str = ""

class RoutingStep(ABC):
    @abstractmethod
    def execute(self, ctx: RoutingContext) -> RoutingContext: ...
```

**Implementaciones**:
- `OverrideStep` — etapa 1 (model_override)
- `CandidateStep` — etapa 2 (obtener candidatos)
- `MultimodalStep` — etapa 3 (preferir multimodal)
- `KimiRoutingStep` — etapa 4 + 7 (Kimi legacy + long-context)
- `FirstAvailableStep` — etapa 5 (pick first)
- `QualityRerankStep` — etapa 6 (rerank por calidad)
- `BudgetStep` — etapa 8 (budget downgrade)
- `QualityFeedbackStep` — etapa 9 (quality feedback)
- `CBFallbackStep` — etapa 10 (circuit breaker fallback)

**Pipeline engine**:
```python
def resolve_model(**kw) -> dict:
    """Version simplificada: pipeline configurable de pasos."""
    ctx = RoutingContext(**kw)
    pipeline = [
        OverrideStep(),
        CandidateStep(),
        MultimodalStep() if ctx.has_images else None,
        KimiRoutingStep(),
        FirstAvailableStep(),
        QualityRerankStep(),
        BudgetStep(),
        QualityFeedbackStep(),
        CBFallbackStep(),
    ]
    for step in filter(None, pipeline):
        ctx = step.execute(ctx)
    return ctx.to_dict()
```

**Beneficio**:
- Cada paso se testea en aislamiento (1 input → 1 output)
- Pipeline configurable: orden, pasos activos/inactivos
- Fácil agregar nueva etapa sin tocar las otras
- Trazabilidad: cada paso puede loggear su decisión

**Costo**: ~200 líneas nuevas para pipeline engine + interfaces. Las etapas existentes se refactorizan a clases.  
**Riesgo**: Medio — refactor profundo de `router.py`.

### D. Consolidación de Calidad

**Problema**: 4 mecanismos de calidad que no hablan entre sí.

**Solución**: QualityStore como **única fuente de verdad** para scores de calidad:

```
                    ┌──────────────────┐
                    │   QualityStore   │
                    │  (single source  │
                    │   of truth)      │
                    └────────┬─────────┘
                             │
              ┌──────────────┼──────────────┐
              ▼              ▼              ▼
     ┌──────────────┐ ┌────────────┐ ┌──────────────┐
     │ EvalPipeline │ │ EtherJudge │ │ (externo)    │
     │ (DeepEval +  │ │ (6 dims)   │ │ DeepEval     │
     │ LLM-as-judge)│ │            │ │ directo      │
     └──────┬───────┘ └─────┬──────┘ └──────────────┘
            │               │
            └───────┬───────┘
                    ▼
          QualityStore.record()
```

**Cambios concretos**:
1. **Eliminar inline sampling de `client.py`**: remover líneas 203-226. El sampling debe ser explícito, no automático en el hot path.
2. **EtherJudge como evaluador adicional que alimenta QualityStore**: no cambia su interfaz, solo se asegura que llame a `QualityStore.record()`.
3. **EvalPipeline como orquestador de evaluación**: puede usar EtherJudge internamente como evaluador, o DeepEval. El resultado siempre va a QualityStore.
4. **QualityStore.record() validación de entrada**: rechazar scores fuera de rango 0-10, verificar que no sean todos idénticos (detectar contaminación).

**Eliminaciones concretas**:
- `eval.py`: rediseñar para que _toda_ evaluación pase por QualityStore
- `judge/__init__.py`: agregar `QualityStore.record()` en su método `evaluate()`
- `client.py`: eliminar inline sampling y auto-eval trigger (se mueve a EvalPipeline programado)

**Beneficio**: Scores confiables, una sola interfaz de query para el router, datos no contaminados.  
**Costo**: ~100 líneas modificadas, 0 nuevas.  
**Riesgo**: Bajo — la interfaz `QualityStore.record()` ya existe.

### E. Simplificación de Flags

**De 11 a 6 flags significativos:**

| Flag actual | Decisión | Flag nuevo |
|-------------|----------|------------|
| `ETHER_MIMO_ENABLED` | ELIMINAR | — |
| `ETHER_MIMO_DIRECT_ENABLED` | ELIMINAR | — |
| `ETHER_KIMI_ENABLED` | RENOMBRAR | `ETHER_KIMI_ROUTING` |
| `ETHER_CONTEXT_ROUTING` | FUSIONAR con KIMI | `ETHER_KIMI_ROUTING` (controla ambas) |
| `ETHER_MULTIMODAL_ENABLED` | FUSIONAR | `ETHER_KIMI_ROUTING` |
| `ETHER_BUDGET_ENFORCEMENT` | CONSERVAR | `ETHER_BUDGET_ENFORCEMENT` |
| `ETHER_LANGFUSE_ENABLED` | CONSERVAR | `ETHER_LANGFUSE_ENABLED` |
| `ETHER_DEEPEVAL_ENABLED` | CONSERVAR | `ETHER_EVAL_ENABLED` (renombrar) |
| `QUALITY_ROUTING_ENABLED` | CONSERVAR | `ETHER_QUALITY_ROUTING` |
| `ETHER_EVAL_SAMPLE_SIZE` | MOVER a config | constante en aether.yaml |
| `ETHER_CIRCUIT_BREAKER_ENABLED` | CONSERVAR | `ETHER_CIRCUIT_BREAKER` |

**Nuevo set de 6 flags:**
1. `ETHER_KIMI_ROUTING` — controla Kimi legacy + multimodal + long-context routing (fusión de 3)
2. `ETHER_BUDGET_ENFORCEMENT` — budget-aware downgrade
3. `ETHER_LANGFUSE_ENABLED` — LangFuse tracing
4. `ETHER_EVAL_ENABLED` — evaluación de calidad (renombrado)
5. `ETHER_QUALITY_ROUTING` — quality-aware rerank
6. `ETHER_CIRCUIT_BREAKER` — circuit breaker

**Beneficio**: 45% menos flags, 100% menos redundancia.  
**Costo**: Actualizar imports en router.py, client.py, eval.py, test files.  
**Riesgo**: Bajo — renombrar es mecánico.

---

## PARTE 4: Diagrama de Arquitectura Propuesta (v3.1)

```
┌─────────────────────────────────────────────────────────────────────────┐
│                          AETHER v3.1 — 10 MÓDULOS                       │
│                    (~3,500 líneas, -17% vs v3)                          │
│                                                                         │
│  ┌─────────────────────────────────────────────────────────────────┐   │
│  │  __init__.py (simplificado — menos exports, sin try/except)    │   │
│  └─────────────────────────────────────────────────────────────────┘   │
│                                                                         │
│  ┌───────────────┐  ┌───────────────┐  ┌───────────────┐             │
│  │  router_call  │  │  api_call     │  │  helpers      │             │
│  │  .py          │  │  .py          │  │  .py          │             │
│  │  chat() solo  │  │  call_provi-  │  │  build_prompt │             │
│  │  orquesta     │──│  der()        │  │  detect_images│             │
│  │               │  │               │  │  estimate_... │             │
│  └───────┬───────┘  └───────┬───────┘  └──────────────┘             │
│          │                  │                                        │
│          ▼                  ▼                                        │
│  ┌──────────────────────────────────────────────────────────────┐  │
│  │  pipeline.py (nuevo — routing pipeline modular)              │  │
│  │  resolve_model() = paso1 → paso2 → ... → paso_N             │  │
│  │  RoutingStep interface                                       │  │
│  │  ┌──────────┐ ┌────────────┐ ┌─────────────┐ ┌──────────┐  │  │
│  │  │Override  │ │Candidate   │ │Multimodal   │ │KimiRule  │  │  │
│  │  │Step      │ │Step        │ │Step         │ │Step      │  │  │
│  │  └──────────┘ └────────────┘ └─────────────┘ └──────────┘  │  │
│  │  ┌──────────┐ ┌────────────┐ ┌─────────────┐ ┌──────────┐  │  │
│  │  │FirstAvail│ │Quality     │ │BudgetStep   │ │Quality   │  │  │
│  │  │Step      │ │RerankStep  │ │             │ │Feedback  │  │  │
│  │  └──────────┘ └────────────┘ └─────────────┘ └──────────┘  │  │
│  │  ┌──────────┐                                               │  │
│  │  │CB        │                                               │  │
│  │  │Fallback  │                                               │  │
│  │  │Step      │                                               │  │
│  │  └──────────┘                                               │  │
│  └──────────────────────────────────────────────────────────────┘  │
│                                                                     │
│  ┌──────────────────────┐     ┌───────────────────────────────┐   │
│  │  providers/          │     │  tracker.py (sin cambios)     │   │
│  │  ├── __init__.py     │     │  EtherTracker                │   │
│  │  │   get_provider()  │     │                               │   │
│  │  ├── base.py (NUEVO) │     └───────────────────────────────┘   │
│  │  │   BaseProvider    │                                           │
│  │  ├── opencode_go.py  │     ┌───────────────────────────────┐   │
│  │  │   (wrapper llm)   │     │  circuit.py (sin cambios)     │   │
│  │  └── router9.py      │     │  CircuitBreaker              │   │
│  │      (reactivado)    │     └───────────────────────────────┘   │
│  └──────────────────────┘                                           │
│                                                                     │
│  ┌──────────────────────────────────────────────────────────┐     │
│  │  config.py + config_loader.py (HOT-RELOAD)                │     │
│  │  - reload_config() expuesto públicamente                  │     │
│  │  - config watch (file mtime check)                        │     │
│  │  - 6 flags en vez de 11                                   │     │
│  │  - ETHER_EVAL_SAMPLE_SIZE movido a aether.yaml const      │     │
│  └──────────────────────────────────────────────────────────┘     │
│                                                                     │
│  ┌────────────────────────────────────────────────────────────┐   │
│  │  quality_store.py (ÚNICA FUENTE DE VERDAD)                │   │
│  │  ▲                                       ▲                │   │
│  │  │                                       │                │   │
│  │  ├── EvalPipeline (eval.py simplificado) │                │   │
│  │  │   → solo llama a QualityStore.record()│                │   │
│  │  │   → sin DeepEval hard dependency      │                │   │
│  │  │                                       │                │   │
│  │  └── EtherJudge (judge/ -> se integra)   │                │   │
│  │      → también llama a QS.record()       │                │   │
│  │      → rúbricas compartidas              │                │   │
│  │                                          │                │   │
│  │  (NO MÁS inline sampling en client.py)   │                │   │
│  └────────────────────────────────────────────────────────────┘   │
│                                                                     │
│  ┌──────────────────────┐     ┌───────────────────────────────┐   │
│  │  observability.py    │     │  cli.py (actualizado)         │   │
│  │  LangFuse + JSONL    │     │  + reload config command      │   │
│  └──────────────────────┘     └───────────────────────────────┘   │
│                                                                     │
│  (ELIMINADOS)                                                       │
│  ✗ ab_testing.py → mover a contrib/ o eliminar                      │
│  ✗ limiter.py → eliminar (nunca usado)                              │
│  ✗ client.py → reemplazado por router_call + api_call + helpers     │
│  ✗ router.py → reemplazado por pipeline.py + steps/                 │
└─────────────────────────────────────────────────────────────────────────┘
```

---

## PARTE 5: Análisis de Rutas Críticas

### Hot Path: `agent_llm_call()` → `resolve_model()` → API call → `track()` → `observe()`

```
PASO                      TIEMPO EST.        RIESGO                     MEJORA
───                       ──────────          ─────                     ──────
1. resolve_model()        1-5ms (pipeline)    CALIDAD: etapas 6 y 9     Cachear QualityStore
  ├─ Override (dict)       0.01ms              leen quality_history.json  en memoria RAM
  ├─ Candidates (dict)     0.02ms              en cada llamada            (evitar I/O en
  ├─ Multimodal (list)     0.01ms                                         hot path).
  ├─ Kimi routing (dict)   0.01ms             BudgetStep lee budget       BudgetStep puede
  ├─ FirstAvailable (loop) 0.05ms              del tracker → I/O         recibir budget_remaining
  ├─ QualityRerank (QS)   1-5ms ⚠️            cada 10 tracks flush()    por parámetro, no
  │                         └── query quality_history.json (I/O)         por tracker.get_stats()
  ├─ BudgetStep (dict)     0.02ms            
  ├─ QualityFeedback (QS) 1-5ms ⚠️           
  │                         └── query quality_history.json otra vez
  └─ CBFallback (dict)     0.02ms            

2. agent_llm_call()       100-5000ms           LATENCIA REAL de API      Sin mejora de
  ├─ _cached_call()        100-5000ms          (depende del modelo)       latencia aquí.
  │  └─ API HTTP call      100-5000ms                                     Cache de prompts
  │                                                                        repetitivos en
  └─ tracker.track()       2-50ms ⚠️           ESCRIBE quality_history    _cached_call()
     └─ _save() (flush)    50-100ms (cada 10)  cada 10 llamadas            Reduce I/O en
                                                                           hot path

TOTAL RUTA CRÍTICA:       ~104ms - ~5060ms

⚠️ RIESGOS DE LATENCIA:
  1. QualityStore query en etapas 6 y 9 del pipeline = 2-10ms dobles
     → **Solución**: QualityStore cache en RAM (dict compartido) que se
       refresca cada N segundos. Latencia baja de 5ms a 0.02ms.
  2. tracker.track() flush cada 10 = pico de 50-100ms
     → **Solución**: Flush async con thread pool. O mantener sync pero
       fuera del hot path (flush en background).
  3. Observability en client.chat() (no en agent_llm_call) = no impacta
     este hot path, pero sí el de chat().

📊 OPORTUNIDADES DE CACHE:
  - QualityStore.get_task_scores(): cache LRU con TTL 60s (los datos de
    calidad no cambian cada segundo)
  - CircuitBreaker.is_available(): cache en RAM (dict) — ya es en RAM
  - _pick_first_available(): cachear resultado por task_type+agent 
    (resolución de candidatos raramente cambia)

📝 LOGGING ESTRATÉGICO (sin afectar performance):
  - resolve_model(): loggear resolved_by + model (cadenas pequeñas, ~50 chars)
  - tracker.track(): loggear solo fallos de I/O
  - observe() en client.chat(): ya por demand sampling (10-80% según tier)
  - NO loggear en hot path de pipeline (cada etapa individual)
  - Usar logging condicional: logger.isEnabledFor(logging.DEBUG) antes
    de construir mensajes complejos
```

---

## PARTE 6: Plan de Migración Arquitectónica

### F0: Quick Wins (no toca arquitectura, solo corrige lo obvio)

**Objetivo**: ~200 líneas cambiadas, 0 nuevas responsabilidades.

| Archivo | Cambio | Líneas |
|---------|--------|--------|
| `client.py` | Eliminar inline sampling contaminante (líneas 203-217) | -15 |
| `client.py` | Eliminar auto_eval_if_needed() del post-chat (línea 221-225) | -5 |
| `aether.yaml` | Agregar `router9-minimax` y `router9-glm` a fallback_chains | +3 |
| `providers/__init__.py` | Agregar `get_provider()` con 3 líneas | +5 |
| `providers/router9.py` | No necesita cambios (interfaz limpia) | 0 |
| `config.py` | Renombrar `ETHER_DEEPEVAL_ENABLED` → `ETHER_EVAL_ENABLED` | 1 |
| `config.py` | Eliminar flag `ETHER_MIMO_ENABLED` y `ETHER_MIMO_DIRECT_ENABLED` | -4 |
| `config.py` | Fusionar `ETHER_KIMI_ENABLED` + `ETHER_CONTEXT_ROUTING` + `ETHER_MULTIMODAL_ENABLED` → `ETHER_KIMI_ROUTING` | -6 |
| `router.py` | Actualizar imports por flags renombrados | +3/-3 |
| `eval.py` | Actualizar imports por `ETHER_EVAL_ENABLED` | +1/-1 |

**Tests**: Ninguno nuevo. Los tests existentes deben pasar sin cambios (misma semántica).  
**Riesgo**: Muy bajo — cambios mecánicos de renombre y eliminación de código muerto.  
**Duración estimada**: 30 minutos.

### F1: Hot-reload + Interfaz Providers + Dashboard mejorado

**Objetivo**: ~180 líneas nuevas, ~50 modificadas.

**Archivos a modificar**:

| Archivo | Cambio | Líneas |
|---------|--------|--------|
| `config_loader.py` | Agregar `reload_config()` no-singleton + `watch_config()` por mtime | +30 |
| `config_loader.py` | `get_config()` → verificar mtime cada 10s si `AUTO_RELOAD=true` | +15 |
| `config.py` | `from lib.aether.config_loader import get_config, reload_config` | +3 |
| `providers/__init__.py` | Implementar `get_provider(name)`, `list_providers()`, `register_provider()` | +25 |
| `providers/base.py` | **NUEVO** — `BaseProvider` + `ProviderResponse` dataclass | +50 |
| `providers/opencode_go.py` | **NUEVO** — wrapper que adapta `agent_llm_call` a `BaseProvider` | +40 |
| `providers/router9.py` | Refactor `Router9Client.chat()` → implementar `BaseProvider` | +15 |
| `cli.py` | Agregar `aether config reload` + flag de provider | +20 |
| `__init__.py` | Exportar nuevos símbolos: `reload_config`, `get_provider`, `list_providers` | +5 |

**Interfaces a respetar**:
```python
# providers/base.py
@dataclass
class ProviderResponse:
    text: str
    model: str
    usage: dict

class BaseProvider(ABC):
    provider_name: str
    chat(messages, model, **kwargs) → ProviderResponse
    is_available() → bool
    get_supported_models() → list[str]

# providers/__init__.py
get_provider(name="opencode-go") → BaseProvider
register_provider(name, instance) → None
list_providers() → dict[str, BaseProvider]
```

**Tests necesarios**:
- `test_providers_base.py`: Test `BaseProvider` interface contract
- `test_providers_opencode.py`: Mock `agent_llm_call`, test `OpenCodeGoProvider`
- `test_providers_router9.py`: Mock `OpenAI`, test `Router9Provider`
- `test_config_reload.py`: Test que `reload_config()` cambia el estado

**Riesgo**: Medio — nueva interfaz de providers puede requerir ajustes en integración.  
**Mitigación**: `get_provider()` default retorna `OpenCodeGoProvider` que envuelve `agent_llm_call()`. Sin cambios en callers existentes.  
**Duración estimada**: 4-6 horas.

### F2: Pipeline Modular + Consolidación Calidad + Reducción Flags

**Objetivo**: ~350 líneas nuevas, ~400 modificadas (refactor router.py + eval.py + quality).

**Archivos a modificar**:

| Archivo | Cambio | Líneas |
|---------|--------|--------|
| `router.py` | **REFACTOR COMPLETO**: cada etapa → `RoutingStep` subclass | -264 |
| `pipeline.py` | **NUEVO**: `resolve_model()` + `RoutingContext` + pipeline engine | +180 |
| `pipeline/steps/__init__.py` | **NUEVO**: exportar todos los steps | +10 |
| `pipeline/steps/override.py` | **NUEVO**: OverrideStep | +20 |
| `pipeline/steps/candidates.py` | **NUEVO**: CandidateStep | +25 |
| `pipeline/steps/multimodal.py` | **NUEVO**: MultimodalStep | +15 |
| `pipeline/steps/kimi.py` | **NUEVO**: KimiRoutingStep + LongContextStep | +30 |
| `pipeline/steps/quality.py` | **NUEVO**: QualityRerankStep + QualityFeedbackStep | +40 |
| `pipeline/steps/budget.py` | **NUEVO**: BudgetStep | +20 |
| `pipeline/steps/circuit.py` | **NUEVO**: CBFallbackStep | +20 |
| `eval.py` | **REFACTOR**: simplificar — siempre escribir a QualityStore. Eliminar DeepEval directo duplicado | -200 |
| `judge/__init__.py` | Agregar `QualityStore.record()` en `evaluate()` | +3 |
| `config.py` | Aplicar renombres finales de flags F0 | 0 (+validación) |
| `quality_store.py` | Agregar `validate_entry()` para detectar contaminación | +15 |

**Interfaces a respetar**:
```python
# pipeline.py (reemplaza router.py)
def resolve_model(**kw) -> dict:
    """Misma firma que antes. Total backward compatibility."""
    ...

class RoutingStep(ABC):
    def execute(self, ctx: RoutingContext) -> RoutingContext: ...

class RoutingContext:
    task_type, agent, model_override, prompt_size, has_images,
    budget_remaining, candidates, model, thinking, tier, resolved_by
    def to_dict() -> dict: ...
```

**Tests necesarios**:
- `test_pipeline_steps.py` — 1 test por cada step (13 tests)
- `test_pipeline_integration.py` — pipeline completo (3-4 escenarios)
- `test_eval_consolidation.py` — EvalPipeline solo escribe a QS
- `test_quality_deduplication.py` — verificar que no hay escrituras duplicadas

**Riesgo**: ALTO — router.py es el corazón y muchos callers lo usan.  
**Mitigación**:
1. `resolve_model()` mantiene EXACTAMENTE la misma firma y tipo de retorno
2. `pipeline.py` re-exporta `resolve_model` para que `from lib.aether.router import resolve_model` siga funcionando (wrapper)
3. Fase F2 se puede revertir individualmente sin afectar F0 ni F1
4. Coexistencia: ambos `resolve_model()` (nuevo y viejo) pueden convivir temporalmente

**Duración estimada**: 10-14 horas.

### F3: Provider Gateway + Integración Router9 + Testing de Integración

**Objetivo**: ~150 líneas nuevas, habilitar Router9 en producción.

| Archivo | Cambio | Líneas |
|---------|--------|--------|
| `providers/gateway.py` | **NUEVO**: ProviderGateway — resuelve qué provider usar según modelo | +60 |
| `providers/__init__.py` | Agregar `gateway = ProviderGateway()` | +5 |
| `pipeline.py` | `api_call.py` usar `gateway.call()` en vez de provider directo | +10 |
| `router9.py` | Asegurar `BaseProvider` compliance + tests de integración | +15 |
| `aether.yaml` | Agregar `provider_gateway` section (model → provider mapping) | +10 |
| `test_integration/` | **NUEVO**: tests de integración provider → router → tracker | +50 |

**ProviderGateway**:
```python
class ProviderGateway:
    """Resuelve qué provider usar según el modelo solicitado.
    
    Modelos go-* → OpenCodeGoProvider
    Modelos router9-* → Router9Provider
    Default → OpenCodeGoProvider
    """
    def call(self, model: str, messages: list, **kwargs) -> ProviderResponse: ...
    def get_provider_for(self, model: str) -> BaseProvider: ...
```

**Tests necesarios**:
- `test_gateway_routing.py` — modelo → provider mapping
- `test_gateway_fallback.py` — fallback entre providers
- `test_router9_integration.py` — Router9 real contra mock server

**Riesgo**: Bajo — es un gateway, no cambia lógica de routing.  
**Duración estimada**: 3-4 horas.

---

## PARTE 7: Recomendaciones Arquitectónicas

### R1: QualityStore como única fuente de verdad — eliminar todo sampling inline

**Justificación**: El inline sampling en `client.py` (líneas 203-217) escribe scores hardcodeados `7.0` en QualityStore, contaminando los datos que usa `resolve_model()` para quality-aware routing. Esto convierte el quality feedback en ruido. Además, `auto_eval_if_needed()` en el post-chat agrega latencia impredecible.

**Acción concreta**:
1. Eliminar líneas 203-226 de `client.py`
2. Eliminar `auto_eval_if_needed()` de `eval.py` (o moverlo a un scheduler externo)
3. EvalPipeline y EtherJudge deben ser los ÚNICOS que escriban a QualityStore

**Costo**: ~30 líneas eliminadas. **Beneficio**: Datos de calidad confiables, hot path más rápido, menos side effects en chat().

### R2: Router9 debe salir de la caja — activar como provider con interfaz unificada

**Justificación**: Router9 ofrece modelos a ~$0.0002/1K tokens (vs $0.14/1K de go-flash). Es un 99.86% más barato. Para tareas de bajo riesgo (lint, extract, health), puede reducir costos de ~$3/semana a centavos. El código ya existe, los cost rates ya están registrados — solo falta la interfaz de provider.

**Acción concreta**:
1. Implementar `BaseProvider` en `providers/base.py` (F1)
2. Hacer que `Router9Client` herede de `BaseProvider` (F1)
3. Agregar routing condicional en pipeline: tareas `lint` y `extract` pueden ir a `router9-minimax` (F3)

**Costo**: ~100 líneas. **Beneficio**: Ahorro semanal de ~$0.50-1.00 en tareas baratas (30-50% del budget de flash). Diversificación de providers — si OpenCode Go cae, Router9 es fallback.

### R3: Desacoplar la resolución del orquestador de la ejecución real (DSOL vinculante)

**Justificación**: `get_dsol_config()` en orchestrator resuelve modelo pero es ignorado por `agent_llm_call()`. Esto rompe la trazabilidad y hace que el orquestador no pueda forzar decisiones de routing.

**Acción concreta**:
1. `agent_llm_call()` debe aceptar `model_override` desde el orquestador
2. El orquestador debe pasar el modelo resuelto como `model_override` a cada tarea de agente
3. Si el agente no recibe `model_override`, `resolve_model()` se llama internamente (backward compat)

**Costo**: Modificar firma de paso de tareas en orchestrator (~20 líneas). Modificar `agent_llm_call()` para priorizar `model_override` de tarea sobre su propia resolución (~5 líneas). **Beneficio**: Trazabilidad total de "orchestrator resolved → agent used". Sin doble resolución.

### R4: Hot-reload de configuración como feature crítico para operaciones

**Justificación**: Cambiar routing ($0.14 flash → $0.0000002 router9-minimax) requiere reinicio completo de KAOS. Cada cambio de YAML = ~30s de downtime. En desarrollo, es inaceptable.

**Acción concreta**:
1. `reload_config()` debe resetear el singleton sin matar el proceso
2. `get_config()` debe verificar mtime del archivo cada N segundos (configurable)
3. El cambio debe ser atómico: la nueva config reemplaza a la vieja sin race conditions

**Costo**: ~45 líneas en `config_loader.py`. **Beneficio**: Zero-downtime config changes. A/B testing sin reinicio.

### R5: Eliminar código muerto agresivamente — menos código = menos bugs

**Justificación**: ~200 líneas de código nunca ejecutado en producción:
- `_base_resolve()`, `_cheapest_fallback()`, `_kimi_fallback()` en router.py
- `call_structured()` en client.py
- `ab_testing.py` completo (nunca integrado)
- `limiter.py` completo (`check_rate_limit()` nunca llamado)
- `build_optimized_context()`, `estimate_cache_ratio()`, `extract_cache_metrics()` en client.py

**Acción concreta**:
1. Eliminar funciones privadas no usadas en router.py
2. Eliminar `call_structured()` (deprecated desde v3)
3. Mover `ab_testing.py` a `contrib/` o eliminarlo
4. Eliminar `limiter.py` (o mover a contrib/)
5. Marcar utilidades no usadas con `__all__` restrictivo

**Costo**: ~200 líneas eliminadas. **Beneficio**: Menos superficie de pruebas, menos falsas expectativas, menos imports condicionales en `__init__.py`.

---

## Apéndice A: Mapa de Migración por Archivo

| Archivo v3 | Estado v3.1 | Acción |
|-----------|-------------|--------|
| `__init__.py` | Modificado | Reducir exports, eliminar try/except |
| `router.py` | → `pipeline.py` + `pipeline/steps/*.py` | Refactor completo |
| `client.py` | → `router_call.py` + `api_call.py` + `helpers.py` | Split |
| `tracker.py` | Sin cambios | — |
| `config.py` | Modificado | Renombrar flags, eliminar redundantes |
| `config_loader.py` | Modificado | +hot-reload |
| `circuit.py` | Sin cambios | — |
| `eval.py` | Modificado | Simplificar, escribir solo a QS |
| `quality_store.py` | Modificado | +validate_entry |
| `observability.py` | Sin cambios | — |
| `judge/__init__.py` | Modificado | +QualityStore.record() |
| `ab_testing.py` | → contrib/ o eliminar | Mover |
| `limiter.py` | Eliminar | Nunca usado |
| `cli.py` | Modificado | +reload command |
| `providers/__init__.py` | Modificado | +get_provider, list_providers |
| `providers/router9.py` | Modificado | +BaseProvider compliance |
| — | `providers/base.py` | **Nuevo** |
| — | `providers/opencode_go.py` | **Nuevo** |
| — | `providers/gateway.py` | **Nuevo** (F3) |
| — | `pipeline.py` | **Nuevo** (F2) |
| — | `pipeline/steps/` | **Nuevo** (F2, 8 archivos) |

**Total**: ~3,500 líneas (v3.1) vs ~4,200 (v3) = **-17% de código, +20% de modularidad, -45% de flags**.

---

*Documento generado por Kosmos — Arquitectura de Sistemas KAOS*
*Basado en análisis de 16 módulos Aether v3, 179 referencias externas, y 3 sistemas de calidad paralelos.*
