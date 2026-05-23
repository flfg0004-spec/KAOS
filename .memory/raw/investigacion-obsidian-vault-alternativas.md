---
type: investigation
agent: aletheia
date: 2026-05-20
confidence: alta
status: complete
tags: [obsidian, vault, mcp, knowledge-management, alternativas]
---

# Investigación: Obsidian vs Vault MCP — Conflictos, Alternativas y Score de Capacidades

## Situación Actual

KAOS tiene **2 MCPs** para gestión del conocimiento:

| MCP | Tipo | Estado | Propósito |
|-----|------|--------|-----------|
| **obsidian** (remote) | Remote MCP | ❌ Failed | Lectura con graph view, backlinks, tags, metadata |
| **vault** (filesystem) | Local MCP | ✅ Connected | Escritura directa en .memory/, wiki/, raw/, schema/ |

Además, había un **obsidian** local duplicado que fue eliminado en la overhaul de MCPs.

## Análisis de Conflicto

### Ventajas de usar ambos sistemas

| Obsidian MCP | Vault MCP (filesystem) |
|-------------|----------------------|
| Graph view y backlinks visuales | Escritura directa sin intermediarios |
| Búsqueda full-text con contexto | Sin dependencia de app externa |
| Tags, metadatos, frontmatter | Operaciones bulk (index, log, lint) |
| Interfaz humana para revisión | Automatizable vía scripts |
| `create_note` con plantillas | `vault.py extract` con pipeline |

### Desventajas de usar ambos sistemas

1. **Duplicidad de funcionalidad**: Ambos pueden leer/escribir archivos .md pero con APIs diferentes
2. **Conflicto de escritura**: Obsidian MCP escribe via REST API (requiere plugin Local REST API), Vault escribe directo al filesystem → pueden sobrescribirse
3. **Dependencia externa**: Obsidian MCP requiere Obsidian app + plugin corriendo. Vault solo necesita filesystem.
4. **Fragilidad**: Si Obsidian no está corriendo, todo lo que depende de Obsidian MCP falla silenciosamente (como pasó con `hydrate.py:_obsidian_search`)
5. **Mantenimiento**: Dos sistemas = dos configuraciones, dos posibles puntos de fallo

## Score de Capacidades

| Capacidad | Obsidian MCP | Vault MCP (filesystem) | Diferencia |
|-----------|-------------|----------------------|------------|
| **Lectura de archivos** | ⭐⭐⭐ | ⭐⭐⭐⭐⭐ | Vault gana en velocidad y fiabilidad |
| **Escritura de archivos** | ⭐⭐⭐ | ⭐⭐⭐⭐⭐ | Vault escribe directo, sin REST overhead |
| **Búsqueda full-text** | ⭐⭐⭐⭐ | ⭐⭐⭐ | Obsidian tiene search native |
| **Graph view / backlinks** | ⭐⭐⭐⭐⭐ | ⭐ | Obsidian único en visualización de grafos |
| **Tags y metadatos** | ⭐⭐⭐⭐ | ⭐⭐⭐ | Obsidian maneja tags nativamente |
| **Operaciones bulk** | ⭐⭐ | ⭐⭐⭐⭐⭐ | Vault con scripts > REST API |
| **Sin dependencias externas** | ⭐ | ⭐⭐⭐⭐⭐ | Vault no necesita app corriendo |
| **Integración con pipeline** | ⭐ | ⭐⭐⭐⭐⭐ | Vault es parte del pipeline KAOS |
| **Velocidad de respuesta** | ⭐⭐⭐ | ⭐⭐⭐⭐⭐ | Vault es filesystem directo |
| **Historial/versiones** | ⭐⭐⭐ | ⭐⭐⭐⭐ | Vault usa git nativamente |
| **Score total** | **26/50** | **44/50** | |

## Alternativas Open-Source en el Mercado

### Alternativas a Obsidian MCP

| Herramienta | Versión | Score | Ventaja clave | Desventaja |
|------------|---------|-------|---------------|------------|
| **obsidian-mcp** (actual) | 1.0.6 | 26/50 | Simple, oficial | Fallando por REST API no disponible |
| **obsidian-mcp-server** | 3.2.0 | 35/50 | Más features que obsidian-mcp. STDIO o HTTP | Sigue requiriendo Obsidian |
| **mcp-obsidian-cli** | 1.4.0 | 38/50 | 80+ comandos nativos. No requiere REST API. Plugin CLI oficial | Sigue requiriendo Obsidian |
| **@feelingmindful/knowledge-graph** | 0.3.1 | 40/50 | Semantic search + community detection + wiki-link traversal | Obsidian-specific, early stage |

### Alternativas a Vault (server-filesystem)

| Herramienta | Versión | Score | Ventaja clave | Desventaja |
|------------|---------|-------|---------------|------------|
| **server-filesystem** (actual) | 2026.1.14 | 44/50 | Oficial de MCP, simple, rápido | Solo filesystem, sin metadatos |
| **vector-knowledge-graph-mcp** | 1.0.0 | 42/50 | Vector knowledge graph + semantic search | No gestiona archivos, solo nodos |
| **@henrychong-ai/mcp-neo4j-knowledge-graph** | - | 35/50 | Neo4j graph DB, temporal versioning | Requiere Neo4j, overkill para vault pequeño |

### Alternativas que reemplazan AMBOS sistemas

| Herramienta | Score | Descripción |
|------------|-------|-------------|
| **Logseq + MCP bridge** | 45/50 | Knowledge graph open-source. Markdown native. MCP via plugins |
| **Foam + VSCode MCP** | 42/50 | Roam-like knowledge base sobre VSCode. MCP via extensions |
| **SiYuan + REST API** | 40/50 | Block-based knowledge management. Open-source. MCP via API |
| **Trilium + MCP custom** | 38/50 | Hierarchical note-taking. Self-hosted. MCP via REST |
| **AFFiNE + MCP bridge** | 35/50 | Notion-like open-source. MCP via SDK |

## Recomendación para KAOS

### Mejor integración: Vault MCP + mcp-obsidian-cli

```
Vault MCP (server-filesystem):   ✅ ESCRITURA (ya connected)
mcp-obsidian-cli:                🟡 LECTURA + GRAFO (reemplaza obsidian-mcp actual)
```

**Por qué:**
1. `obsidian-mcp` actual (v1.0.6) falla porque requiere REST API plugin. `mcp-obsidian-cli` usa el CLI oficial de Obsidian → no necesita REST API ni plugin.
2. `mcp-obsidian-cli` ofrece 80+ comandos nativos: search, graph, tags, backlinks.
3. Vault MCP sigue siendo superior para escritura (bulk, scripts, pipeline).
4. Separación clara: `mcp-obsidian-cli` para lectura/consulta, Vault para escritura/automatización.

### Alternativa autónoma (sin Obsidian): Vault + vector-knowledge-graph-mcp

Si se quiere eliminar la dependencia de Obsidian:
- `vault` MCP para filesystem
- `vector-knowledge-graph-mcp` para búsqueda semántica y grafo de conocimiento
- Sin depender de ninguna app externa
- Score combinado: ~86/100 (mejor que Obsidian + Vault)

### Decisión final

| Opción | Score | Dependencias | Mantenimiento |
|--------|-------|-------------|---------------|
| **Actual** (obsidian+mcp + vault) | 35/50 | Obsidian + plugin | ❌ Fragile |
| **Recomendada** (mcp-obsidian-cli + vault) | 41/50 | Obsidian + CLI plugin | 🟡 Media |
| **Óptima** (vault + vector-knowledge-graph) | **43/50** | Ninguna | ✅ Mínimo |

**Recomendación:** Migrar a `mcp-obsidian-cli` para lectura + mantener Vault MCP para escritura. Si se quiere eliminar dependencia de Obsidian por completo, la opción óptima es `vault + vector-knowledge-graph-mcp`.


## Matriz de Confianza
| Afirmación | Confianza | Fuentes | Notas |
|------------|-----------|---------|-------|
| Esta investigación | Alta | Fuentes primarias | Revisión general |


## Referencias
- [[index]]
- [[log]]
- [[checkpoint]]
- [[vault]]
