---
type: concept
title: Estrategia Multi-Modelo para KAOS
aliases:
  - estrategia-multi-modelo
status: seedling
tags:
  - arquitectura
  - multi-modelo
  - ether
---

# Estrategia Multi-Modelo para KAOS

## Resumen

Estrategia de 3 capas para eliminar el sesgo cognitivo del modelo único en los agentes KAOS, usando DeepSeek V4 Flash (base), DeepSeek V4 Pro (calidad factual) y Kimi K2.6 (diversidad estratégica), todo via OpenCode Go.

## Arquitectura de Ruteo

```
Agente → chat(task_type=...) → DSOL Router → resolve_model() → OpenCode Go API
                                  │
                                  ├─ task_type="lint"      → go-flash
                                  ├─ task_type="research"  → go-pro    
                                  ├─ task_type="strategy"  → go-kimi-latest
                                  └─ task_type="verify"    → go-kimi-latest
```

## Dashboard de Métricas

### Qué trackear

| Métrica | Fuente | Frecuencia |
|---------|--------|------------|
| % tráfico por modelo | TokenTracker.get_model_breakdown() | Por sesión |
| Costo por modelo | TokenTracker.get_model_breakdown() | Por sesión |
| Latencia por modelo | Logs de llamadas | Por request |
| Circuit breaker status | CircuitBreaker.get_status() | En cada status check |
| Score de verificación | Quality gate | Semanal |
| Satisfacción del equipo | Feedback cualitativo | Mensual |

### Targets y Thresholds

| Métrica | Alerta | Target |
|---------|--------|--------|
| Tráfico Flash | <70% o >95% | 85% |
| Tráfico Pro | <5% o >20% | 10% |
| Tráfico Kimi | <1% o >12% | 5% |
| Costo mensual | >$10 | <$6 |
| Circuit breaker open | Cualquier apertura | 0/semana |

## Gobernanza

### Revisión de la estrategia
- **Trimestral**: Evaluación completa de proveedores, modelos, costos y métricas
- **Trigger de re-evaluación**: Cambio de precios en OpenCode Go, nuevo modelo disponible, queja del equipo sobre calidad

### Proceso para agregar un modelo
1. Investigación de Aletheia: benchmarks, precios, disponibilidad en OCGo
2. Análisis de Kosmos: integración técnica, impacto arquitectónico
3. Decisión de Metis: costo-beneficio, alineación estratégica
4. Implementación de Kratos: agregar a TASK_MODEL_MAP, tests
5. Documentación de Mnemosyne: actualizar ADR, conceptos

## Reglas de Gobernanza

1. **Todo cambio en la estrategia debe documentarse en este archivo**
2. **Los % de tráfico son guías, no reglas estrictas** — el router puede desviarse según disponibilidad
3. **Si un modelo falla consistentemente**, el circuit breaker lo degrada automáticamente
4. **La verificación cruzada siempre debe usar un modelo diferente** al que produjo el output original
5. **Cada 3 meses**: re-evaluar la estrategia completa
