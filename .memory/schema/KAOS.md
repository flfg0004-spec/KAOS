# KAOS Schema — Memory Vault Rules

## Structure
- `raw/`: Immutable sources, Aletheia-owned. Research outputs, papers, articles.
- `wiki/`: LLM-maintained pages.
  - `entities/`: Agent and system entity pages with YAML frontmatter.
  - `concepts/`: Concept pages with [[wikilinks]].
  - `sources/`: Source summaries and metadata.
  - `index.md`: Catalog with one-line summaries per page.
  - `log.md`: Append-only chronological record of all operations.
- `schema/`: Configuration files, ADRs, perfiles de evaluación.
- `.tools/`: Scripts de automatización (score_engine, session_runner, distill, etc.).
- `.vault/quality/`: Datos de calidad (sessions, timeseries, verifications, dashboard).
- `.github/workflows/`: CI/CD pipelines.

## Conventions
- Every claim must cite its source using [[wikilink]] to sources/.
- Naming: kebab-case.md
- On ingest, update 10-15 related pages.
- Flag contradictions explicitly with "⚠️ Contradiction:".
- index.md is the primary navigation — search here first before querying.
- Las investigaciones se destilan automáticamente raw→wiki via `distill.py`.

## Workflow
1. **Ingest**: New source → raw/ → distill.py → auto-extract concepts & sources → update wiki/ → update index.md → append log.md
2. **Cross-link**: distill.py detecta conceptos compartidos entre investigaciones y crea [[wikilinks]] automáticos.
3. **Query**: Read index.md → drill into relevant pages → synthesize response
4. **Lint**: Scan for broken links, orphan pages, stale claims, contradictions
5. **Quality**: Cada escritura al vault gatilla post_output_hook (smoke + distill)

## Memory System
- **Core Memory**: Always in context (volátil, por sesión).
- **Working Memory**: Recent history + scratchpad FIFO.
- **Archival Memory**: vault markdown + git backend + time-to-knowledge tracking (promedio actual: 1.8h).
- **Vector Store**: Futuro — sqlite-vec cuando vault >100 páginas (ADR-005).

## Quality System
- **Score Compuesto**: 5 dimensiones (veracidad, coherencia, completitud, reproducibilidad, utilidad)
- **Perfiles**: exploración 🟢, desarrollo 🟡 (default), producción 🔴, auditoría 🟣
- **Sesiones**: smoke (2min), functional (15min/diario), audit (60min/semanal)
- **Verificación**: Cadena triangular Aletheia→Kosmos→Metis→Aletheia
- **Dashboard**: `.vault/quality/dashboard.md` con scores, tendencias, alertas

## MCP Configuration (Per-Agent)
Los MCP servers están restringidos por agente para optimizar tokens:
- **Aletheia**: firecrawl, brave-search, scholar-search, rss-reader, context7, sequential-thinking, vault
- **Kosmos**: depwire, structurizr, excalidraw, git, database, postgres, github, lucidity, sequential-thinking, vault
- **Metis**: firecrawl, brave-search, paperjsx, excalidraw, sequential-thinking, vault
- **Todos**: firecrawl, brave-search, sequential-thinking, vault

## Plugins
- @opencode-ai/sdk: ✅ Adoptado (para automatización programática)
- opencode-firecrawl: ⏳ Posponer (no disponible en npm)
- opencode-supermemory: ❌ No adoptar (vault propio es suficiente)
- opencode-background-agents: ⏳ Posponer (task tool nativa suficiente)

## Agents
- **Aletheia**: Writes raw/. Reads wiki/. Permission: edit deny. Color: #4A90D9. Steps: 15. Temp: 0.3.
- **Kosmos**: Reads raw/ + wiki/. Writes schema/ADRs. Permission: edit ask. Color: #7B68EE. Steps: 10. Temp: 0.1.
- **Metis**: Reads all. Writes reports to wiki/ or PaperJSX. Permission: edit ask. Color: #E8A87C. Steps: 8. Temp: 0.4.

## Commands
- `/quality` — ejecuta smoke check
- `/investigate` — invoca Aletheia (subtask)
- `/architect` — invoca Kosmos (subtask)
- `/strategy` — invoca Metis (subtask)
