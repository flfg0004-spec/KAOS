---
type: concept
title: GPU Pricing — Panorama 2025-2026
aliases: [GPU Pricing, GPU Cost, GPU Market, GPU Price Comparison]
tags: [concept, gpu, pricing, h100, a100, mi300x, l40s, compute, ai-ml]
related_entities: [metis, cloud-research-report]
related_concepts: [neoclouds, hyperscaler-comparison, spot-compute-strategy, cloud-computing, hybrid-cloud-strategy]
confidence: alta
tier: 2
created: 2026-05-27
status: active
---

# GPU Pricing — Panorama 2025-2026

## Bifurcación Estructural

El mercado GPU se divide en tres segmentos con dinámicas de precio distintas:

### 1. H100 Comoditizado ($1.38-2.49/GPU-hr on-demand)
- El H100 ha perdido ~70% de su valor desde el pico en 2023
- Los neoclouds ofrecen precios 3-4× menores que hyperscalers
- Spot H100 desde $0.80/hr (Verda/DataCrunch)

### 2. B200/Blackwell Premium ($3.50-$5.00+/GPU-hr)
- Nuevo hardware con scarcity pricing
- Sigue el arco típico: premium inicial → commodity en 18-24 meses

### 3. AMD MI300X como Alternativa ($1.71-2.50/GPU-hr)
- 192 GB VRAM (2.4× más que H100) a 30-40% menos costo
- Ideal para inferencia de modelos grandes sin model parallelism
- Barrera: ecosistema ROCm menos maduro que CUDA

### 4. A100 Clearance ($0.93-2.15/GPU-hr)
- Bajada del 30-40% interanual
- Opción budget para inference en modelos <30B parámetros
- ~85% del rendimiento H100 a ~55% del costo

## Tabla Comparativa Rápida

| GPU | VRAM | On-Demand Rango ($/hr) | Spot ($/hr) | Mejor Para |
|-----|:----:|:---------------------:|:-----------:|------------|
| **H100 SXM** | 80GB | 1.38-16.16 | 0.80-4.25 | Training, large model inference |
| **A100 80GB** | 80GB | 0.93-3.12 | 0.42-0.98 | Fine-tuning, <30B inference |
| **A100 40GB** | 40GB | 0.10-1.48 | 0.08-0.64 | Budget training |
| **L40S** | 48GB | 0.47-2.86 | 0.34-0.97 | Inference <30B, batch inference |
| **L4** | 24GB | 0.35-0.80 | 0.22-0.33 | Light inference, edge |
| **MI300X** | **192GB** | 1.71-3.60 | 1.11 | Large model inference (≥70B) |
| **B200 (est.)** | 192GB | ~3.50-5.00+ | — | Next-gen training |

## Insight Estratégico

Para equipos técnicos que pueden gestionar su propia infraestructura, los neoclouds ofrecen **ahorro masivo** (40-60%) vs hyperscalers por el mismo hardware. La prima de hyperscaler se justifica por ecosistema, soporte y disponibilidad global.

## Las GPUs Más Costo-Eficientes por Caso de Uso

| Caso de Uso | GPU Recomendada | Costo Efectivo | Justificación |
|-------------|----------------|:-------------:|---------------|
| **Training large (>30B)** | H100 spot (neocloud) | ~$1-2/hr | Mayoría del ecosistema CUDA |
| **Training budget (<30B)** | A100 PCIe spot (RunPod) | $0.42/hr | 85% perf H100 a 55% costo |
| **Batch inference** | L40S spot (AWS G6e) | $0.34/hr | 70-85% off, 48GB VRAM |
| **Production inference (≥70B)** | MI300X (TensorWave) | $1.71/hr | 192GB sin model parallelism |
| **Production inference (<30B)** | L40S reserved | $0.50-0.79/hr | Mejor balance VRAM/costo |
| **Experimentación** | Vast.ai H100 spot | ~$1.00/hr | Precios más bajos del mercado |

## Patrón de Evolución de Precios

Nuevo hardware → scarcity pricing (6-12 meses) → oferta se expande → neoclouds bajan precios → generación anterior se comoditiza. El B200/Blackwell sigue este arco ahora mismo.

## Referencias

- [[cloud-research-report#Precios de GPU Detalle]]
- [[neoclouds]]
- [[hyperscaler-comparison]]
- [[spot-compute-strategy]]
- [[cloud-computing]]
