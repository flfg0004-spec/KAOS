---
audience: agent
type: model
name: MiMo-V2.5-Pro
role: llm-flagship
description: "Modelo flagship MoE 1.02T/42B activos, #1 open-source en benchmarks de agente — entrena con MOPD + MTP, licencia MIT"
status: active
vendor: Xiaomi
version: V2.5-Pro
tags: [xiaomi, mimo, moe, flagship, agent, mopd, mtp, mit, open-source]
aliases: [MiMo Pro, Xiaomi MiMo V2.5 Pro, MiMo V2.5 Pro]
created: 2026-05-26
modified: 2026-05-26
params:
  total: 1.02T
  active: 42B
  architecture: MoE
  license: MIT
  context: 256K
  benchmark: "#1 open-source agent"
confidence: high
sources:
  - https://www.mimo-v2.com/docs/pricing
  - https://huggingface.co/Xiaomi
---

# MiMo-V2.5-Pro — Modelo Flagship 1.02T/42B

## Descripción

**MiMo-V2.5-Pro** es el modelo flagship de la familia [[MiMo]] y actualmente **#1 open-source en benchmarks de agente**. Con 1.02T parámetros totales (42B activos), representa el esfuerzo más ambicioso de Xiaomi en IA generativa.

## Arquitectura

- **Total params**: 1.02T | **Activos**: 42B
- **Arquitectura**: Mixture of Experts (MoE)
- **Atención**: [[Hybrid-Attention]] — SWA+GA
- **Contexto máximo**: 256K tokens
- **Licencia**: MIT (open-weight)
- **Precio**: $1.00/M tokens (input ≤256K), $3.00/M tokens (output ≤256K)

## Técnicas de Entrenamiento

### [[MOPD]] (Multi-Teacher On-Policy Distillation)
Técnica de destilación donde múltiples modelos teacher guían el entrenamiento on-policy, permitiendo que MiMo-V2.5-Pro supere a sus teachers individuales.

### [[Multi-Token-Prediction-MTP]]
Predicción de múltiples tokens futuros simultáneamente — técnica nativa de speculative decoding que acelera la generación sin pérdida de calidad.

## Rendimiento

| Dominio | Rendimiento |
|---------|-------------|
| **Agente (benchmark unificado)** | **#1 open-source** — supera a todos los modelos abiertos |
| Código | Competitivo con flagships propietarios |
| Razonamiento | Excelente |
| Seguimiento de instrucciones | Superior |

## Integración en KAOS

El modelo está referenciado en el sistema de token tracking como **go-mimo**:
- `go-mimo` → `mimo-v2-pro` → Xiaomi

```yaml
# Config example para DSOL
go-mimo:
  model: mimo-v2-pro
  provider: xiaomi
  pricing:
    input: 1.00  # /1M tokens
    output: 3.00 # /1M tokens
```

## Posicionamiento

| Aspecto | MiMo-V2.5-Pro | [[kimi]] K2.6 | DeepSeek Pro |
|---------|--------------|---------------|--------------|
| Params | 1.02T/42B | ¿? | ¿? |
| Licencia | **MIT** | Propietaria | Propietaria |
| Benchmark Agente | **#1 open-source** | ¿? | ¿? |
| Costo input | $1.00/M | ~$0.95/M | $1.74/M |
| Contexto | 256K | 262K | 128K |

La ventaja clave de MiMo-V2.5-Pro es su **licencia MIT**: es el modelo más potente disponible como open-weight para tareas de agente.

## Fuentes
- [MiMo Pricing](https://www.mimo-v2.com/docs/pricing)
- [HuggingFace Xiaomi](https://huggingface.co/Xiaomi)
- Paper técnico MOPD (Xiaomi AI Lab, 2025)
