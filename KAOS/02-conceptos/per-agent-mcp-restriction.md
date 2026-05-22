---
type: concept
title: Per-Agent MCP Restriction
aliases:
- per-agent-mcp-restriction
- mcp-ecosistema
- configuracion-opencode
tags:
- concept
created: '2026-05-20'
modified: '2026-05-21'
confidence: media
status: draft
source: OpenCode MCP docs + investigación Aletheia
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
| **Aletheia** | scholar-search, rss-reader, context7, gptr-deep-research, searxng, crawl4ai, exa-search, depwire, mcp-obsidian-cli, obsidian, sequential-thinking, vault, txtai |
| **Kosmos** | depwire, structurizr, excalidraw, git, lucidity, mcp-obsidian-cli, obsidian |
| **Metis** | excalidraw, paperjsx, exa-search, mcp-obsidian-cli, obsidian |
| **Mnemosyne** | sequential-thinking, mcp-obsidian-cli, obsidian, vault, txtai, knowledge-graph |
| **Kratos** | vault, sequential-thinking, git, exa-search, mcp-obsidian-cli, obsidian |

### MCPs Activos (19)
mcp-obsidian-cli, sequential-thinking, depwire, excalidraw, paperjsx, scholar-search, git, rss-reader, context7, vault, exa-search, gptr-deep-research, searxng, crawl4ai, txtai, structurizr, lucidity, obsidian, knowledge-graph

### MCPs Planificados (4, disabled)
github, lucidity, postgres, structurizr

## Referencias Cruzadas
- Relacionado: [[lucidity]]
- Relacionado: [[github-mcp-oficial]]
- Relacionado: [[tool-calling]]
- ADR-007: Optimización de Arquitectura KAOS
- Relacionado: [[arquitectura-integracion-herramientas]]
