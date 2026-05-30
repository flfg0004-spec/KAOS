---
type: technique
name: Multi-Token Prediction (MTP)
role: inference-optimization
description: "Técnica de speculative decoding nativa — el modelo predice múltiples tokens futuros simultáneamente, acelerando la generación sin pérdida de calidad"
status: active
vendor: Xiaomi
tags: [xiaomi, mimo, mtp, speculative-decoding, inference, optimization, generation]
aliases: [Multi-Token Prediction, MTP, MiMo MTP]
created: 2026-05-26
modified: 2026-05-26
confidence: medium
sources:
  - Paper técnico Xiaomi AI Lab (2025)
  - Meta (2024) — Multi-Token Prediction original paper
---

# Multi-Token Prediction (MTP)

## Descripción

**Multi-Token Prediction (MTP)** es una técnica de optimización de inferencia implementada en los modelos flagship de [[MiMo]]. Permite que el modelo prediga **múltiples tokens futuros simultáneamente**, funcionando como un mecanismo nativo de **speculative decoding** sin necesidad de un modelo draft externo.

## Cómo Funciona

A diferencia de la generación autónoma tradicional (1 token a la vez):

```
Generación tradicional:
  Token₁ → Token₂ → Token₃ → Token₄ → ... (secuencial, 1 paso por token)

MTP:
  Token₁ ↓
  Token₂ ←─── Predicción simultánea
  Token₃ ←─── de tokens futuros
  Token₄ ←─── (múltiples cabezas de predicción)
```

### Mecanismo

1. El modelo tiene **múltiples cabezas de predicción** además de la cabeza principal
2. Cada cabeza predice un token futuro en una posición diferente (head₁→t+1, head₂→t+2, ...)
3. Durante entrenamiento: todas las cabezas se entrenan simultáneamente
4. Durante inferencia: el modelo genera bloques de tokens en paralelo, verificados y aceptados en lote

## Ventajas

| Aspecto | Generación Tradicional | Con MTP |
|---------|----------------------|---------|
| Tokens por paso | 1 | **2-4×** |
| Calidad | - | Sin pérdida |
| Modelo draft externo | Requerido para spec. decoding | **No requerido** |
| Latencia | Mayor | **2-4× menor** |
| Entrenamiento | Estándar | Cabezas auxiliares adicionales |

## Aplicación en MiMo

MTP es utilizado por [[MiMo-V2.5-Pro]] como técnica nativa de speculative decoding:

- **Sin modelo draft externo**: a diferencia de DeepSeek (que usa drafts separados), MiMo integra MTP en el propio modelo
- **Entrenamiento conjunto**: las cabezas MTP se entrenan junto con el modelo principal
- **Aceleración 2-4×**: en generación de texto largo

## Relaciones

- [[MiMo-V2.5-Pro]] — Implementa MTP
- [[MiMo-V2-Flash]] — Implementa MTP (especulado)
- [[MiMo]] — Familia que implementa esta técnica
- [[Hybrid-Attention]] — Arquitectura complementaria

## Fuentes
- Paper técnico MTP — Xiaomi AI Lab (2025)
- Meta (2024) — "Better & Faster Large Language Models via Multi-token Prediction" (base teórica)
