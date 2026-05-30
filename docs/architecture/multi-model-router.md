# Multi-Model Router — Arquitectura del Sistema de Ruteo Inteligente

> **Nota:** Este sistema fue renombrado de **DSOL** a **Ether** (Environment for Token Harmonization & Execution Regulation) en mayo 2026. Ver ADR-004 para historial completo.

## Diagrama de Arquitectura

```
┌─────────────────────────────────────────────────────────────┐
│                     AGENTES KAOS                             │
│  ┌──────────┐ ┌──────────┐ ┌──────────┐ ┌──────────┐       │
│  │ Aletheia │ │  Kosmos  │ │  Kratos  │ │  Metis   │       │
│  │research/ │ │ lint/    │ │code/     │ │strategy/ │       │
│  │synthesize│ │ analyze  │ │code_agent│ │ verify   │       │
│  └────┬─────┘ └────┬─────┘ └────┬─────┘ └────┬─────┘       │
│       │            │            │            │              │
│       └────────────┼────────────┼────────────┘              │
│                    │ chat(task_type)                        │
└────────────────────┼────────────────────────────────────────┘
                     ▼
┌─────────────────────────────────────────────────────────────┐
│               ETHER ROUTER (lib/ether/)                      │
│                                                             │
│  Paquete: lib/ether/                                        │
│  ├── router.py    → resolve_model(), _resolve_fallback()    │
│  ├── circuit.py   → CircuitBreaker (unificado, persistente) │
│  ├── tracker.py   → EtherTracker (thread-safe, atomic I/O)  │
│  ├── limiter.py   → RateLimiter                             │
│  ├── client.py    → chat(), call_api(), build_*             │
│  └── config.py    → TASK_MODEL_MAP, BUDGETS, env vars      │
│                                                             │
│  La fachada legacy lib/dsol.py re-exporta de lib/ether/     │
│  para backward compatibility (eliminar en v3.0).            │
│                                                             │
│  ┌──────────────────────────────────────────────────────┐  │
│  │  chat(task_type, messages, agent)                     │  │
│  │                                                      │  │
│  │  1. resolve_model(task_type, agent)                  │  │
│  │     → {"model": "go-kimi-latest", "thinking": None}  │  │
│  │                                                      │  │
│  │  2. CircuitBreaker.is_available(model)               │  │
│  │     → si no: fallback chain                          │  │
│  │                                                      │  │
│  │  3. agent_llm_call(agent, prompt, model_override,    │  │
│  │                     task_type)                       │  │
│  │                                                      │  │
│  │  4. CircuitBreaker.record_success/failure            │  │
│  └──────────────────────────────────────────────────────┘  │
└──────────────────────────┬──────────────────────────────────┘
                           ▼
┌─────────────────────────────────────────────────────────────┐
│                 LLM CLIENT (lib/llm.py)                      │
│                                                             │
│  agent_llm_call() → MODELS dict → OpenCode Go API          │
│                                                             │
│  MODELS = {                                                 │
│    "go-flash":       {"provider": "opencode-go", "model": "deepseek-v4-flash"},       │
│    "go-pro":         {"provider": "opencode-go", "model": "deepseek-v4-pro"},         │
│    "go-kimi-latest": {"provider": "opencode-go", "model": "kimi-k2.6"},               │
│  }                                                          │
└─────────────────────────────────────────────────────────────┘
```

## Componentes

### 1. Router (`lib/ether/router.py`) — Motor de decisión

```
resolve_model(task_type, agent, model_override):
  1. model_override explícito → usar ese
  2. TASK_MODEL_MAP[task_type] → resolver
  3. AGENT_DEFAULT_TASK[agent] → TASK_MODEL_MAP
  4. default: go-flash

  Output: {"model": str, "thinking": str|None, "resolved_by": str}
```

### 2. Circuit Breaker (`lib/ether/circuit.py`) — Protección por modelo

| Estado | Transición | Acción |
|--------|-----------|--------|
| closed | 3 fallos consecutivos → open | Bloquear llamadas al modelo |
| open | 5 min sin fallos → half-open | Permitir 1 llamada de prueba |
| half-open | 1 éxito → closed | Restaurar modelo |
| half-open | 1 fallo → open | Reiniciar temporizador |

Persistencia: escribe a `.memory/cache/circuit_breaker.json` con atomic writes y threading lock.

### 3. EtherTracker (`lib/ether/tracker.py`) — Tracking de tokens

Tracking persistente de tokens con:
- **Thread safety**: threading.Lock en todas las operaciones de escritura
- **Atomic writes**: escribe a `.tmp` y renombra (os.replace)
- **Batch flush**: cada 10 llamadas
- **Misma ruta**: `.memory/cache/token-usage.json` (compatible con DSOL legacy)

### 4. chat() — Entry point principal

```python
def chat(task_type, messages, agent="", model=None, thinking=None, ...):
    # 1. Resolver modelo
    resolved = resolve_model(task_type, agent, model)
    
    # 2. Verificar circuit breaker
    if not _ETHER_CIRCUIT_BREAKER.is_available(resolved["model"]):
        resolved = _resolve_fallback(task_type, agent)
    
    # 3. Llamar a través de llm.py
    result = agent_llm_call(
        agent=agent,
        prompt=prompt_text,
        model_override=resolved["model"],
        task_type=task_type,
    )
    
    # 4. Actualizar circuit breaker
    if result.startswith("# LLM Error"):
        _ETHER_CIRCUIT_BREAKER.record_failure(resolved["model"])
    else:
        _ETHER_CIRCUIT_BREAKER.record_success(resolved["model"])
    
    return result
```

## Estrategia de Fallback

| Modelo primario | Fallback 1 | Fallback 2 |
|----------------|------------|------------|
| go-flash | go-pro | go-kimi-latest |
| go-pro | go-flash | go-kimi-latest |
| go-kimi-latest | go-pro | go-flash |

## Monitoreo

### EtherTracker — Métricas
- `get_model_breakdown()`: Desglose de uso y costo por modelo
- `get_routing_report()`: Reporte completo con estado del circuit breaker

### Alertas
- Circuit breaker abierto para cualquier modelo → log warning
- % tráfico se desvía >10% del target → revisar configuración
- Costo semanal >$5 → revisar uso
