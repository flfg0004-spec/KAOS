---
type: technique
name: Hybrid Attention
role: architecture
description: "Arquitectura de atención híbrida SWA+GA (Sliding Window + Global Attention) con attention sink bias — optimizada para contexto largo eficiente en modelos MoE"
status: active
vendor: Xiaomi
tags: [xiaomi, mimo, attention, swa, ga, architecture, transformer, moe]
aliases: [SWA+GA Hybrid Attention, Hybrid Attention Sink, Xiaomi Hybrid Attention]
created: 2026-05-26
modified: 2026-05-26
confidence: medium
sources:
  - Paper técnico Xiaomi AI Lab (2025)
---

# Hybrid Attention — SWA+GA con Attention Sink Bias

## Descripción

**Hybrid Attention** es la arquitectura de atención patentada por Xiaomi para sus modelos [[MiMo]]. Combina **Sliding Window Attention (SWA)** con **Global Attention (GA)** y añade un **attention sink bias** para optimizar el procesamiento de contexto largo.

## Componentes

### Sliding Window Attention (SWA)
- Atiende solo a un contexto local (ventana deslizante)
- Bajo costo computacional: O(n × w) donde w es el tamaño de ventana
- Captura relaciones locales y de corto alcance

### Global Attention (GA)
- Atiende a tokens selectos globales (tokens especiales, cabeceras de segmento)
- Proporciona comprensión global del contexto
- Similar a atención completa pero esparsa

### Attention Sink Bias
- Mecanismo que sesga la atención hacia los primeros tokens (attention sink)
- Previene la degradación en contexto muy largo
- Basado en el fenómeno observado en modelos como StreamingLLM

## Beneficios

| Aspecto | Transformer Estándar | Hybrid Attention |
|---------|---------------------|------------------|
| Complejidad contexto largo | O(n²) | O(n × w + n × g) |
| Calidad en contexto largo | Buena | **Excelente** (sink bias) |
| Eficiencia computacional | Baja | **Alta** |
| Ideal para | Contextos medianos | **Contextos muy largos** |

## Implementación en MiMo

Todos los modelos LLM de la familia [[MiMo]] ([[MiMo-V2-Flash]], [[MiMo-V2.5-Pro]]) utilizan Hybrid Attention como mecanismo de atención principal:

```
Input Tokens
    │
    ├──► SWA (ventana local) ──► Atención local
    │
    ├──► GA (tokens globales) ──► Atención global esparsa
    │
    └──► Attention Sink Bias ──► Estabilidad en contexto largo
    │
    ▼
Output Combinado
```

## Relaciones

- [[MiMo-V2-Flash]] — Implementa Hybrid Attention
- [[MiMo-V2.5-Pro]] — Implementa Hybrid Attention
- [[MiMo]] — Arquitectura estándar de la familia
- [[Multi-Token-Prediction-MTP]] — Técnica complementaria de generación

## Fuentes
- Paper técnico de arquitectura — Xiaomi AI Lab (2025)
- StreamingLLM (Xiao et al., 2023) — Base teórica del attention sink
