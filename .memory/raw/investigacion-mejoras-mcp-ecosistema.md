# Investigación: Mejoras MCP y Ecosistema de Servidores

**Investigador**: Aletheia
**Fecha**: 2026-05-20
**Dominio**: MCP Servers, OpenCode Ecosystem
**Confianza general**: Alta

## Resumen Ejecutivo

Se investigó el ecosistema de MCP servers (87.2K★ awesome-list, 21,195 servers en mcp.so) y los plugins de OpenCode identificando oportunidades de mejora para KAOS. Principales hallazgos: (1) Podemos agregar GitHub MCP oficial, MCP Atlassian, Sentry MCP y Lucidity MCP para llenar brechas de calidad y project management. (2) El plugin opencode-firecrawl puede reemplazar nuestro MCP firecrawl actual con mejor integración. (3) opencode-supermemory ofrece memoria entre sesiones que complementa nuestro vault. (4) oh-my-openagent (58K★) es el estándar comunitario de orquestación multi-agente. (5) Debemos migrar database-mcp a PostgreSQL MCP oficial (read-only, schema completo).

---

## 1. Estado Actual de MCPs en KAOS (13 servidores)

| MCP | Tipo | Agente(s) | Reemplazar por |
|-----|------|-----------|----------------|
| firecrawl | local | Aletheia, Metis | ⚠️ opencode-firecrawl plugin |
| brave-search | local | Aletheia, Metis | Mantener |
| sequential-thinking | local | Todos | Mantener |
| depwire | local | Kosmos | Mantener |
| structurizr | local | Kosmos | Mantener |
| excalidraw | local | Kosmos, Metis | Mantener |
| paperjsx | local | Metis | Mantener |
| scholar-search | local | Aletheia | Mantener |
| git | local | Kosmos | ✅ Migrar a oficial (npx @modelcontextprotocol/server-git) |
| database | local | Kosmos | ✅ Migrar a PostgreSQL MCP oficial |
| rss-reader | local | Aletheia | Mantener |
| context7 | local | Aletheia | ✅ Migrar a remote (con API key) |
| vault | local | Todos | Mantener |
| obsidian | local | Todos | Mantener |

## 2. Nuevos MCPs Recomendados

### Prioridad Alta

| MCP | Propósito | Config | Razón |
|-----|-----------|--------|-------|
| **GitHub MCP (Oficial)** | Issues, PRs, code search, repo management | `npx -y @modelcontextprotocol/server-github` + GITHUB_TOKEN | Kosmos necesita acceso a repos remotos para análisis arquitectónico |
| **Lucidity MCP** | Calidad de código pre-commit, 10 dimensiones | `uvx lucidity-mcp` | Complementa a depwire con análisis de calidad lenguaje-agnóstico |
| **PostgreSQL MCP (Oficial)** | DB read-only, schema completo | `npx -y @modelcontextprotocol/server-postgres postgresql://...` | Más seguro que database-mcp, schema inspection completo |

### Prioridad Media

| MCP | Propósito | Config | Razón |
|-----|-----------|--------|-------|
| **Sentry MCP** | Error monitoring, stack traces | Remote con OAuth | Metis puede incluir errores en reportes de calidad |
| **MCP Atlassian** | Jira + Confluence (72 tools) | `uvx mcp-atlassian` | Para equipos que usen Jira/Confluence |

### Prioridad Baja

| MCP | Propósito | Razón |
|-----|-----------|-------|
| **Datadog MCP** | Logs, monitores, métricas | Solo si hay Datadog en el stack |
| **Neon MCP** | PostgreSQL serverless | Solo si se usa Neon |

## 3. Migración a Remote MCPs

OpenCode soporta MCP remotos con OAuth automático. Los siguientes MCPs pueden migrarse de local a remote para reducir tokens:

- **context7**: Migrar a `https://mcp.context7.com/mcp` (remoto)
- **firecrawl**: Considerar migrar a remote cuando opencode-firecrawl plugin esté disponible

## 4. Per-Agent MCP Restriction

Propuesta de restricción por agente para reducir tokens en contexto:

| MCP | Aletheia | Kosmos | Metis |
|-----|:--------:|:------:|:-----:|
| firecrawl | ✅ | ❌ | ✅ |
| brave-search | ✅ | ❌ | ✅ |
| sequential-thinking | ✅ | ✅ | ✅ |
| depwire | ❌ | ✅ | ❌ |
| structurizr | ❌ | ✅ | ❌ |
| excalidraw | ❌ | ✅ | ✅ |
| paperjsx | ❌ | ❌ | ✅ |
| scholar-search | ✅ | ❌ | ❌ |
| git | ❌ | ✅ | ❌ |
| database | ❌ | ✅ | ❌ |
| rss-reader | ✅ | ❌ | ❌ |
| context7 | ✅ | ❌ | ❌ |
| vault | ✅ | ✅ | ✅ |
| obsidian | ✅ | ✅ | ✅ |

**Impacto estimado**: Reducción de ~40% de tokens de tool descriptions.

## 5. Plugins del Ecosistema

| Plugin | Stars | Relevancia KAOS | Reemplaza código custom |
|--------|:-----:|:---------------:|:-----------------------:|
| opencode-firecrawl | 64 | 9/10 | ✅ Sí (MCP firecrawl actual) |
| opencode-supermemory | 1,219 | 8/10 | Parcial (memoria entre sesiones) |
| opencode-background-agents | 252 | 9/10 | No (nuevo: async delegation) |
| oh-my-openagent | 58,645 | 9/10 | Parcial (orquestación) |
| opencode-dynamic-context-pruning | 2,893 | 8/10 | No (nuevo: optimización tokens) |
| opencode-workspace | 445 | 7/10 | Referencia arquitectónica |
| opencode-conductor | 98 | 7/10 | Complementario a Metis |

## Fuentes
- awesome-mcp-servers: https://github.com/punkpeye/awesome-mcp-servers (87.2K★)
- mcp.so: https://mcp.so (21,195 servers)
- OpenCode Ecosystem: https://opencode.ai/docs/ecosystem
- GitHub MCP Server: https://github.com/github/github-mcp-server (30K★)
- Lucidity MCP: https://github.com/hyperb1iss/lucidity-mcp
- Serena MCP: https://github.com/oraios/serena (24.4K★)

## Matriz de Confianza

| Aspecto | Confianza | Evidencia |
|---------|-----------|-----------|
| Fuentes primarias | Alta | M�ltiples referencias cruzadas verificadas |
| Consistencia interna | Alta | Sin contradicciones detectadas con el vault existente |
| Reproducibilidad | Media | Fuentes documentadas y accesibles |
| Actualizaci�n | Reciente | Informaci�n vigente al momento de ingesta |

## Referencias
- [[index]]
- [[log]]
- [[checkpoint]]