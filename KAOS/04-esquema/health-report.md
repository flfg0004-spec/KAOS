---
type: adr
title: Vault Health Report
aliases:
- health-report
tags:
- adr
created: '2026-05-19'
modified: '2026-05-21'
confidence: media
status: draft
---

# Vault Health Report
*Generated: 2026-05-21 11:01*
## WARNING: Uncommitted Changes

```
M _pipeline/log.md
 M _pipeline/status.md
 M _scripts/lib/dsol.py
 M _scripts/lib/hydrate.py
 M _scripts/lib/pipeline.py
 M _scripts/vault.py
 D cache/embeddings.json
 M cache/hydrate-cache.json
 M cache/test-results.json
 M cache/token-usage.json
 M schema/adr-007-optimizacion-arquitectura.md
 M schema/health-report.md
 M schema/lint-report.md
 M wiki/concepts/add-only-extraction.md
 M wiki/concepts/alcance-temporal.md
 M wiki/concepts/arquitectura-integracion-herramientas.md
 M wiki/concepts/checkpoint.md
 M wiki/concepts/cobertura-completa.md
 M wiki/concepts/compile-then-query.md
 M wiki/concepts/confianza-general.md
 M "wiki/concepts/conversi\303\263n-completa.md"
 M "wiki/concepts/conversi\303\263n-parcial.md"
 M "wiki/concepts/evaluaci\303\263n.md"
 M wiki/concepts/fuentes-consultadas.md
 M wiki/concepts/github-mcp-oficial.md
 M wiki/concepts/hallazgos-clave.md
 M wiki/concepts/herramientas.md
 M wiki/concepts/idiomas.md
 M wiki/concepts/json-output.md
 M wiki/concepts/llm-wiki.md
 M wiki/concepts/lucidity-mcp.md
 M wiki/concepts/memory-blocks.md
 M "wiki/concepts/m\303\251todo.md"
 M "wiki/concepts/par\303\241metros.md"
 M wiki/concepts/per-agent-mcp-restriction.md
 M wiki/concepts/pipeline-conocimiento-raw-wiki.md
 M wiki/concepts/pipeline-maid.md
 M wiki/concepts/postgresql-mcp-oficial.md
 M wiki/concepts/precio.md
 M "wiki/concepts/qu\303\251-hace.md"
 M "wiki/concepts/recomendaci\303\263n-para-kaos.md"
 M wiki/concepts/sentry-mcp.md
 M "wiki/concepts/sin-p\303\241ginas-hu\303\251rfanas.md"
 M wiki/concepts/thinking.md
 M wiki/concepts/tool-calling.md
 M wiki/concepts/veredicto.md
 M wiki/entities/aletheia.md
 M wiki/entities/kosmos.md
 M wiki/entities/metis.md
 M wiki/entities/mnemosyne.md
 M wiki/index.md
 M wiki/log.md
?? _pipeline/context.json
?? _pipeline/profiles/
?? _scripts/lib/obsidian.py
?? _scripts/run_curation.py
?? raw/investigacion-c4-model-arquitectura.md
?? raw/investigacion-gestion-conocimiento.md
?? raw/investigacion-okr-estrategia.md
?? raw/investigacion-prompt-engineering.md
?? raw/investigacion-rag-arquitectura.md
?? raw/investigacion-sistemas-multiagente.md
?? raw/investigacion-software-testing.md
?? schema/mcp-security-audit.md
?? wiki/concepts/adr.md
?? wiki/concepts/agentes-inteligentes.md
?? wiki/concepts/arquitectura-software.md
?? wiki/concepts/brecha.md
?? wiki/concepts/c4-model.md
?? wiki/concepts/cadena-verificacion.md
?? wiki/concepts/chain-of-thought-cot.md
?? wiki/concepts/code-nivel-4.md
?? wiki/concepts/coherencia.md
?? wiki/concepts/completitud.md
?? wiki/concepts/component-nivel-3.md
?? wiki/concepts/conflicto-de-escritura.md
?? wiki/concepts/container-nivel-2.md
?? wiki/concepts/context-nivel-1.md
?? wiki/concepts/corporizado.md
?? wiki/concepts/dependencia-externa.md
?? wiki/concepts/duplicidad-de-funcionalidad.md
?? wiki/concepts/embebido.md
?? wiki/concepts/espiral-seci.md
?? wiki/concepts/evaluacion.md
?? "wiki/concepts/expl\303\255cito.md"
?? wiki/concepts/gestion-conocimiento.md
?? wiki/concepts/initiatives.md
?? wiki/concepts/key-results.md
?? wiki/concepts/kosmos--deepeval.md
?? wiki/concepts/kosmos--langfuse.md
?? wiki/concepts/lucidity.md
?? wiki/concepts/metricas-calidad.md
?? wiki/concepts/multi-shot-few-shot.md
?? "wiki/concepts/m\303\241quinas-de-estado.md"
?? wiki/concepts/objective.md
?? wiki/concepts/obsidian.md
?? wiki/concepts/okr-framework.md
?? wiki/concepts/orquestacion-agentes.md
?? "wiki/concepts/para-kosmos-testingevaluaci\303\263n.md"
?? wiki/concepts/para-metis-estrategia.md
?? wiki/concepts/planeacion-estrategica.md
?? wiki/concepts/prompt-engineering.md
?? wiki/concepts/rag-architecture.md
?? wiki/concepts/reproducibilidad.md
?? wiki/concepts/retrieval-augmented-generation.md
?? wiki/concepts/role-assignment.md
?? wiki/concepts/score-engine.md
?? wiki/concepts/self-consistency.md
?? wiki/concepts/sistemas-multiagente.md
?? wiki/concepts/software-testing.md
?? wiki/concepts/structurizr-mcp.md
?? wiki/concepts/structurizr.md
?? wiki/concepts/tree-of-thought-tot.md
?? wiki/concepts/txtai.md
?? "wiki/concepts/t\303\241cito.md"
?? wiki/concepts/utilidad.md
?? wiki/concepts/vault.md
?? wiki/concepts/vector-store.md
?? wiki/concepts/veracidad.md
?? wiki/glosario-kaos.md
```
## Frontmatter Validation
- WARNING: wiki\concepts\adr.md missing frontmatter
- WARNING: wiki\concepts\agentes-inteligentes.md missing frontmatter
- WARNING: wiki\concepts\arquitectura-software.md missing frontmatter
- WARNING: wiki\concepts\c4-model.md missing frontmatter
- WARNING: wiki\concepts\cadena-verificacion.md missing frontmatter
- WARNING: wiki\concepts\coherencia.md missing frontmatter
- WARNING: wiki\concepts\completitud.md missing frontmatter
- WARNING: wiki\concepts\evaluacion.md missing frontmatter
- WARNING: wiki\concepts\gestion-conocimiento.md missing frontmatter
- WARNING: wiki\concepts\lucidity.md missing frontmatter
- WARNING: wiki\concepts\metricas-calidad.md missing frontmatter
- WARNING: wiki\concepts\okr-framework.md missing frontmatter
- WARNING: wiki\concepts\orquestacion-agentes.md missing frontmatter
- WARNING: wiki\concepts\planeacion-estrategica.md missing frontmatter
- WARNING: wiki\concepts\prompt-engineering.md missing frontmatter
- WARNING: wiki\concepts\rag-architecture.md missing frontmatter
- WARNING: wiki\concepts\reproducibilidad.md missing frontmatter
- WARNING: wiki\concepts\retrieval-augmented-generation.md missing frontmatter
- WARNING: wiki\concepts\score-engine.md missing frontmatter
- WARNING: wiki\concepts\sistemas-multiagente.md missing frontmatter
- WARNING: wiki\concepts\software-testing.md missing frontmatter
- WARNING: wiki\concepts\structurizr-mcp.md missing frontmatter
- WARNING: wiki\concepts\structurizr.md missing frontmatter
- WARNING: wiki\concepts\txtai.md missing frontmatter
- WARNING: wiki\concepts\utilidad.md missing frontmatter
- WARNING: wiki\concepts\vector-store.md missing frontmatter
- WARNING: wiki\concepts\veracidad.md missing frontmatter

## Directory Structure
- OK: wiki/entities (4 .md files, 4 total entries)
- OK: wiki/concepts (89 .md files, 89 total entries)
- OK: wiki/sources (29 .md files, 29 total entries)
- OK: raw (21 .md files, 22 total entries)
- OK: schema (16 .md files, 18 total entries)
- OK: _scripts (0 .md files, 18 total entries)
- OK: _pending (1 .md files, 1 total entries)
- OK: _pipeline (3 .md files, 5 total entries)
---
**Vault health: WARNING Issues found**

