---
type: concept
title: Cloud Storage — Estrategia de Precios 2025-2026
aliases: [Cloud Storage, Storage Pricing, Block Storage, Object Storage, File Storage]
tags: [concept, storage, block-storage, object-storage, cloud, pricing, oracle, aws, azure, gcp, cloudflare]
related_entities: [metis, cloud-research-report]
related_concepts: [cloud-computing, hyperscaler-comparison, hybrid-cloud-strategy]
confidence: alta
tier: 2
created: 2026-05-27
status: active
---

# Cloud Storage — Estrategia de Precios 2025-2026

## Block Storage (SSD) — Comparativa por GB/mes

| Proveedor | Tier | $/GB/mes | IOPS Incluidas |
|-----------|------|:--------:|:--------------:|
| 🥇 **Oracle** | Balanced | **$0.0255** | 60/GB (hasta 25K) |
| 🥇 **Oracle** | Lower Cost | **$0.0255** | 2/GB (hasta 3K) |
| 🥈 **AWS** | gp3 (SSD) | $0.080 | 3,000 gratis |
| 🥉 **Azure** | Premium SSD v2 | $0.081 | 3,000 gratis |
| GCP | pd-balanced (SSD) | $0.100 | 6R/W por GB |
| AWS | io2 (SSD) | $0.125 | IOPS aparte |

**Ganador**: Oracle Block Volumes — 68% más barato que AWS gp3.

## Object Storage — Comparativa por GB/mes

| Proveedor | Hot | Frío | Archive | Egress |
|-----------|:---:|:----:|:-------:|:------:|
| 🥇 **Azure Blob** | **$0.0184** | $0.01 | $0.002 | $0.087 |
| **AWS S3** | $0.023 | $0.0125 (IA) | **$0.00099** (Deep Archive) | $0.09 |
| **GCP Storage** | $0.020 | $0.01 (Nearline) | $0.0012 (Archive) | **$0.12** |
| **Oracle Object** | $0.0255 | ~$0.01 (IA) | ~$0.0026 | **$0.0085** (10TB free) |
| 🥇 **Cloudflare R2** | $0.015 | — | — | **$0.00** |

**Ganadores**: Azure Blob para Hot, AWS Glacier para Archive, Cloudflare R2 para Egress.

## File Storage (NAS)

| Proveedor | $/GB/mes | Notas |
|-----------|:--------:|-------|
| AWS EFS Standard | $0.30 | Elastic throughput |
| AWS EFS IA | $0.0165 | Lifecycle automático |
| Azure Files Premium | $0.10-0.16 | SMB/NFS |
| GCP Filestore Basic HDD | $0.16 | Mín 1 TiB |
| Oracle FSS | ~$0.03 | Datos no confirmados |

## Recomendaciones Estratégicas

1. **Block Storage**: Oracle Block Volumes — ahorro del 68% vs AWS gp3
2. **Object Storage**: Cloudflare R2 para datos activos (zero egress) + AWS Glacier Deep Archive para archive
3. **Egress**: Cloudflare R2 ($0/GB) u Oracle ($0.0085/GB con 10TB free)
4. **Riesgo**: Evaluar vendor lock-in y costo de migración antes de comprometerse

## Referencias

- [[cloud-research-report#Precios de Almacenamiento]]
- [[cloud-computing]]
- [[hyperscaler-comparison]]
