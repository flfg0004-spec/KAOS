---
type: model
name: Kimi
role: llm-backend
description: "Modelo LLM de Moonshot AI — HLE #1, multimodal nativo, 262K contexto, costo inferior a DeepSeek Pro"
status: active
vendor: Moonshot AI
tags: [kimi, llm, multimodal, cost-optimization, hle, agentic]
aliases: [Kimi K2.5, Kimi K2.6, Moonshot AI]
created: 2026-05-26
modified: 2026-05-26
---

# Kimi — Modelo LLM de Moonshot AI

## Hallazgos de Valor Diferencial

### Costo: 45% más barato que Pro en input

| Métrica | Kimi | DeepSeek Pro | Diferencia |
|---------|------|-------------|------------|
| Input price / 1K tokens | **$0.00095** | $0.00174 | **−45.4%** |
| Output price / 1K tokens | *pendiente* | *pendiente* | *pendiente* |

Kimi input es 45% MÁS BARATO que Pro input. Esto representa un ahorro significativo en tareas de alto volumen como research y synthesize.

### Rendimiento: HLE #1

| Benchmark | Kimi | DeepSeek Pro (est.) | Diferencia |
|-----------|------|---------------------|------------|
| **HLE (Humanity's Last Exam)** | **54%** | 37.7% | **+16.3 pp** |
| GPQA Diamond | *pendiente* | *pendiente* | *pendiente* |
| MATH-500 | *pendiente* | *pendiente* | *pendiente* |

Kimi tiene HLE #1 (54%) vs Pro est. 37.7%. Esto lo posiciona como el modelo más inteligente disponible para tareas de razonamiento complejo.

### Contexto: 262K tokens

| Modelo | Contexto Máximo |
|--------|----------------|
| **Kimi K2.6** | **262K tokens** |
| DeepSeek Pro | 128K tokens |
| DeepSeek Flash | 128K tokens |

Kimi soporta 262K tokens vs 128K de DeepSeek. Más del doble de capacidad de contexto, habilitando procesamiento de documentos extensos, codebases grandes y sesiones prolongadas.

### Multimodal: MoonViT-3D Nativo

Kimi K2.5 tiene **MoonViT-3D** multimodal nativo:
- Procesamiento de imágenes, video y 3D sin plugins externos
- Diferencial clave vs. DeepSeek (solo texto)
- Aplicable a: análisis visual en Aletheia, diagramas en Kosmos, UI en Kratos

### Compresión Automática de Contexto

Kimi K2.6 incorpora **compresión automática de contexto**:
- Reduce tokens hasta 60% en contextos largos
- Sin pérdida de información relevante
- Impacto directo en costo y latencia para tareas de contexto extenso

### Autonomía: code_agentic (13h)

Kimi K2.5/K2.6 ofrece **code_agentic con hasta 13 horas de autonomía**:
- No está siendo aprovechado actualmente en KAOS
- Habilitaría sesiones de código autónomas mucho más largas que las actuales (~2h)
- Ideal para: investigaciones profundas, refactors extensos, pipelines complejos

## Posicionamiento Estratégico

```
Cost-effectiveness (HLE/$)
        ▲
        │           Kimi ◄── SWEET SPOT
        │              ●
        │        ┌─────┴─────┐
        │   Flash●           ●Pro
        └─────────────────────────► HLE Score
```

Kimi ocupa el **sweet spot** del espacio costo-capacidad: supera a Pro en HLE con 45% menos costo, y ofrece multimodal y contexto 2×.

## Capacidades Clave para KAOS

| Capacidad | Aplicación en KAOS | Prioridad |
|-----------|-------------------|-----------|
| HLE #1 (54%) | Tareas de razonamiento complejo, synthesize, estrategia | Alta |
| 262K contexto | Sesiones largas, codebases grandes, documentos extensos | Alta |
| MoonViT-3D | Análisis multimodal, diagramas, UI | Media |
| Compresión contexto | Reducción de costo en tareas de contexto largo | Alta |
| code_agentic 13h | Sesiones autónomas prolongadas de Kratos | Alta |
| Costo −45% input | Reducción general de OPEX en inferencia | Alta |

## Riesgos

| Riesgo | Probabilidad | Impacto | Mitigación |
|--------|-------------|---------|------------|
| Menor madurez operativa en ecosistema KAOS | Media | Medio | Circuit breaker diferencial (Ether), fallback a Pro |
| Rate limits más restrictivos | Alta | Medio | Pooling de requests, cola de prioridad |
| API no disponible en ciertas regiones | Baja | Alto | Fallback automático a DSOL |
| Latencia desconocida vs. DeepSeek | Media | Bajo | Benchmarking en Fase 1 de integración |

## Referencias
- [[Ether-Kimi-Strategy]] — Estrategia de integración
- [[ether]] — Capa de routing para Kimi
- [[DSOL]] — Fallback layer
- [[metis]] — Análisis estratégico de valor diferencial
