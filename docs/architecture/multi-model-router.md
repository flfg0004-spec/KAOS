# Multi-Model Router — Arquitectura del Sistema de Ruteo Inteligente

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
│                   DSOL ROUTER (lib/dsol.py)                  │
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

### 1. Router — Motor de decisión

```
resolve_model(task_type, agent, model_override):
  1. model_override explícito → usar ese
  2. TASK_MODEL_MAP[task_type] → resolver
  3. AGENT_DEFAULT_TASK[agent] → TASK_MODEL_MAP
  4. default: go-flash

  Output: {"model": str, "thinking": str|None, "resolved_by": str}
```

### 2. Circuit Breaker — Protección por modelo

| Estado | Transición | Acción |
|--------|-----------|--------|
| closed | 3 fallos consecutivos → open | Bloquear llamadas al modelo |
| open | 5 min sin fallos → half-open | Permitir 1 llamada de prueba |
| half-open | 1 éxito → closed | Restaurar modelo |
| half-open | 1 fallo → open | Reiniciar temporizador |

### 3. chat() — Entry point principal

```python
def chat(task_type, messages, agent="", model=None, thinking=None, ...):
    # 1. Resolver modelo
    resolved = resolve_model(task_type, agent, model)
    
    # 2. Verificar circuit breaker
    if not CIRCUIT_BREAKER.is_available(resolved["model"]):
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
        CIRCUIT_BREAKER.record_failure(resolved["model"])
    else:
        CIRCUIT_BREAKER.record_success(resolved["model"])
    
    return result
```

## Estrategia de Fallback

| Modelo primario | Fallback 1 | Fallback 2 |
|----------------|------------|------------|
| go-flash | go-pro | go-kimi-latest |
| go-pro | go-flash | go-kimi-latest |
| go-kimi-latest | go-pro | go-flash |

## Monitoreo

### TokenTracker — Nuevos métodos
- `get_model_breakdown()`: Desglose de uso y costo por modelo
- `get_routing_report()`: Reporte completo con estado del circuit breaker

### Alertas
- Circuit breaker abierto para cualquier modelo → log warning
- % tráfico se desvía >10% del target → revisar configuración
- Costo semanal >$5 → revisar uso
