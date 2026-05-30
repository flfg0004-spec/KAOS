---
type: technique
name: MOPD
role: training-distillation
description: "Multi-Teacher On-Policy Distillation — técnica de destilación donde múltiples modelos teacher guían el entrenamiento on-policy, permitiendo que el modelo estudiante supere a sus teachers individuales"
status: active
vendor: Xiaomi
tags: [xiaomi, mimo, distillation, training, mopd, multi-teacher, on-policy]
aliases: [Multi-Teacher On-Policy Distillation, MOPD Training]
created: 2026-05-26
modified: 2026-05-26
confidence: medium
sources:
  - Paper técnico Xiaomi AI Lab (2025)
---

# MOPD — Multi-Teacher On-Policy Distillation

## Descripción

**MOPD** (Multi-Teacher On-Policy Distillation) es una técnica de entrenamiento desarrollada por Xiaomi AI Lab, utilizada como método principal de destilación para los modelos flagship de la familia [[MiMo]]. 

## Cómo Funciona

A diferencia de la destilación tradicional (off-policy, un solo teacher), MOPD:

1. **Múltiples teachers**: Varios modelos expertos (cada uno especializado en diferentes dominios) actúan como teachers simultáneamente
2. **On-policy**: La destilación ocurre durante el entrenamiento activo, no post-entrenamiento
3. **Superación del teacher**: El modelo estudiante puede superar a cada teacher individual al integrar conocimiento de múltiples fuentes

## Aplicación

MOPD fue la técnica clave que permitió a [[MiMo-V2.5-Pro]] alcanzar **#1 open-source en benchmarks de agente**, superando a sus modelos teacher.

## Diagrama Conceptual

```
Teacher A (Código) ──┐
Teacher B (Razonamiento) ──┤
Teacher C (Agente) ──┤──► MOPD ──► MiMo-V2.5-Pro (1.02T/42B)
Teacher D (Seguridad) ──┤                     │
Teacher E (Multimodal) ──┘                     ▼
                                          #1 Open-Source Agent
```

## Relaciones

- [[MiMo-V2.5-Pro]] — Modelo entrenado con MOPD
- [[MiMo]] — Familia que utiliza esta técnica
- [[Hybrid-Attention]] — Arquitectura complementaria usada en los modelos

## Fuentes
- Paper técnico MOPD — Xiaomi AI Lab (2025)
