---
title: "ADR-ANTH-001: Claude como Tier Premium en Ecosistema KAOS"
date: 2026-05-29
agent: kosmos
status: draft
type: adr
tags: [anthropic, claude, integration, routing, architecture]
---

# ADR-ANTH-001: Claude como Tier Premium, no Backbone

## Contexto

Anthropic ha alcanzado $965B valoración y $47B ARR (Mayo 2026). Sus modelos Claude Opus 4.8 (SWE-bench 80.8%), Sonnet 4.6 (76.5%) y Haiku 4.5 representan el estado del arte. Sin embargo, KAOS opera con DeepSeek V4 Flash ($0.00014/1K) que cuesta **357x menos** que Claude Opus ($0.005/1K).

El sistema KAOS actual ya tiene:
- Aether v3 router con 10 etapas de resolución
- agy-bridge que expone Claude Sonnet/Opus como MCP tools
- QualityStore, EtherJudge, Circuit Breaker, AB Testing
- 25+ MCP servers

## Decisión

**Claude se integra como tier premium (3-5% del tráfico) para tareas de alto valor específicas, no como backbone del sistema.**

| Modelo | % Tráfico | Costo/semana | Tareas |
|--------|-----------|-------------|--------|
| Opus 4.8 | ~2% | $0.30 | Estrategia crítica, ADRs complejos, validación dual |
| Sonnet 4.6 | ~5% | $0.50 | ADR validation, design review, quality audit |
| Haiku 4.5 | ~3% | $0.20 | Clasificación pipeline, quick review |
| DeepSeek V4 Flash | ~70% | ~$3.00 | Backbone: lint, code gen, general |
| MiMo | ~15% | ~$0.50 | Ultra-barato: wikilinks, extracción |
| Kimi K2.6 | ~5% | ~$0.50 | Contexto largo, estrategia general |

## Consecuencias

**Positivas:**
- +15-25% calidad en tareas críticas por solo +$35/mes ($27→$62)
- Ahorro 68.5% en llamadas Claude vía Prompt Caching
- Sin riesgo de vendor lock-in (DeepSeek mantiene 70% tráfico)
- Reutilización de infraestructura existente (Aether, agy-bridge)

**Negativas:**
- Complejidad adicional en routing (5 tiers vs 4 anteriores)
- Costo tracking más granular necesario
- Latencia Opus 2-3x mayor que DeepSeek (mitigado: solo asíncrono)

**Riesgos:**
- Dependencia bridge agy (mitigado: fallback chain a go-kimi-latest)
- Costos descontrolados (mitigado: cost_caps estrictos)
- Rate limits Anthropic (mitigado: Circuit Breaker + fallback)

## Implementación

Ver `arquitectura-anthropic-claude-ecosistema.md` sección 6 para plan detallado de 3 fases.

## Referencias

- `arquitectura-anthropic-claude-ecosistema.md` — Documento completo de arquitectura
- `dossier-anthropic-kaos.md` — Dossier estratégico Anthropic
- `estrategia-anthropic-kaos.md` — Estrategia y RICE scoring
- `analisis-arquitectonico-anthropic-kaos.md` — Análisis de errores y oportunidades
