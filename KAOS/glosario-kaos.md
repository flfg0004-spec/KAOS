---
type: concept
title: Glosario Global — KAOS
aliases:
- glosario-kaos
tags:
- concept
- glosario
created: '2026-05-20'
modified: '2026-05-21'
confidence: alta
status: draft
---

# Glosario Global — KAOS Knowledge Agent Operating System
*Actualizado: 2026-05-21*

## Agentes

### Aletheia (Ἀλήθεια) — Investigación
- **Propósito**: Búsqueda web, papers académicos, investigación profunda, fact-checking
- **Modo**: subagent | **Steps**: 15 | **Temperatura**: 0.3
- **MCPs**: scholar-search, rss-reader, context7, gptr-deep-research, searxng, crawl4ai, exa-search, depwire, mcp-obsidian-cli, obsidian, sequential-thinking, knowledge-graph
- **Permisos**: websearch/webfetch allow, edit deny
- **Outputs**: `raw/<slug>.md`
- **Perfiles**: flash (5min), standard (30min), deep (2-4h), massive (4h+)
- **Tags**: #aletheia #investigacion

### Kosmos (Κόσμος) — Arquitectura
- **Propósito**: Análisis de código, diagramas C4, ADRs, documentación técnica
- **Modo**: subagent | **Steps**: 10 | **Temperatura**: 0.1
- **MCPs**: depwire, structurizr, excalidraw, git, lucidity, mcp-obsidian-cli, obsidian, sequential-thinking, vault, knowledge-graph
- **Permisos**: read/glob/grep allow, edit ask
- **Outputs**: `schema/<slug>-adr.md`
- **Tags**: #kosmos #arquitectura

### Metis (Μῆτις) — Estrategia
- **Propósito**: Planeación, OKRs, roadmaps, reportes ejecutivos, calidad
- **Modo**: subagent | **Steps**: 8 | **Temperatura**: 0.4
- **MCPs**: excalidraw, paperjsx, exa-search, mcp-obsidian-cli, obsidian, sequential-thinking, vault, knowledge-graph
- **Permisos**: websearch/webfetch allow, edit ask
- **Outputs**: `wiki/<slug>-strategy.md`
- **Tags**: #metis #estrategia

### Mnemosyne (Μνημοσύνη) — Curación
- **Propósito**: Curación de conocimiento, wikilinks, calidad del vault, compresión
- **Modo**: subagent | **Steps**: 8 | **Temperatura**: 0.1
- **MCPs**: sequential-thinking, mcp-obsidian-cli, obsidian, vault, txtai, knowledge-graph
- **Permisos**: read/glob/grep/edit allow, bash limited
- **Ciclo**: 8 fases (Ingest→Link→Dedup→Quality→Compress→Index→Lint→Cross-Ref)
- **Auto-curation**: `run_curation.py` se gatilla al completar pipeline
- **Tags**: #mnemosyne #curacion

### Kratos (Κράτος) — Código
- **Propósito**: Generación, depuración, revisión y testeo de código con memoria experiencial APEX-EM
- **Modo**: subagent | **Steps**: 12 | **Temperatura**: 0.2
- **MCPs**: vault, sequential-thinking, git, exa-search, mcp-obsidian-cli, obsidian
- **Framework**: PRGII (Plan→Retrieve→Generate→Iterate→Ingest)
- **Memoria**: CodeExperience (FTS5 + vector search + AST signature, contextual bandit feedback)
- **Tags**: #kratos #codigo #code-agent

---

## MCPs — 19 activos, 1 disabled

### mcp-obsidian-cli
- **Tipo**: local | **Comando**: `npx -y mcp-obsidian-cli`
- **Tools**: search, backlinks, tags, files, read, properties, recents
- **Proxy**: No | **Estado**: ✅ Enabled

### obsidian (@swarogan/obsidian-mcp-rest)
- **Tipo**: local | **Comando**: `npx -y @swarogan/obsidian-mcp-rest`
- **Tools**: 18 tools — CRUD (vault + active), search (simple, DQL, semantic), patch, template, fetch
- **Proxy**: No | **Estado**: ✅ Enabled
- **Requiere**: `obsidian-local-rest-api` plugin (puerto 27124) + API key en env

### sequential-thinking
- **Tipo**: local | **Comando**: `py -3 .memory/_scripts/mcp_proxy.py -- npx -y @modelcontextprotocol/server-sequential-thinking`
- **Tools**: sequential_thinking | **Proxy**: Sí | **Estado**: ✅ Enabled

### excalidraw
- **Tipo**: local | **Comando**: `py -3 .memory/_scripts/mcp_proxy.py -- npx -y excalidraw-mcp`
- **Tools**: create_diagram, export_diagram | **Proxy**: Sí | **Estado**: ✅ Enabled

### vault (server-filesystem)
- **Tipo**: local | **Comando**: `py -3 .memory/_scripts/mcp_proxy.py -- npx -y @modelcontextprotocol/server-filesystem .memory/...`
- **Tools**: read_file, write_file, edit_file, search, directory_tree | **Proxy**: Sí | **Estado**: ✅ Enabled

### rss-reader
- **Tipo**: local | **Comando**: `py -3 .memory/_scripts/mcp_proxy.py -- npx -y rss-reader-mcp`
- **Tools**: rss tools | **Proxy**: Sí | **Estado**: ✅ Enabled

### depwire
- **Tipo**: local | **Comando**: `npx -y @iflow-mcp/depwire-depwire`
- **Tools**: get_health_score, simulate_change, get_temporal_graph | **Proxy**: No | **Estado**: ✅ Enabled

### exa-search
- **Tipo**: local | **Comando**: `npx -y exa-mcp-server`
- **Tools**: exa_search | **Proxy**: No | **Estado**: ✅ Enabled
- **Nota**: EXA_API_KEY en env var + config (belt and suspenders)

### gptr-deep-research
- **Tipo**: local | **Comando**: `npx -y gpt-researcher-mcp`
- **Tools**: deep_research | **Proxy**: No | **Estado**: ✅ Enabled

### paperjsx
- **Tipo**: local | **Comando**: `npx -y @paperjsx/mcp-server`
- **Tools**: create_presentation | **Proxy**: No | **Estado**: ✅ Enabled

### scholar-search
- **Tipo**: local | **Comando**: `npx -y scholar-search-mcp`
- **Tools**: scholar_search | **Proxy**: No | **Estado**: ✅ Enabled

### git
- **Tipo**: local | **Comando**: `npx -y @modelcontextprotocol/server-git --repository .`
- **Tools**: git log, diff, blame | **Proxy**: No | **Estado**: ✅ Enabled

### context7
- **Tipo**: remote | **URL**: `https://mcp.context7.com/mcp`
- **Tools**: documentación técnica | **Proxy**: N/A (remote) | **Estado**: ✅ Enabled

### searxng
- **Tipo**: local | **Comando**: `npx -y searxng-mcp --url http://127.0.0.1:8888`
- **Tools**: metasearch | **Proxy**: No | **Estado**: ✅ Enabled (requiere Docker: kaos-searxng)

### crawl4ai
- **Tipo**: local | **Comando**: `npx -y crawl4ai-mcp-sse-stdio --url http://127.0.0.1:11235`
- **Tools**: web crawl | **Proxy**: No | **Estado**: ✅ Enabled (Docker unhealthy pero funcional)

### txtai
- **Tipo**: local | **Comando**: `py -3 .memory/_scripts/mcp_txtai.py`
- **Tools**: semantic_search, deduplicate | **Proxy**: No | **Estado**: ✅ Enabled (Python local, sin Docker)

### structurizr
- **Tipo**: local | **Comando**: `py -3 .memory/_scripts/mcp_structurizr.py`
- **Tools**: validate_dsl, export_diagram, list_views | **Proxy**: No | **Estado**: ✅ Enabled

### lucidity
- **Tipo**: local | **Comando**: `py -3 .tools/run_lucidity.py`
- **Tools**: analyze_changes | **Proxy**: No | **Estado**: ✅ Enabled
- **Nota**: Instalado desde GitHub (hyperb1iss/lucidity-mcp). Originalmente configurado como npm (falló). Corregido a Python vía pip.

### knowledge-graph
- **Tipo**: local | **Comando**: `npx -y mcp-knowledge-graph --memory-path ...`
- **Tools**: knowledge graph | **Proxy**: No | **Estado**: ✅ Enabled

### supermemory
- **Tipo**: remote | **URL**: `https://mcp.supermemory.ai/mcp`
- **Estado**: ❌ Disabled — requiere API key no configurada. Mantenido para futuro.

### postgres
- **Tipo**: local | **Comando**: `npx -y @modelcontextprotocol/server-postgres`
- **Estado**: ❌ Disabled — no hay instancia PostgreSQL local.

---

## Scripts

### .tools/session_runner.py
- **Propósito**: Session runner unificado
- **Modos**: smoke (2min), functional (15min, guarda sesión), audit (60min, genera reporte)
- **Dependencias**: verification_chain.py, score_engine.py, weekly_report.py

### .tools/schedule.py
- **Propósito**: Ejecuta tareas programadas del dashboard
- **Tareas**: Distill (daily), Functional (daily), VaultHealth (Sun), Verification (Mon), Audit (Mon)

### .tools/install_schedule.py
- **Propósito**: Crea tareas en Windows Task Scheduler (ejecutar como Admin)
- **Tareas**: KAOS-Daily-Quality (8AM), KAOS-Weekly-Audit (Mon 6AM), KAOS-Vault-Health (Sun 10PM)

### .tools/verification_chain.py
- **Propósito**: Cadena triangular de verificación (Kosmos→Aletheia, Metis→Kosmos, Aletheia→Metis)

### .tools/score_engine.py
- **Propósito**: Motor de 5 dimensiones (V, C, CP, R, U)

### .tools/weekly_report.py
- **Propósito**: Reporte semanal de calidad (Markdown + PaperJSX opcional)

### .tools/run_lucidity.py
- **Propósito**: Wrapper para ejecutar lucidity-mcp desde el repo clonado

### .memory/_scripts/mcp_proxy.py
- **Propósito**: Proxy MCP que intercepta prompts/list para servers que no lo implementan

### .memory/_scripts/mcp_txtai.py
- **Propósito**: MCP server de búsqueda semántica con sentence-transformers

### .memory/_scripts/mcp_structurizr.py
- **Propósito**: MCP server para structurizr CLI (C4 diagrams)

### .memory/_scripts/run_curation.py
- **Propósito**: Ciclo completo de 8 fases de Mnemosyne en un comando

### .memory/_scripts/clean_opencode_db.py
- **Propósito**: Analizar, VACUUM y limpiar opencode.db
- **Flags**: --analyze, --vacuum, --clean-days N, --clean-last N, --dry-run

### .memory/_scripts/vault.py
- **Propósito**: CLI unificado del vault — 20+ subcomandos
- **Subcomandos clave**: hydrate, extract, lint, health, index, wikilinks, log, pipeline, dsol

---

## Pipeline Cross-Agent

| Step | Agent | Output | Routing | Duración |
|------|-------|--------|---------|----------|
| 1 | Aletheia | `raw/<slug>.md` | Siempre | 5min-4h según perfil |
| 2 | Kosmos | `schema/<slug>-adr.md` | Siempre | 10-30min |
| 3 | Metis | `wiki/<slug>-strategy.md` | Siempre | 8-15min |
| 4 | **Kratos** | `code/<slug>.md` | Solo si el tópico es código | 10-30min |
| 5 | Mnemosyne | Curación automática | Siempre | 2-5min |

- **Init**: `vault.py pipeline init --topic X --profile Y`
- **Routing**: Metis → Kratos si el tópico contiene keywords de código, → Mnemosyne si no
- **Orquestador**: LangGraph DAG con checkpointing SQLite, LangSmith tracing
- **Context sharing**: `_pipeline/context.json` — cada agente deja resumen para el siguiente
- **Auto-curation**: Al completarse el pipeline (step_done sin next_agent), se gatilla `run_curation.py`

---

## Quality System

- **Score actual**: 76.8/100 (perfil: desarrollo)
- **Thresholds**: V≥65, C≥60, CP≥55, R≥50, U≥55, Compuesto≥70
- **Dimensiones**: Veracidad (V), Coherencia (C), Completitud (CP), Reproducibilidad (R), Utilidad (U)
- **Perfiles**: desarrollo (default), produccion, exploracion, auditoria
- **Anti-hallucination**: L1 (DeepEval), L2 (cross-agent), L3 (blind peer)
- **Dashboard**: `.vault/quality/dashboard.md`
- **Reportes**: `.vault/reports/week-*.md`

---

## Vault Structure

```
.memory/
  raw/              → 21 investigaciones inmutables (Aletheia)
  wiki/
    concepts/       → 53 conceptos con wikilinks
    entities/       → 4 entidades de agentes
    sources/        → 29 fuentes documentadas
    index.md        → ~130 entries auto-generados
    log.md          → Actividad cronológica
  schema/           → 8 ADRs, policies, configs
  _scripts/         → Scripts de mantenimiento
  _pipeline/        → Coordinación cross-agent
  cache/            → DSOL, knowledge-graph, hydrate

.vault/
  quality/          → Dashboard, sesiones, verifications
  reports/          → Reportes semanales

---

## Obsidian Integration — Vault Enriquecido

### Arquitectura

```
.memory/wiki/ (source of truth) ──vault-sync.py──▶ KAOS/KAOS/ (vault Obsidian)
  Agents escriben aquí              (one-way,       Vista enriquecida READ-ONLY
                                    sanitize,       132 files, frontmatter unificado,
                                    enrich)         233 wikilinks, MOC con dataview
```

### Plugins instalados (11 total)

| Plugin | ID | Propósito |
|--------|----|-----------|
| **Dataview** | `dataview` | Queries SQL-like sobre frontmatter, MOC dinámico, dashboards |
| **Templater** | `templater-obsidian` | Templates avanzados con metadatos dinámicos |
| **Obsidian Git** | `obsidian-git` | Auto-commit del vault enriquecido cada 60 min |
| **Excalidraw** | `obsidian-excalidraw-plugin` | Diagramas visuales en notas (complementa MCP) |
| **Tasks** | `obsidian-tasks-plugin` | OKRs y action items de Metis |
| **Calendar** | `calendar` | Navegación de daily notes |
| **Folder Notes** | `folder-notes` | Index automático por carpeta |
| **obsidian-local-rest-api** | — | REST API + MCP (puerto 27124) |
| **Smart Connections** | — | Búsqueda semántica local (bge-micro-v2) |
| **Smart Context** | — | Contexto XML para AI |
| **Smart ChatGPT** | — | ChatGPT en notas (deshabilitado hasta configurar API key) |

### Plugins deshabilitados por port conflict

| Plugin | Motivo |
|--------|--------|
| `mcp-rest` (vigeron) | Dependía de `obsidian-api`, port conflict con `obsidian-local-rest-api` |
| `rest-api`/`obsidian-api` (vigeron) | Puerto 27124 compartido, ganó `obsidian-local-rest-api` |

### CSS Snippet

`kaos.css` en `.obsidian/snippets/` — colores de agents (aletheia=#4A90D9, kosmos=#7B68EE, metis=#E8A87C, mnemosyne=#C0C0C0), badges, dataview tables.

### Pipeline de Hidratación

`_obsidian_search()` en `hydrate.py` reactivado — usa `ObsidianClient` (REST API directa, no MCP). Busca en el vault y devuelve snippets como contexto a los agents.

### Script de Sync

`.tools/vault-sync.py` — migración one-way de `.memory/wiki/` al vault:
- Sanitiza filenames (acentos → ASCII, backtick)
- Unifica frontmatter (type, title, aliases, tags, created, modified)
- Genera MOC con queries Dataview
- Uso: `py -3 .tools/vault-sync.py [--dry-run --force --quick]`

---

## Deprecated / Eliminado

| Componente | Motivo | Fecha |
|-----------|--------|-------|
| GitHub MCP | No necesario para KAOS. GITHUB_TOKEN expuesto. Eliminado. | 2026-05-20 |
| lucidity-mcp (npm) | No existe como paquete npm. Reemplazado por instalación desde GitHub. | 2026-05-19→20 |
| brave-search | No existe como MCP. OpenCode tiene `websearch` built-in. | 2026-05-20 |
| firecrawl (MCP) | ❌ Deprecado. Reemplazado por Crawl4AI + SearXNG. Ver ADR-009. | 2026-05-24 |
| DSOL build_prompt() | Llamaba a api.deepseek.com directamente. Reemplazado por build_optimized_context() para hydratación en OpenCode. | 2026-05-20 |
| .tools/session_runner.py (sin args) | Los comandos anteriores sin perfil explícito. Ahora requiere `smoke|functional|audit [perfil]`. | 2026-05-20 |
