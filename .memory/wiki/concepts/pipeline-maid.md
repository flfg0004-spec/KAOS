---
audience: agent
type: concept
source: Sistema MAID
tags: [pipeline, arquitectura, ingesta, destilacion]
auto-distilled: false
---

# Pipeline MAID — Multi-Agent Ingestion & Distillation

Arquitectura del pipeline de conocimiento de KAOS, desde la ingesta masiva hasta la destilación cognitiva y el almacenamiento semántico.

## Arquitectura General

```
[Fuentes Externas] (URLs, PDFs, Wikipedia, Docs, APIs)
       │
       ▼
┌──────────────────────────────────────┐
│ 1. INGESTA (ingest.py)              │
│    - SHA-256 deduplicación          │
│    - Wikipedia API / SearXNG        │
│    - Crawl4AI (crawling masivo)     │
└──────────────┬───────────────────────┘
               ▼ raw/
┌──────────────────────────────────────┐
│ 2. ANÁLISIS (distill.py v2)         │
│    - DSOL extraction vía DeepSeek    │
│    - Fallback: extracción por regex  │
│    - Clasificación de perfil         │
└──────────────┬───────────────────────┘
               ▼ wiki/concepts/ + wiki/sources/
┌──────────────────────────────────────┐
│ 3. SINAPSIS (synapse.py)            │
│    - Búsqueda semántica (embeddings) │
│    - Cross-linking [[wikilinks]]     │
│    - Indexado en cache/embeddings    │
└──────────────┬───────────────────────┘
               ▼ wiki/ + cache/
┌──────────────────────────────────────┐
│ 4. CURACIÓN (Mnemosyne)             │
│    - 8 fases de curación automática │
│    - Lint, index, log, cross-ref     │
└──────────────┬───────────────────────┘
               ▼ vault integro
```

## Perfiles de Pipeline

| Perfil | Duración | Profundidad | Herramientas | Uso |
|--------|----------|-------------|--------------|-----|
| **flash** | 5-10 min | 1 nivel | Brave + SearXNG | Fact-checking rápido |
| **standard** | 30-60 min | 2 niveles | Brave + SearXNG + Scholar | Investigación general |
| **deep** | 2-4 hrs | 4 niveles | GPT-Researcher + SearXNG + Crawl4AI | Deep Research |
| **massive** | 4+ hrs | Crawl completo | Crawl4AI + txtai + STORM | Ingesta de sitios completos |

## Agentes del Pipeline

| Agente | Rol | Pipeline |
|--------|-----|----------|
| **Aletheia** | Investigación, ingesta, búsqueda | Inicio del pipeline |
| **Kosmos** | Arquitectura, ADRs, esquemas | Post-investigación |
| **Metis** | Estrategia, síntesis, OKRs | Post-arquitectura |
| **Mnemosyne** | Curación, wikilinks, calidad | Post-pipeline (opcional) |

## MCPs Integrados

| MCP | Propósito | Estado |
|-----|-----------|--------|
| `firecrawl` | ~~Búsqueda y extracción web~~ | ❌ Deprecado — Crawl4AI + SearXNG (ADR-009) |
| `brave-search` | Búsqueda web privada | ✅ Activo |
| `scholar-search` | Búsqueda académica | ✅ Activo |
| `gptr-deep-research` | Deep Research multi-query | ✅ Configurado |
| `searxng` | Metasearch privado (Docker) | ✅ Docker up |
| `crawl4ai` | Crawling masivo (Docker) | ✅ Docker up |
| `txtai` | Knowledge base semántico | ⬜ Pendiente Docker |
| `sequential-thinking` | Razonamiento estructurado | ✅ Activo |
| `vault` | Escritura en filesystem | ✅ Activo |
| `obsidian` | ~~Lectura con metadatos~~ | ❌ Deprecado (REST MCP deshabilitado 2026-05-26) |

## Flujo de Datos

1. **Usuario/cli** inicia pipeline con `vault.py pipeline init --topic X --profile Y`
2. **Aletheia** hace hydrate, lee input.md, selecciona herramientas según perfil
3. **Ingesta**: ingest.py convierte fuentes → raw/ con frontmatter
4. **Destilación**: distill.py extrae conceptos → wiki/concepts/ y wiki/sources/
5. **Sinapsis**: synapse.py cruza [[wikilinks]] y actualiza embeddings
6. **Post-hook**: post_output_hook.py orquesta todo automáticamente

## Comandos Útiles

```bash
# Iniciar pipeline con perfil
vault.py pipeline init --topic "tema" --profile deep

# Ingestar contenido
vault.py ingest url --ref https://...
vault.py ingest wikipedia --ref "topic" --max 100

# Ver estado
vault.py ingest status
vault.py embeddings status
vault.py synapse status
vault.py pipeline check

# Generar dashboard
vault.py dashboard
```


## Referencias Cruzadas
- Relacionado: [[add-only-extraction]]
- Relacionado: [[qué-hace]]
- Relacionado: [[recomendación-para-kaos]]
- Relacionado: [[sin-páginas-huérfanas]]
- Relacionado: [[cobertura-completa]]
- Relacionado: [[confianza-general]]
- Relacionado: [[herramientas]]
- Relacionado: [[pipeline-conocimiento-raw-wiki]]
- Relacionado: [[arquitectura-integracion-herramientas]]
- Relacionado: [[context-nivel-1]]
- Relacionado: [[container-nivel-2]]
- Relacionado: [[conversión-parcial]]
