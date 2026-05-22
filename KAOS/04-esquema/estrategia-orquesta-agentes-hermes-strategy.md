---
type: strategy
title: 'Estrategia: Code Agent, Orquesta DAG + Integracion Hermes'
aliases:
- estrategia-orquesta-agentes-hermes-strategy
tags:
- strategy
- multi-agent
- orchestration
- code-agent
- hermes
- langgraph
- a2a
- mcp
- roadmap
- strategic-planning
created: 2026-05-21
modified: '2026-05-21'
confidence: media
status: draft
agent: metis
---

# Estrategia: Code Agent, Orquesta DAG + Integracion Hermes

> *Basada en la investigacion de Aletheia: `raw/investigacion-orquesta-agentes-hermes.md` (78+ fuentes, 4 batches Deep Research)*

---

## Resumen Ejecutivo

KAOS debe evolucionar de su pipeline lineal actual (Aletheia -> Kosmos -> Metis -> Mnemosyne) a una **arquitectura DAG multi-agente** con orquestacion stateful, un Code Agent como 5o especialista con memoria procedural, y Hermes Agent como gateway de comunicacion multiplataforma. La investigacion confirma que LangGraph es el orquestador optimo (9% token overhead, 96% error recovery, checkpointing nativo), Hermes v0.14.0 aporta Kanban durable y MCP bidireccional, y APEX-EM ofrece +48pp de mejora en generacion de codigo mediante memoria procedural. Este plan entrega un roadmap de 6 meses con 3 horizontes, OKRs medibles, y acciones concretas dia por dia para la primera semana.

**Recomendacion principal**: Implementar en paralelo (a) Code Agent como agente OpenCode nativo en semana 1-2, (b) LangGraph Orchestrator como reemplazo del pipeline lineal en semana 2-4, (c) Hermes Gateway como capa de comunicacion externa en mes 2-3. No intentar los 3 simultaneamente - secuenciar con superposicion controlada.

---

## 1. Diagnostico Estrategico

### 1.1 Analisis FODA

#### Fortalezas (Internas)
| # | Fortaleza | Detalle |
|---|-----------|---------|
| F1 | **Pipeline funcional** | Pipeline 4-agentes probado con smoke test PASS, context.json funcional |
| F2 | **Memoria vectorial madura** | sqlite-vec con 161 paginas, 3610 chunks, embeddings unificados, synapse cross-linking |
| F3 | **Infraestructura MCP robusta** | 18 MCPs activos con per-agent restriction, arquitectura probada |
| F4 | **Sistema de calidad operando** | Scores 5-dimensiones, perfiles de evaluacion, cadena de verificacion cruzada |
| F5 | **Vault Obsidian como UI rica** | 180+ conceptos wiki, 21 raw investigations, distill pipeline funcional |
| F6 | **Equipo multi-agente diferenciado** | 4 agentes especializados con skills y personalidades definidas |
| F7 | **Base de ADRs solida** | 10 ADRs documentando decisiones arquitectonicas clave |

#### Oportunidades (Externas)
| # | Oportunidad | Detalle |
|---|-------------|---------|
| O1 | **LangGraph v1.0 maduro** | 126K+ estrellas, estandar de facto en produccion, checkpointing nativo, LangSmith |
| O2 | **Hermes v0.14.0 Kanban** | Sistema Kanban SQLite-backed para colaboracion multi-perfil durable - resuelve el problema de estado compartido entre agentes |
| O3 | **APEX-EM memoria procedural** | +48pp en benchmarks de codigo - directamente aplicable al Code Agent |
| O4 | **A2A v1.0 bajo Linux Foundation** | Protocolo inter-agente estandarizado, soporte Go SDK, open source |
| O5 | **Ecosistema de agentes de codigo** | AtomCode (Rust, MCP), memori (FTS5+vector), tree-sitter (AST multi-lenguaje) |
| O6 | **SleepGate + Agenternal** | Consolidacion de memoria inspirada en sueno con compresion 2,000,000:1 |
| O7 | **OpenAgents unico con MCP+A2A** | Framework de referencia para interoperabilidad nativa |

#### Debilidades (Internas)
| # | Debilidad | Detalle |
|---|-----------|---------|
| D1 | **Pipeline lineal secuencial** | Sin paralelismo, sin DAG, sin orquestacion stateful - cuello de botella en produccion |
| D2 | **Sin Code Agent** | No hay capacidad de generacion, revision o reparacion de codigo dentro del ecosistema KAOS |
| D3 | **Sin comunicacion externa** | No hay gateway para usuarios externos (Telegram, Discord, CLI) - KAOS solo existe dentro de OpenCode |
| D4 | **Sin memoria experiencial** | No hay captura de errores, soluciones previas ni reutilizacion procedural entre sesiones |
| D5 | **Sin observabilidad unificada** | No hay tracing, metricas de rendimiento ni dashboards de operacion multi-agente |
| D6 | **Sin A2A readiness** | No hay Agent Cards, task lifecycle ni comunicacion inter-agente estandarizada |

#### Amenazas (Externas)
| # | Amenaza | Detalle |
|---|---------|---------|
| A1 | **Ritmo de cambio tecnologico** | MCP, A2A, frameworks evolucionan trimestralmente - riesgo de invertir en tecnologia que cambia |
| A2 | **Complejidad de integracion** | 3 sistemas nuevos (Code Agent, LangGraph, Hermes) incrementan riesgo de fallo de integracion |
| A3 | **OpenAI sin soporte A2A** | Holdout de OpenAI en A2A puede fragmentar el ecosistema de interoperabilidad |
| A4 | **Costos de LLM** | Orquestacion multi-agente incrementa consumo de tokens - LangGraph mitiga (9% overhead) pero aun asi escala |
| A5 | **Dependencia de Hermes Agent** | Proyecto open source de Nous Research - riesgo de cambio de direccion o mantenimiento |

### 1.2 Los 3 Desafios Principales

1. **Migrar del pipeline lineal al DAG sin romper la operacion existente** - El pipeline actual funciona y tiene tests pasando. La migracion debe ser transparente: envolver el pipeline actual como un subgraph de LangGraph, luego refactorizar progresivamente. Riesgo: tiempo de inactividad, perdida de estado.

2. **Disenar la memoria procedural del Code Agent sin sobrecarga arquitectonica** - APEX-EM promete +48pp pero requiere PRGII workflow + dual-outcome memory + triple retrieval (semantico + AST + DAG). El riesgo es construir algo demasiado complejo que nunca se termine. Solucion: MVP con FTS5 + vector search primero, AST y DAG despues.

3. **Integrar Hermes como gateway manteniendo KAOS autocontenido** - Hermes necesita correr como proceso separado, con su propia base de datos Kanban. La integracion no debe crear dependencia externa que comprometa la operacion local de KAOS en OpenCode.

### 1.3 Las 3 Oportunidades Principales

1. **Code Agent como el agente de mayor impacto** - Con APEX-EM mejorando +48pp en benchmarks, un Code Agent no es un lujo: es la capacidad que mas valor agrega al ecosistema KAOS. Puede revisar codigo existente, generar nuevo, y autocorregirse.

2. **Hermes Kanban como el sistema de coordinacion multi-agente que KAOS necesita** - El Kanban de Hermes resuelve exactamente el problema que KAOS tiene hoy: estado compartido entre agentes. Cada agente puede leer/escribir tickets, ver que hacen los otros, y reanudar tareas interrumpidas.

3. **LangGraph como habilitador de patrones avanzados** - Con LangGraph, KAOS puede implementar evaluator-optimizer loops, routing condicional, parallel fan-out, y humano-en-el-bucle - patrones imposibles con el pipeline lineal actual.

---

## 2. Vision Arquitectonica

### 2.1 Frase Vision

> **KAOS sera un sistema multi-agente DAG con orquestacion stateful, memoria procedural experiencial y gateway multiplataforma, donde agentes especializados colaboran en paralelo bajo un orquestador determinista que nunca ejecuta trabajo - solo descompone, delega, monitorea y sintetiza.**

### 2.2 Diagrama de Arquitectura Objetivo

```
+------------------------------------------------------------------+
|                        USERS / EXTERNAL                          |
|    (Telegram - Discord - Slack - CLI - Web - Email)              |
+-----------------------------+------------------------------------+
                              |
+-----------------------------v------------------------------------+
|                    HERMES GATEWAY (v0.14+)                        |
|  +------------------------------------------------------------+  |
|  |  - 22+ plataformas unificadas                              |  |
|  |  - Kanban SQLite-backed (triage-todo-ready-running-done)   |  |
|  |  - MCP Server (expone tools de KAOS a externos)            |  |
|  |  - MCP Client (consume tools de LangGraph y agentes)       |  |
|  |  - Cron scheduler en lenguaje natural                      |  |
|  |  - Human-in-the-loop via kanban_comment                    |  |
|  +------------------------------------------------------------+  |
+-----------------------------+------------------------------------+
                              | A2A / MCP / ACP
                              |
+-----------------------------v------------------------------------+
|                    LANGGRAPH ORCHESTRATOR (v1.0)                  |
|  +------------------------------------------------------------+  |
|  |  - Stateful graph con checkpointing nativo                 |  |
|  |  - LangSmith tracing + observabilidad                     |  |
|  |  - Output contracts JSON por agente                       |  |
|  |  - Token budget enforcement + limites duros               |  |
|  |  - Human-in-the-loop interrupts                           |  |
|  |  - Evaluator-optimizer loop (max 3 reintentos)           |  |
|  |  - Subgraph pipeline KAOS legacy (retrocompatibilidad)    |  |
|  +------------------------------------------------------------+  |
+------+--------------+--------------+--------------+--------------+
       |              |              |              |
       v              v              v              v
+-------------+ +-----------+ +-----------+ +------------------+
| ALETHEIA    | |  KOSMOS   | |  METIS    | |   CODE AGENT *   |
| (Research)  | |(Arquitect)| |(Estrate.) | |   (Nuevo 5o)     |
|             | |           | |           | |                   |
| - web_search| | - analyze | | - analyze | | - APEX-EM PRGII   |
| - synthesize| | - C4      | | - OKRs    | | - memori (FTS5)   |
| - triangul. | | - ADRs    | | - Paper   | | - AST tree-sitter |
|             | |           | | - RRR     | | - Bandit LinUCB   |
| 15 steps    | | 10 steps  | | 8 steps   | | - Hermes Kanban   |
| temp 0.3    | | temp 0.1  | | temp 0.4  | | - test/repair     |
+-------------+ +-----------+ +-----------+ | - error capture   |
       |              |              |       +------------------+
       |              |              |                |
       +--------------+--------------+----------------+
                              |
                   +----------v-----------+
                   |  MNEMOSYNE (6o)      |
                   |  Curacion + Sleep    |
                   | - Consolidacion L0-L3|
                   | - Agenternal sleep   |
                   | - Compresion 2M:1   |
                   | - Poda periodica    |
                   +---------------------+
                              |
                   +----------v--------------------------------------+
                   |         INFRAESTRUCTURA COMPARTIDA               |
                   |  +----------+ +----------+ +-----------------+  |
                   |  | sqlite-vec| |   MCP    | | Vault Obsidian  |  |
                   |  | 3610 chk | | 18 srv.  | | 180+ conceptos  |  |
                   |  +----------+ +----------+ +-----------------+  |
                   |  +----------+ +----------+ +-----------------+  |
                   |  | LangSmith| | Hermes   | | Kanban DB       |  |
                   |  | Tracing  | | Kanban   | | SQLite (WAL)    |  |
                   |  +----------+ +----------+ +-----------------+  |
                   +------------------------------------------------+
```

### 2.3 Principios Arquitectonicos

1. **Orquestador nunca ejecuta trabajo** - Solo descompone, delega, monitorea, sintetiza
2. **Output contracts antes de construir agentes** - Schema JSON definido para comunicacion entre nodos
3. **Tool discipline** - Cada agente tiene solo las MCPs de su rol
4. **Diseno para fallo** - Checkpointing, reclaim de tareas, failure modes definidos
5. **Compaction strategy** - Al 70-80% de contexto, resumir interacciones previas
6. **Limites duros** - Budget de tokens, tiempo de ejecucion, reintentos maximos (3)

---

## 3. Roadmap de Implementacion

### H1 - Tactico (Semanas 1-4): Fundacion

**Objetivo**: Code Agent operativo + LangGraph reemplazando pipeline lineal + memoria experiencial basica

| Semana | Code Agent (5o) | LangGraph Orchestrator | Hermes Gateway | Memoria |
|--------|----------------|----------------------|----------------|---------|
| **S1** | - MVP agente OpenCode con tools basicas | - Setup LangGraph + checkpointing SQLite | - Instalar Hermes v0.14+ local | - FTS5 error capture |
| | - Config en opencode.json como 5o agente | - Wrapper pipeline lineal como subgraph | - kanban_create funcional | - Schema exitos/fallos |
| **S2** | - Integracion memori (FTS5 + vector) | - Migracion Aletheia-Kosmos-Metis como DAG | - delegate_task Hermes a LangGraph | - PRGII Plan-Retrieve |
| | - dual-outcome capture | - LangSmith tracing basico | - kanban_list + kanban_complete | - Hybrid retrieval S1 |
| **S3** | - PRGII workflow completo | - Routing condicional | - MCP server Hermes | - AST signature matching |
| | - tree-sitter 3 lenguajes | - Token budget por tarea | - kanban_comment HITL | - FTS5 + vector RRF |
| **S4** | - Code Agent test/repair loop | - Evaluator-optimizer loop | - MCP client Hermes | - Error rate tracking |
| | - smoke test + perfil evaluacion | - Smoke test pipeline DAG | - CRON scheduler basico | - Baseline pre-sleep |

### H2 - Estrategico (Meses 2-3): Escalamiento

**Objetivo**: Hermes como gateway completo + Kanban multi-agente durable + pipeline de consolidacion

| Mes | Code Agent | LangGraph | Hermes | Memoria |
|-----|-----------|-----------|--------|---------|
| **M2** | - Bandit LinUCB | - Parallel fan-out | - Gateway Telegram | - Agenternal sleep v0.1 |
| | - 9 lenguajes tree-sitter | - HITL con interrupts | - Gateway Discord | - DBSCAN clustering |
| | - Memoria cross-sesion | - LangSmith dashboards | - Gateway CLI | - Compresion 10:1 |
| **M3** | - Contextual bandit prod | - A2A Agent Cards | - MCP bidireccional | - Reconsolidacion activa |
| | - Code review multi-agente | - Budget enforcement | - 5+ plataformas | - Poda semanal |
| | - Auto-deploy git | - Error recovery 96% | - OMH skills | - Sleep consolidation |

### H3 - Vision (Meses 4-6): Evolucion

**Objetivo**: Auto-evolucion, federacion, sleep cycles completos

| Mes | Code Agent | LangGraph | Hermes | Memoria |
|-----|-----------|-----------|--------|---------|
| **M4** | - Auto-generacion skills | - Federacion multi-instancia | - Quality-gated delegation | - NREM consolidation |
| | - Optimizacion bandit | - Subgraph composable | - Acceptance criteria | - REM dreaming |
| **M5** | - Code Agent autonomo | - Dynamic routing carga | - A2A nativo gateway | - SleepGate tagger |
| | - SWE-bench evaluation | - Costo optimizado | - Federacion Hermes | - Forgetting gate |
| **M6** | - Code Agent orquestador | - Auto-evolucion grafo | - 10+ plataformas | - Sleep cycle completo |
| | - Benchmark OpenCode | - Self-healing grafo | - Full OMH suite | - Memory matrix L0-L3 |

---

## 4. OKRs

### Objetivo Estrategico 1: Sistema Multi-Agente DAG con Orquestacion Stateful

> *Migrar del pipeline lineal a una orquestacion DAG stateful con LangGraph, manteniendo 100% de funcionalidad existente y mejorando el throughput en 3x.*

| Key Result | Linea Base | Target H1 | Target H2 | Target H3 | Dueno |
|-----------|-----------|-----------|-----------|-----------|-------|
| KR1.1: Pipeline DAG operativo | Pipeline lineal 4 pasos | DAG funcional 5 agentes (S4) | Routing condicional + fan-out | Subgraph + federacion | Kosmos + Metis |
| KR1.2: Throughput (tareas/hora) | ~1 tarea/secuencial | 3 tareas/hora | 8 tareas/hora | 15+ tareas/hora | Metis |
| KR1.3: Token overhead pipeline | ~40% (estimado) | <=15% | <=10% | <=8% | Kosmos |
| KR1.4: Error recovery rate | ~70% (sin checkpoint) | >=85% | >=92% | >=96% | Kosmos |

### Objetivo Estrategico 2: Code Agent con Memoria Procedural y Gateway Externo

> *Construir un Code Agent como 5o especialista con memoria procedural APEX-EM (+20pp mejora en precision de codigo) e integrar Hermes como gateway multiplataforma.*

| Key Result | Linea Base | Target H1 | Target H2 | Target H3 | Dueno |
|-----------|-----------|-----------|-----------|-----------|-------|
| KR2.1: Code Agent operativo | No existe | MVP (S2): read/write + FTS5 | PRGII completo + 9 lenguajes | Bandit LinUCB + auto-skills | Metis + Kosmos |
| KR2.2: Mejora precision codigo | 0% | +10pp tareas simples | +25pp tareas complejas | +35pp benchmark interno | Metis |
| KR2.3: Plataformas externas | 0 (solo OpenCode) | 1 (CLI) | 3 (CLI + Telegram + Discord) | 6+ plataformas | Metis |
| KR2.4: Memoria cross-sesion | 0 capturas | 50+ experiencias | 500+ con AST tagging | 2000+ con sleep | Mnemosyne |

### Seguimiento de Progreso

| KR | S1 | S2 | S3 | S4 | M2 | M3 | M4 | M5 | M6 |
|----|----|----|----|----|----|----|----|----|----|
| KR1.1 | 20% | 40% | 70% | 100% | 100% | 100% | 100% | 100% | 100% |
| KR1.2 | 1/h | 1.5/h | 2/h | 3/h | 5/h | 8/h | 10/h | 12/h | 15/h |
| KR1.3 | 40% | 30% | 20% | 15% | 12% | 10% | 9% | 8.5% | 8% |
| KR1.4 | 70% | 75% | 80% | 85% | 88% | 92% | 94% | 95% | 96% |
| KR2.1 | 30% | 60% | 85% | 100% | 100% | 100% | 100% | 100% | 100% |
| KR2.2 | 0% | +5pp | +8pp | +10pp | +15pp | +20pp | +25pp | +30pp | +35pp |
| KR2.3 | 0 | 0 | 0 | 1 | 2 | 3 | 4 | 5 | 6 |
| KR2.4 | 0 | 20 | 50 | 100 | 250 | 500 | 1000 | 1500 | 2000 |

---

## 5. Riesgos y Mitigaciones

| # | Riesgo | Prob (1-5) | Impacto (1-5) | Severidad | Mitigacion | Contingencia |
|---|--------|-----------|--------------|-----------|------------|--------------|
| R1 | **Code Agent demasiado complejo para H1**: APEX-EM + tree-sitter + bandit en 4 semanas | 4 (Alta) | 4 (Alto) | **16 - Critico** | Scope reduction: S1-S2 solo MVP basico (read/write + FTS5). PRGII y bandit a H2 | Si S2 <60%, posponer AST a H2 |
| R2 | **Migracion pipeline a DAG rompe operacion**: Smoke test pasa hoy | 3 (Media) | 5 (Alto) | **15 - Critico** | Wrapper retrocompatibilidad: subgraph legacy envuelve pipeline actual | Mantener pipeline lineal paralelo 1 semana |
| R3 | **Hermes compite con recursos KAOS**: Proceso separado + DB propia | 3 (Media) | 3 (Medio) | **9 - Alto** | Hermes lightweight (solo kanban + MCP, sin TUI) | Mover a Docker si >500MB RAM |
| R4 | **Costos LLM escalan**: Overhead 9% pero volumen crece | 3 (Media) | 3 (Medio) | **9 - Alto** | Budget enforcement por tarea desde dia 1 | DeepSeek para tareas no criticas |
| R5 | **Falta de adopcion del equipo**: Agentes a nuevo flujo DAG | 2 (Baja) | 4 (Alto) | **8 - Alto** | Migracion gradual: DAG paralelo 2 semanas | Mantener pipeline lineal 1 mes |

---

## 6. Proximos Pasos - Semana 1 Dia por Dia

### Dia 1: Fundacion Code Agent

**AM:**
- [ ] Crear agente "code" en opencode.json: name:code, type:subagent, steps:10, temperature:0.2, color:#00BFA5, tools:[vault,sequential-thinking,git,excalidraw]
- [ ] Configurar MCPs para Code Agent (vault + seq-thinking + git + excalidraw)

**PM:**
- [ ] Crear .memory/wiki/entities/code.md con frontmatter (type:agent, status:draft, capabilities:[code-generation,code-review,memory-procedural])
- [ ] Smoke test: agente responde, tools funcionales
- [ ] Crear perfil "code" en eval-profile.yaml

### Dia 2: Memoria Experiencial Basica (FTS5)

**AM:**
- [ ] Schema procedural_memory: id, task_hash, task_desc, plan, code, outcome, error_msg, language, tags, timestamp, success BOOL
- [ ] Indice FTS5 sobre task_desc + plan + code + error_msg
- [ ] Hook post_output: capturar errores en tool calls

**PM:**
- [ ] Retrieval: FTS5 MATCH -> top 5 similares, fallback a busqueda por lenguaje
- [ ] Test: 3 tareas con errores forzados, verificar captura

### Dia 3: LangGraph Setup + Pipeline Wrapper

**AM:**
- [ ] pip install langgraph langgraph-checkpoint langsmith
- [ ] Configurar checkpoint SQLite
- [ ] Wrapper graph: aletheia_node -> kosmos_node -> metis_node -> mnemosyne_node

**PM:**
- [ ] Smoke test wrapper DAG: mismo input/output que pipeline lineal
- [ ] Verificar checkpointing (reanudar desde nodo intermedio)
- [ ] Configurar LangSmith tracing basico

### Dia 4: Integracion Code Agent + LangGraph

**AM:**
- [ ] Routing condicional: si tarea contiene keywords de codigo -> Code Agent
- [ ] Code Agent como nodo LangGraph

**PM:**
- [ ] PRGII S1 (Plan -> Retrieve): LLM descompone tarea -> FTS5 query por experiencia previa
- [ ] Test: tarea con experiencia previa -> mejora medible

### Dia 5: Hermes Setup Inicial

**AM:**
- [ ] pip install hermes-agent; hermes init
- [ ] Verificar kanban create/list/show funcional
- [ ] hermes mcp serve --port 8100

**PM:**
- [ ] Integrar Kanban con LangGraph: al iniciar tarea -> kanban_create, al procesar -> kanban_list, al completar -> kanban_complete
- [ ] Test: tarea end-to-end via Kanban

### Dia 6: Integracion y Test Cross-Agent

**AM:**
- [ ] PRGII S2 (Generate -> Iterate): Generate con contexto -> test -> repair loop (max 3) -> Ingest como exito o fallo

**PM:**
- [ ] Test cross-agent completo: Aletheia -> Kosmos -> Code Agent -> Metis
- [ ] Verificar Kanban refleja cada paso
- [ ] Smoke test: Pipeline DAG PASS, Code Agent PASS, Hermes Kanban PASS

### Dia 7: Buffer + Documentacion + OKR Review

**AM:**
- [ ] Buffer para bugs, ajustes, issues de integracion
- [ ] ADR-009: Code Agent Architecture
- [ ] ADR-010: LangGraph Orchestration Migration
- [ ] ADR-011: Hermes Integration Strategy

**PM:**
- [ ] Revision OKRs H1: KR2.1 progreso 30%+? KR1.1 wrapper funcional? KR2.4 50 experiencias?
- [ ] Actualizar dashboard de calidad: score compuesto, alertas
- [ ] Preparar reporte de semana 1

### Indicadores de Exito - Semana 1

| Indicador | Target | Como medirlo |
|-----------|--------|-------------|
| Code Agent responde | SI | /code "hello world" -> genera codigo |
| Memoria experiencial captura | SI | Error forzado -> capturado en FTS5 |
| Pipeline DAG wrapper | SI | Mismo input/output que pipeline lineal |
| LangGraph checkpointing | SI | Reanudar desde nodo intermedio |
| Hermes Kanban operativo | SI | kanban_create -> kanban_complete |
| Smoke test global | SI | Todos los tests PASS |

---

## 7. Stack Tecnologico Recomendado

| Capa | Tecnologia | Version | Justificacion |
|------|-----------|---------|---------------|
| **Orquestador** | LangGraph | v1.0+ | 9% overhead, checkpointing, LangSmith |
| **Gateway** | Hermes Agent | v0.14+ | 22+ plataformas, MCP bidireccional, Kanban |
| **Code Agent** | OpenCode subagent | N/A | Nativo en ecosistema |
| **Memoria codigo** | memori-inspired | Custom | SQLite FTS5 + all-MiniLM-L6-v2 (384d) + RRF |
| **AST parsing** | tree-sitter | Latest | 9+ lenguajes, WASM |
| **Memoria procedural** | APEX-EM PRGII | Custom | Dual-outcome, Plan-Retrieve-Generate-Iterate-Ingest |
| **Contextual bandit** | LinUCB (custom) | Custom | Seleccion adaptativa estrategia |
| **Protocolo inter-agente** | A2A v1.0 | GA Mar 2026 | Linux Foundation, SDK Go |
| **Protocolo herramienta** | MCP | Latest | Estandar industria |
| **Consolidacion** | Agenternal/SleepGate | Custom | Compresion 2M:1 |
| **Observabilidad** | LangSmith + OTel | Latest | Tracing, debugging |
| **Memoria vectorial** | sqlite-vec | Existente | 161 paginas, 3610 chunks |

---

## 8. Conclusiones

### Resumen de la Estrategia

1. **Code Agent es la prioridad tactica** - En 4 semanas tenemos un 5o agente funcional con memoria experiencial FTS5, PRGII basico y test/repair loop.

2. **LangGraph es el habilitador estructural** - Reemplazar pipeline lineal por DAG stateful desbloquea paralelismo, routing, HITL y checkpointing. Wrapper legacy minimiza riesgo.

3. **Hermes es la puerta al mundo exterior** - Kanban resuelve estado compartido entre agentes. MCP bidireccional permite exportar/importar capacidades.

4. **El orden importa: Code Agent -> LangGraph -> Hermes** - Secuencia maximiza valor temprano mientras construye infraestructura.

5. **Sleep cycles de Mnemosyne son el diferenciador Largo Plazo** - Compresion 2,000,000:1 y 99.5% retrieval accuracy son targets ambiciosos pero alcanzables para H3.

### Costo Estimado

| Horizonte | Esfuerzo | Riesgo | Valor |
|-----------|---------|--------|-------|
| H1 (S1-S4) | ~28 dias-hombre | Alto | Code Agent + DAG MVP |
| H2 (M2-M3) | ~40 dias-hombre | Medio | Gateways + Kanban + Sleep v0.1 |
| H3 (M4-M6) | ~50 dias-hombre | Bajo | Auto-evolucion + Federacion |
| **Total** | **~118 dias-hombre** | **Medio** | **Sistema multi-agente completo** |

### Proximo Paso Inmediato

> **Comenzar Dia 1**: Crear agente "code" en opencode.json, configurar MCPs, crear entity page, smoke test.

---

## Apendices

### A. Referencias Cruzadas

| Documento | Relacion |
|-----------|---------|
| `raw/investigacion-orquesta-agentes-hermes.md` | Investigacion base (78+ fuentes) |
| `schema/KAOS.md` | Reglas del vault, agentes, MCPs |
| `schema/adr-001-sistema-memoria.md` | Arquitectura de memoria existente |
| `schema/adr-005-vector-store.md` | sqlite-vec como vector store |
| `schema/adr-006-sleep-time-compute.md` | Sleep-time compute |
| `schema/adr-007-optimizacion-arquitectura.md` | MCPs, pipeline |
| `schema/adr-008-plugin-decision.md` | Plugin decisions |
| `schema/health-report.md` | Salud del vault |
| `wiki/entities/aletheia.md` | Entity Aletheia |
| `wiki/entities/kosmos.md` | Entity Kosmos |
| `wiki/entities/metis.md` | Entity Metis |
| `wiki/entities/mnemosyne.md` | Entity Mnemosyne |

### B. ADRs a Crear

| ADR | Titulo | Semana | Dueno |
|-----|--------|--------|-------|
| ADR-009 | Code Agent Architecture | S1 | Kosmos |
| ADR-010 | LangGraph Orchestration Migration | S2 | Kosmos |
| ADR-011 | Hermes Integration Strategy | S3 | Kosmos |
| ADR-012 | APEX-EM Procedural Memory | S4 | Kosmos |

### C. Skills a Crear/Modificar

| Skill | Tipo | Semana |
|-------|------|--------|
| `metis` - actualizar con Code Agent | Modificar | S1 |
| `mnemosyne` - actualizar sleep cycles | Modificar | M2 |
| `code` (nuevo skill) | Nuevo | S1 |
| `omh-code-review` (contribucion OMH) | Nuevo | M3 |
| `omh-deploy` (contribucion OMH) | Nuevo | M3 |

### D. Glosario

| Termino | Definicion |
|---------|-----------|
| **PRGII** | Plan -> Retrieve -> Generate -> Iterate -> Ingest (APEX-EM) |
| **Dual-outcome memory** | Exitos (+ejemplos) y fallos (-anotaciones) |
| **RRF** | Reciprocal Rank Fusion - BM25 + vector |
| **DAG** | Directed Acyclic Graph |
| **HITL** | Human-in-the-loop |
| **Kanban** | Tickets SQLite con columnas de estado |
| **Agent Card** | Descripcion de capacidades (A2A) |
| **Sleep cycle** | Consolidacion de memoria biologica |
| **LinUCB** | Linear Upper Confidence Bound |
| **MoME** | Mixture of Memory Experts |

---

*Estrategia desarrollada por Metis el 2026-05-21.*
*Basada en investigacion de Aletheia (78+ fuentes, 4 batches Deep Research).*
*Validacion arquitectonica: Kosmos (pendiente).*
*Proxima revision: 2026-05-28 (semana 1 completa).*
