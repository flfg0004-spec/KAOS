---
audience: agent
type: concept
title: Spot Compute — Estrategia para AI/ML
aliases: [Spot Instances, Spot GPU, Preemptible, Spot Strategy, Spot Computing]
tags: [concept, spot, preemptible, gpu, cost-optimization, ai-ml, training, inference]
related_entities: [metis, cloud-research-report]
related_concepts: [cloud-computing, gpu-pricing, neoclouds, hyperscaler-comparison, hybrid-cloud-strategy]
confidence: alta
tier: 2
created: 2026-05-27
status: active
---

# Spot Compute — Estrategia para AI/ML

Las instancias spot (o preemptibles) ofrecen descuentos de **60-91%** vs on-demand, con el riesgo de interrupción. Son el *single biggest cost lever* para AI/ML.

## Ahorro por GPU y Proveedor

| GPU | Proveedor | On-Demand ($/hr) | Spot ($/hr) | Ahorro | Ventana Preemptción |
|-----|-----------|:--------------:|:-----------:|:------:|:------------------:|
| **H100** | Verda (DataCrunch) | $2.29 | **$0.80** | **65%** | 5 min (RunPod) |
| **H100** | GCP (a3-highgpu) | $14.17 | $3.25 | **77%** | 30 seg |
| **H100** | AWS (p5.48xlarge) | $16.62 | $7.23 | 58% | 2 min |
| **A100** | RunPod (PCIe) | $1.19 | $0.42 | **65%** | 5 min |
| **A100** | GCP (a2-highgpu) | $2.28 | $0.90 | 66% | 30 seg |
| **L40S** | AWS (g6e.xlarge) | $1.861 | $0.491 | **74%** | 2 min |
| **L4** | GCP (g2-std-4) | $0.35 | $0.22 | 37% | 30 seg |

## Casos de Uso

### ✅ Training con Checkpointing (Recomendado)
- Checkpointing cada 15-30 min
- ROI típico: 3-5× en el primer mes
- Ideal para training distribuido tolerante a fallos

### ❌ Production Inference (No Recomendado)
- Sin fallback, la interrupción causa caídas de servicio
- Solo viable con nodos de respaldo on-demand

### ✅ Batch Inference (Recomendado)
- Workloads idempotentes y particionables
- Reintentar instancias fallidas es trivial

### ✅ Experimentación (Recomendado)
- Exploración de hiperparámetros
- Fine-tuning de prueba de concepto
- Máxima flexibilidad al menor costo

## Estrategia Recomendada para KAOS

1. **Training estable**: Base reserved en neocloud (Lambda Labs o CoreWeave)
2. **Burst training**: GCP A3 spot (77% off, checkpointing cada 15 min)
3. **Batch inference**: AWS G6e (L40S) spot (74% off)
4. **Experimentación**: Vast.ai o Verda spot (precios más bajos)

## Riesgos y Mitigaciones

| Riesgo | Probabilidad | Impacto | Mitigación |
|--------|:-----------:|:-------:|-----------|
| Interrupción durante training crítico | Alta | Medio | Checkpointing 15-30 min, nodos de respaldo |
| Disponibilidad de spot variable | Alta | Bajo | Diversificar entre 2-3 proveedores |
| Precios spot volátiles | Media | Medio | Usar reserved para base, spot para bursts |

## Referencias

- [[cloud-research-report#Spot Preemptible Resumen de Ahorro]]
- [[gpu-pricing]]
- [[neoclouds]]
- [[hyperscaler-comparison]]
- [[cloud-computing]]
- [[metis#Investigación Cloud 2025-2026 Hallazgos Estratégicos Incorporados]]
