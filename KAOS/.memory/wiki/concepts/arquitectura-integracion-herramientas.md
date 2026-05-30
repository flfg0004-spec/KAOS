---
type: concept
source: arquitectura KAOS
related: [pipeline-maid, dsol]
---

# Estrategia de Integración de Herramientas — KAOS Ecosystem

## Evaluación de Herramientas

### LangFuse (LLM Observabilidad)
- **Release:** 3.38.20 (npm) / 4.6.1 (Python SDK)
- **Licencia:** MIT (core) — self-hosted vía Docker
- **Valor para KAOS:** Observabilidad total de llamadas DSOL: tracing, prompts, costos, latencia
- **Integración:** Instrumentar `call_api()` en dsol.py con `langfuse.decorators.observe()`
- **Infra:** Docker compose con PostgreSQL (langfuse + langfuse-db)
- **Riesgo:** Consume ~500MB RAM + PostgreSQL adicional. Para un equipo pequeño, puede ser overkill. DeepEval + token-usage.json pueden ser suficientes.

**Veredicto:** ✅ Alta prioridad si se necesita tracing visual. Baja prioridad si el tracking de tokens actual (28 calls, $0.85) es suficiente.

### Leantime (OKR & Estrategia)
- **Docker:** `leantime/leantime` (60 stars, official)
- **Licencia:** AGPL-3.0 (self-hosted)
- **Valor para KAOS:** OKRs, strategy canvas, roadmaps, retrospectivas
- **Integración:** API REST — Metis podría crear/actualizar OKRs vía `curl` o Python
- **Infra:** Requiere PHP + MySQL/MariaDB — más pesado que Plane.so
- **Alternativa:** Plane.so (49.5K⭐, TypeScript, Docker) — UX moderna tipo Linear pero SIN OKR nativo

**Veredicto:** 🟡 Media prioridad. Evaluar si realmente se necesita OKR tracking o si los reportes de Quarto + vault.md son suficientes.

### Quarto (Reportes Ejecutivos)
- **Estado:** ✅ Instalado v1.9.37
- **Integración:** `vault.py report` → genera `.qmd` → `quarto render` → PDF+PPTX+HTML
- **Valor:** Reportes semanales de calidad del vault desde una sola fuente

### DeepEval (Testing LLM)
- **Estado:** ✅ Instalado, 5 tests creados
- **Integración:** `test_llm_quality.py` en suite de tests. Metrics: hallucination, relevancy, faithfulness
- **Valor:** Validación objetiva de calidad de extracción de conceptos vía DSOL

### Mermaid CLI (Diagramas)
- **Estado:** ✅ Instalado
- **Integración:** Diagrama C4 creado en schema/diagrams/c4-context.mmd
- **Valor:** Documentación arquitectónica versionable

---

## Estrategia de Integración

### Capa 0: Infraestructura (Docker)
```
docker-compose.yml:
  searxng      :8888  → Metasearch (búsqueda privada)
  crawl4ai     :11235 → Crawling web
  langfuse     :3000  → LLM Observabilidad (NUEVO)
  langfuse-db  :5432  → PostgreSQL para LangFuse (NUEVO)
```

### Capa 1: Core Pipeline (existente, consolidado)
```
ingest.py  → SHA-256 dedup + Crawl4AI + Wikipedia API fallback
distill.py → DSOL extraction + DeepSeek v4 Flash + regex fallback  
synapse.py → Cosine similarity + BM25 fallback + cross-linking
pipeline.py → 4 profiles (flash/standard/deep/massive) + Mnemosyne step
```

### Capa 2: LLM & Búsqueda (actualizado)
```
exa-search MCP     → Búsqueda web semántica (reemplaza a brave)
crawl4ai MCP       → Crawling masivo (reemplaza a firecrawl)
jina-reader MCP    → Conversión URL→Markdown rápida
gptr-deep-research → Deep Research (backends: Exa + DeepSeek v4)
dsol.py v2         → API client + TokenTracker + retry + JSON mode
```

### Capa 3: Testing & Calidad (NUEVO)
```
test_llm_quality.py → DeepEval metrics (hallucination, relevancy, faithfulness)
token-usage.json    → Tracking de costos y tokens de DSOL
dashboard.json      → Métricas de calidad, pipeline, ingesta, sinapsis
```

### Capa 4: Reporting & Estrategia (NUEVO)
```
template-report.qmd → Quarto template (HTML+PDF+PPTX)
c4-context.mmd      → Mermaid diagrama C4 del sistema
Leantime/Plane.so   → OKRs y planificación (pendiente de evaluar)
```

### Capa 5: Agentes (actualizado)
```
Aletheia → exa-search + gptr-deep-research + SearXNG + Crawl4AI + DeepSeek v4
Kosmos   → Structurizr CLI + Mermaid + SonarQube + DeepEval
Metis    → Quarto + Excalidraw + Leantime + Metabase
Mnemosyne→ vault scripts + lint + quality + embeddings
```

---

## Recomendación Final

| Herramienta | Integrar | Por qué |
|-------------|----------|---------|
| **LangFuse** | 🟡 Evaluar | Si el equipo necesita tracing visual. Por ahora token-usage.json es suficiente |
| **Leantime** | 🟡 Evaluar | Si se necesitan OKRs formales. Alternativa más ligera: usar Quarto + vault.md |
| **Quarto** | ✅ YA | Reportes multi-formato desde Markdown |
| **DeepEval** | ✅ YA | Testing de calidad LLM en pipeline CI |
| **Mermaid** | ✅ YA | Diagramas versionables en la documentación |
| **exa-search** | ✅ YA | Búsqueda web semántica primaria |
| **gptr-deep-research** | ✅ YA | Deep Research con Exa backend |

## Próximas Acciones

1. Iniciar LangFuse: `docker compose -f .tools/docker-compose.yml up -d langfuse langfuse-db`
2. Instrumentar dsol.py: agregar `@observe()` a `call_api()` usando LangFuse Python SDK
3. Evaluar Leantime: `docker run -p 8080:80 leantime/leantime` y probar API REST
4. Crear comando `vault.py report` que ejecute Quarto con datos del dashboard
5. Integrar DeepEval tests en el GitHub Actions workflow


## Referencias Cruzadas
- Relacionado: [[estado-memoria-sesion]]
- Relacionado: [[pipeline-maid]]
- Relacionado: [[investigacion-pipeline-conocimiento]]
- Relacionado: [[per-agent-mcp-restriction]]
- Relacionado: [[software-testing]]
- Relacionado: [[para-kosmos-testingevaluación]]
- Relacionado: [[para-metis-estrategia]]
- Relacionado: [[github-mcp-oficial]]
- Relacionado: [[lucidity-mcp]]
- Relacionado: [[herramientas]]
- Relacionado: [[vault]]
- Relacionado: [[herramientas-utilizadas]]
