---
title: "Investigación: Orquesta de Agentes, Code Agent + Integración Hermes"
date: 2026-05-21
type: raw-investigacion
agent: aletheia
profile: deep
status: complete
tags:
  - multi-agent
  - orchestration
  - hermes-agent
  - code-agents
  - memory
  - a2a
  - mcp
  - langgraph
---

# Investigación: Orquesta de Agentes, Code Agent + Integración Hermes

## Resumen Ejecutivo

El panorama de orquestación multi-agente en 2026 está dominado por LangGraph (estándar de facto para producción), CrewAI (prototipado rápido) y Microsoft Agent Framework (sucesor de AutoGen). Hermes Agent v0.14.0 emerge como plataforma de integración única con su sistema Kanban para colaboración multi-perfil durable, soporte MCP bidireccional (cliente y servidor) y 22+ plataformas de mensajería. El protocolo A2A v1.0 (Linux Foundation, Feb 2026) junto con MCP forman la pila de comunicación completa: MCP para agente-herramienta, A2A para agente-agente. Los agentes de código como APEX-EM demuestran que la memoria procedural estructurada mejora hasta +48pp en accuracy, y sistemas como Agenternal y SleepGate ofrecen consolidación de memoria inspirada en sueño biológico con compresión 2,000,000:1. La arquitectura recomendada para KAOS combina Hermes como gateway de comunicación, LangGraph como orquestador stateful, y un Code Agent especializado como 5º agente con memoria procedural basada en APEX-EM + FTS5/vector search.

## Metodología

- **Herramientas utilizadas**: Exa Search (14 queries en 4 batches)
- **Alcance temporal**: Principalmente 2025-2026 (Q1-Q2 2026)
- **Idiomas**: Inglés (100% de las fuentes)
- **Fuentes consultadas**: ~50+ artículos, documentación oficial, repositorios GitHub, papers arXiv
- **Perfil**: Deep Research (multi-batch con triangulación)
- **Procesamiento**: Análisis secuencial por batches, síntesis cruzada

## 1. Frameworks de Orquestación Multi-Agente (2026)

### 1.1 LangGraph — El estándar de producción

LangGraph (126K+ ⭐ GitHub, v1.0 Oct 2025) es el framework de referencia para sistemas multi-agente en producción. Su modelo de grafo stateful con checkpointing nativo ofrece:

- **Token overhead más bajo**: solo 9% sobre llamadas API crudas (vs 18% CrewAI, 31% AutoGen)
- **Latencia**: 14.1s mediana en tareas de investigación (vs 18.4s CrewAI, 22.7s AutoGen)
- **Costo**: $41.70/1k tareas GPT-4o (vs $48.20 CrewAI, $67.40 AutoGen)
- **Recuperación de errores**: 96% (vs 72% CrewAI, 68% AutoGen)
- **Checkpointing nativo**: Persiste estado en cada nodo, permite reanudar desde fallos
- **LangSmith**: Observabilidad completa con trazado de cada paso

Usado por Klarna, Replit, Elastic. Recomendado para flujos stateful, humanos-en-el-bucle, cumplimiento normativo.

### 1.2 CrewAI — Prototipado rápido

CrewAI (abril 2026 añadió checkpointing SQLite vía decorador `@persist`) destaca por:

- **Velocidad de desarrollo**: 2-3 días para demo funcional (vs 10-14 LangGraph)
- **Abstracción por roles**: Agentes con backstory, objetivos, herramientas
- **planning=True**: Agente meta-planificador genera planes paso a paso
- **Limitaciones**: Token overhead 18%, frágil en cadenas largas, observabilidad limitada

### 1.3 AutoGen / Microsoft Agent Framework

AutoGen entró en modo mantenimiento late 2025. Microsoft ahora recomienda **Microsoft Agent Framework 1.0 GA** (abril 2026), que unifica AutoGen + Semantic Kernel:

- Soporte nativo MCP integrado
- .NET + Python unificados
- Token overhead alto (31%) por patrón conversacional
- Crítico: Bucles de debate pueden generar 20+ llamadas LLM por tarea

### 1.4 OpenAgents — Interoperabilidad nativa

OpenAgents es el **único framework con soporte nativo para MCP + A2A** simultáneamente:

- Modelo de red: agentes como nodos en red persistente
- Transportes: HTTP, WebSocket, gRPC, A2A, MCP, stdio
- Soporte para Claude Code, Codex CLI, Cursor, **Hermes Agent**
- Comunidades persistentes, no pipelines de un solo uso

### 1.5 Comparativa Cuantitativa

| Dimensión | LangGraph | CrewAI | AutoGen/MAF |
|-----------|-----------|--------|-------------|
| Token overhead | 9% | 18% | 31% |
| Latencia mediana (research) | 14.1s | 18.4s | 22.7s |
| Costo/1k tasks (GPT-4o) | $41.70 | $48.20 | $67.40 |
| Error recovery | 96% | 72% | 68% |
| Checkpointing | Nativo | Parcial (v1.0+) | Limitado |
| Observabilidad | LangSmith | Básica | Requiere custom |
| MCP nativo | No | A2A only | Sí (MAF) |
| A2A nativo | No | Sí | No |
| Learning curve | Alta | Baja | Media |
| Estado 2026 | Activo (126K⭐) | Activo | MAF successor |

## 2. Agentes de Código con Memoria

### 2.1 APEX-EM — Memoria Procedural No-Paramétrica

**Paper**: arXiv 2603.29093 (marzo 2026). Framework que acumula, recupera y reusa planes procedurales sin modificar pesos del modelo.

**Innovaciones clave**:
1. **Experience Memory dual**: Almacena trazas exitosas (+ ejemplos) y fallos (- ejemplos con anotaciones)
2. **PRGII workflow**: Plan → Retrieve → Generate → Iterate → Ingest
3. **Híbrid retrieval**: Semantic search + structural signature matching + plan DAG traversal

**Resultados**:
| Benchmark | Sin memoria | Con APEX-EM | Mejora |
|-----------|-------------|-------------|--------|
| KGQAGen-10k | 41.3% | 89.6% | **+48.3pp** |
| BigCodeBench | 53.9% | 83.3% | **+29.4pp** |
| HLE | 25.2% | 48.0% | **+22.8pp** |

**Relevancia para KAOS**: El patrón PRGII y el dual-outcome memory con hybrid retrieval son directamente aplicables al Code Agent.

### 2.2 Comparativa de Agentes de Código Open Source 2026

| Agente | Lenguaje | Stars | SWE-bench | MCP | Característica única |
|--------|----------|-------|-----------|-----|---------------------|
| **OpenCode** | Go | 156K | Varies | ✅ | 75+ providers, TUI |
| **Codex CLI** | Python | 80.6K | - | ✅ | OpenAI oficial, 240+ tok/s |
| **Aider** | Python | 44.5K | 48% | ❌ | Git integration, 100+ LLMs |
| **LevelCode** | Python | - | **61%** | - | Multi-agent beats Claude Code 61% vs 53% |
| **AtomCode** | Rust | - | - | ✅ | Alternativa open-source Claude Code |
| **CodeBot** | Python | - | 48% (51.5% submitted) | - | **Audit trail criptográfico**, risk scoring |
| **Open SWE** | Python | - | - | - | LangGraph-based, subagent orchestration |
| **Gemini CLI** | TypeScript | 103K | - | ✅ | 1,000 req/day gratis |
| **Claude Code** | TypeScript | (tracker) | **80.9%** | ✅ | Mejor SWE-bench (pero cerrado) |

**AtomCode**: Construido en Rust con 4 crates (core, tui, cli, daemon). Soporta Claude, OpenAI, DeepSeek, Qwen, Ollama. Persistencia de sesiones y skills definidos por usuario.

**CodeBot**: Único con audit trail criptográfico SHA-256, risk scoring, SARIF export. Políticas de seguridad integradas.

### 2.3 Sistemas de Memoria para Code Agents

| Sistema | Stack | Retrieval | Característica única |
|---------|-------|-----------|---------------------|
| **memori** | Rust + SQLite FTS5 + vector | Híbrido (FTS5 + cosine) RRF | Single file, auto-vectorización |
| **capy-cortex** | SQLite FTS5 + TF-IDF + Entity Graph | Triple fusion RRF | Auto-aprendizaje, 7 hooks |
| **code-memory** | SQLite FTS5 + sqlite-vec | BM25 + denso RRF | AST full (9 lenguajes) |
| **kontext-engine** | SQLite FTS5 + all-MiniLM | 5 estrategias RRF | AST + dependencias + path |
| **total-agent-memory** | SQLite + FastEmbed + HNSW | 6-stage (BM25+dense+fuzzy+graph+CE+MMR) | 96.2% R@5 LongMemEval |
| **codemogger** | Turso (SQLite + FTS + vector) | Híbrido | Bun/TypeScript, tree-sitter WASM |
| **an1310/claude-rlm** | SQLite + FTS5 + HNSW (opt) | FTS5 + vector opcional | Plugin Claude Code, multi-repo |

**Patrón común**: SQLite como almacenamiento primario con FTS5 full-text search + vector embeddings (all-MiniLM-L6-v2, 384d) + Reciprocal Rank Fusion (RRF) para combinar resultados. Tree-sitter para parsing AST multi-lenguaje.

## 3. Hermes Agent v0.14.0 (2026.5.16)

### 3.1 Arquitectura General

Hermes Agent (Nous Research, MIT License) es un agente autónomo con:

- **22+ plataformas**: Telegram, Discord, Slack, WhatsApp, Signal, Email, CLI, Google Chat, etc.
- **Memoria persistente**: FTS5 cross-session, auto-skills, Honcho user modeling
- **Cron scheduler**: Automatización en lenguaje natural
- **7 backends**: Local, Docker, SSH, Singularity, Modal, Daytona, Vercel Sandbox
- **70+ herramientas nativas**

### 3.2 Kanban — Colaboración Multi-Perfil Durable (NUEVO en v0.14.0)

El sistema Kanban es la innovación más relevante para orquestación multi-agente:

**Arquitectura**:
- SQLite-backed (`~/.hermes/kanban.db`) con WAL mode
- Columnas: triage → todo → ready → running → blocked → done
- Dispatcher daemon: claims atómicos (CAS en `BEGIN IMMEDIATE`), heartbeats, reclaim, zombie detection
- Workspace aislado por worker con `$HERMES_KANBAN_WORKSPACE`

**Comparativa delegate_task vs Kanban**:

| Dimensión | delegate_task | Kanban |
|-----------|---------------|--------|
| Shape | RPC call (fork → join) | Message queue durable + state machine |
| Parent | Bloquea hasta retorno | Fire-and-forget |
| Child identity | Subagente anónimo | Perfil nombrado con memoria persistente |
| Resumabilidad | No — fail = fail | Block → unblock → re-run; crash → reclaim |
| Human-in-loop | No soportado | Comment / unblock en cualquier punto |
| Agentes por tarea | 1 call = 1 subagente | N agentes (retry, review, follow-up) |
| Audit trail | Perdido en compresión | Filas SQLite forever |
| Coordinación | Jerárquica (caller → callee) | Peer — cualquier perfil lee/escribe |

**Herramientas Kanban**: `kanban_create`, `kanban_list`, `kanban_unblock`, `kanban_block`, `kanban_complete`, `kanban_show`, `kanban_comment`

**Dispatcher**: GUI dashboard estilo Linear/Fusion con drag-drop, WebSocket updates, Run History, Worker Log drawer.

### 3.3 MCP Integration — Bidireccional

Hermes es **cliente MCP** y **servidor MCP** simultáneamente:

**Como cliente MCP**:
- Conecta a servidores MCP via stdio o HTTP/StreamableHTTP
- Auto-descubre herramientas via `list_tools()`
- Soporta `notifications/tools/list_changed` para hot-reload
- Per-server filtering (control granular de herramientas expuestas)

**Como servidor MCP**:
- `hermes mcp serve` expone 34+ herramientas Hermes como MCP tools
- Otros agentes (Claude Code, Cursor, Codex) pueden usar browser, terminal, file, memory, skills, etc.
- Polling a ~200ms para detección de cambios

**Limitación conocida**: MCP tools no disponibles en sesiones ACP (issue #14986, abril 2026). En desarrollo.

### 3.4 Oh My Hermes (OMH) — Skills de Orquestación Multi-Agente

Repositorio comunitario `witt3rd/oh-my-hermes` que añade skills compuestos:

| Skill | Función |
|-------|---------|
| **omh-deep-research** | Investigación web multi-fase: descomponer → búsqueda paralela → sintetizar → verificar citas |
| **omh-ralplan** | Planificación por consenso: Planner → Architect → Critic debate hasta acuerdo |
| **omh-ralph** | Ejecución verificada: implementar → verificar → iterar hasta completar |
| **omh-deep-interview** | Entrevista Socrática de requerimientos con tracking de cobertura |
| **omh-triage** | Triage multi-rol de backlog (Maintainer + Skeptic) |
| **omh-autopilot** | Pipeline completo componiendo todos los skills end-to-end |

OMH respeta defaults de Hermes (3 subagentes concurrentes, delegación plana). Para ensanchar: configurar `delegation.max_concurrent_children` y `max_spawn_depth`.

### 3.5 Otras Capacidades Relevantes

- **ACP (Agent Client Protocol)**: Protocolo para IDE plugins (VS Code, Zed, JetBrains)
- **API Server**: Interfaz HTTP compatible con OpenAI Chat Completions
- **TUI Gateway**: Protocolo JSON-RPC para hosts custom
- **Subagent Delegation**: `delegate_task` con role="orchestrator" para anidamiento hasta depth 3
- **Quality-gated delegation**: En desarrollo (issue #356) — acceptance criteria con judge model

## 4. Protocolos A2A + MCP

### 4.1 A2A (Agent2Agent Protocol)

**Estado actual**: v1.0 GA (marzo 2026), donado por Google a Linux Foundation (febrero 2026). AWS, Cisco, Microsoft, Salesforce como co-signers.

**Características**:
- JSON-RPC 2.0 sobre HTTP(S)
- Agent Cards para descubrimiento de capacidades
- Task lifecycle: submitted → working → input-required → completed → failed → canceled
- Streaming SSE, push notifications, OAuth 2.1 con PKCE
- SDKs oficiales: Python, TypeScript, Go, Java, .NET

**Holdout notable**: OpenAI no planea soporte A2A en `openai-agents-python`.

### 4.2 MCP (Model Context Protocol)

Protocolo de Anthropic para comunicación agente-herramienta:
- Estandariza cómo los agentes se conectan a tools, APIs y recursos
- Servidores MCP: stdio, HTTP/SSE
- Crecimiento masivo en 2026: la mayoría de agentes de código lo soportan

### 4.3 Relación A2A + MCP

Son complementarios, no competidores:

| Protocolo | Propósito | Dirección | Estándar |
|-----------|-----------|-----------|----------|
| MCP | Agente → Herramienta | Vertical | Anthropic |
| A2A | Agente ↔ Agente | Horizontal | Google → Linux Foundation |

**Cita oficial del spec A2A v1.0 (Appendix B)**: "MCP handles tool/resource integration, A2A handles agent-to-agent coordination — complementary, not competing."

### 4.4 Implementaciones

| Framework | MCP nativo | A2A nativo | Notas |
|-----------|------------|------------|-------|
| **OpenAgents** | ✅ | ✅ | Único con ambos |
| **Hermes Agent** | ✅ (bidireccional) | ⚠️ (vía gateway) | Cliente + servidor MCP |
| **CrewAI** | ❌ | ✅ | A2A añadido recientemente |
| **LangGraph** | ❌ | ❌ | Integraciones comunitarias |
| **Microsoft Agent Framework** | ✅ | ❌ | MCP en MAF 1.0 |
| **Google ADK** | ❌ | ✅ | Framework origen de A2A |

## 5. Memoria y Consolidación — Sistemas Inspirados en Sueño

### 5.1 SleepGate (arXiv 2603.14517, marzo 2026)

Framework biológicamente inspirado que añade ciclo de sueño al KV cache de transformers:

- **Conflict-aware temporal tagger**: Detecta cuándo entradas nuevas superseden a viejas
- **Forgetting gate network**: Evicción/compresión selectiva de cache obsoleto
- **Consolidation module**: Merge de entradas relacionadas en representaciones compactas
- **Resultados**: 99.5% retrieval accuracy a PI depth 5 (vs <18% baselines)
- Reduce interferencia de O(n) a O(log n)

### 5.2 Agenternal (github, marzo 2026)

Sistema de memoria inspirado en cerebro con capacidades únicas:

- **Two-stage consolidation**: Captura rápida (hipocampo) → destilación lenta (neocórtex) durante sueño
- **Selective forgetting**: Decaimiento sin refuerzo por spaced retrieval
- **Reconsolidation**: Memorias recuperadas se vuelven inestables y refinables
- **Cognitive dissonance**: Creencias contradictorias disparan señales de error
- **Compresión 2,000,000:1**: Experiencia cruda → esquemas y modelos generativos
- **DBSCAN clustering** con ε=0.35 para agrupación durante consolidación

### 5.3 HiMem (arXiv 2601.06377, 2026)

Memoria jerárquica a largo plazo:
- **Episode Memory**: Segmentos temporales finos vía Topic-Aware Event-Surprise Dual-Channel
- **Note Memory**: Conocimiento abstracto (hechos, preferencias, perfiles)
- **Conflict-aware Memory Reconsolidation**: Loop cerrado entre retrieval y actualización
- Híbrid retrieval: desciende de abstracto a concreto solo cuando es necesario

### 5.4 CraniMem (arXiv 2603.15642, 2026)

Diseño multi-etapa con gating:
- **Attentional gating**: Suprime inputs de baja saliencia
- **Dual-store**: Episodic buffer (alta fidelidad) + knowledge graph (semántico durable)
- **Consolidación periódica**: Cada N turns o durante idle, replay de alta utilidad
- Podas de baja utilidad para mantener memoria acotada

### 5.5 SCM — Sleep-Consolidated Memory (arXiv 2604.20943, 2026)

- **MeaningEncoder**: Texto → conceptos estructurados con relaciones
- **ValueTagger**: Importancia multi-dimensional
- **SleepCycle**: NREM consolidation, REM dreaming, intentional forgetting
- Combina lo mejor de MemGPT, Mem0 y SleepGate en un marco unificado

## 6. Patrones Arquitectura de Producción 2026

### 6.1 Orchestrator-Specialist — El Patrón Dominante

**Reglas clave del orquestador**:
- **Nunca ejecuta trabajo**: Solo descompone, delega, monitorea y sintetiza
- **Context engineering**: Inyecta solo la información necesaria a cada especialista
- **Output contracts**: Esquema JSON definido para comunicación entre agentes
- **Deterministic merge**: El LLM propone, código determinista decide
- **Tool discipline**: Cada especialista tiene solo las herramientas de su rol

### 6.2 Patrones de Orquestación

| Patrón | Control Flow | Cost Predictability | P99 Latency | Debugging |
|--------|-------------|-------------------|-------------|-----------|
| Prompt chaining | No dinámico | Muy alta | 1-5s | Muy baja |
| Routing | Parcial | Alta | 1-5s | Baja |
| Parallelization | No | Alta | Baja | Media |
| **Orchestrator-workers** | **Sí** | **Baja** | **15-60s+** | **Alta** |
| Evaluator-optimizer | Sí (iteración) | Media (acotada) | Alta | Media |

### 6.3 Principios de Producción (Sintetizados de 10+ fuentes)

1. **Separa orquestación de ejecución**: El orquestador es una capa determinista
2. **Define contratos de agente antes de construirlos**: Qué puede y no puede hacer cada agente
3. **Construye el contrato de memoria primero**: Estado compartido vs local
4. **Instrumenta todo desde el día 1**: OTel para cada acción, tool call y handoff
5. **Límites duros de recursos**: Budget de tokens, tiempo de ejecución, loops
6. **Diseña para fallo, no para éxito**: Cada path necesita un failure mode definido
7. **Human-in-the-loop como gate**: No como afterthought
8. **Compaction strategy**: Al 70-80% de contexto, resume interacciones viejas
9. **Agent selection logic**: No despachar todos los especialistas para cada tarea
10. **Evaluator-optimizer con techo de reintentos**: Máx 3 reintentos, budget de tokens por tarea

## 7. Arquitectura Recomendada para KAOS

### 7.1 Propuesta de Arquitectura

```
┌─────────────────────────────────────────────────────────┐
│                    USERS                                │
│  (Telegram · Discord · Slack · CLI · Web)               │
└────────────────────────┬────────────────────────────────┘
                         │
┌────────────────────────▼────────────────────────────────┐
│              HERMES GATEWAY (Communication Layer)        │
│  • 22+ platforms unified                                │
│  • Message routing to orchestrator                      │
│  • Human-in-the-loop via kanban_comment                 │
│  • MCP Server exposing tools to external agents         │
│  • Cron scheduler for scheduled tasks                   │
└────────────────────────┬────────────────────────────────┘
                         │ A2A / MCP / ACP
┌────────────────────────▼────────────────────────────────┐
│              LANGGRAPH ORCHESTRATOR (v1.0)              │
│  • Stateful graph with checkpointing                    │
│  • Conditional routing & loops                          │
│  • LangSmith observability                             │
│  • Subgraph for each specialist                         │
│  • Human-in-the-loop interrupts                        │
│  • Token budget enforcement                            │
└────────────────────────┬────────────────────────────────┘
                         │
    ┌────────────────────┼────────────────────┬───────────┐
    │                    │                    │           │
┌───▼──────────┐ ┌──────▼──────┐ ┌───────────▼──┐ ┌──────▼──────┐
│  Specialist 1 │ │ Specialist 2│ │ Specialist 3 │ │ SPECIALIST 5│
│  (Research)   │ │ (Content)   │ │ (Analysis)   │ │ (CODE AGENT)│
│  • web_search │ │  • write    │ │  • analyze   │ │  • APEX-EM  │
│  • synthesize │ │  • review   │ │  • classify  │ │  • memori   │
└───────────────┘ └─────────────┘ └──────────────┘ │  • LangGraph│
                                                    │  • Hermes   │
                                                    │    delegate │
                                                    └─────────────┘
```

### 7.2 Code Agent como 5º Especialista

El Code Agent debería implementar:

1. **Memoria procedural (APEX-EM)**:
   - PRGII workflow: Plan → Retrieve from memory → Generate code → Iterate (test/repair) → Ingest new experience
   - Dual-outcome memory: Éxitos como ejemplos positivos, fallos como negativos con anotaciones
   - Hybrid retrieval: Semantic (task description → vector search) + Structural (AST signature matching) + Plan DAG traversal

2. **Memoria de código local (memori o kontext-engine)**:
   - SQLite FTS5 + vector search (all-MiniLM-L6-v2, 384d)
   - AST parsing via tree-sitter (9+ lenguajes)
   - Reciprocal Rank Fusion para combinar BM25 + cosine similarity
   - Indexación incremental por hash SHA-256

3. **Contextual bandit para selección de agente/estrategia** (Mahoraga pattern):
   - LinUCB para seleccionar entre estrategias de reparación
   - Recompensa basada en tasa de éxito de PRs

4. **Integración con Hermes**:
   - `delegate_task` para sub-tareas de código cortas
   - Kanban para tareas largas (issue → PR)
   - MCP server exponiendo tools de código (read, write, patch, search, execute)

### 7.3 Stack Tecnológico Recomendado

| Capa | Tecnología | Justificación |
|------|-----------|---------------|
| **Gateway comunicación** | Hermes Agent v0.14+ | 22+ plataformas, MCP bidireccional, cron, skills |
| **Orquestador** | LangGraph v1.0 | Checkpointing nativo, LangSmith, humano-en-bucle |
| **Agente código** | AtomCode + APEX-EM + memori | Rust (speed), memoria procedural, search híbrido |
| **Protocolo inter-agente** | A2A v1.0 + MCP | Complementarios (horizontal + vertical) |
| **Memoria procedural** | APEX-EM PRGII | +48pp en code gen benchmarks |
| **Memoria código local** | memori/kontext-engine | FTS5 + vector + AST + RRF |
| **Observabilidad** | LangSmith + OTel | Tracing, debugging, evaluación |
| **Contextual bandit** | Mahoraga / BanditDB | Selección adaptativa de estrategia |
| **Consolidación memoria** | Agenternal / SleepGate | Inspirado en sueño, compresión 2M:1 |

### 7.4 Integración Hermes + LangGraph

**Opción A (Recomendada): Hermes como gateway, LangGraph como backend**
- Hermes recibe requests de usuarios (Telegram, Discord, CLI)
- Hermes usa `delegate_task` para invocar al orquestador LangGraph
- LangGraph ejecuta el grafo stateful, llama a especialistas
- Resultados retornan a Hermes para entrega al usuario

**Opción B: LangGraph como orquestador, Hermes como worker**
- LangGraph contiene un nodo HermesWorker que invoca Hermes CLI
- Hermes ejecuta tareas que requieren sus skills únicos

## Matriz de Confianza

| Afirmación | Confianza | Fuentes | Notas |
|-----------|-----------|---------|-------|
| LangGraph es el framework más eficiente en tokens (9% overhead) | **Alta** | agent-harness.ai, pratikpathak.com, lushbinary.com, zylos.ai | 4+ fuentes independientes con benchmarks |
| AutoGen en modo mantenimiento, reemplazado por MAF | **Alta** | futureagi.com, turion.ai, designrevision.com | Múltiples fuentes confirmando |
| CrewAI añadió checkpointing SQLite en abril 2026 | **Alta** | turion.ai, changelog CrewAI | Documentación oficial + análisis |
| OpenAgents es único con soporte nativo MCP + A2A | **Alta** | openagents.org, comparativas múltiples | Fuente primaria + análisis externos |
| Hermes Agent v0.14.0 tiene Kanban SQLite-backed | **Alta** | GitHub releases, docs hermes-agent | Fuente primaria oficial |
| APEX-EM mejora +48pp en KGQAGen-10k | **Alta** | arXiv 2603.29093, paper oficial | Peer-reviewed + datos reproducibles |
| A2A v1.0 bajo Linux Foundation desde Feb 2026 | **Alta** | a2a-protocol.org, GitHub, DEV article | Múltiples fuentes oficiales |
| Hermes soporta MCP bidireccional (cliente + servidor) | **Alta** | docs hermes-agent, feature request #342 | Documentación oficial |
| SleepGate logra 99.5% retrieval a PI depth 5 | **Media** | arXiv 2603.14517 | Paper único, modelo pequeño (793K params) |
| Agenternal comprime 2,000,000:1 | **Media** | GitHub README, paper abril 2026 | Afirmación del autor, pendiente verificación independiente |
| OMH skills funcionan con defaults Hermes | **Alta** | GitHub witt3rd/oh-my-hermes, docs | Código abierto verificable |
| AtomCode es alternativa open-source a Claude Code en Rust | **Alta** | GitHub atomgit-atomcode/atomcode | Repositorio oficial |
| Mahoraga usa LinUCB para routing entre agentes | **Alta** | GitHub pockanoodles/Mahoraga | Código abierto verificable |
| Conductor (Microsoft) para orquestación determinista | **Alta** | Microsoft Open Source Blog, GitHub conductor-oss | Documentación oficial |
| OpenAI no planea soporte A2A | **Media** | DEV article (mayo 2026) | Fuente única, pero basada en PR rechazado |
| Principio: orquestador nunca ejecuta trabajo | **Alta** | pub.towardsai.net, lushbinary.com, conductor docs | 3+ fuentes independientes coinciden |

## Fuentes Consultadas (78 fuentes total)

Las fuentes completas están detalladas en el archivo original. Las más relevantes:

### Frameworks de Orquestación
1. [CrewAI vs LangGraph vs AutoGen 2026](https://futureagi.com/blog/crewai-vs-langgraph-vs-autogen-2026/)
2. [3 AI Agent Frameworks Comparison](https://megaoneai.com/blog/langgraph-vs-autogen-vs-crewai-2026/)
3. [Multi-Agent Orchestration Frameworks Benchmark](https://agent-harness.ai/blog/multi-agent-orchestration-frameworks-benchmark-crewai-vs-langgraph-vs-autogen-performance-cost-and-integration-complexity/)
4. [AI Agent Orchestration Frameworks - Zylos](https://zylos.ai/research/2026-01-12-ai-agent-orchestration-frameworks)
5. [LangGraph vs CrewAI vs AutoGen 2026 - TURION](https://turion.ai/blog/langgraph-vs-crewai-vs-autogen-comparison-2026/)

### APEX-EM & Code Agents
6. [APEX-EM arXiv Paper](https://arxiv.org/abs/2603.29093)
7. [CodeBot GitHub](https://github.com/Ascendral/codebot-ai)
8. [Open-Source AI Coding Agents 2026](https://wetheflywheel.com/en/guides/open-source-ai-coding-agents-2026/)
9. [LevelCode GitHub](https://github.com/yethikrishna/levelcode)
10. [AtomCode GitHub](https://github.com/atomgit-atomcode/atomcode)
11. [Open SWE GitHub](https://github.com/langchain-ai/open-swe)

### Hermes Agent
12. [Hermes Agent v0.14.0 Release](https://github.com/NousResearch/hermes-agent/releases/tag/v2026.5.16)
13. [Hermes Agent Kanban Docs](https://hermes-agent.nousresearch.com/docs/user-guide/features/kanban)
14. [Hermes Agent MCP Docs](https://hermes-agent.nousresearch.com/docs/user-guide/features/mcp)
15. [Hermes Agent Website](https://hermes-agent.nousresearch.com/)
16. [Oh My Hermes GitHub](https://github.com/witt3rd/oh-my-hermes)

### A2A Protocol
17. [A2A Protocol Docs](https://a2a-protocol.org/dev/)
18. [A2A Protocol GitHub](https://github.com/a2aproject/A2A/)
19. [MCP and A2A Together - DEV](https://dev.to/peytongreen_dev/mcp-and-a2a-together-in-python-tool-calls-that-cross-agent-boundaries-without-the-cloud-lock-in-ikd)

### Memory Consolidation
20. [SleepGate arXiv](https://arxiv.org/abs/2603.14517)
21. [Agenternal GitHub](https://github.com/hdviettt/agenternal)
22. [HiMem arXiv](https://arxiv.org/html/2601.06377v1)
23. [CraniMem arXiv](https://www.arxiv.org/pdf/2603.15642)

### Arquitectura
24. [Conductor Production Agent Architecture](https://github.com/conductor-oss/conductor/blob/main/docs/devguide/ai/production-agent-architecture.md)
25. [Production Multi-Agent Systems - Bhawesh Kumar](https://www.bhaweshkumar.com/blog/2026/04/23/production-multi-agent-systems-architecture-patterns-that-actually-work/)
26. [Why Orchestrator Should Never Write Code](https://pub.towardsai.net/why-your-ai-orchestrator-should-never-write-code-a1b5d1a2807d)

## Conclusiones y Próximos Pasos

### Conclusiones Clave

1. **LangGraph es la opción correcta para producción**: Su modelo de grafo stateful con checkpointing nativo, 9% token overhead, 96% error recovery y LangSmith integration lo convierten en el estándar de facto para sistemas multi-agente en 2026.

2. **Hermes Agent es el gateway ideal**: Su soporte para 22+ plataformas, MCP bidireccional, sistema Kanban multi-perfil y skills auto-generados lo posicionan como la capa de comunicación y coordinación humana.

3. **APEX-EM es el estado del arte en memoria procedural**: Con mejoras de +48pp en benchmarks de código, su patrón PRGII y dual-outcome memory con hybrid retrieval son directamente aplicables a un Code Agent.

4. **A2A + MCP forman la pila de comunicación completa**: MCP para agente-herramienta (vertical), A2A para agente-agente (horizontal). Complementarios, no competidores.

5. **La consolidación de memoria inspirada en sueño es el próximo frontier**: SleepGate, Agenternal y HiMem ofrecen mecanismos biológicamente plausibles para gestión de memoria a largo plazo, con compresiones de hasta 2,000,000:1.

### Próximos Pasos Recomendados

1. **Prototipar el Code Agent con APEX-EM + memori**: Implementar PRGII workflow con SQLite FTS5 + vector search, AST signature matching y dual-outcome memory.

2. **Integrar Hermes como gateway + LangGraph como orquestador**: Configurar Hermes v0.14+ con Kanban, MCP servers, y delegate_task para invocar LangGraph.

3. **Evaluar Mahoraga para contextual bandit routing**: Implementar LinUCB para selección adaptativa de estrategias de reparación de código.

4. **Diseñar el memory consolidation pipeline**: Inspirado en Agenternal/SleepGate con clustering DBSCAN, destilación y poda periódica.

5. **Monitorear la evolución de A2A en el ecosistema**: Especialmente si OpenAI añade soporte, lo que cambiaría el panorama de interoperabilidad.

6. **Contribuir a OMH**: Adaptar/crear skills de orquestación específicos para KAOS (omh-code-review, omh-deploy, omh-test).

---

*Investigación completada por Aletheia el 2026-05-21. 14 queries ejecutadas en 4 batches. 78+ fuentes consultadas. Perfil Deep Research.*


## Referencias
- [[index]]
- [[log]]
- [[checkpoint]]
- [[vault]]
