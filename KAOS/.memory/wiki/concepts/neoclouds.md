---
type: concept
title: Neoclouds — Proveedores GPU-Especializados
aliases: [Neocloud, Neocloud Providers, GPU Cloud, AI Cloud]
tags: [concept, neocloud, gpu, cloud, ai-ml, compute, strategic]
related_entities: [metis, cloud-research-report]
related_concepts: [cloud-computing, gpu-pricing, hyperscaler-comparison, hybrid-cloud-strategy]
confidence: alta
tier: 2
created: 2026-05-27
status: active
---

# Neoclouds — Proveedores GPU-Especializados

Los neoclouds son proveedores de cloud especializados en GPUs para AI/ML, que han emergido como alternativa a los hyperscalers tradicionales (AWS, Azure, GCP).

## Por qué importan

Los neoclouds ofrecen **3-4× menor precio** que los hyperscalers por el mismo hardware NVIDIA H100, porque:
- Operan con infraestructura más ligera (sin ecosistema enterprise completo)
- Se enfocan exclusivamente en GPU compute (sin storage, networking enterprise, etc.)
- Modelo de negocios optimizado para alta rotación de GPUs

## Mapa de Proveedores

| Proveedor | Diferenciador | Mejor Para | Riesgo |
|-----------|--------------|-----------|--------|
| **CoreWeave** (CRWV) | Neocloud más grande, Nasdaq, backlog $ | Clusters grandes, contratos multi-año | Dependencia NVIDIA |
| **Lambda Labs** | Developer-first, zero egress, pre-IPO | Equipos que valoran experiencia dev | Disponibilidad variable |
| **RunPod** | Mejor balance precio/confiabilidad, 31 regiones | Equipos pequeños/medianos, serverless inference | Menos enterprise |
| **Vast.ai** | Precios más bajos (marketplace P2P) | Experimentación, presupuesto limitado | Calidad inconsistente |
| **Verda (DataCrunch)** | Spot más bajo ($0.80/hr H100), EU/GDPR | Workloads tolerantes a interrupción | Solo 3 DCs en EU |
| **Nebius** | Soberanía europea, inversión NVIDIA | Clientes EU con req. compliance | Menos presencia global |
| **Crusoe** | Energía limpia, flare gas mitigation | Empresas con objetivos ESG | Precios más altos |
| **TensorDock** | H100 más barato ($1.20/hr), zero egress | Costo-sensitivos sin compromiso | Menos conocido |
| **FluidStack** | Edge computing distribuido | Edge workloads | Disponibilidad limitada |

## Proyección de Mercado

- **2025**: ~$8B en ingresos
- **2031**: ~$80B proyectado (Synergy Research Group)
- **Riesgo**: Consolidación de ~200 neoclouds → 4-5 jugadores dominantes

## Precios Referencia (H100 80GB, 2026)

| Proveedor | On-Demand ($/GPU-hr) | Spot ($/GPU-hr) |
|-----------|:--------------------:|:---------------:|
| CoreWeave | 2.76 (8× nodo) | ~1.07/GPU (6mo reserved) |
| Lambda Labs | 1.49-2.49 | — |
| RunPod | 1.69 (SXM) | 0.81 (70% off) |
| Vast.ai | 1.40-3.10 | ~2.00 |
| TensorDock | **1.20** | 0.60 |
| Verda (DataCrunch) | 2.29 | **0.80** |
| Hyperbolic | 2.29 | — |

## Referencias

- [[cloud-research-report#Proveedores Alternativos Neoclouds Perfiles Estratégicos]]
- [[cloud-computing]]
- [[hyperscaler-comparison]]
- [[gpu-pricing]]
- [[metis#Investigación Cloud 2025-2026 Hallazgos Estratégicos Incorporados]]
