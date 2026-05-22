---
type: adr
title: 'ADR-011: Memory Matrix — Modelo Jerarquico de Memoria L0-L3'
aliases:
- adr-011-memory-matrix
tags:
- adr
created: '2026-05-21'
modified: '2026-05-21'
confidence: media
status: draft
---

# ADR-011: Memory Matrix — Modelo Jerarquico de Memoria L0-L3

## Estado
Aceptado

## Contexto
ADR-001 define 3 niveles de memoria: Core (volatil) → Working (volatil) → Archival (persistente). La investigacion de Aletheia (78+ fuentes) y la estrategia de Metis proponen 4 niveles (L0-L3) con consolidacion jerarquica inspirada en systems de SOTA (SleepGate, Agenternal, HiMem). Es necesario unificar ambos modelos.

## Decision
Adoptar el modelo L0-L3 con mapeo directo a ADR-001 y deprecar ADR-006.

### Mapeo ADR-001 → L0-L3

| Nivel KAOS | Nombre | ADR-001 Equiv. | Stack | Persistencia | TTL |
|-----------|--------|----------------|-------|-------------|-----|
| **L0** | Raw | Core | sqlite-vec (161 pages, 3610 chunks) | Disco | Indefinido |
| **L1** | Episodic | Working | CodeExperience DB + hydrate cache | Disco + Cache | Dias |
| **L2** | Semantic | Archival | Knowledge Graph MCP + conceptos wiki | Disco (KG) | Meses |
| **L3** | Schema | Archival | Patrones consolidados (sleep output) | Disco + Schema | Permanente |

### Transiciones entre Niveles
```
L0 → L1: DBSCAN clustering sobre vectores similares (cosine > 0.85)
           → LLM destila cluster en episodio estructurado
           → Almacena en CodeExperience con pattern_category

L1 → L2: Re-clustering de episodios semanticamente cercanos
           → Extraccion de entidades y relaciones
           → Insercion en Knowledge Graph MCP
           → Actualizacion de conceptos wiki

L2 → L3: Re-clustering semantico cross-dominio
           → LLM sintetiza esquemas abstractos
           → Almacena como esquemas consolidados
           → Actualiza ADRs si aplica
```

### Ciclo de Sueño (reemplaza ADR-006)
```
NREM (70% del ciclo):
  1. Seleccionar entradas no consolidadas en L1
  2. DBSCAN(eps=0.35, min_samples=3) sobre vectores
  3. Por cluster: LLM destila patron → L2 insert
  4. Decaimiento central: experiencias con baja centralidad se degradan

REM (30% del ciclo):
  1. Re-clustering (eps=0.45) sobre entidades L2
  2. LLM sintetiza esquemas → L3
  3. Descubrimiento de edges causales cross-dominio

Compaction:
  1. Nodos L1 sin acceso > 30 dias → resumir a 10% del tamano
  2. Nodos con confidence < 0.2 y > 90 dias → archivo profundo

Forgetting:
  strength(t) = 1 / (1 + 0.15 * t) donde t = dias sin acceso
  Si strength < 0.1 → mover a archivo frio (preserva para auditoria)
```

## Consecuencias
### Positivas
+ Modelo de memoria escalable y jerarquico (4 niveles vs 7000+ chunks planos)
+ Consolidacion automatica sin intervencion humana
+ Deprecacion formal de ADR-006 (Sleep-Time Compute)
+ Mapeo claro con ADR-001 existente

### Negativas
- DBSCAN es O(n²) en el peor caso → espacial para vaults > 10000 entradas
- LLM distillation cuesta tokens (~10K por cluster)
- Sleep cycle requiere el vault idle (no bloquear pipelines activos)

### ADRs Afectados
- ADR-001: Mapeado a L0-L3 (no se modifica, se extiende)
- ADR-005: Vector Store (sqlite-vec) = infraestructura de L0
- ADR-006: **DEPRECADO** — reemplazado por este ADR

## Referencias
- SleepGate: arXiv 2603.14517 (NREM/REM sobre KV-cache)
- Agenternal: Produccion 2026 (DBSCAN + LLM distill, compresion 2M:1)
- HiMem: arXiv 2601.06377 (reconsolidacion conflict-aware)
- ADR-001: Sistema de Memoria (3 niveles originales)
- ADR-005: Vector Store (sqlite-vec)
- ADR-006: Sleep-Time Compute (DEPRECADO)

