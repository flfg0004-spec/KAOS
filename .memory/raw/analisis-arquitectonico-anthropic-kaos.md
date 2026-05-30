---
title: "Análisis Arquitectónico: Integración Anthropic × KAOS"
date: 2026-05-29
agent: kosmos
status: complete
type: analysis
tags: [anthropic, kaos, architecture, integration, aether, routing]
---

## 1. Diagnóstico del Análisis de Metis

### 7 errores críticos detectados

1. **No detectó Aether v3** — El sistema de routing actual es Aether v3 (16 archivos en lib/aether/), no DSOL. Tiene resolve_model() de 10 etapas, Circuit Breaker, QualityStore, EtherTracker, EtherJudge, AB Testing, Observabilidad.

2. **No detectó agy-bridge Claude ya existente** — agy-bridge YA expone Claude Sonnet 4.6 y Opus 4.6 como tools MCP (agy_ask_sonnet, agy_ask_opus). Metis sugirió "crear" lo que ya existe.

3. **No detectó QualityStore/EtherJudge** — KAOS tiene sistema de calidad completo: EtherJudge con 6 dimensiones y rúbricas por tarea, QualityStore con histórico persistente, auto-eval sampling 10%. Metis sugirió crearlo.

4. **No detectó AB testing framework** — ab_testing.py en Aether v3 tiene ABTest class con análisis estadístico (chi-cuadrado, mínimo 10 muestras). Metis sugirió implementarlo.

5. **No detectó Rego policies** — KAOS tiene 3 archivos Rego (agents.rego, architecture.rego, synthesis.rego) con 13+ reglas + validación general. opa_bridge.py con native Python fallback + Prometheus metrics.

6. **Ignoró MiMo y 9Router** — KAOS tiene acceso a Xiaomi MiMo ($0.000014/1K) y 9Router ($0.0000002/1K) — modelos 100-1000x más baratos que Claude. Metis asumió DeepSeek como único backbone.

7. **Recomendó Claude como backbone** — Sugerencia críticamente incorrecta. Claude Opus cuesta 357x más que MiMo. Claude debe ser tier premium (3-5% del tráfico), no backbone.

## 2. Oportunidades de Integración

### A. Routing Aether v3 con Claude (PRIORIDAD: ALTA, +$0.10/sem)

**Dónde**: aether.yaml, config.py, router.py, client.py

Agregar en aether.yaml:
- cost_rates: claude-sonnet ($0.003/$0.015), claude-haiku ($0.001/$0.005), claude-opus ($0.005/$0.025), cache_read con 90% descuento
- task_model_map: adr_validation, design_review, quality_audit → claude-sonnet; strategy_critical, ethics_review → claude-opus; quick_review → claude-haiku
- fallback_chains: claude-sonnet → claude-opus → go-kimi-latest → go-pro → go-flash; claude-opus → go-kimi-latest → go-pro → go-flash; claude-haiku → claude-sonnet → go-flash → go-mimo
- model_tiers: sonnet (target_pct: 3), haiku (target_pct: 2), opus (target_pct: 1)
- cost_caps: sonnet ($0.50/sem, 10 calls/día), opus ($0.30/sem, 3 calls/día), haiku ($0.20/sem, 20 calls/día)

En config.py: AGY_MODELS dict mapeando claude-* a agy_tier. Nuevos tier constants.

En router.py: Nueva etapa 2.5 _resolve_via_agy() que redirige modelos claude-* al agy-bridge.

En client.py: chat() detecta modelo claude-* y llama a call_agy() en vez de agent_llm_call(). QualityStore sampling incluye tiers Claude.

### B. Constitutional AI vía Rego + EtherJudge (PRIORIDAD: ALTA, $0 costo)

**Dónde**: policy/agents.rego, policy/synthesis.rego, opa_bridge.py, judge/__init__.py

Reglas CAI en agents.rego (10+):
- CAI-HARM-001: Prohibir instrucciones de malware/exploits sin mitigación
- CAI-TRUTH-001: Output de Aletheia debe incluir fuentes citadas
- CAI-TRUTH-002: Prohibir "I think" sin sustento
- CAI-TRANSP-001: Overconfidence sin confianza explícita
- CAI-TRANSP-002: Output debe incluir confidence level

En synthesis.rego (+3 reglas):
- Accuracy: Score mínimo 10
- Citation required para claims factuales
- Confidence levels en cada afirmación

En opa_bridge.py: evaluate_with_constitutional_review() que ejecuta Rego + CAI auto-crítica (5% sampling). Llama a EtherJudge.constitutional_review().

En judge/__init__.py: Nuevo método constitutional_review() que hace segunda pasada criticando el output contra principios CAI. Nueva dimensión reasoning_depth (weight 0.15) para rúbrica strategy.

### C. Batch API Nocturna (PRIORIDAD: ALTA, +$1.00/sem)

**Dónde**: anthropic_batch.py (NUEVO), run_curation.py

Pipeline sleep cycle nocturno:
1. Mnemosyne recopila documentos pendientes (raw/ sin curar, archive/ viejos)
2. Clasificar por complejidad: SIMPLE (80% → go-mimo $0.000014/1K), STANDARD (15% → claude-sonnet batch $0.0015/1K), COMPLEX (5% → claude-opus batch $0.0025/1K)
3. Enviar lote COMPLEX+STANDARD a Anthropic Batch API (50% descuento)
4. Sincronizar resultados: actualizar vault, regenerar índices txtai

Costos: SIMPLE 800 docs = $0.011, STANDARD 150 docs = $0.90, COMPLEX 50 docs = $1.00. Total ~$1.91/noche.

### D. Extended Thinking (PRIORIDAD: MEDIA)

**Dónde**: mcp_agy_bridge.py, judge/__init__.py

Extended Thinking de Claude Opus 4.8 para Metis (estrategia) y Kosmos (ADRs). Implementar como nuevo tool agy_ask_opus_thinking en mcp_agy_bridge.py. Thinking visible integrado en EtherJudge como nueva dimensión reasoning_depth.

### E. AB Testing (PRIORIDAD: MEDIA, $0 costo)

Activar experimentos A/B en ab_testing.py:
- go-pro vs claude-sonnet para task_type "analyze"
- go-kimi-latest vs claude-opus para task_type "strategy_critical"
- Mínimo 10 muestras por grupo, análisis chi-cuadrado

### F. Unificar Tool Use bajo MCP (PRIORIDAD: MEDIA, +$0.20/sem)

chat_with_tools() en client.py que unifica tool calling para todos los modelos. Claude usa tool use nativo con JSON schema. DeepSeek/Kimi usan function calling. MCP como capa universal.

## 3. Deep Dives Arquitectónicos

### Deep Dive 1: Routing Aether v3 con Claude

Diagrama de flujo:
```
Aether Router:
  1. model_override → verificar si es claude-*
  2. TASK_MODEL_MAP → strategy_critical → claude-opus
  3. Quality-aware rerank → INCLUYE modelos claude-*
  4. Budget-aware → cost_caps.opus = $0.30/semana
  5. Circuit Breaker → nuevo CB para agy-bridge
  6. Fallback → claude-opus → go-kimi-latest → go-pro

client.py chat():
  if model_key.startswith("claude-"):
    agy_tier = AGY_MODELS[model_key]["agy_tier"]
    result = call_agy(prompt, tier=agy_tier)
  else:
    result = agent_llm_call(model_override=model_key)

EtherJudge (sampling 10%):
  score = judge.evaluate(prompt, response, task_type)
  QualityStore.record(model, task_type, score)
  # QualityStore alimenta el rerank
```

Archivos: aether.yaml, config.py, router.py, client.py, quality_store.py, config_loader.py

### Deep Dive 2: Constitutional AI via Rego + EtherJudge

Diagrama:
```
Output del agente → OPA Bridge (Rego):
  agents.rego: Contenido requerido, Seguridad, CAI (No harm, Truthful)
  architecture.rego: Patrones aprobados, ADR completeness, CAI (Transparency)
  synthesis.rego: Score mínimo, Diff ratio, CAI (Accuracy)
  → EtherJudge: 6 dimensiones + CAI auto-crítica
  → QualityStore: Histórico para reranking
```

### Deep Dive 3: Batch API Nocturna

Diagrama:
```
Sleep Cycle (3 AM):
  1. Recopilar docs pendientes → .memory/_pending/ + .memory/_archive/
  2. Clasificar: SIMPLE (80%) → go-mimo, STANDARD (15%) → claude-sonnet batch, COMPLEX (5%) → claude-opus batch
  3. Batch API (50% descuento) → procesamiento asíncrono
  4. Sincronizar → vault + índices txtai
```

## 4. Matriz Costo-Beneficio Real

| Modelo | Input/1K | vs go-flash | vs go-mimo | Caso de uso óptimo |
|--------|----------|-------------|------------|-------------------|
| 9Router MiniMax | $0.0000002 | 0.001x | 0.01x | Fallback ultra-barato |
| go-mimo (MiMo) | $0.000014 | 0.10x | 1.0x | Wikilinks, extracción |
| go-flash (DS V4 Flash) | $0.00014 | 1.0x | 10x | Code gen, lint, general |
| go-qwen | $0.00010 | 0.71x | 7.1x | Backup multimodal |
| claude-haiku | $0.001 | 7.1x | 71.4x | Quick review |
| go-kimi-latest (K2.6) | $0.00095 | 6.8x | 67.9x | Estrategia, síntesis |
| go-pro (DS V4 Pro) | $0.00174 | 12.4x | 124.3x | Research, analyze, ADR |
| claude-sonnet | $0.003 | 21.4x | 214.3x | ADR validation, design review |
| claude-opus | $0.005 | 35.7x | 357.1x | Strategy critical, ethics review |

Break-even quality: Sonnet necesita 1.58x mejora (score 7.0→8.9) para justificar costo vs go-pro. Opus necesita 2.19x (7.0→10.0, casi imposible). Solo justificable para tareas cortas (ADR <500 tokens output) y batch nocturno (50% descuento).

Claude NO es costo-efectivo para: reemplazar go-flash (linting, code gen), go-mimo (wikilinks, extracción), go-kimi (estrategia general).

## 5. Roadmap de Integración

H1 (semanas 1-2, Quick Wins, +$0.10/sem):
- aether.yaml: cost_rates, task_model_map, fallback_chains claude-*
- config.py: AGY_MODELS, CLAUDE_TIERS
- router.py: _resolve_via_agy()
- client.py: chat() maneja claude-*
- agents.rego: +10 reglas CAI

H2 (semanas 3-6, Integración, +$1.00/sem):
- policy/synthesis.rego: +3 reglas
- opa_bridge.py: constitutional_review()
- judge/__init__.py: CAI auto-crítica
- anthropic_batch.py (NUEVO)
- run_curation.py: integración batch
- quality_store.py: thresholds por modelo

H3 (semanas 7-12, Transformación, +$0.20/sem):
- client.py: chat_with_tools() MCP universal
- llm.py: tool calling para Claude
- quality-dashboard.html: panel SAEs

Total post-H3: ~$1.80-2.30/semana ($0.50-1.00 actual)

## 6. Riesgos Arquitectónicos

| Riesgo | Prob | Impacto | Mitigación |
|--------|------|---------|------------|
| Dependencia bridge agy | Alta | Alto | CB + fallback a go-kimi/go-pro |
| Costos descontrolados | Media | Alto | cost_caps estrictos + budget enforcement |
| Calidad inconsistente | Media | Medio | QualityStore min_samples=10 antes de reranking |
| Latencia agy (5-30s) | Alta | Medio | Timeout 300s, tareas asíncronas |
| Rego policies bloquean outputs válidos | Media | Alto | Sampling 5% para CAI review (no bloqueante) |
| Anthropic rate limits | Alta | Bajo | CB per-model + fallback chain |

## 7. Anti-recomendaciones

1. ❌ No hacer de Claude el backbone (50x más caro)
2. ❌ No migrar a CLAUDE.md (KAOS tiene SOUL.md, SKILL.md, opencode.json)
3. ❌ No crear nuevos MCPs Anthropic (duplican funcionalidad existente, 21 MCPs ya)
4. ❌ No reemplazar QualityStore/EtherJudge (sistema KAOS es más completo)

## 8. Conclusión

KAOS tiene una arquitectura más sofisticada de lo que Metis asumió. Claude debe integrarse como tier premium (3-5% del tráfico, ~$2/semana) para tareas específicas de alto valor. La integración más valiosa es Constitutional AI via Rego ($0 costo runtime, alto impacto en alineación). El roadmap prioriza Quick Wins de bajo costo y alto retorno.

## Fuentes
- Código fuente KAOS: .memory/_scripts/lib/aether/ (16 archivos)
- Configuración: .memory/_scripts/aether.yaml
- Políticas: policy/agents.rego, policy/architecture.rego, policy/synthesis.rego
- Bridge: .memory/_scripts/mcp_agy_bridge.py
- Dossier Anthropic: .memory/raw/dossier-anthropic-kaos.md
- Investigación gaps: .memory/raw/investigacion-anthropic-gaps.md
