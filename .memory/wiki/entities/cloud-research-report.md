---
type: strategic_report
title: "Investigación Estratégica: Recursos de Cómputo en la Nube 2025-2026"
agent: metis
created: 2026-05-27
status: active
confidence_level: high
tags: [cloud, gpu, pricing, aws, azure, gcp, oracle, storage, compute, neocloud, strategic-research]
aliases: [Cloud-Research-Report-2026, GPU-Pricing-Research]
related_entities: [metis]
related_concepts: [cloud-computing, neoclouds, gpu-pricing, hyperscaler-comparison, cloud-storage-strategy, spot-compute-strategy]
---

# Investigación Estratégica: Recursos de Cómputo en la Nube 2025-2026

**Elaborado por**: Metis (Μῆτις) — Agente de Estrategia KAOS  
**Fecha**: 27 de mayo de 2026  
**Fuentes trianguladas**: 30+ (oficiales, agregadores, analistas)  
**Perfil de confianza**: Alto — datos confirmados por múltiples fuentes independientes

---

## Resumen Ejecutivo

El mercado de cómputo cloud en 2025-2026 atraviesa una **transformación estructural**. Tres fuerzas concurrentes están redefiniendo la economía de la nube:

**1. Fragmentación de precios de GPU.** Los precios de NVIDIA H100 han caído ~70% desde su pico en 2023 (/hr → .38-.49/hr en proveedores especializados), pero los hyperscalers mantienen primas de 3-4× (-14/hr). Aparece una **bifurcación estructural**: H100 se comoditiza mientras B200/Blackwell mantiene pricing premium (.50-/hr). AMD MI300X emerge con 192 GB VRAM a .71-.50/hr (30-40% menos que H100).

**2. Neoclouds vs Hyperscalers.** Los neoclouds (CoreWeave, Lambda Labs, RunPod, Vast.ai) capturan el segmento de más rápido crecimiento con ingresos de ~ en 2025 (proyectados a  para 2031). CoreWeave cotiza en Nasdaq (CRWV) con backlog de + en contratos. Los hyperscalers responden con recortes de precios: AWS redujo H100 18% y hasta 44% en junio 2025.

**3. Guerra de precios de almacenamiento.** Oracle Cloud lidera en block storage (.0255/GB/mes), significativamente más barato que AWS EBS gp3 (.08/GB). Azure Blob Hot lidera object storage (.0184/GB). AWS Glacier Deep Archive sigue siendo el archive más barato (.00099/GB/mes). Cloudflare R2 fuerza presión a la baja en egress (/GB).

**Recomendación estratégica principal**: Para workloads de AI/ML, la estrategia óptima es **híbrida**: base bare metal o reserved en neocloud para cargas estables (>55% utilización) + spot en hyperscalers para bursts. Esto puede reducir el TCO 40-60% vs on-demand puro en hyperscalers.

---

## Comparativa Rápida de Proveedores

| Proveedor | GPU H100 (/hr) | GPU A100 (/hr) | Storage SSD (/GB/mes) | Compute General 4vCPU/16GB (/hr) | Descuento Spot Máx |
|-----------|:--------------:|:--------------:|:---------------------:|:-------------------------------:|:------------------:|
| **AWS** | .22¹ | .10 | .080 (gp3) | .163 (m7g.4x) | 90% |
| **Azure** | .19¹ | .56 | .081 (PSSDv2) | .154 (D4ps v5) | 90% |
| **GCP** | .06¹ | .28 | .100 (pd-balanced) | .134 (e2-s4) | **91%** |
| **Oracle** | .12¹ | .00 | **.0255** (block) | **.074** (E4.Flex) | 50% |
| **CoreWeave** | .23¹ | .70 | N/A² | N/A² | — |
| **Lambda Labs** | .49¹ | .52 | N/A² | N/A² | 35% |
| **RunPod** | .39¹ | .39 | N/A² | N/A² | **70%** |
| **Vast.ai** | **.40¹** | **.93** | N/A² | N/A² | 60% |

*¹ Precio por GPU en configuración 8-GPU. ² Proveedores GPU-focused sin oferta de storage generalista.*

---

## Precios de GPU (Detalle)

### NVIDIA H100 (80GB) — 2025-2026

#### Hyperscalers — 8× H100 SXM Nodo Completo

| Proveedor | Instancia | On-Demand (nodo/hr) | On-Demand ($/GPU-hr) | Spot ($/GPU-hr) | 1yr Reserved ($/GPU-hr) |
|-----------|-----------|:------------------:|:--------------------:|:---------------:|:-----------------------:|
| **AWS** | p5.48xlarge | .62 (post-cut Ene 2026) | .08 | .23 (~58% off) | .55 (35% off) |
| **AWS** | p5.48xlarge (pre-cut) | .32 | .29 | ~.50 (70% off) | .88 |
| **GCP** | a3-highgpu-8g | .17 (post-cut) | .77 | .25-.91 (60-91%) | .96 (39% off) |
| **GCP** | a3-megagpu-8g | .21 | .53 | ~.00 | — |
| **Azure** | ND96isr_H100_v5 | .88 (post-cut) | .11 | .50-.44 (56-65%) | .47 (36% off) |
| **Azure** | ND96isr_H100_v5 (pre-cut) | .32 | .29 | .17-.55 | — |
| **Oracle** | BM.GPU.H100.8 | .00 | .00 | N/A | Contact sales |

#### Proveedores Especializados — 1× H100

| Proveedor | On-Demand ($/GPU-hr) | Spot ($/GPU-hr) | Reserved ($/GPU-hr) |
|-----------|:--------------------:|:---------------:|:-------------------:|
| **CoreWeave** (8× H100) | .76/hr nodo (.85/GPU) | N/A | .07/GPU (6mo) |
| **Lambda Labs** (1× H100) | .49-.49 | — | .89-.99 (3mo) |
| **RunPod** (1× H100 SXM) | .69 | .81 (70% off) | — |
| **RunPod** (1× H100 PCIe) | .99 | .72 (64% off) | — |
| **Vast.ai** (1× H100 SXM) | .40-.10 | ~.00 | 50% off (3-6mo) |
| **Hyperbolic** | .29 | — | — |
| **Hyperstack** | .90 | — | — |
| **FluidStack** | .49 | — | .19 (3mo) |
| **Nebius** | .95 | — | .00 (commit) |
| **Verda** (DataCrunch) | .29 | **.80** (spot más bajo) | — |
| **TensorDock** | .20 | .60 | — |

**💡 Insight estratégico**: AWS, Azure y GCP cobran **3-4× más** que los neoclouds por el mismo hardware H100. La brecha se justifica por ecosistema, soporte y disponibilidad global, pero para equipos técnicos que pueden gestionar su propia infraestructura, los neoclouds ofrecen ahorro masivo.

---

### NVIDIA A100 (40GB / 80GB)

#### 8× A100 SXM Nodo Completo

| Proveedor | Instancia | VRAM | On-Demand (nodo/hr) | On-Demand ($/GPU-hr) | Spot ($/GPU-hr) |
|-----------|-----------|:----:|:------------------:|:--------------------:|:---------------:|
| **AWS** | p4d.24xlarge | 40GB | .77 | .10 | .08-.64 (60-70%) |
| **AWS** | p4de.24xlarge | 80GB | .97 | .12 | .98 (63% off) |
| **Azure** | ND96asr_v4 | 80GB | .50 | .56 | .07 (70% off) |
| **GCP** | a2-highgpu-8g | 40GB | .27-.20 | .28-.40 | .90 (~66%) |
| **GCP** | a2-ultragpu-8g | 80GB | .22 | .03 | .69 (~66%) |
| **Oracle** | BM.GPU.A100-v2.8 | 80GB | .00 | **.00** | N/A |

#### Proveedores Especializados — 1× A100

| Proveedor | On-Demand ($/GPU-hr) | Spot ($/GPU-hr) |
|-----------|:--------------------:|:---------------:|
| **Lambda Labs** (40GB) | .48 | — |
| **Lambda Labs** (80GB SXM) | .99 | — |
| **RunPod** (A100 SXM) | .39 | .59 (58% off) |
| **RunPod** (A100 PCIe) | .19 | .42 (65% off) |
| **CoreWeave** (8× A100) | .70/GPU | .01/GPU reservado |
| **Vast.ai** (80GB) | .93-.15 | .95 |
| **Cudo Compute** | .37-.63 | — |

**💡 Insight**: A100 ha entrado en territorio de *clearance pricing* — bajada del 30-40% interanual. Es la opción budget para inference en modelos <30B parámetros (~85% del rendimiento H100 a ~55% del costo).

---

### NVIDIA L40S (48GB) / L4 (24GB)

#### L40S — AWS G6e

| Instancia | GPUs | On-Demand (instancia/hr) | Spot ($/hr) | Ahorro Spot |
|-----------|:----:|:----------------------:|:-----------:|:-----------:|
| g6e.xlarge | 1× L40S | .861 | .491 | **74%** |
| g6e.12xlarge | 4× L40S | .493 | .659 | **84%** |
| g6e.48xlarge | 8× L40S | .131 | .973 | 80% |

#### L40S — Otros Proveedores

| Proveedor | On-Demand ($/GPU-hr) | Spot ($/hr) |
|-----------|:--------------------:|:-----------:|
| **RunPod** | .79-.86 | .34 (57% off) |
| **TensorDock** | **.47** | — |
| **Vast.ai** | .60-.90 | — |
| **Massed Compute** | .88 | — |
| **Civo** | .29 | — |
| **CoreWeave** | .25 | .90+ reservado |
| **Vultr** | .67 | .848 (3yr) |
| **Median mercado** | **.56/hr** | **.50/hr** |

#### L4 — Google G2 / AWS G6

| Proveedor | On-Demand ($/GPU-hr) | Spot ($/GPU-hr) |
|-----------|:--------------------:|:---------------:|
| **GCP** (g2-standard-4) | .35 | .22 (37% off) |
| **AWS** (g6.xlarge) | .805 | .328 (59% off) |
| **RunPod** | .44 | — |
| **Median mercado** | **.90/hr** | **.32/hr** |

**💡 Insight**: L40S es la GPU de inferencia más costo-eficiente. A .47-0.79/hr en proveedores especializados, ofrece 48 GB VRAM perfecto para modelos de 7-13B parámetros. Spot L40S (70-85% off) es ideal para batch inference.

---

### AMD MI300X (192GB)

| Proveedor | GPUs | On-Demand ($/GPU-hr) | Spot |
|-----------|:----:|:------------------:|:----:|
| **Azure** (ND96isr_MI300X_v5) | 8× MI300X | .44 (nodo .52/hr) | .11 |
| **Azure** (ND96is_MI300X_v5) | 1× MI300X | .60 (caro outlier) | .87 |
| **DigitalOcean** | 1× | .99 | — |
| **Hotaisle** | 8× | .99 | — |
| **TensorWave** | 1× | **.71** | — |
| **Crusoe** | 1× | .45 | — |
| **Mediana mercado** | 1× | **.99** | .49 |

**💡 Insight**: El MI300X ofrece 192 GB VRAM (2.4× más que H100) a ~.99/GPU-hr — 30-40% menos que H100. Ventaja en inferencia de modelos grandes (menos necesidad de model parallelism). Barreras: disponibilidad limitada y ecosistema ROCm menos maduro que CUDA.

---

## Precios de Almacenamiento

### Block Storage (SSD) — Comparativa por GB/mes

| Proveedor | Tier | $/GB/mes | IOPS Incluidas | Notas |
|-----------|------|:--------:|:--------------:|-------|
| **Oracle** | Balanced | **.0255** | 60/GB (hasta 25K) | Más barato del mercado |
| **Oracle** | Lower Cost | **.0255** | 2/GB (hasta 3K) | Ideal para backup |
| **AWS** | gp3 (SSD) | .080 | 3,000 gratis | 95% de workloads |
| **AWS** | io2 (SSD) | .125 | IOPS aparte | Alta durabilidad 99.999% |
| **AWS** | st1 (HDD) | .045 | Burst | Throughput |
| **AWS** | sc1 (HDD) | .015 | Burst | Archive |
| **Azure** | Premium SSD v2 | .081 | 3,000 gratis | IOPS extra: .0052/IOPS |
| **Azure** | Standard HDD | .045 | — | Por capacidad usada |
| **Azure** | Ultra Disk | .115 | IOPS aparte | Max 400K IOPS |
| **GCP** | pd-standard (HDD) | .040 | 0.75R/1.5W por GB | Bulk, backups |
| **GCP** | pd-balanced (SSD) | .100 | 6R/W por GB | Uso general |
| **GCP** | pd-ssd (SSD) | .170 | 30R/W por GB | Alta IOPS |

**🏆 Ganador**: Oracle Block Volumes — .0255/GB/mes es ~68% más barato que AWS gp3 y sin variación regional.

---

### Object Storage — Comparativa por GB/mes

| Proveedor | Tier Caliente | Tier Frío | Tier Archive | Egress (/GB) | Notas |
|-----------|:------------:|:---------:|:------------:|:------------:|-------|
| **AWS S3** | .023 | .0125 (IA) | **.00099** (Deep Archive) | .09 | Líder en eco-sistema |
| **Azure Blob** | **.0184** (Hot) | .01 (Cool) | .002 (Archive) | .087 | Más barato en Hot |
| **GCP Storage** | .020 | .01 (Nearline) | .0012 (Archive) | **.12** | Egress más caro |
| **Oracle Object** | .0255 | ~.01 (IA) | ~.0026 | **.0085** (10TB free) | Egress más barato |
| **Cloudflare R2** | .015 | — | — | **.00** | Zero-egress |

**🏆 Ganador Hot**: Azure Blob Hot (.0184/GB)  
**🏆 Ganador Archive**: AWS Glacier Deep Archive (.00099/GB)  
**🏆 Ganador Egress**: Cloudflare R2 (/GB) | Oracle (.0085/GB con 10TB free)

---

### File Storage (NAS) — Comparativa

| Proveedor | Tier | $/GB/mes | Capacidad Mín | Notas |
|-----------|------|:--------:|:-------------:|-------|
| **AWS EFS** | Standard | .30 | None | Elastic throughput |
| **AWS EFS** | IA | .0165 | 128KB min file | Lifecycle automático |
| **Azure Files** | Premium (SSD) | .10-.16 | Provisionado | SMB/NFS |
| **Azure Files** | Standard TX Opt. | .06 | Pay-as-you-go | |
| **GCP Filestore** | Basic HDD | .16 | 1 TiB | |
| **GCP Filestore** | Basic SSD | ~.30 | 2.5 TiB | |
| **Oracle FSS** | Base | ~.03 | — | Datos no confirmados |

---

## Precios de Compute / Servidores

### General Purpose — 4 vCPU, 16 GB RAM (On-Demand Linux/hr)

| Proveedor | Instancia | $/hr | $/mes (730h) | Arquitectura |
|-----------|-----------|:----:|:------------:|:------------:|
| 🥇 **OCI** | VM.Standard.E5.Flex | **.074** | **** | AMD Genoa |
| 🥇 **OCI** | VM.Standard.A1.Flex (ARM) | .066 |  | Ampere ARM |
| 🥈 **GCP** | e2-standard-4 | .134 |  | Intel |
| 🥉 **Azure** | D4ps v5 (ARM) | .154 |  | Cobalt 100 |
| **AWS** | m7g.xlarge (ARM) | .163 |  | Graviton3 |
| **GCP** | n2-standard-4 | .194 |  | Intel |
| **AWS** | m7i.xlarge (Intel) | .202 |  | Xeon |

**💡 OCI es 45-64% más barato** en compute on-demand vs hyperscalers, especialmente con A1.Flex ARM.

---

### Optimizado para Cómputo

| Proveedor | Familia | vCPU:RAM | Desde/hr | Spot Máx |
|-----------|---------|:-------:|:-------:|:--------:|
| **AWS** | C8g (Graviton4) | 1:2 | .0399 (1vCPU) | ~71% |
| **AWS** | C7gn (ARM) | 1:2 | .0624 (1vCPU) | **~80%** |
| **GCP** | C3 (Intel) | 1:4 | .2016 (4vCPU) | **~83%** |
| **GCP** | C3D (AMD) | 1:4 | .1816 (4vCPU) | ~82% |
| **Azure** | Fsv2 | 1:2 | .0846 (2vCPU) | ~86% |

---

### Descuentos — Comparativa de Programas

| Programa | 1yr | 3yr | Spot Máx | Flexibilidad |
|----------|:---:|:---:|:--------:|:-----------:|
| **AWS Savings Plans** | 27-42% | **62-72%** | 90% | Alta |
| **Azure RI** | 30-46% | 55-72% | 90% | Baja |
| **Azure Savings Plan** | 11-33% | 32-65% | — | Media |
| **GCP CUD Resource** | 37% | 55-57% | **91%** | Media |
| **GCP Flex CUD** | 28% | 46% | — | Alta |
| **GCP SUDs** | hasta 30% | automático | — | Máxima |
| **OCI Universal Credits** | ~10-20% | ~25-40% | 50% (fijo) | Alta |

---

## Soluciones Alternativas

### Spot / Preemptible — Resumen de Ahorro

| GPU | Proveedor | On-Demand ($/GPU-hr) | Spot ($/GPU-hr) | Ahorro | Ventana Preemptción |
|-----|-----------|:-------------------:|:---------------:|:------:|:------------------:|
| **H100** | Verda (DataCrunch) | .29 | **.80** | **65%** | 5 min (RunPod) |
| **H100** | GCP (a3-highgpu) | .77 | .25 | 77% | 30 seg |
| **H100** | AWS (p5.48xlarge) | .08 | .23 | 58% | 2 min |
| **A100** | RunPod (PCIe) | .19 | .42 | **65%** | 5 min |
| **A100** | GCP (a2-highgpu) | .28 | .10 | 66% | 30 seg |
| **L40S** | AWS (g6e.xlarge) | .861 | .491 | **74%** | 2 min |
| **L4** | GCP (g2-std-4) | .35 | .22 | 37% | 30 seg |

**Recomendación**: Spot es el *single biggest cost lever* para AI/ML. Para training con checkpointing cada 15-30 min, el ROI típico es 3-5× en el primer mes. No usar para production inference sin fallback.

---

### Bare Metal vs Cloud — Punto de Equilibrio

| Métrica | Valor |
|---------|:-----:|
| Punto de equilibrio bare metal < cloud | >55-60% utilización sostenida |
| Cloud más barato | <40-55% utilización |
| Break-even on-prem vs on-demand | ~8,556 hrs continuas (~12 meses 24/7) |
| Utilización real típica enterprise | 15-25% |
| GPU utilization en K8s (promedio) | **5%** (según Cast AI 2026) |

**Ejemplo 8-GPU H100 Node, 3 años**:

| Modalidad | Costo 3 años | Costo efectivo/GPU-hr |
|-----------|:-----------:|:--------------------:|
| Cloud On-Demand | .58M | .29 |
| Cloud 1yr Reserved | .62M | .69 |
| Cloud 3yr Reserved | .03M | .92 |
| **Bare Metal** (100% ut.) | **-760K** | **.85** |
| **Bare Metal** (40% ut.) | Igual | .13 |

**Estrategia óptima**: Híbrido — base bare metal o reserved para cargas estables + spot cloud para bursts. Reduce TCO 40-50%.

---

### Proveedores Alternativos (Neoclouds) — Perfiles Estratégicos

| Proveedor | Diferenciador | Mejor Para | Riesgo |
|-----------|--------------|-----------|--------|
| **CoreWeave** | Neocloud más grande (Nasdaq: CRWV), backlog  | Clusters grandes, contratos multi-año | Dependencia NVIDIA |
| **Lambda Labs** | Developer-first, zero egress, pre-IPO | Equipos que valoran experiencia dev | Disponibilidad variable |
| **RunPod** | Mejor balance precio/confiabilidad, 31 regiones | Equipos pequeños/medianos, serverless inference | Menos enterprise |
| **Vast.ai** | Precios más bajos (marketplace P2P) | Experimentación, presupuesto limitado | Calidad inconsistente |
| **Verda (DataCrunch)** | Spot más bajo (.80/hr H100), EU/GDPR | Workloads tolerantes a interrupción | Solo 3 DCs en EU |
| **Nebius** | Soberanía europea, inversión NVIDIA  | Clientes EU con req. compliance | Menos presencia global |
| **Crusoe** | Energía limpia, flare gas mitigation | Empresas con objetivos ESG | Precios más altos |
| **TensorDock** | H100 más barato (.20/hr), zero egress | Costo-sensitivos sin compromiso | Menos conocido |
| **FluidStack** | Edge computing distribuido | Edge workloads | Disponibilidad limitada |

---

## Tendencias del Mercado 2025-2026

### 1. Capex Histórico — Inversión en Infraestructura

| Año | Capex Big-5 (AMZN, GOOG, META, MSFT, ORCL) | Crecimiento YoY |
|:---:|:-------------------------------------------:|:---------------:|
| 2024 | ~ | — |
| 2025 | ~ | +73% |
| **2026 (guidance)** | **~** | **+64%** |

**75% (~)** se dirige a infraestructura específica de AI: GPUs, servidores, DC, enfriamiento.  
**9 mayores CSPs globales**: ~ en 2026 (incluye ByteDance, Tencent, Alibaba, Baidu).

### 2. Evolución de Precios GPU (H100)

| Período | H100 On-Demand ($/hr) | Spot ($/hr) |
|:-------:|:--------------------:|:-----------:|
| Q1 2023 | ~.00 | ~.00 |
| Q1 2024 | ~.00 | ~.20 |
| Q1 2025 | ~.20 | ~.00 |
| Q2 2026 | **.38-.50** | **.80-.00** |

**Patrón**: Nuevo hardware lanza con scarcity pricing → oferta se expande 18-24 meses → neoclouds bajan precios → generación anterior se comoditiza. **B200/Blackwell sigue este arco ahora** (.50-/hr).

### 3. Auge de ASICs Custom

| Año | Cuota NVIDIA en Aceleradores AI |
|:---:|:------------------------------:|
| 2022 | ~95% |
| 2024 | ~84% |
| 2025 | ~73% |
| **2026 (est.)** | **62-66%** |
| 2028 (proy.) | ~20-30% en inferencia |

**Despliegue ASICs 2026**: ~1.9M aceleradores (900K TPU, 600K Trainium, 250K Maia, 180K MTIA).  
**Ventaja TCO**: 30-65% mejor que NVIDIA para inferencia a escala.

### 4. Regulación y Export Controls

- **Ene 2026**: BIS afloja controles — H200/MI325X a China pasan a revisión caso por caso (con tope 50% volumen)
- **Tarifa 232**: 25% a ciertos semiconductores desde enero 2026
- Contexto político: propuesta de revenue sharing del 25% para exportaciones a China

### 5. Kubernetes y Serverless

- **66%** de organizaciones usan K8s para inferencia GenAI (CNCF 2026)
- **Serverless GPU market**: .89B (2024) → .92B (2033) — CAGR 36.7%
- DRA (Dynamic Resource Allocation) graduó a GA en K8s 1.34 — nuevo estándar para gestión de GPUs

---

## Recomendaciones Estratégicas

### 1. Para workloads de AI/ML Training
**Estrategia**: Base reserved en neocloud (Lambda Labs o CoreWeave) + spot GCP para bursts.  
**Ahorro estimado**: 50-70% vs on-demand en hyperscalers.  
**Riesgo clave**: Disponibilidad de spot — implementar checkpointing cada 15 min.

### 2. Para Production Inference
**Estrategia**: L40S en spot (AWS G6e, 70-85% off) para modelos <30B. MI300X para modelos ≥70B.  
**Ahorro estimado**: 60-80% vs H100 on-demand.  
**Justificación**: L40S ofrece 48GB VRAM a .34/hr spot — costo-eficiencia máxima para inferencia.

### 3. Para Almacenamiento
**Estrategia**: Oracle Block Volumes para block storage (68% más barato que AWS). Cloudflare R2 para object con egress .  
**Ahorro estimado**: 50-70% en storage costos + 100% en egress.  
**Riesgo**: Vendor lock-in evaluar costo de migración.

### 4. Para Compute General
**Estrategia**: OCI A1.Flex (ARM) o GCP E2 con committed use discounts.  
**Ahorro estimado**: 45-64% vs AWS/Azure Intel.  
**Justificación**: ARM (Graviton, Cobalt, Ampere) es 20-55% más barato que x86 con rendimiento comparable.

### 5. Estrategia Híbrida Óptima
| Componente | Proveedor | Modalidad | Ahorro vs On-Demand |
|-----------|-----------|----------|:------------------:|
| Base estable (>55% util.) | Bare Metal + Lambda/CoreWeave | 3yr reserved | 55-70% |
| Burst training | GCP A3 spot | Spot | 60-91% |
| Batch inference | AWS G6e (L40S) spot | Spot | 70-85% |
| Production inference | OCI + Reserved MI300X | 1yr reserved | 35-50% |
| Storage block | Oracle Block Volumes | On-demand | 68% vs AWS |
| Storage object | Cloudflare R2 | On-demand | 35% + 0 egress |
| Compute general | OCI A1.Flex / GCP E2 | CUD / Savings Plan | 40-64% |

---

## Riesgos y Mitigaciones

| Riesgo | Probabilidad | Impacto | Mitigación |
|--------|:-----------:|:-------:|-----------|
| **Escasez de HBM3e** limita producción B200 | Alta | Alto | Asegurar compromisos multi-mes, diversificar con MI300X |
| **Subida de precios neocloud** por demanda | Media | Medio | Contratos reservados con lock de precio |
| **Egresos inesperados** en hyperscalers | Alta | Alto | Usar Cloudflare R2, Oracle (10TB free), monitorear con FinOps |
| **Vendor lock-in** en ASICs custom (TPU, Trainium) | Media | Alto | Mantener portabilidad con K8s + modelos framework-agnostic |
| **Interrupción spot** durante training crítico | Alta | Medio | Checkpointing cada 15-30 min, nodos de respaldo |
| **Cambios regulatorios** (export controls) | Media | Medio | Diversificar proveedores geográficamente |
| **Consolidación de neoclouds** (~200 → 4-5) | Alta | Medio | Diversificar entre top 3-4 neoclouds |

---

## Próximos Pasos

1. **Validación de precios actuales** — Verificar en calculadoras oficiales antes de comprometer gasto (los precios cambian frecuentemente)
2. **Análisis TCO para workload específico** — Modelar escenario concreto (volumen GPU, storage, egress, horas/mes)
3. **Contactar neoclouds top** — Solicitar cotizaciones de Lambda Labs, CoreWeave, RunPod para cargas predecibles
4. **Setup de monitoreo de precios** — RSS quincenal de gpucost.org, gpufinder.dev, cloud-gpus.com
5. **Prueba piloto** — Desplegar workload de prueba en 2-3 proveedores para medir rendimiento real y costos ocultos
6. **Implementar FinOps** — Budget tracking, cost alerts, tagging strategy desde el día 1

---

## Fuentes Consultadas

### Páginas Oficiales
- AWS EBS Pricing: https://aws.amazon.com/ebs/pricing/
- AWS S3 Pricing: https://aws.amazon.com/s3/pricing/
- AWS EC2 Pricing: https://aws.amazon.com/ec2/pricing/
- Azure Managed Disks Pricing: https://azure.microsoft.com/en-us/pricing/details/managed-disks/
- Azure Blob Pricing: https://azure.microsoft.com/en-us/pricing/details/storage/blobs/
- GCP Persistent Disk Pricing: https://cloud.google.com/compute/disks-image-pricing
- GCP Storage Pricing: https://cloud.google.com/storage/pricing
- Oracle Block Volumes: https://www.oracle.com/cloud/storage/block-volumes/pricing/
- Oracle Object Storage: https://www.oracle.com/cloud/storage/object-storage/pricing/

### Agregadores de Precios
- Presenc AI: GPU Supply and Pricing 2026
- ComputeStacker: GPU Cloud Pricing Guide 2026
- Compute Exchange: Reserved GPUs March 2026
- GPU Tracker: Spot GPU Savings Analysis 2026
- CompuX: GPU Pricing Trends 2026
- Silicon Analysts: GPU Price/Performance Comparison 2026
- CloudGPUTracker: Cloud GPU Rental Pricing April 2026
- DeployBase: GPU Cloud Pricing Comparison 2026
- gpucost.org, gpufinder.dev, cloud-gpus.com

### Reportes de Analistas
- Synergy Research Group: Neocloud Market Forecast ( by 2031)
- Omdia: Global Cloud Infrastructure Spending Q4 2025
- Dell'Oro Group: Data Center Capex Surges 57% in 2025
- TrendForce: North American AI Data Center CapEx 2026
- CNCF Annual Survey 2026: Kubernetes for GenAI Inference
- Cast AI 2026: State of Kubernetes Optimization Report
- Fortune Business Insights: GPUaaS Market .23B→.84B by 2032
- Growth Market Reports: Serverless GPU Market .89B→.92B by 2033

### Medios y Blogs
- SemiAnalysis: GPU pricing trends
- Tom's Hardware: Custom AI ASIC state of play (May 2026)
- TechCrunch, The Register, Ars Technica
- Hacker News, r/cloud

---

## Conceptos Relacionados

- [[metis]] — Agente de Estrategia que elaboró este reporte
- [[cloud-computing]] — Panorama Estratégico del Cloud Computing 2025-2026
- [[neoclouds]] — Proveedores GPU-Especializados (CoreWeave, Lambda Labs, RunPod, Vast.ai)
- [[gpu-pricing]] — GPU Pricing: Panorama completo de precios por GPU y proveedor
- [[hyperscaler-comparison]] — Comparativa Estratégica AWS vs Azure vs GCP vs Oracle
- [[cloud-storage-strategy]] — Estrategia de Precios de Almacenamiento Cloud
- [[spot-compute-strategy]] — Spot Compute: Estrategia para AI/ML y ahorro máximo

---

*Reporte generado por [[metis|Metis]] (Μῆτις) — KAOS AI Agent System*  
*27 de mayo de 2026 | Fuentes trianguladas: 30+ | Perfil de confianza: Alto*
