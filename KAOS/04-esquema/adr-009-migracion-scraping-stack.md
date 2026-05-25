---
type: adr
title: 'ADR-009: Migración de Stack de Scraping y Nuevo Pipeline de Investigación'
aliases:
- adr-009-migracion-scraping-stack
tags:
- adr
created: '2026-05-24'
modified: '2026-05-24'
confidence: alta
status: draft
---

# ADR-009: Migración de Stack de Scraping y Nuevo Pipeline de Investigación

## Contexto

Firecrawl ha sido deprecado como herramienta de scraping en el ecosistema KAOS. La investigación de Aletheia (mayo 2026) identificó alternativas superiores en costo, velocidad y capacidades. Paralelamente, el pipeline de investigación de Aletheia necesita evolucionar de 6 fases a un modelo de 3 fases (Scope → Research → Synthesis) alineado con el state-of-the-art de agentes de investigación (STORM, Open Deep Research, GPT-Researcher). Finalmente, se identificó la necesidad de integración bidireccional entre Aletheia (investigación) y Mnemosyne (curación de conocimiento).

## Stack Anterior (Deprecado)

| Componente | Estado | Reemplazo |
|-----------|--------|-----------|
| Firecrawl MCP | ❌ Deprecado | Crawl4AI + Jina Reader + SearXNG |
| Pipeline 6 fases | ❌ Obsoleto | Pipeline 3 fases (Scope→Research→Synthesis) |
| Comunicación Aletheia→Mnemosyne | ❌ Inexistente | Contexto cross-agent bidirectional |

## Opciones Evaluadas para Scraping

| Herramienta | Precio | Anti-bot | Velocidad | ⭐ GitHub | Veredicto |
|------------|--------|----------|-----------|:---------:|-----------|
| **Crawl4AI** | Gratis (Apache 2.0) | 3 niveles con proxy | ~4x Firecrawl | 66K | 🥇 Motor principal |
| **Jina Reader API** | Gratis (20 RPM) | Medio | Rápido | — | 🥈 URL→Markdown rápido |
| **Firecrawl** | $19-299/mes | Bajo (0% en LinkedIn/X) | Medio | 113K | ❌ Deprecado |
| **ZenRows** | $69/mes | 70-94% | Medio | — | 🔒 Respaldo sitios protegidos |
| **Scrapfly** | $30/mes | 98.7% | Medio | — | 🔒 Respaldo enterprise |

## Decisiones

### Decisión 1: Migrar de Firecrawl a Crawl4AI + Jina Reader + SearXNG
- **Crawl4AI**: Motor principal de crawling (gratuito, 66K⭐, anti-detección, extracción LLM nativa vía LiteLLM)
- **Jina Reader API**: Conversión rápida URL→Markdown (gratis 20 RPM)
- **SearXNG**: Metasearch privado autogestionado (ya implementado, refuerza capacidad)

### Decisión 2: Nuevo Pipeline de Investigación de 3 Fases
Reemplazar el protocolo de 6 fases (Formular→Explorar→Profundizar→Triangular→Sintetizar→Verificar) por:

1. **Scope**: Interpretación → Clarificación → Brief de investigación → Selección de perfil (flash/standard/deep/massive)
2. **Research**: Plan multi-query → Ejecución paralela (Crawl4AI + SearXNG + Exa + Scholar) → Triangulación ≥3 fuentes → Loop de reflexión
3. **Synthesis**: Organización jerárquica → Faithfulness check → Niveles de confianza (✅/⚡/❓/❌) → Revisión crítica → Entrega estructurada

### Decisión 3: Integración Bidireccional Aletheia ↔ Mnemosyne
- **Pre-research**: Aletheia consulta a Mnemosyne `query_gaps(topic)` para conocer gaps existentes antes de investigar
- **Post-research**: Aletheia pasa research_output + confidence_matrix + sources a Mnemosyne para curación targeted (fases 1-5)
- **Feedback loop**: Mnemosyne genera research prompts basados en graph analysis (topic islands, decay detection)

### Decisión 4: Niveles de Confianza Estandarizados
Toda investigación de Aletheia debe incluir matriz de confianza:

| Nivel | Indicador | Definición |
|-------|:---------:|------------|
| Confirmado | ✅ | 3+ fuentes independientes de alta autoridad coinciden |
| Probable | ⚡ | 2+ fuentes coinciden, evidencia consistente pero limitada |
| Especulativo | ❓ | 1 fuente, o conflicto entre fuentes de peso similar |
| No determinado | ❌ | Sin fuentes suficientes o información contradictoria |

## Consecuencias

### Positivas
- **Costo cero** en scraping (Crawl4AI es gratuito, Jina Reader tiene tier gratis)
- **Mayor velocidad**: Crawl4AI es ~4x más rápido que Firecrawl en sitios sin JS
- **Mejor anti-detección**: Sistema de 3 niveles con escalado de proxies
- **Pipeline más efectivo**: 3 fases alineadas con SOTA (STORM, GPT-Researcher, Open Deep Research)
- **Conocimiento más sólido**: Triangulación forzada + niveles de confianza reducen alucinaciones
- **Sin reinvención**: Mnemosyne informa gaps antes de investigar

### Negativas
- Crawl4AI requiere infraestructura propia (VPS/Docker) para crawling a escala
- Jina Reader tiene límite de 20 RPM en tier gratis
- Migración requiere actualizar ~27 archivos de configuración
- Integración Mnemosyne requiere desarrollo de nuevos métodos (query_gaps)

### Neutrales
- Firecrawl sigue siendo funcional para quienes prefieran API-first con MCP nativo
- Crawl4AI tiene cloud API en beta cerrada (futura opción)
- El pipeline de 3 fases puede coexistir con el anterior durante transición

## Integración Aletheia ↔ Mnemosyne

### Flujo Bidireccional

```
Pre-Research:
  Aletheia → query_gaps(topic) → Mnemosyne → gaps/conceptos/decay
  Mnemosyne responde: qué ya existe, qué falta, qué está obsoleto

Post-Research:
  Aletheia → context.json: aletheia_to_mnemosyne → Mnemosyne
  Mnemosyne ejecuta curación targeted (fases 1-5) sobre nuevo contenido
  Mnemosyne retroalimenta: contradicciones, calidad, nuevos conceptos

Feedback Loop (asíncrono):
  Mnemosyne (Graph Phase 9) → topic_islands → prompts para Aletheia
  Mnemosyne (Lifecycle Phase 12) → decay detection → refresh prompts
```

### Cambios Técnicos
- **pipeline.py**: Nuevo `cross_agent.aletheia_to_mnemosyne` con research_output, confidence_matrix, sources, key_topics
- **orchestrator.py**: Nuevo nodo `mnemosyne_gap_check` + ruta condicional `route_after_aletheia`
- **Mnemosyne**: Nuevo método `query_gaps(topic)` + targeted curation mode (fases 1-5)

## Estado de Implementación

| # | Decisión | Estado | Archivos afectados |
|---|----------|--------|-------------------|
| 1 | Migrar Firecrawl→Crawl4AI+JinaReader+SearXNG | ✅ Completado | ~27 archivos config + docs |
| 2 | Pipeline 3 fases | ✅ Completado | 3 archivos de agente Aletheia + SKILL.md |
| 3 | Integración Aletheia↔Mnemosyne | ✅ Completado | pipeline.py + orchestrator.py + 4 archivos agente |
| 4 | Niveles de confianza | ✅ Completado | SKILL.md + agent config |

## Referencias
- ADR-007: Optimización de Arquitectura KAOS (Decisión 4 reemplazada)
- ADR-008: Plugin Architecture Decision (opencode-firecrawl deprecado)
- Investigación: `raw/investigacion-mejoras-mcp-ecosistema.md`
- Investigación Aletheia: Mayo 2026 — Stack de scraping SOTA
- https://github.com/unclecode/crawl4ai
- https://r.jina.ai
