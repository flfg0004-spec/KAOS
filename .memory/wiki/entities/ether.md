---
type: service
name: Ether
role: routing
description: "Capa de routing inteligente — conexión agentes ↔ modelos con routing adaptativo, cost-awareness, circuit breaker y soporte multimodal"
status: proposed
score: 30
score_target: 75
owner: kratos
tags: [ether, routing, optimization, kimi, cost-caps, circuit-breaker]
aliases: [Ether Routing Layer, Ether Router]
created: 2026-05-26
modified: 2026-05-26
related_adrs:
  - ADR-004-deepseek-optimization-layer
  - ADR-010-integracion-dsol-langgraph
  - ADR-012-dsol-refactor-medio
  - ADR-013-circuitbreaker-unificado
---

# Ether — Capa de Routing Inteligente

## Propósito

Ether es la capa de routing que conecta agentes KAOS con modelos LLM. Evoluciona el concepto de DSOL hacia un router multi-modelo con conciencia de contexto, costo y capacidad. Ether decide **dónde** y **cómo** ejecutar cada tarea según su perfil.

## Cambios Propuestos

### synthesize movido de Pro a Kimi
- La tarea `synthesize` (compilación de hallazgos múltiples) se reasigna de DeepSeek Pro → Kimi
- Justificación: Kimi tiene HLE #1 (54% vs 37.7% Pro), mejor capacidad de síntesis
- Impacto en costo: ~45% más barato en input tokens

### Nuevo Routing por Contexto
| Rango de Contexto | Modelo | Justificación |
|-------------------|--------|---------------|
| ≤32K tokens | DeepSeek Flash | Baja latencia, tareas simples |
| 32K–128K tokens | Kimi K2.5/K2.6 | Máxima capacidad (HLE #1), costo óptimo |
| ≥128K tokens | Kimi K2.6 | Único modelo con 262K soporte nativo |
| Fallback (Kimi rate-limit) | DeepSeek Pro | Resiliencia |

### COST_CAPS para Budget Tracking
- Límites de gasto por agente y por sesión
- COST_CAPS: warning al 70%, soft stop al 90%, hard stop al 100%
- Integración con TokenTracker de DSOL para contabilidad
- Dashboard de costos en tiempo real

### Thresholds Diferenciales en Circuit Breaker
| Modelo | Error Threshold | Cooldown | Rate Limit |
|--------|----------------|----------|------------|
| DeepSeek Flash | 10% | 30s | 100 req/min |
| DeepSeek Pro | 15% | 60s | 50 req/min |
| Kimi | 20% | 120s | 30 req/min |

Los thresholds diferenciales reconocen que Kimi tiene menos madurez operativa en el ecosistema KAOS, por lo que se le otorga mayor tolerancia a errores y rate limits más conservadores.

## Arquitectura Propuesta

```
Agent → Ether Router → resolve_model(context_len, task_type, cost_budget)
                       ↓
              ┌────────┴────────┐
              ▼                 ▼
        Kimi Gateway      DSOL Fallback
        (K2.5/K2.6)       (Flash/Pro)
              │                 │
              ▼                 ▼
          Response ◄────────── Response
```

## Estado

- **Score actual**: 30/100 (propuesta conceptual)
- **Score target**: 75/100 (post-implementación)
- **Dependencias**: DSOL refactor (ADR-012), API key Kimi
- **Responsable**: [[kratos]]
- **Valida**: [[kosmos]]

## Referencias
- [[Ether-Kimi-Strategy]] — Estrategia completa de optimización Kimi
- [[kimi]] — Entidad del modelo Kimi
- [[DSOL]] — Predecesor y capa de fallback
- [[ADR-012-dsol-refactor-medio]] — Refactor necesario para Ether
- [[ADR-013]] — Circuit breaker unificado, base para thresholds diferenciales
