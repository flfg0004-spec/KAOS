---
audience: agent
title: "Guía de Integración de Modelos Anthropic en KAOS"
date: 2026-05-29
agent: kosmos
status: complete
type: concept
tags: [anthropic, claude, integration, aether, agy-bridge, routing]
aliases: [Claude-KAOS, Anthropic-Integration, claude-routing]
---

## Modelos Anthropic Disponibles en KAOS

KAOS tiene acceso a modelos Anthropic vía agy-bridge (CLI de Gemini que enruta a Claude). Actualmente disponibles:

| Modelo | Tool agy | Input/1K | Output/1K | Thinking |
|--------|----------|----------|-----------|----------|
| Claude Sonnet 4.6 | agy_ask_sonnet | $0.003 | $0.015 | No nativo |
| Claude Opus 4.6/4.8 | agy_ask_opus | $0.005 | $0.025 | Sí (Opus 4.8 nativo) |
| Claude Haiku 4.5 | (nuevo tool) | $0.001 | $0.005 | No |

Además, vía agy-bridge:
- Gemini 3.5 Flash (agy_ask_flash): FREE — exploración rápida
- GPT-5.5 (agy_ask_gpt55): ~$20/mes — estrategia
- GPT-5.5 Thinking (agy_ask_gpt55_thinking): ~$20/mes — problemas complejos

## Comparativa de Costos vs Modelos KAOS

| Modelo | Input/1K | vs go-flash | vs go-mimo | Posicionamiento |
|--------|----------|-------------|------------|-----------------|
| 9Router MiniMax | $0.0000002 | 0.001x | 0.01x | Ultra-económico |
| go-mimo (MiMo) | $0.000014 | 0.10x | 1.0x | Clasificación barata |
| go-flash (DS V4 Flash) | $0.00014 | 1.0x | 10x | Backbone general |
| go-qwen | $0.00010 | 0.71x | 7.1x | Backup multimodal |
| claude-haiku | $0.001 | 7.1x | 71.4x | Quick review |
| go-kimi-latest (K2.6) | $0.00095 | 6.8x | 67.9x | Estrategia general |
| go-pro (DS V4 Pro) | $0.00174 | 12.4x | 124.3x | Research, ADR |
| claude-sonnet | $0.003 | 21.4x | 214.3x | ADR validation premium |
| claude-opus | $0.005 | 35.7x | 357.1x | Decisiones críticas |

## Cuándo Usar Cada Modelo

### ✅ Claude Sonnet 4.6 (tier premium, 3% tráfico)
**Costo**: $0.003/$0.015 por 1M. **vs go-pro**: 1.7x input, 4.3x output.
**Usar para**: ADRs complejos, design reviews, quality audits, validación cruzada.
**No usar para**: Tareas largas (>500 tokens output), alto volumen.
**Break-even**: Necesita 1.58x mejora en weighted_score (ej: 7.0→8.9).

### ✅ Claude Opus 4.8 (tier crítico, 1% tráfico)
**Costo**: $0.005/$0.025 por 1M. **vs go-kimi-latest**: 5.3x input, 6.3x output.
**Usar para**: Estrategia crítica, ethics review, validación dual con GPT-5.5.
**No usar para**: Tareas rutinarias, ADRs estándar.
**Break-even**: Necesita 2.19x mejora (prácticamente imposible — solo justificable para tareas muy cortas).

### ✅ Claude Haiku 4.5 (tier ligero, 2% tráfico)
**Costo**: $0.001/$0.005 por 1M. **vs go-flash**: 7.1x. **vs go-mimo**: 71.4x.
**Usar para**: Quick reviews, clasificación simple, verificación rápida.
**No usar para**: Alto volumen (go-mimo es 71x más barato).

### ❌ NO usar Claude para (mantener DeepSeek/MiMo):
- Linting de código → go-flash ($0.00014)
- Wikilinks y extracción → go-mimo ($0.000014)
- Curación rutinaria → go-flash ($0.00014)
- Búsquedas web → go-flash ($0.00014)
- Código boilerplate → go-flash o go-mimo
- Consultas rápidas → go-flash ($0.00014)

## Integración en Aether v3 (Routing)

Para integrar Claude en el routing de Aether, se requieren cambios en:

### aether.yaml
```yaml
cost_rates:
  claude-sonnet:
    input: 0.003
    output: 0.015
    cache_read: 0.0003
  claude-haiku:
    input: 0.001
    output: 0.005
    cache_read: 0.0001
  claude-opus:
    input: 0.005
    output: 0.025
    cache_read: 0.0005

task_model_map:
  adr_validation: {model: claude-sonnet, thinking: null, tier: sonnet}
  design_review: {model: claude-sonnet, thinking: null, tier: sonnet}
  quality_audit: {model: claude-sonnet, thinking: null, tier: sonnet}
  strategy_critical: {model: claude-opus, thinking: high, tier: opus}
  ethics_review: {model: claude-opus, thinking: high, tier: opus}
  quick_review: {model: claude-haiku, thinking: null, tier: haiku}

fallback_chains:
  claude-sonnet: [claude-sonnet, claude-opus, go-kimi-latest, go-pro, go-flash]
  claude-opus: [claude-opus, go-kimi-latest, go-pro, go-flash]
  claude-haiku: [claude-haiku, claude-sonnet, go-flash, go-mimo]

cost_caps:
  sonnet: {weekly_usd: 0.50, daily_calls: 10}
  opus: {weekly_usd: 0.30, daily_calls: 3}
  haiku: {weekly_usd: 0.20, daily_calls: 20}

model_tiers:
  sonnet: {description: "Claude Sonnet — balanced quality/cost", target_pct: 3}
  haiku: {description: "Claude Haiku — fast and cheap", target_pct: 2}
  opus: {description: "Claude Opus — maximum quality", target_pct: 1}
```

### config.py
`AGY_MODELS` dict mapeando `claude-*` a `agy_tier` + nuevas constantes de tier.

### router.py
Nueva etapa 2.5 `_resolve_via_agy()` que intercepta modelos `claude-*` y redirige al agy-bridge.

### client.py
`chat()` modificado para detectar modelos `claude-*` y llamar a `call_agy()` en vez de `agent_llm_call()`. Calidad registrada en QualityStore con sampling 10%.

## Integración agy-bridge

El MCP server `mcp_agy_bridge.py` expone tools para cada modelo:

| Tool actual | Modelo | Timeout | Propósito |
|-------------|--------|---------|-----------|
| agy_ask_flash | Gemini 3.5 Flash | 120s | Exploración, review |
| agy_ask_sonnet | Claude Sonnet 4.6 | 180s | ADRs, diseño |
| agy_ask_opus | Claude Opus 4.6 | 300s | Estrategia, decisiones |
| agy_ask_gpt55 | GPT-5.5 | 180s | Estrategia |
| agy_ask_gpt55_thinking | GPT-5.5 Thinking | 300s | Problemas complejos |

**Nuevos tools recomendados:**
- `agy_ask_opus_thinking`: Claude Opus 4.8 con Extended Thinking (300s timeout)
- `agy_ask_haiku`: Claude Haiku 4.5 para quick reviews (60s timeout)

Mecanismo: `call_agy()` ejecuta `agy --dangerously-skip-permissions -p <prompt>`, cambia `settings.json` para seleccionar tier, lee respuesta del transcript. Thread-safe con file locking.

## Constitutional AI para Rego Policies

Los principios de Constitutional AI de Anthropic (constitución 2026, ética aristotélica) se traducen a reglas Rego:

### agents.rego (+10 reglas)
- CAI-HARM-001: No contenido dañino (malware, exploits sin mitigación)
- CAI-TRUTH-001: Output de investigación debe citar fuentes
- CAI-TRUTH-002: Prohibir "I think" sin sustento factual
- CAI-TRANSP-001: Overconfidence sin nivel de confianza explícito
- CAI-TRANSP-002: Output debe incluir confidence level
- CAI-RESP-001: Responsabilidad en outputs de código
- CAI-FAIR-001: No discriminación en outputs

### synthesis.rego (+3 reglas)
- CAI-ACC-001: Score mínimo 10
- CAI-ACC-002: Claims factuales requieren citas
- CAI-ACC-003: Niveles de confianza en cada afirmación

### opa_bridge.py
`evaluate_with_constitutional_review()` ejecuta Rego + CAI auto-crítica (5% sampling via EtherJudge).

## Batch API para Curaduría Nocturna

Anthropic Batch API ofrece 50% descuento para procesamiento asíncrono.

Pipeline nocturno:
1. Mnemosyne recopila documentos pendientes de `.memory/raw/` y `.memory/_archive/`
2. Clasificar por complejidad:
   - SIMPLE (80%): go-mimo ($0.000014/1K) — curación básica, wikilinks
   - STANDARD (15%): claude-sonnet batch ($0.0015/1K) — síntesis, contexto largo
   - COMPLEX (5%): claude-opus batch ($0.0025/1K) — reestructuración, CANONICAL
3. Enviar lote COMPLEX+STANDARD a Anthropic Batch API
4. Sincronizar resultados: vault + índices txtai

Costos: 800 SIMPLE ($0.011) + 150 STANDARD ($0.90) + 50 COMPLEX ($1.00) = ~$1.91/noche.

Nuevo módulo: `.memory/_scripts/lib/anthropic_batch.py`.

## Costo Semanal Estimado (post-integración)

| Componente | Costo/semana | % del total |
|------------|-------------|-------------|
| DeepSeek Flash | $0.30 | 17% |
| DeepSeek Pro | $0.10 | 6% |
| Kimi K2.6 | $0.15 | 9% |
| Xiaomi MiMo | $0.05 | 3% |
| Claude Sonnet | $0.10 | 6% |
| Claude Opus | $0.05 | 3% |
| Claude Haiku | $0.02 | 1% |
| **Batch Opus** | **$1.00** | **57%** |
| **Total** | **~$1.77** | **100%** |

## Archivos a Modificar para Integración Completa

| Archivo | Cambio | Prioridad |
|---------|--------|-----------|
| `.memory/_scripts/aether.yaml` | cost_rates, task_model_map, fallback, cost_caps | H1 |
| `.memory/_scripts/lib/aether/config.py` | AGY_MODELS, CLAUDE_TIERS | H1 |
| `.memory/_scripts/lib/aether/router.py` | `_resolve_via_agy()` | H1 |
| `.memory/_scripts/lib/aether/client.py` | chat() maneja claude-* | H1 |
| `.memory/_scripts/lib/aether/config_loader.py` | Parsear nuevos campos | H1 |
| `.memory/_scripts/lib/aether/quality_store.py` | Thresholds por modelo | H2 |
| `policy/agents.rego` | +10 reglas CAI | H1 |
| `policy/synthesis.rego` | +3 reglas CAI | H2 |
| `.memory/_scripts/lib/opa_bridge.py` | `constitutional_review()` | H2 |
| `.memory/_scripts/lib/aether/judge/__init__.py` | CAI auto-crítica | H2 |
| `.memory/_scripts/lib/anthropic_batch.py` | NUEVO | H2 |
| `.memory/_scripts/run_curation.py` | Integración batch | H2 |
| `.opencode/opencode.json` | Nuevos tools agy | H2 |

## Principios de Integración

1. **Claude NO es el backbone** — DeepSeek/MiMo mantienen 80%+ del tráfico
2. **Integración quirúrgica** — Claude solo donde su calidad superior justifica el costo premium
3. **Cost caps estrictos** — Opus $0.30/semana, Sonnet $0.50/semana
4. **Fallback automático** — Si Claude falla (timeout, rate limit), caer a Kimi/DeepSeek
5. **Quality-aware** — QualityStore decide basado en evidencia, no en preferencia
6. **Batch para volumen** — 50% descuento para procesamiento masivo nocturno
7. **Constitutional AI via Rego** — Principios CAI sin costo runtime

## Fuentes
- Dossier: `.memory/raw/dossier-anthropic-kaos.md`
- Análisis: `.memory/raw/analisis-arquitectonico-anthropic-kaos.md`
- Estrategia: `.memory/raw/estrategia-anthropic-kaos.md`
- Aether: `.memory/wiki/concepts/aether-routing-v3.md`
- Código: `.memory/_scripts/mcp_agy_bridge.py`, `.memory/_scripts/lib/aether/`
- Políticas: `policy/agents.rego`, `policy/architecture.rego`, `policy/synthesis.rego`
- Config: `.memory/_scripts/aether.yaml`
