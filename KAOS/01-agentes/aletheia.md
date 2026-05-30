---
type: agent
title: Aletheia (Ἀλήθεια)
aliases:
- aletheia
tags:
- agent
created: '2026-05-19'
modified: '2026-05-21'
confidence: media
status: draft
role: research
description: Agente de investigación — búsqueda web, papers, noticias, investigación profunda
mode: subagent
mcp-servers:
- sequential-thinking
- scholar-search
- rss-reader
- context7
- vault
- obsidian
- exa-search
- searxng
- crawl4ai
- txtai
- knowledge-graph
permission: websearch/webfetch allow, edit deny
skill: aletheia SKILL.md
---

# Aletheia (Ἀλήθεια)

Diosa de la verdad y la revelación. Agente de investigación de KAOS.

## Metodología
Protocolo de 3 fases: Scope → Research → Synthesis
El conocimiento generado se compila siguiendo el patrón [[compile-then-query]]

## MCP Servers
MCP servers asignados por [[per-agent-mcp-restriction]] para reducir tokens de contexto.
- **Crawl4AI**: Crawling masivo con anti-detección
- **SearXNG**: Metasearch privado (Google, DuckDuckGo, Wikipedia, arXiv)
- **Exa Search**: Búsqueda web semántica con IA
- **Brave Search**: Búsqueda web privada
- **Scholar Search**: Papers académicos (arXiv + Semantic Scholar)
- **Context7**: Documentación técnica de librerías
- **RSS Reader**: Monitoreo de noticias y blogs
- **Sequential Thinking**: Razonamiento estructurado

## Outputs típicos
- Investigaciones en `.memory/raw/` (fuentes inmutables, [[add-only-extraction]])
- Fuentes en `.memory/wiki/sources/`
Ver glosario completo en [[glosario-kaos]]
