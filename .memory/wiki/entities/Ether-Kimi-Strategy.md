---
audience: agent
type: strategy
agent: metis
date: 2026-05-26
confidence: alta
status: complete
tags: [kimi, ether, strategy, optimization, routing, multimodal, cost-optimization]
---

# Estrategia: Optimización Kimi para el Ecosistema KAOS via Ether

## Síntesis Ejecutiva

La estrategia completa de optimización Kimi ha sido diseñada para Ether — la capa de routing inteligente que conecta agentes KAOS con modelos. Kimi representa un salto cualitativo en capacidad (HLE #1, 262K contexto, multimodal nativo) y costo (45% más barato que Pro en input). Esta estrategia operacionaliza la integración Kimi en Ether en 4 frentes.

## Componentes de la Estrategia

### F1 — Rebalance 80/5/15
- **80% Kimi K2.5/K2.6**: Carga base — tareas estándar, code agentic de hasta 13h de autonomía
- **5% DeepSeek Pro**: Tareas críticas que requieren mayor madurez del ecosistema
- **15% DeepSeek Flash**: Tareas simples y de baja latencia
- **Estado**: F1 es implementable en **0h de ingeniería** — solo configuración en Ether routing table
- **Impacto**: Reducción de ~40% en costo operativo vs. asignación actual

### F2 — Routing Adaptativo por Contexto
- Contexto ≤32K tokens → Flash (baja latencia, bajo costo)
- Contexto 32K–128K → Kimi (máxima capacidad, HLE #1)
- Contexto ≥128K → Kimi (único modelo con soporte nativo)
- Fallback: Si Kimi rate-limit, degradar a Pro
- Dinámico: Evaluación en cada request vía Ether router

### F3 — Cost-Awareness con COST_CAPS
- Budget tracking por agente y por sesión
- COST_CAPS thresholds: warning a 70%, hard stop a 100%
- Dashboard de costos en tiempo real
- Integración con TokenTracker de DSOL

### F4 — Multimodal Nativo
- Kimi K2.5 MoonViT-3D: procesamiento multimodal sin plugins externos
- Kimi K2.6: compresión automática de contexto (reduce tokens hasta 60% en contextos largos)
- Habilitar para agentes con necesidades multimodales (Aletheia, Kosmos)

## Plan de Implementación por Fase

| Fase | Componente | Esfuerzo | Dependencias | Score Impacto |
|------|-----------|----------|-------------|---------------|
| F1 | Rebalance 80/5/15 | 0h (config) | Ether routing table | Alto |
| F2 | Routing adaptativo | 2d | F1, Ether router | Medio |
| F3 | COST_CAPS + budget tracking | 1d | TokenTracker DSOL | Alto |
| F4 | Multimodal habilitación | 3d | F2, Kimi API key | Medio |

## Score Proyectado

| Métrica | Actual | Target Post-F1 | Target Post-F4 |
|---------|--------|----------------|----------------|
| Costo por 1K tokens (promedio ponderado) | ~$0.0015 | ~$0.0010 | ~$0.0008 |
| Contexto máximo disponible | 128K | 262K | 262K |
| HLE Score | 37.7% (Pro est.) | 54% (Kimi) | 54% (Kimi) |
| Autonomía code agentic | ~2h | ~13h (Kimi) | ~13h (Kimi) |

## Referencias
- [[ether]] — Capa de routing Ether
- [[kimi]] — Entidad del modelo Kimi
- [[metis]] — Estratega responsable
- [[DSOL]] — DeepSeek Optimization Layer (predecesor de Ether)
- [[ADR-012-dsol-refactor-medio]] — Refactor DSOL
