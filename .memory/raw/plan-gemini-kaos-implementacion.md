---
title: "Plan de Implementación: Integración Gemini en KAOS"
date: 2026-05-29
agent: kosmos
status: draft
type: plan
tags: [gemini, implementation, plan, aether, agy, adk, gemma]
---

# Plan de Implementación: Google Gemini en KAOS

## Resumen

Costo estimado del plan: **~2 semanas hombre** distribuido en 4 fases.
Impacto: **Reducción de costos de $27/mes a ~$12/mes** + calidad mejorada.

---

## Fase 1: Configuración Aether (Inmediata — Días 1-2)

### Tareas

1. **Modificar `aether.yaml`** — agregar:
   - Nuevos tiers: `gemini_free`, `gemini_ultra`, `gemini_value`, `gemini_agentic`, `gemini_pro`, `gemini_embed`
   - Cost rates para gemini-3.5-flash-AGY ($0), gemini-3.5-flash, gemini-3.1-pro, gemini-3-flash, gemini-3.1-flash-lite, gemini-embedding-2
   - Cost caps semanales para cada tier
   - Fallback chains multi-provider
   - Feature flags: `ether_gemini_free_enabled`, `ether_gemini_api_enabled`, `ether_agy_priority`, `ether_gemini_mcp_routing`

2. **Extender `config.py`** — agregar constantes:
   - `ETHER_GEMINI_FREE_ENABLED`, `ETHER_GEMINI_API_ENABLED`, `ETHER_AGY_PRIORITY`
   - Env var overrides

3. **Modificar `router.py`** — agregar Stage 11 (AGY preference):
   ```python
   def _apply_agy_preference(chosen):
       if ETHER_AGY_PRIORITY and chosen.model == "gemini-3.5-flash":
           return agy_version if CB_available else chosen
       return chosen
   ```

### Archivos a modificar
- `.memory/_scripts/aether.yaml`
- `.memory/_scripts/lib/aether/config.py`
- `.memory/_scripts/lib/aether/router.py`
- `.memory/_scripts/lib/aether/providers/__init__.py`

### Verificación
```bash
py -3 -m pytest .memory/_scripts/tests/test_aether_*.py -v --no-header
```

---

## Fase 2: AGY como Provider Formal (Corto plazo — Días 3-5)

### Tareas

1. **Crear `lib/aether/providers/agy.py`**:
   - `agy_ask_flash()` → wrapper subprocess
   - `agy_ask_with_subagents()` → subagentes paralelos (ventaja diferencial)
   - `agy_available()` → health check
   - `agy_status()` → rate limit info, version

2. **Registrar AGY en el Circuit Breaker**:
   - Provider: `gemini_agy` — threshold: 8 failures, timeout: 30s

3. **Configurar AGY como default para tareas de exploración**:
   - `task_model_map.exploration` → `gemini-3.5-flash-AGY`
   - `task_model_map.prototyping` → `gemini-3.5-flash-AGY`
   - `task_model_map.quick_review` → `gemini-3.5-flash-AGY`

### Archivos a crear/modificar
- `.memory/_scripts/lib/aether/providers/agy.py` (NUEVO)
- `.memory/_scripts/lib/aether/circuit.py` (modificar)
- `.memory/_scripts/aether.yaml` (modificar task_model_map)

### Verificación
```bash
# Test AGY wrapper
py -3 -c "from lib.aether.providers.agy import agy_available; print('AGY:', agy_available())"

# Test routing
py -3 -c "from lib.aether.router import resolve_model; print(resolve_model(task_type='exploration'))"
```

---

## Fase 3: Gemini Embedding 2 + ChromaDB (Días 6-8)

### Tareas

1. **Implementar wrapper Gemini Embedding 2**:
   - `embed()` con soporte multimodal (texto, imagen, PDF)
   - MRL truncable (256, 512, 1024, 2048, 3072 dims)
   - Batching (100 por lote)
   - Free tier detection

2. **Integrar con ChromaDB**:
   - Nueva colección `gemini_emb_{modality}`
   - Almacenar en 1024d, buscar en 3072d
   - Metadata con dims originales

3. **Configurar RAG pipeline**:
   - Ingesta multimodal
   - Re-ranking con Gemini 3.5 Flash (AGY = gratis)
   - Hybrid search (vector + keyword)

### Archivos a crear/modificar
- `.memory/_scripts/lib/gemini_embedding.py` (NUEVO)
- `.memory/_scripts/lib/vectorstore.py` (modificar)

### Verificación
```bash
py -3 -c "
from lib.gemini_embedding import GeminiEmbedding
emb = GeminiEmbedding()
result = emb.embed('test text', dimensions=1024)
print(f'Dims: {len(result)}')
"
```

---

## Fase 4: Gemma 4 + ADK (Mediano plazo — Días 9-14)

### Tareas

1. **Instalar LiteRT-LM + Gemma 4 E2B (2.6B)**:
   ```bash
   # LiteRT-LM runtime
   pip install litert lmstudio
   # Descargar Gemma 4 E2B
   lmstudio pull google/gemma-4-e2b-it
   ```

2. **Fine-tuning con Unsloth para clasificación de memoria**:
   - Dataset: 10,000 entries del vault etiquetadas
   - LoRA (r=16, target: q_proj, k_proj, v_proj, o_proj)
   - 4-bit quantization (4GB VRAM suficiente)

3. **Probar ADK 2.0 para flujos paralelos**:
   - ParallelAgent para investigación multi-fuente
   - LoopAgent para auto-mejora de outputs
   - A2A bridge con LangGraph

4. **Migración completa AGY antes del 18 Jun 2026**:
   - Verificar que todos los flujos que usaban Gemini CLI migraron a AGY
   - Test de regresión en `mcp_agy_bridge.py`
   - Actualizar documentación

### Archivos a crear/modificar
- `.memory/_scripts/lib/gemma_local.py` (NUEVO)
- `.memory/_scripts/lib/adk_integration.py` (NUEVO)
- `.memory/_scripts/lib/aether/providers/agy.py` (finalizar)

### Verificación
```bash
# Test Gemma local
py -3 -c "from lib.gemma_local import GemmaLocal; m=GemmaLocal('e2b'); print(m.generate('Classify this memory entry'))"

# Test ADK
py -3 -c "
from lib.adk_integration import ParallelResearchAgent
agent = ParallelResearchAgent(subagents=3)
result = agent.run('Research topic X')
"
```

---

## Resumen de Archivos

| Archivo | Acción | Tamaño estimado |
|---------|--------|----------------|
| `.memory/_scripts/aether.yaml` | Modificar (+30 líneas) | ~150 líneas total |
| `.memory/_scripts/lib/aether/config.py` | Modificar (+15 líneas) | ~300 líneas total |
| `.memory/_scripts/lib/aether/router.py` | Modificar (+20 líneas) | ~250 líneas total |
| `.memory/_scripts/lib/aether/providers/agy.py` | **Crear** | ~120 líneas |
| `.memory/_scripts/lib/gemini_embedding.py` | **Crear** | ~200 líneas |
| `.memory/_scripts/lib/vectorstore.py` | Modificar (+50 líneas) | ~400 líneas total |
| `.memory/_scripts/lib/gemma_local.py` | **Crear** | ~150 líneas |
| `.memory/_scripts/lib/adk_integration.py` | **Crear** | ~180 líneas |

**Total: ~6 archivos modificados, ~4 nuevos (~650 líneas nuevas de código)**

---

## Riesgos y Mitigaciones

| Riesgo | Probabilidad | Impacto | Mitigación |
|--------|-------------|---------|-----------|
| AGY cambia términos/deja de ser gratis | Baja | Alto | Tener fallback a Gemini API (OpenRouter) |
| Deadline 18 Jun no se cumple | Media | Alto | AGY bridge con Gemini CLI legacy como backup |
| Rate limits AGY muy restrictivos | Media | Medio | Degradar a DeepSeek Flash automáticamente |
| Gemma 4 no corre en hardware actual | Alta (31B) | Medio | Usar solo E2B/E4B, diferir 31B |
| ADK 2.0 inestable (versión reciente) | Media | Bajo | LangGraph sigue disponible como fallback |
| Gemini Embedding free tier se acaba | Baja | Medio | Migrar a GTE-Qwen2-7B local |

---

## Métricas de Éxito

- [ ] Costo mensual reducido de $27 a ~$12 (con Gemini AGY + API)
- [ ] 30%+ del tráfico servido por AGY (gemini-3.5-flash-AGY) a costo $0
- [ ] MCP Atlas score de KAOS mejora (tool-use con Gemini 3.5 Flash)
- [ ] Embeddings multimodales funcionales en ChromaDB
- [ ] Gemma 4 E2B corriendo offline para tagging/clasificación
- [ ] Migración AGY completada antes del 18 Jun 2026
- [ ] ADK 2.0 ejecutando al menos un flujo paralelo en producción
