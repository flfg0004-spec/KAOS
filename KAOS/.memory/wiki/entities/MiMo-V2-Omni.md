---
audience: agent
type: model
name: MiMo-V2-Omni
role: multimodal
description: "Modelo multimodal de Xiaomi — procesa texto, imagen, video y audio simultáneamente — integrado en HyperOS y SU7"
status: active
vendor: Xiaomi
version: V2-Omni
tags: [xiaomi, mimo, multimodal, vision, audio, video, hyperos, su7]
aliases: [MiMo Omni, Xiaomi MiMo V2 Omni]
created: 2026-05-26
modified: 2026-05-26
confidence: high
sources:
  - https://huggingface.co/Xiaomi
---

# MiMo-V2-Omni — Modelo Multimodal

## Descripción

**MiMo-V2-Omni** es el modelo multimodal de la familia [[MiMo]]. Capaz de procesar y comprender simultáneamente **texto, imagen, video y audio**, está diseñado para funcionar como cerebro sensorial unificado en el ecosistema Xiaomi.

## Capacidades

| Modalidad | Soporte | Aplicación |
|-----------|---------|------------|
| Texto | Nativo | Chat, documentos, código |
| Imagen | Nativo | Análisis visual, OCR, descripción |
| Video | Nativo | Comprensión de escenas, seguimiento temporal |
| Audio | Nativo | Transcripción, comprensión auditiva, comandos de voz |

## Integración en el Ecosistema Xiaomi

- **[[hyperos|HyperOS]]**: Comprensión multimodal para asistentes ([[Miclaw]])
- **[[xiaomi-su7|Xiaomi SU7]]**: Procesamiento visual en tiempo real para [[XLA-Cognitive-Model]]
- **Dispositivos smart home**: Procesamiento de cámaras y sensores
- **Teléfonos Xiaomi**: Asistente con comprensión visual y de audio

## Posicionamiento

A diferencia de modelos multimodales que requieren plugins externos (tipo DeepSeek-VL), MiMo-V2-Omni ofrece **procesamiento multimodal nativo** similar a [[kimi]] (MoonViT-3D). Su ventaja diferencial es la integración vertical con hardware Xiaomi.

## Relaciones

- [[MiMo-V2-TTS]] — Complemento de síntesis de voz
- [[Miclaw]] — Consumidor primario de capacidades multimodales
- [[XLA-Cognitive-Model]] — Consumidor de visión en tiempo real
- [[kimi]] — Competidor (MoonViT-3D multimodal nativo)

## Fuentes
- [HuggingFace Xiaomi](https://huggingface.co/Xiaomi) — checkpoints multimodales
- Anuncios oficiales Xiaomi AI Lab (2025-2026)
