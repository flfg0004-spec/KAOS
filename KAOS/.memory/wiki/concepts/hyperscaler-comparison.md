---
type: concept
title: Hyperscalers — Comparativa Estratégica
aliases: [Hyperscalers, AWS vs Azure vs GCP vs Oracle, Cloud Providers]
tags: [concept, hyperscaler, aws, azure, gcp, oracle, cloud, compute, storage]
related_entities: [metis, cloud-research-report]
related_concepts: [cloud-computing, neoclouds, gpu-pricing, cloud-storage-strategy, spot-compute-strategy, hybrid-cloud-strategy]
confidence: alta
tier: 2
created: 2026-05-27
status: active
---

# Hyperscalers — Comparativa Estratégica AWS vs Azure vs GCP vs Oracle

## Resumen de Posicionamiento

| Proveedor | Fortaleza Principal | Debilidad Principal | Mejor Para |
|-----------|-------------------|-------------------|------------|
| **AWS** | Ecosistema más amplio, madurez | Precios más altos en general | Empresas establecidas, workloads diversos |
| **Azure** | Integración Microsoft, AI/ML services | Precios altos en GPU | Clientes enterprise Microsoft |
| **GCP** | Big Data, K8s nativo, spot más barato | Egress más caro, menos servicios | Startups data-driven, burst training |
| **Oracle (OCI)** | Precios más bajos (compute, storage) | Menos servicios, menor adopción | Budget-conscious, storage-heavy |

## Comparativa de Precios (H100 8-GPU Nodo/hr)

| Proveedor | On-Demand | Spot | 1yr Reserved |
|-----------|:---------:|:----:|:-----------:|
| **AWS** (p5.48xlarge) | $16.62 | $7.23 (58% off) | $10.55 (35% off) |
| **Azure** (ND96isr_H100_v5) | $16.88 | $7.44 (56% off) | $10.47 (36% off) |
| **GCP** (a3-highgpu-8g) | $14.17 | $3.25 (77% off) | $8.96 (39% off) |
| **Oracle** (BM.GPU.H100.8) | $12.00 | N/A | Contact sales |

## Compute General (4vCPU/16GB Linux/hr)

| Proveedor | $/hr | $/mes (730h) | Arquitectura |
|-----------|:----:|:-----------:|:------------:|
| **OCI** | $0.074 | $54 | AMD Genoa / Ampere ARM |
| **GCP** | $0.134 | $98 | Intel |
| **Azure** | $0.154 | $112 | Cobalt 100 ARM |
| **AWS** | $0.163 | $119 | Graviton3 ARM |

OCI es **45-64% más barato** que otros hyperscalers en compute on-demand.

## Descuentos por Compromiso

| Programa | 1yr | 3yr | Spot Máx |
|----------|:---:|:---:|:--------:|
| AWS Savings Plans | 27-42% | 62-72% | 90% |
| Azure RI | 30-46% | 55-72% | 90% |
| Azure Savings Plan | 11-33% | 32-65% | — |
| GCP CUD Resource | 37% | 55-57% | **91%** |
| OCI Universal Credits | ~10-20% | ~25-40% | 50% (fijo) |

## Recomendación Estratégica

Para KAOS: **GCP para spot GPU** (máximo descuento 91%) + **OCI para compute general** (precios más bajos) + **Cloudflare R2 para storage object** (zero egress).

## Referencias

- [[cloud-research-report#Comparativa Rápida de Proveedores]]
- [[neoclouds]]
- [[gpu-pricing]]
- [[cloud-storage-strategy]]
- [[spot-compute-strategy]]
- [[cloud-computing]]
