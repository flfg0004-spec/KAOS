---
audience: agent
type: concept
source: OpenCode MCP docs + investigación Aletheia
related: [mcp-ecosistema, configuracion-opencode]
tags: ["practice/api-design", "practice/model-context-protocol", "principle/architecture-decision-record", "subject/agent", "subject/arquitectura", "subject/concept", "subject/dsol", "subject/graph"]
---

# Per-Agent MCP Restriction

Técnica para reducir tokens de contexto restringiendo MCP servers por agente, en lugar de tenerlos todos disponibles globalmente.

## Cómo funciona
OpenCode permite deshabilitar MCPs globalmente via `tools { "mcp*": false }` y habilitarlos por agente en `agent.tools`.

## Beneficio estimado
Reducción de ~40% de tokens de tool descriptions al eliminar MCPs irrelevantes para cada agente.

## Implementación en KAOS (Final — post-limpieza táctica)

### Config Global
```json
"tools": {
  "depwire_*": false, "structurizr_*": false, "excalidraw_*": false,
  "paperjsx_*": false, "scholar-search_*": false, "rss-reader_*": false,
  "context7_*": false, "postgres_*": false, "git_*": false,
  "github_*": false, "lucidity_*": false, "mcp-obsidian-cli_*": false
}
```

### Tools por Agente

| Agente | MCPs Habilitados |
|--------|-----------------|
| **Aletheia** | scholar-search, rss-reader, context7, searxng, crawl4ai, exa-search, sequential-thinking, vault, txtai, knowledge-graph, hermes-gateway, firecrawl, agy-bridge |
| **Kosmos** | depwire, structurizr, excalidraw, git, lucidity, agy-bridge |
| **Metis** | excalidraw, paperjsx, exa-search, sequential-thinking, mcp-obsidian-cli, vault, strategy-mcp, strategy-extras, mcp-speed, mcp-dsol, mcp-pandas, agy-bridge |
| **Mnemosyne** | sequential-thinking, mcp-obsidian-cli, vault, txtai, knowledge-graph, mcp-embed, gaps, contradictions, lifecycle, quality, crossref, agy-bridge, mcp-dsol |
| **Kratos** | vault, sequential-thinking, git, exa-search, agy-bridge |

### MCPs Activos (25+ en opencode.json)
Lista representativa: mcp-obsidian-cli, sequential-thinking, depwire, excalidraw, paperjsx, scholar-search, git, rss-reader, context7, vault, exa-search, searxng, crawl4ai, txtai, structurizr, lucidity, knowledge-graph, mcp-embed, mcp-speed, mcp-dsol, agy-bridge, strategy-mcp, strategy-extras, mcp-pandas, hermes-gateway

Nota: `obsidian` (REST) fue deshabilitado en limpieza 2026-05-26. Solo `mcp-obsidian-cli` está activo para Mnemosyne y Metis.
`gptr-deep-research` fue eliminado 2026-05-25 (no implementado, reemplazado por pipeline multi-tool).

### MCPs Inactivos / No Implementados
- `github` — No necesario para KAOS. Eliminado.
- `postgres` — No hay instancia PostgreSQL local.
- `supermemory` — Requiere API key no configurada.
- `obsidian` (REST) — Puerto conflict con obsidian-local-rest-api. Deshabilitado.

## Referencias Cruzadas
- Relacionado: [[lucidity]]
- Relacionado: [[github-mcp-oficial]]
- Relacionado: [[tool-calling]]
- ADR-007: Optimización de Arquitectura KAOS
- Relacionado: [[arquitectura-integracion-herramientas]]
