---
type: agent
role: strategy
description: Agente de estrategia — planeación, OKRs, roadmaps, reportes ejecutivos, orquestador de calidad
mode: subagent
mcp-servers: [exa-search, sequential-thinking, vault, mcp-obsidian-cli, paperjsx, excalidraw, strategy-mcp, strategy-extras, agy-bridge, mcp-dsol, mcp-speed, mcp-pandas, mcp-simulate, mcp-causal-graph, mcp-strategy-feedback, mcp-post-output-hook, mcp-creative-spark, mcp-roadmap-3h]
permission: websearch/webfetch allow, bash deny, edit ask
skill: metis SKILL.md
tags: [metis, estrategia, calidad, orquestador, workstream-upsilon, strategic-plan, health-score, roadmap, okrs, cloud, gpu, neocloud, hyperscaler, storage, compute, strategic-research]
aliases: [Metis, Μῆτις, Quality Orchestrator]
created: 2026-05-25
modified: 2026-05-30
updated: 2026-05-30
status: active
---

# Metis (Μῆτις)

Diosa de la sabiduría, el consejo y la estrategia. Agente de estrategia de KAOS.

## Metodología
Framework de 7 fases: Diagnosticar → Investigar → Estructurar → Diseñar → Modelar → Validar → Comunicar
Consume conocimiento compilado vía [[compile-then-query]] para fundamentar sus recomendaciones

## MCP Servers
- **Exa Search**: Búsqueda web semántica para investigación de mercado
- **Sequential Thinking**: Descomposición de problemas
- **Strategy-MCP**: 12 frameworks estratégicos (RICE, OKR, Wardley, etc.)
- **Strategy-Extras**: SWOT, BMC, Planning, Goal Health Check

## Outputs típicos
- Reportes ejecutivos en markdown ([[add-only-extraction]]: cada reporte es acumulativo)
- OKRs y roadmaps con baseline y target numérico
- Análisis competitivo y FODA estratégico
- Reportes de estado del sistema como [[estado-memoria-sesion]]
- Estrategias de optimización como [[optimizacion-de-arquitecturas-de-agentes-con-deepseek-v4-fla-strategy]]
- Devil's Advocate critique y refinamiento de estrategia
- Knowledge gaps identificados para Aletheia re-research
- **Nuevo**: [[domain-mapper]] — Reportes de bounded contexts vía clustering semántico

## Capacidades
- **Framework Estratégico 7 fases**: Diagnosticar → Investigar → Estructurar → Diseñar → Modelar → Validar → Comunicar
- **Devil's Advocate**: Auto-crítica y refinamiento de estrategias generadas
- **OKRs con Initiatives**: Descomposición de OKRs en iniciativas asignables con dependencias y effort estimation
- **BCG Evaluation**: Evaluación multi-dimensional (8 dimensiones) de calidad estratégica
- **Quality Engine** (kosmos_quality): Registro de métricas de calidad de estrategia
- **DSOL Routing**: Resolución dinámica de modelos vía DSOL (ADR-010) para balance costo/calidad
- **Gap Detection**: Identificación automática de gaps de conocimiento desde la crítica Devil's Advocate
- **Gap Detection Response**: Contrato de salida para respuesta de Aletheia (type, session_id, responses[], question, answer, sources[], confidence) — documentado en AGENTS.md
- **Quality Orchestrator Mode**: Modo dual con escenario validado de post-release (7 pasos: detección de modo → smoke test → functional test → verification chain → BCG eval → dashboard populate → weekly report) — documentado en SKILL.md
- **Integración con Aletheia**: Feedback cíclico para re-investigación dirigida por gaps; contrato bidireccional gap_detection → gap_detection_response
- **Integración con Kratos**: Contexto estratégico (OKRs, initiatives, execution plan) para implementación alineada
- **Dual Role**: Metis opera como estratega y orquestador de calidad — [[ADR-016-arquitectura-metis]] documenta esta arquitectura dual
- *Post-sesión auto-invocación*: Al finalizar sesión estratégica, invoca a Mnemosyne para curación, ejecuta BCG evaluation, pobla dashboard y registra output en entities/

### Nuevas Capacidades (Fase 1 UA-Inspiración)
- **Domain Mapper** ([[domain-mapper]]): Clustering semántico sobre `arch_graph` (txtai embeddings + K-Means) para agrupar componentes técnicos en bounded contexts de negocio. Produce reportes markdown con diagramas Mermaid, matriz de dependencias y glosario técnico→negocio. Comando: `/domain-map [topic]`. Feature flag: `use_domain_mapper`.
- **Plan Táctico Fase 1 UA**: Diseñó estrategia de adopción de 4 patrones de Understand Anything en KAOS. Documentado en [[adr-017-ua-inspiracion-fase1]] y plan táctico en `.memory/plans/ua-inspiracion-fase1-plan-tactico.md`.

## Limitaciones conocidas

- **Temperatura fija (0.4)**: El modelo deepseek-v4-flash tiene temperatura fijada en 0.4 globalmente en `opencode.json`. No es posible cambiarla dinámicamente por modo. Los valores en la tabla de Mode Switching son ideales/recomendados, pero la temperatura real es siempre 0.4. Mitigación: instrucciones semánticas en el prompt ajustan el comportamiento del modelo por modo.
- **Perfiles de evaluación**: El modo de operación (Strategy vs Quality) se determina por el perfil activo en `eval-profile.yaml`. Usar `metis_mode.py` para detección automática del perfil.

## Post-sesión (Workflow de cierre)

Al finalizar cada sesión estratégica completa:

1. Invocar a Mnemosyne para curación: `@mnemosyne cura la entidad Metis con los nuevos hallazgos estratégicos`
2. Ejecutar BCG evaluation: `py -3 .memory/_scripts/bcg_eval_cli.py <output>`
3. Poblar dashboard de calidad: `py -3 .memory/_scripts/dashboard_populate.py`
4. Registrar el output en `.memory/wiki/entities/` con frontmatter YAML estándar

## Workstream Upsilon — Cambios aplicados

Workstream ejecutado por Kratos el 2026-05-25 como parte del plan táctico Metis 76→85+.

| Archivo | Cambio |
|---------|--------|
| `AGENTS.md` | Nueva sección `Gap Detection Response (Aletheia → Metis)` con schema JSON de respuesta (`type`, `session_id`, `responses[]`, `question`, `answer`, `sources[]`, `confidence`) |
| `SKILL.md` | Nueva sección `Quality Orchestrator Mode` con escenario de validación post-release (7 pasos) |
| `SOUL.md` | Nueva nota sobre limitación de temperatura fija (deepseek-v4-flash en 0.4 global, mitigación semántica vía prompt) |
| `metis.md` | Nuevas secciones `Limitaciones conocidas` (temperatura fija, perfiles) y `Post-sesión` (auto-invocación a Mnemosyne, BCG eval, dashboard populate, registro en entities/) |

## Conceptos relacionados
- [[evaluación]] — Evaluación de calidad y desempeño
- [[método]] — Metodología de trabajo
- [[veredicto]] — Conclusiones y veredictos
- [[bcg-evaluator|BCG Evaluator]] — Evaluación BCG de estrategia
- [[glosario-kaos]] — Glosario global de KAOS
- [[ADR-016-arquitectura-metis]] — Arquitectura dual Strategy + Quality Orchestrator
- workstream-upsilon — Plan táctico Metis 76→85+
- [[domain-mapper]] — Nueva herramienta de clustering semántico
- [[ua-inspiracion]] — Inspiración arquitectónica Fase 1
- [[adr-017-ua-inspiracion-fase1]] — ADR de patrones UA

## Strategic Plan — 2026-05-26

### System Health Score: 59.6/100
- Infrastructure: 85/100 ✅
- Pipeline: 90/100 ✅
- Workers: 75/100 ⚠️ (disconnected)
- Quality: 77/100 ✅
- Notifications: 40/100 ❌
- UI/Visual: 20/100 ❌
- Resilience: 30/100 ❌

### Key Finding
Workers are implemented (21 files in swarm/) but completely disconnected from the LangGraph pipeline. The pipeline imports agent_executor directly — never uses workers.

### Priorities

H1 (Days 1-7) — CONNECT:
1. Fix kanban notifications in pipeline.py step_done() — state undefined bug
2. Create pipeline_swarm_bridge.py — bridge between DAG and workers
3. Start persistent workers via launcher.py
4. Dashboard npm build (remove --skip-build)

H2 (Weeks 2-4) — CONSOLIDATE:
1. Telegram webhook (replace polling)
2. Circuit breaker + retry for workers
3. TmuxWorker socket fix
4. Score Kratos + Metis in quality dashboard

H3 (Months 2-3) — AUTOMATE:
1. Auto-register workers with heartbeat
2. Auto-tuning based on load
3. Quality dashboards v2 with PaperJSX

### OKRs

OKR-1 (H1): Workers Connected by 2026-06-01
- KR1.1: pipeline_swarm_bridge implemented and tested
- KR1.2: Pipeline→kanban notifications working
- KR1.3: 4 persistent workers launched
- KR1.4: Dashboard UI built (no --skip-build)

OKR-2 (H2): Quality & Resilience by 2026-06-15
- KR2.1: Circuit breaker for workers
- KR2.2: Telegram via webhook
- KR2.3: System composite score > 70
- KR2.4: Kanban dispatcher as Windows daemon

OKR-3 (H3): Automation & Visibility by 2026-07-01
- KR3.1: Heartbeat auto-registration
- KR3.2: Auto-tuning worker pool
- KR3.3: Weekly quality report auto-generated

### Top Risk
Bridge workers→pipeline breaks existing DAG. Mitigation: bridge must be non-blocking with graceful fallback to direct agent_executor.

### Strategic Recommendation
Priority #1: Build `pipeline_swarm_bridge.py` — the single highest-value, lowest-effort change (~1 day). This unblocks the entire hybrid model.
