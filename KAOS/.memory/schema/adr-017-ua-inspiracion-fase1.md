---
type: adr
title: ADR-017 — Adopción de patrones de análisis incremental y paralelo inspirados en Understand Anything
aliases:
  - adr-017-ua-inspiracion
tags:
  - adr
  - ua-inspiracion
  - incremental
  - paralelismo
created: '2026-05-27'
confidence: alta
status: accepted
---

# ADR-017: Adopción de Patrones UA en KAOS

## Status
Accepted — Implementado en Fase 1 de iniciativa UA-Inspiración (mayo 2026)

## Context
KAOS ejecuta pipelines completos de curación (Mnemosyne) re-analizando archivos no modificados. El pipeline ejecuta 10 fases secuenciales cada vez, sin importar si hubo cambios reales en el vault. El proyecto Understand Anything (37.8k ⭐) demuestra que el análisis incremental vía hash fingerprinting + git diff reduce drásticamente el tiempo de pipelines.

Además, Phase B de Mnemosyne solo paraleliza 2 tareas (wikilinks + crystallize), mientras que hay 4-5 tareas potencialmente paralelizables.

## Decision
Adoptar 4 patrones arquitectónicos del proyecto Understand Anything sin integrarlo como dependencia directa:

1. **Hash fingerprinting (SHA-256) + git diff HEAD** para detección incremental de cambios en el vault, evitando re-procesar archivos no modificados.
2. **ThreadPoolExecutor configurable** para Phase B de Mnemosyne (`PHASE_B_WORKERS=5`), moviendo lint y tagger de Phase A a Phase B como workers paralelos, y añadiendo GapDetector como worker opcional.
3. **Topological sort de VaultGraph** para Knowledge Tours — guías de aprendizaje ordenadas por dependencia para Kosmos.
4. **Clustering semántico sobre arch_graph** para Domain Mapping — agrupación de componentes en bounded contexts vía embeddings + K-Means para Metis.

### Detalles Técnicos

- **Módulo `lib/incremental.py`**: SHA-256 hashing de archivos `.md`, cache en `.memory/cache/file-hashes.json`, integración con `git diff --name-only HEAD` como fuente secundaria.
- **Pipeline incremental**: Mnemosyne skipea fases C-J (quality, compress, index, graph, crossref, lifecycle, dashboard) si no hay cambios detectados. Fases A y B solo se ejecutan sobre archivos modificados.
- **Feature flags**: `use_incremental_analysis`, `use_enhanced_parallelism`, `use_knowledge_tour`, `use_domain_mapper` — todos default `False`.
- **Knowledge Tour**: Función `topological_layers()` implementa Kahn's algorithm sobre NetworkX DiGraph. Output en markdown con secciones Start Here → Core Concepts → Advanced Topics + diagrama Mermaid.
- **Domain Mapper**: Extrae features de nodos de `arch_graph`, genera embeddings via txtai MCP, clusteriza con K-Means (sklearn), fallback rule-based por `node_type`.

## Consequences

### Positivas
- Pipelines 40-60% más rápidos (estimado: 120-180s → 48-72s)
- Onboarding reducido de 2-4h a <30 min via Knowledge Tours
- Stakeholders no técnicos pueden entender la arquitectura via Domain Maps
- Costo operativo NO aumenta (hash = CPU local, clustering = txtai local)
- Phase B escala de 2 a 5 workers sin incrementar costo LLM

### Negativas
- 3 nuevos módulos a mantener (`incremental.py`, `knowledge_tour.py`, `domain_mapper.py`)
- Carga cognitiva adicional en el nodo Mnemosyne (lógica condicional incremental)
- Dependencia de `scikit-learn` para K-Means (Domain Mapper) — fallback rule-based disponible

### Riesgos
- git diff puede fallar en CI con shallow clone → fallback a solo hash cache
- Race conditions en Phase B con 5 workers → file locking obligatorio
- Falsos negativos en detección incremental → doble validación hash + git

## Referencias
- [[adr-015-mnemosyne-architecture]]
- [[adr-014-arch-graph]]
- repo:Lum1104/Understand-Anything (37.8k ⭐, Tree-sitter + LLM híbrido)
- `lib/incremental.py` — Hash fingerprinting + git diff
- `lib/knowledge_tour.py` — Topological sort + markdown generator
- `lib/domain_mapper.py` — Feature extraction + clustering + reports
