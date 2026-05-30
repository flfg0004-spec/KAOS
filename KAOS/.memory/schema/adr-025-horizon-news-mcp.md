# ADR-025: Integración de Horizon AI News Aggregator como Fuente de Investigación

**Estado:** Propuesto  
**Fecha:** 2026-05-30  
**Contexto:** Evaluación de Horizon (5.2K⭐, Python, MCP Server) como pipeline de noticias AI para Aletheia

## Contexto

Aletheia, el agente de investigación de KAOS, depende actualmente de:

1. **Exa Search API** — búsqueda web externa (costo por API call).
2. **RSS Reader MCP** — feeds RSS tradicionales (contenido limitado, formato irregular).
3. **SearXNG** — meta-buscador local (alcance limitado).
4. **Crawl4AI** — scraping de páginas web (pesado para news diarias).

No existe un pipeline estructurado de **noticias AI** que alimente a Aletheia diariamente con contenido curado, scorteado y deduplicado.

**Horizon** (5.2K⭐, Python) es un agregador de noticias AI con:

1. **Pipeline MCP de 7 pasos**: fetch_items → score_items → dedupe → classify → enrich → summarize → store.
2. **MCP Server** con tools: `hz_fetch_items`, `hz_score_items`, `hz_dedupe`, `hz_classify`, `hz_enrich`, `hz_summarize`, `hz_store`.
3. **Scoring** de items por relevancia y calidad.
4. **Deduplicación** de noticias similares.
5. **Clasificación** por categorías (research, product, funding, etc.).
6. **Enriquecimiento** con metadatos adicionales.
7. **Resumen** automático de cada item.

## Opciones Consideradas

### Opción 1: Integrar Horizon como MCP Server Externo

Ejecutar Horizon como proceso independiente, conectado vía MCP a KAOS.

- **Pros**: 7-step pipeline listo, Python stack alineado, MCP nativo, 5.2K⭐.
- **Cons**: Dependencia externa, infraestructura adicional (proceso separado), posible duplicación con RSS Reader.

### Opción 2: Adoptar el Pipeline de Horizon en Aletheia

Extraer la lógica del pipeline de 7 pasos e implementarla dentro del skill de Aletheia.

- **Pros**: Control total, integración profunda, sin dependencia externa.
- **Cons**: Mayor esfuerzo, reinvento de rueda.

### Opción 3: Usar Horizon Solo para News Discovery

Integrar solo `hz_fetch_items` + `hz_score_items` como fuentes de descubrimiento, manteniendo el resto del pipeline de Aletheia.

- **Pros**: Bajo esfuerzo (~1-2 días), beneficio inmediato, sin acoplamiento fuerte.
- **Cons**: No aprovecha dedup, clasificación y resumen de Horizon.

### Opción 4: No Integrar

Mantener el status quo con Exa + RSS + SearXNG + Crawl4AI.

- **Pros**: Sin esfuerzo, sin dependencia.
- **Cons**: Sin pipeline estructurado de noticias AI, Aletheia pierde contenido valioso.

## Decisión

**Opción 3 — Horizon solo para News Discovery (hz_fetch_items + hz_score_items).**

Se integrarán 2 tools de Horizon como MCP server adicional, complementando las fuentes existentes de Aletheia:

### Arquitectura

```
                    ┌─────────────────────────────────────┐
                    │            Aletheia Pipeline          │
                    │                                      │
                    │  Fuentes existentes:                  │
                    │  ├── Exa Search API                   │
                    │  ├── RSS Reader MCP                  │
                    │  ├── SearXNG                          │
                    │  └── Crawl4AI                         │
                    │                                      │
                    │  Nueva fuente:                        │
                    │  └── Horizon MCP ───────────────────┐│
                    │      ├── hz_fetch_items (categorías) ││
                    │      └── hz_score_items (ranking)   ││
                    │                                      │
                    │  Procesamiento (existente):           │
                    │  ├── Dedup (Aletheia)                 │
                    │  ├── Clasificación (Aletheia)         │
                    │  └── Compilación → raw/               │
                    └─────────────────────────────────────┘
```

### Implementación

1. **MCP Config**: añadir Horizon MCP server a `opencode.json`.
2. **Aletheia Skill**: modificar SKILL.md para incluir Horizon como fuente de discovery diario.
3. **Pipeline**: ejecutar `hz_fetch_items` al inicio de cada sesión de investigación.
4. **Scoring**: usar `hz_score_items` para priorizar qué noticias investigar primero.

## Consecuencias

### Positivas
+ **Discovery curado**: noticias AI scorteadas por relevancia, no ruido.
+ **Bajo esfuerzo**: ~1-2 días para integración MCP básica.
+ **Stack align**: Python, MCP nativo.
+ **Reversibilidad**: si Horizon deja de funcionar, Aletheia vuelve a fuentes existentes.
+ **Sin vendor lock-in**: Horizon es OSS, self-hosted.

### Negativas
- **Pipeline parcial**: no usamos dedup, clasificación, ni resumen de Horizon.
- **Infraestructura adicional**: proceso Horizon debe correr.
- **Dependencia de mantenimiento**: proyecto de 5.2K⭐, mantenimiento no garantizado.

### Alternativa futura

Si Horizon demuestra valor y estabilidad (v1.0+, 10K+⭐), migrar a **Opción 1** (Horizon completo como pipeline MCP) o **Opción 2** (adoptar el pipeline en Aletheia nativamente).

## Referencias
- Horizon: 5.2K⭐, Python, pipeline MCP de 7 pasos
- ADR-009: Migración de Stack de Scraping (Firecrawl → Crawl4AI)
- Aletheia SKILL.md: pipeline de investigación de 3 fases
