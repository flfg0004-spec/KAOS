---
type: model
name: MiMo-V2-Flash
role: llm-fast
description: "Modelo MoE 309B/15B activos, licencia MIT, arquitectura híbrida SWA+GA con attention sink bias — modelo de razonamiento general rápido de Xiaomi"
status: active
vendor: Xiaomi
version: V2-Flash
tags: [xiaomi, mimo, moe, swa, ga, hybrid-attention, mit, llm]
aliases: [MiMo Flash, Xiaomi MiMo V2 Flash]
created: 2026-05-26
modified: 2026-05-26
params:
  total: 309B
  active: 15B
  architecture: MoE
  license: MIT
  context: 256K
  embedding_dim: 3840
confidence: high
sources:
  - https://www.mimo-v2.com/docs/pricing
---

# MiMo-V2-Flash — Modelo MoE 309B/15B

## Descripción

**MiMo-V2-Flash** es el modelo de razonamiento general rápido de la familia [[MiMo]]. Con arquitectura MoE de 309B parámetros totales (15B activos por token), está diseñado para tareas de inferencia de alta velocidad con calidad competitiva.

## Arquitectura

- **Total params**: 309B | **Activos**: 15B
- **Arquitectura**: Mixture of Experts (MoE)
- **Atención**: [[Hybrid-Attention]] — SWA (Sliding Window Attention) + GA (Global Attention) con **attention sink bias**
- **Contexto máximo**: 256K tokens
- **Licencia**: MIT (open-weight)
- **Precio**: $0.20/M tokens (input), $0.60/M tokens (output)

## Rendimiento

| Benchmark | MiMo-V2-Flash | DeepSeek-V4-Flash (est.) |
|-----------|--------------|--------------------------|
| Razonamiento general | Competitivo | Líder |
| Velocidad de inferencia | Alta (15B activos) | Alta |
| Costo por token | Muy bajo | Bajo |

## Técnicas Asociadas

- [[Hybrid-Attention]] — SWA + GA con attention sink bias para contexto largo eficiente
- [[Multi-Token-Prediction-MTP]] — Speculative decoding para generación más rápida

## Casos de Uso

- Chat y asistentes conversacionales en [[hyperos|HyperOS]]
- Razonamiento general con alta velocidad
- Tareas de bajo costo donde la calidad no requiere el flagship

## Posicionamiento

Similar estratégico a [[deepseek-v4-flash|DeepSeek V4 Flash]] — el modelo "rápido y barato" de la familia MiMo, ideal para tareas de alto volumen donde el [[MiMo-V2.5-Pro]] sería excesivo.

## Fuentes
- [MiMo Pricing](https://www.mimo-v2.com/docs/pricing)
- Paper técnico de Xiaomi AI Lab (2025)
