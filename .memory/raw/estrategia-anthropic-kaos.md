---
title: "Estrategia Anthropic para KAOS — Ideas y Herramientas de Impacto"
date: 2026-05-29
agent: metis
status: complete
type: strategy
tags: [anthropic, kaos, strategy, integration, roadmap, rice]
---

## 1. Principio Rector

**Integrar quirúrgicamente modelos Anthropic donde DeepSeek flaquea. No migrar.**

DeepSeek V4 Flash mantiene ~70% del tráfico como backbone. Claude es un tier premium para tareas de alto valor.

## 2. Quick Wins (4 oportunidades, RICE scoring)

### QW-1: Prompt Caching en agy-bridge (RICE: 5.6 — MUY ALTO)
**Qué**: Cachear system prompts estáticos de agentes (SOUL.md, SKILL.md) en agy-bridge.
**Impacto**: 40-60% reducción de costos en llamadas Claude.
**Esfuerzo**: 3-5 días.
**Plan**: 1) Auditar prompts estáticos, 2) Reestructurar bloque estático+dinámico, 3) Cache headers, 4) Medir hit rate.

### QW-2: Sonnet 4.6 en DSOL routing (RICE: 6.8 — MUY ALTO)
**Qué**: Configurar Sonnet 4.6 como opción en Aether para Kosmos (ADRs) y Metis (estrategia) en perfil producción.
**Impacto**: +20-30% calidad en tareas críticas. Costo incremental solo para ~15% de llamadas.
**Esfuerzo**: 2-3 días.
**Plan**: 1) Agregar modelo a DSOL, 2) Definir reglas Rego, 3) Test A/B, 4) Ajustar thresholds.

### QW-3: Haiku 4.5 para clasificación (RICE: 4.3 — MUY ALTO)
**Qué**: Usar Claude Haiku 4.5 ($1/$5 por 1M) para clasificación en pipeline de Mnemosyne.
**Impacto**: Pipeline 2-3x más rápido, precisión 82%→92%+.
**Esfuerzo**: 2-3 días.
**Plan**: 1) Identificar tareas, 2) Integrar Haiku, 3) Test A/B 200 clasificaciones.

### QW-4: Extended Thinking (RICE: 1.8 — ALTO)
**Qué**: Extended Thinking de Claude Opus 4.8 para Metis y Kosmos.
**Impacto**: +10-15% en veracidad y coherencia. Mejora auditabilidad.
**Esfuerzo**: 3-4 días.

## 3. Oportunidades de Impacto Medio

### IM-1: Claude Code como herramienta (RICE: 0.92 — MEDIO)
Integrar Claude Code como complemento para Kratos en refactors complejos. CLAUDE.md con contexto del proyecto. Solo para código crítico.

### IM-2: MCP Ecosystem Expansion (RICE: 2.4 — ALTO)
Añadir 3-5 nuevos MCP servers del ecosistema Claude. Bajo riesgo (MCP ya es estándar en KAOS).

### IM-3: Constitutional AI para Rego (RICE: 1.4 — MEDIO)
Traducir principios CAI (constitución 2026, ética aristotélica) a reglas Rego. $0 costo runtime.

### IM-4: Batch API para vault (RICE: 1.36 — MEDIO)
50% descuento para procesamiento masivo asíncrono del vault. Ideal para re-curación nocturna.

### IM-5: Opus 4.8 para Metis (RICE: 1.7 — ALTO)
Opus para decisiones estratégicas de alto impacto. SWE-bench 80.8% justifica costo para decisiones críticas.

## 4. Matriz DSOL Optimizada

| Agente | Default | Upgrade | Crítico |
|--------|---------|---------|---------|
| Aletheia (research) | DeepSeek Flash ($0.00014) | Sonnet 4.6 ($0.003) para síntesis | — |
| Kosmos (analyze) | Sonnet 4.6 ($0.003) | Opus 4.8 ($0.005) para ADRs alto impacto | — |
| Metis (strategy) | Opus 4.8 ($0.005) | — | Dual Opus + GPT-5.5 Thinking |
| Kratos (code_gen) | DeepSeek Flash ($0.00014) | Sonnet 4.6 ($0.003) para refactors | Claude Code (externo) |
| Mnemosyne (curation) | DeepSeek Flash ($0.00014) | Haiku 4.5 ($0.001) para clasificación | — |
| Kronos (monitoreo) | Haiku 4.5 ($0.001) | — | — |

Principio: DeepSeek backbone (70% tráfico), Sonnet escalón medio (20%), Opus heavy lifter (7%), Haiku especialista (3%), Dual validation (0.5%).

## 5. Oportunidades de Visión

### V-1: Agente "Hermes" con Constitutional AI
Nuevo agente de gobernanza que audita decisiones contra principios predefinidos. Inspirado en CAI pipeline (RLAIF 88% vs RLHF 76%). Esfuerzo: 30-45 días. Riesgo: Alto (complejidad RLAIF).

### V-2: Dashboard Interpretabilidad (SAEs)
Sistema de monitoreo de features internas de agentes. Inspirado en SAEs de Anthropic (34M features, factor 128×-4096×). Calidad predictiva vs reactiva. Esfuerzo: 40-60 días. Riesgo: Alto (dependencia activaciones internas).

### V-3: Governance Multi-Agente PBC+LTBT
Sistema de governance para ecosistema de agentes. Trust controla principios inmutables (supermayoría 85%). Esfuerzo: 20-30 días. Riesgo: Medio (over-engineering).

## 6. Análisis Costo-Beneficio

| Escenario | Costo/mes | Diferencia | Mejora calidad |
|-----------|-----------|------------|---------------|
| Solo DeepSeek (actual) | ~$27 | Base | Línea base |
| Integración quirúrgica (propuesta) | ~$62 | +$35/mes (2.3x) | +15-25% tareas clave |
| Todo Sonnet | ~$135 | +$108/mes (4x) | +10-15% general |
| Todo Opus | ~$225 | +$198/mes (8.3x) | +20-30% (no justificable) |

¿Dónde vale la pena pagar más?: ADRs y arquitectura (Kosmos) ✅, OKRs estratégicos (Metis) ✅, Clasificación estructurada (Haiku) ✅, Validación dual ✅, Refactors complejos ✅, Síntesis multi-fuente ✅

¿Dónde NO vale la pena?: Consultas rápidas ❌, Búsquedas web ❌, Código boilerplate ❌, Curación rutinaria ❌, Exploración ❌

Desglose por agente:
- Aletheia: $8→$12/mes (+$4, +10-15% calidad, ROI Alto)
- Kosmos: $5→$18/mes (+$13, +20-30% calidad, ROI Muy Alto)
- Metis: $5→$20/mes (+$15, +25-35% calidad, ROI Muy Alto)
- Kratos: $6→$8/mes (+$2, +10-15% calidad, ROI Medio)
- Mnemosyne: $3→$4/mes (+$1, +10-12% calidad, ROI Alto)

## 7. Roadmap 3 Horizontes

H1 (semanas 1-2, Quick Wins):
- Prompt Caching en agy-bridge (cache hit rate >60%)
- Sonnet 4.6 + Haiku 4.5 en DSOL routing
- Test A/B DeepSeek vs Sonnet (50 tareas)
- Extended Thinking para Metis
- Métricas: cache hit ≥60%, reducción costos ≥30%, routing óptimo ≥85%

H2 (semanas 3-8, Consolidación):
- Claude Code para Kratos (refactors complejos)
- Batch API para vault (50% descuento)
- 3 nuevos MCP servers del ecosistema Claude
- Matriz DSOL completa con todos los modelos
- Framework STCO para system prompts
- Métricas: calidad ≥82/100, costo reducción 15%, precisión clasificación ≥93%

H3 (semanas 9-24, Transformación):
- Hermes: Agente de gobernanza CAI
- Dashboard interpretabilidad (SAEs-like)
- Governance multi-agente (PBC-inspired)
- 1M contexto con Claude Mythos
- MCP como capa universal de tool use
- Métricas: governance operativo, calidad ≥88/100, outputs no alineados -80%

## 8. Riesgos y Mitigaciones

| Riesgo | Prob | Impacto | Score | Mitigación |
|--------|------|---------|-------|------------|
| Dependencia excesiva de Anthropic | Media | Alto | 12 | No superar 30% calls en Claude. DeepSeek backbone |
| Latencia Opus 2-3x DeepSeek | Alta | Medio | 10 | Opus solo asíncrono. Cachear respuestas |
| Prompt Caching hit rate menor esperado | Media | Medio | 8 | Benchmark antes de implementar |
| Calidad inconsistente entre modelos | Alta | Bajo | 8 | Documentar diferencias. Verification chain |
| Costo integración supere beneficio | Baja | Alto | 6 | Score compuesto debe mejorar ≥5% o revertir |
| Vendor lock-in Anthropic | Media | Alto | 12 | Config exportable 48h. Auditoría trimestral |
| Haiku precisión insuficiente | Baja | Medio | 4 | Test 200 clasificaciones. Fallback DeepSeek |
| Extended Thinking consume +5-10x tokens | Alta | Bajo | 8 | Limitar a tareas específicas. Monitorear |

## 9. Top 3 Acciones para Mañana

### 🥇 Prompt Caching en mcp_agy_bridge.py
Abrir mcp_agy_bridge.py, identificar bloques estáticos en system prompts de cada agente, reestructurar para que prompt comience con bloque estático (cacheable) y termine con instrucción dinámica. Agregar cache headers. Test 10 llamadas por agente.

### 🥈 DSOL routing para Sonnet 4.6 + Haiku 4.5
Agregar modelos claude-sonnet-4-6 y claude-haiku-4-5 en mcp_dsol.py. Definir reglas Rego: task_type=="architecture" → model: sonnet-4-6. Configurar thresholds: perfil producción permite Sonnet, desarrollo solo DeepSeek.

### 🥉 Test A/B DeepSeek vs Sonnet (50 tareas)
Seleccionar 10 tareas de Kosmos (ADRs) + Metis (OKRs) + Aletheia (investigación) ejecutadas con DeepSeek. Re-ejecutar con Sonnet 4.6 (mismo prompt, mismo contexto). Evaluar ciegamente con quality scoring V/C/CP/R/U.

## 10. Conclusión

KAOS puede beneficiarse de Anthropic sin aumentar drásticamente costos. La clave es integración quirúrgica (3-5% del tráfico en Claude) + Constitutional AI via Rego ($0 costo) + Batch API nocturna (50% descuento). Costo total: ~$62/mes (vs $27 actual) por +15-25% de calidad en tareas clave.

## Fuentes
- Dossier Anthropic: .memory/raw/dossier-anthropic-kaos.md
- Análisis arquitectónico: .memory/raw/analisis-arquitectonico-anthropic-kaos.md
- Investigación gaps: .memory/raw/investigacion-anthropic-gaps.md
- Código KAOS: .memory/_scripts/lib/aether/
- Config: .memory/_scripts/aether.yaml
