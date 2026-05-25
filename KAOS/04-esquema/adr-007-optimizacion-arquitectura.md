---
type: adr
title: 'ADR-007: Optimización de Arquitectura KAOS — MCPs, Configuración y Pipeline'
aliases:
- adr-007-optimizacion-arquitectura
tags:
- adr
created: '2026-05-20'
modified: '2026-05-21'
confidence: media
status: draft
---

# ADR-007: Optimización de Arquitectura KAOS — MCPs, Configuración y Pipeline

## Contexto

La investigación de Aletheia sobre el ecosistema MCP, la configuración de OpenCode y el pipeline de conocimiento de KAOS reveló 12 oportunidades de mejora concretas. Este ADR consolida las decisiones derivadas de esa investigación.

## Decisiones

### Decisión 1: Per-Agent MCP Restriction
**Problema**: 13 MCPs globales consumen ~40% de tokens innecesariamente.
**Decisión**: Restringir MCPs por agente via `tools { "mcp*": false }` + habilitación selectiva.
**Detalle**: Ver tabla en concepto `per-agent-mcp-restriction`.

### Decisión 2: Migrar database-mcp a PostgreSQL MCP Oficial
**Problema**: database-mcp permite writes y no tiene schema completo.
**Decisión**: Usar `@modelcontextprotocol/server-postgres` (read-only, schema completo).
**Estado**: Reemplazar en próxima iteración.

### Decisión 3: Migrar context7 a Remote
**Problema**: Context7 local consume tokens de instalación.
**Decisión**: Migrar a `https://mcp.context7.com/mcp` (remoto, con API key opcional).

### Decisión 4: Evaluar opencode-firecrawl Plugin
**Problema**: MCP firecrawl actual funciona pero no está optimizado para OpenCode.
**Decisión**: Evaluar opencode-firecrawl plugin como reemplazo cuando esté estable.

### Decisión 5: Evaluar opencode-supermemory
**Problema**: KAOS no tiene memoria entre sesiones de OpenCode (solo dentro del vault).
**Decisión**: Evaluar opencode-supermemory para memoria entre sesiones del agente principal.

### Decisión 6: Agregar GitHub MCP Server
**Problema**: Kosmos no puede acceder a repos remotos directamente.
**Decisión**: Agregar GitHub MCP oficial para Kosmos.

### Decisión 7: Agregar Lucidity MCP
**Problema**: No hay análisis de calidad de código pre-commit.
**Decisión**: Agregar Lucidity MCP para Kosmos.

### Decisión 8: Optimizar Configuración de Agentes
**Problema**: Sin colors, steps, temperature configurados.
**Decisión**:
- Aletheia: color #4A90D9, steps 15, temperature 0.3
- Kosmos: color #7B68EE, steps 10, temperature 0.1
- Metis: color #E8A87C, steps 8, temperature 0.4

### Decisión 9: Automatizar Destilación raw→wiki
**Problema**: Solo 40% de investigaciones llegan a wiki/.
**Decisión**: Extender post_output_hook para extraer conceptos y cross-linkear automáticamente.

### Decisión 10: Agregar Custom Commands
**Problema**: Operaciones frecuentes requieren comandos complejos.
**Decisión**: Crear /quality, /investigate, /architect commands.

## Consecuencias

### Positivas
- Reducción de ~40% de tokens de tool descriptions.
- MCPs más seguros (PostgreSQL read-only).
- Pipeline de conocimiento con 100% de conversión raw→wiki.
- Agent config con colors, steps y temperature optimizados.
- Custom commands para operaciones frecuentes.

### Negativas
- Migración de MCPs requiere cambios en opencode.json.
- Algunos plugins requieren evaluación antes de adopción.
- La automatización raw→wiki requiere desarrollo adicional.

### Neutrales
- Las configuraciones de agente (colors, steps, temperature) no afectan funcionalidad.
- Los custom commands son opcionales.

## Estado

Aceptada — Implementada parcialmente (Fase Táctica + Estratégica completadas).

## Estado de Implementación

| # | Decisión | Estado | Notas |
|---|----------|--------|-------|
| 1 | Per-Agent MCP Restriction | ✅ **Implementada** | 14 MCPs enabled + `tools global: false` + filtro por agente |
| 2 | Migrar database-mcp a PostgreSQL MCP | 🔄 **Entry creado** | `postgres` MCP agregado (enabled: false, pendiente conexión) |
| 3 | Migrar context7 a Remote | ✅ **Implementada** | context7 en remote `https://mcp.context7.com/mcp` |
| 4 | ~~Evaluar opencode-firecrawl Plugin~~ | ❌ **Reemplazado** | Ver ADR-009 — migrado a Crawl4AI + SearXNG |
| 5 | Evaluar opencode-supermemory | ✅ **Implementada** | supermemory MCP agregado y habilitado |
| 6 | ~~Agregar GitHub MCP Server~~ | ❌ **Descartado** | GitHub removido — no necesario para KAOS |
| 7 | ~~Agregar Lucidity MCP~~ | ❌ **Eliminado** | `lucidity-mcp` no existe en npm |
| 8 | Optimizar Configuración de Agentes | ✅ **Implementada** | colors, steps, temperature configurados |
| 9 | Agregar Structurizr MCP | ✅ **Implementada** | MCP wrapper Python para structurizr CLI (sin licencia) |
| 10 | Agregar txtai MCP | ✅ **Implementada** | MCP Python con sentence-transformers (semsearch + dedup) |
| 11 | Agregar knowledge-graph MCP | ✅ **Implementada** | MCP local para grafo de conocimiento |
| 12 | Automatizar Destilación raw→wiki | ✅ **Implementada** | Sprint Táctico H1 (distill.py + trigger + schedule) |
| 13 | Custom Commands | ✅ **Implementada** | /quality, /investigate, /architect, /strategy creados |

## Referencias
- Investigación: `raw/investigacion-mejoras-mcp-ecosistema.md`
- Investigación: `raw/investigacion-configuracion-opencode.md`
- Investigación: `raw/investigacion-pipeline-conocimiento.md`
- Concepto: `wiki/concepts/per-agent-mcp-restriction.md`
- Concepto: `wiki/concepts/pipeline-conocimiento-raw-wiki.md`
- ADR-001: Sistema de Memoria de KAOS

## Arquitectura MCP Final (post-limpieza)

```
18 activos:  mcp-obsidian-cli, sequential-thinking, depwire, excalidraw,
             paperjsx, scholar-search, git, rss-reader, context7, vault,
             exa-search, gptr-deep-research, searxng, crawl4ai,
             txtai, structurizr, supermemory, knowledge-graph

1 disabled: postgres (no hay PostgreSQL local)

Per-Agent Restriction: tools global {todos false} + agent.tools {solo propios}
```

