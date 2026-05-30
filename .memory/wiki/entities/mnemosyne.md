---
type: agent
role: knowledge-curator
description: Guardiana de la memoria — curación de conocimiento, wikilinks, calidad del vault, knowledge scoring, síntesis automática
mode: subagent
mcp-servers: [sequential-thinking, vault, txtai, knowledge-graph, mcp-embed]
permission: read/glob/grep allow, edit auto (wiki/concepts, wiki/sources, raw), delete allow (concepts, raw, quality), bash allow
skill: mnemosyne SKILL.md
skills: [mnemosyne, mnemosyne-curator]
aliases: [Mnemosyne, Μνημοσύνη, Mnemosyne-Curator]
created: 2026-05-25
modified: 2026-05-28
updated: 2026-05-28
status: active
---

# Mnemosyne (Μνημοσύνη)

Titánide de la memoria, madre de las Musas. Guardiana del conocimiento de KAOS.

## Rol
Mnemosyne opera en background tras cada extracción de cualquier agente. Su trabajo es invisible pero esencial: convertir información en conocimiento estructurado.

## Metodología
Ciclo de 14 fases: Ingest → Tag → Link → Dedup → Quality → **D2: Knowledge Scoring** → Compress → Index → Graph → Gaps → Cross-Ref → **K: Knowledge Synthesis** → Lifecycle → Dashboard → Report

### Knowledge Scoring (Fase D2) — 28 May 2026

**Módulo**: `lib/knowledge_scorer.py` · **Flag**: `use_knowledge_scorer`

Evalúa cada documento contra 8 métricas con pesos fijos. Asigna un score 0-100 y un Knowledge Level (RAW→CANONICAL).

| Métrica | Peso | Descripción |
|---------|:----:|-------------|
| Completitud | 15% | Frontmatter + estructura markdown |
| Confianza | 20% | Matriz de confianza o Ebbinghaus decay |
| Conectividad | 15% | Wikilinks + PageRank |
| Frescura | 10% | Fecha de modificación |
| Precisión factual | 15% | Citas URL + cross-refs |
| Legibilidad | 10% | Ratio párrafos/headings, longitud oraciones |
| Utilidad | 10% | Similaridad semántica vía txtai |
| Coherencia | 5% | Sin TODO/WIP, sin broken links |

**Knowledge Levels**: RAW(0-20) → ROUGH(21-40) → DRAFT(41-60) → REVIEW(61-75) → CURATED(76-90) → CANONICAL(91-100)

### Knowledge Synthesis (Fase K) — 28 May 2026

**Módulo**: `lib/knowledge_synthesis.py` · **Flag**: `use_knowledge_synthesis`

Síntesis automática para documentos con score < 60. Operaciones:
- **Frontmatter**: Genera title, tags, created, confidence si faltan
- **Wikilinks**: Busca conceptos similares vía txtai, agrega "Véase también"
- **Estructura**: Reorganiza en Introducción/Desarrollo/Conclusión si >500 palabras
- **Fuentes**: Extrae URLs y crea sección de Referencias

**Guardrails**: max 3 intentos/doc, max 5 docs/corrida, diff ratio ≤50%, backup .bak, CANONICAL excluido, dry-run por defecto.

### Skill mnemosyne-curator
Nuevo skill con permisos elevados de escritura y eliminación:
- `.opencode/skills/mnemosyne-curator/SKILL.md`
- Permisos: `edit: auto`, `delete: allow` en `wiki/concepts/`, `raw/`, `quality/`
- Registrado en `opencode.json` como agente `mnemosyne-curator`

### Mejoras Fase 1 UA-Inspiración

#### Análisis Incremental ([[analisis-incremental]])
El pipeline ahora soporta modo **incremental** vía hash fingerprinting SHA-256 + git diff HEAD:
- **Detección dual**: Hash cache (`.memory/cache/file-hashes.json`) + `git diff --name-only HEAD`
- **Pipeline condicional**: Si `len(changed_files) == 0`, skipea fases C-J (gap, quality, compress, index, graph, crossref, lifecycle, dashboard)
- **Phase B selectiva**: Solo procesa archivos modificados + sus vecinos en VaultGraph
- **Feature flag**: `use_incremental_analysis`
- **Impacto**: 40-60% más rápido (120-180s → ≤72s diario, ≤48s post-commit)

#### Paralelismo Extendido Phase B
Phase B migra de 2 a **5 workers** concurrentes:
1. Wikilinks
2. Crystallize
3. Lint (migrado de Phase A)
4. Tagger (migrado de Phase A)
5. GapDetector (opcional, cuando `use_enhanced_parallelism` está activo)

**Configuración**: `PHASE_B_WORKERS = 5` configurable vía `KAOS_PHASE_B_WORKERS` env var

### Nuevos Módulos a Mantener
| Módulo | Propósito | Epic |
|--------|-----------|------|
| `lib/incremental.py` | Hash fingerprinting, git diff, detección de cambios | UA-EPIC-01 |
| `lib/config.py` (modificado) | `PHASE_B_WORKERS` constante + env var | UA-EPIC-02 |
| `lib/feature_flags.py` (modificado) | 4 nuevos flags: `use_incremental_analysis`, `use_enhanced_parallelism`, `use_knowledge_tour`, `use_domain_mapper` | Todos |

## Outputs típicos
- Conceptos curados en `.memory/wiki/concepts/`
- Wikilinks sugeridos y aplicados
- Log comprimido (entradas >30 días resumidas, >90 días archivadas)
- Index.md regenerado con referencias correctas
- Lint report con 0 issues
- **Nuevo**: Reporte incremental con `incremental: true`, `files_skipped: N`, `files_processed: M`
- **Nuevo**: Knowledge Scoring Report con scores por documento, distribución de tiers, docs que necesitan síntesis
- **Nuevo**: Synthesis Report con operaciones realizadas, diff ratios, scores pre/post

## Patrones
Implementa el patrón [[compile-then-query]] en su fase de destilación raw→wiki, y [[add-only-extraction]] en su fase de archive.

## Referencias
- [[analisis-incremental]] — Detección de cambios y pipeline condicional
- [[ua-inspiracion]] — Inspiración arquitectónica
- [[adr-017-ua-inspiracion-fase1]] — ADR de adopción de patrones
- adr-015-mnemosyne-architecture — ADR de arquitectura (incluye D2 y K)
- [[glosario-kaos]] — Glosario completo
- Plan Táctico Fase 1: `.memory/plans/ua-inspiracion-fase1-plan-tactico.md`
- Skill mnemosyne-curator: `.opencode/skills/mnemosyne-curator/SKILL.md`
- Knowledge Scorer: `lib/knowledge_scorer.py`
- Knowledge Synthesis: `lib/knowledge_synthesis.py`
- Knowledge Levels: `lib/knowledge_levels.py`
