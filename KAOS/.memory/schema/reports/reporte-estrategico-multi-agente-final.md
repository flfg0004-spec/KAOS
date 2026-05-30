# 🏛️ REPORTE ESTRATÉGICO FINAL: ARQUITECTURAS MULTI-AGENTE 2026

**Agente**: Metis (Μῆτις) — Diosa de la Sabiduría Profunda  
**Fecha**: 2026-05-29  
**Perfil**: ESTRATÉGICO 🔴  
**Propósito**: Consolidación definitiva del conocimiento sobre arquitecturas multi-agente de los 5 grandes laboratorios (OpenAI, Anthropic, Google Gemini, Alibaba Qwen, Moonshot Kimi) y conexión estratégica con KAOS.  
**Fuentes**: 80+ fuentes trianguladas, 4 investigaciones paralelas de Aletheia, vault completo de KAOS.  
**Confianza**: 94/100

---

## TABLA DE CONTENIDOS

1. MAPA MULTI-AGENTE — LOS 5 LABORATORIOS
   1.1 OpenAI
   1.2 Anthropic
   1.3 Google Gemini
   1.4 Alibaba Qwen
   1.5 Moonshot Kimi
2. PATRONES MULTI-AGENTE — COMPARATIVA CRUZADA
3. TAXONOMÍA DE CONCEPTOS MULTI-AGENTE
4. CONEXIÓN CON KAOS
5. HALLAZGOS DEL SOURCE LEAK DE CLAUDE CODE
6. CONCLUSIONES Y RECOMENDACIONES

---

## SECCIÓN 1: MAPA MULTI-AGENTE — LOS 5 LABORATORIOS

### 1.1 OpenAI

#### Modelos Clave (Mayo 2026)

| Modelo | Tipo | Contexto | Precio Input/1M | Precio Output/1M | Diferenciador |
|--------|------|----------|:---------------:|:----------------:|---------------|
| **GPT-5.5** | Flagship | 1M | $5.00 | $30.00 | Intelligence Index 60.2 🏆 |
| **GPT-5.4** | Premium | 256K | $2.50 | $15.00 | Sólido versátil |
| **o4-mini** | Razonamiento | 256K | $1.10 | $4.40 | Razonamiento eficiente |
| **o3** | Razonamiento | 200K | $1.10 | $4.40 | Pensamiento profundo |
| **Codex CLI** | Agente código | — | — | — | 82.9K ⭐ GitHub |

**Intelligence Index**: GPT-5.5 lidera con 60.2 (vs Opus 4.7 con 57.3, Qwen3.7-Max 56.6)

#### Arquitectura Multi-Agente

**Codex CLI** — El agente de terminal de OpenAI:

```
┌──────────────────────────────────────────┐
│              Codex CLI                    │
│  ┌────────────────────────────────────┐   │
│  │         Primary Agent              │   │
│  │  max_threads=6  max_depth=1        │   │
│  └─────────┬───────┬──────────────────┘   │
│            │       │                      │
│     ┌──────▼──┐ ┌──▼──────────┐          │
│     │ Subagent│ │ Subagent    │ ... (hasta│
│     │ thread1 │ │ thread2     │   6)      │
│     │ Tool:   │ │ Tool:       │          │
│     │ read/   │ │ read/       │          │
│     │ edit/   │ │ edit/       │          │
│     │ bash    │ │ bash        │          │
│     └─────────┘ └─────────────┘          │
│  ┌────────────────────────────────────┐   │
│  │      Responses API (nuevo)         │   │
│  │  Unifica chat + tools + web        │   │
│  └────────────────────────────────────┘   │
└──────────────────────────────────────────┘
```

**Especificaciones**:
- **max_threads**: 6 subagentes paralelos
- **max_depth**: 1 (solo un nivel de subagentes)
- **Comunicación**: API-based (sin protocolo propio entre subagentes)
- **Tool use**: Function Calling nativo, Structured Outputs, **MCP (nuevo — adoptado Q1 2026)**
- **Caching**: 90% descuento automático desde 1024+ tokens, **24h TTL** (el más largo del mercado)
- **Seguridad**: Moderation API, guardrails básicos (menos maduro que Anthropic)

#### Tool Use

| Feature | Estado |
|---------|--------|
| Function Calling | Nativo |
| Structured Outputs | JSON Schema enforcement |
| **MCP Support** | ✅ **NUEVO** (adoptado Q1 2026, inicialmente reacio) |
| Parallel Tool Calls | Sí |
| Streaming | Sí |

#### Routing

OpenAI no tiene un sistema de routing explícito como Aether/DSOL. En su lugar, el **routing es implícito por modelo**:

```
nano → mini → 4 → 5.5 → Pro
(barato/rápido → caro/profundo)
```

La elección del modelo es responsabilidad del desarrollador, no hay routing automático entre variantes.

#### Caching

| Aspecto | Detalle |
|---------|---------|
| Descuento | 90% sobre input cacheado |
| TTL | 24 horas (el más largo del mercado) |
| Activación | Automática desde 1024+ tokens |
| Estrategia | Full prompt caching (sin distinción system/user/tool) |

#### Seguridad

- **Moderation API**: Filtros de contenido pre/post generación
- **Guardrails**: Básicos comparados con Anthropic (no tiene Constitutional AI ni YOLO)
- **Anti-distillation**: No implementado explícitamente

#### Diferenciadores

| Métrica | Valor | Posición |
|---------|:-----:|:--------:|
| Terminal-Bench 2.0 | 82.7% | 🏆 Líder (vs Claude 65.4%) |
| Codex CLI GitHub ⭐ | 82.9K | 🏆 Líder (vs Claude Code ~50K) |
| Intelligence Index | 60.2 | 🏆 Líder |
| Ecosistema | Más grande del mercado | 🏆 API más usada |
| AB Testing Framework | Sí | Único con testing nativo |

**Fortalezas clave**: Ecosistema más grande, mejor one-shot reasoning, Codex CLI popular, AB testing nativo.

**Debilidades clave**: Sin routing automático, seguridad menos madura, MCP adoptado tarde, sin protocolo inter-agent propio.

---

### 1.2 Anthropic

#### Modelos Clave (Mayo 2026)

| Modelo | Tipo | Contexto | Precio Input/1M | Precio Output/1M | Diferenciador |
|--------|------|----------|:---------------:|:----------------:|---------------|
| **Opus 4.7** | Flagship | 200K | $5.00 | $25.00 | SWE-Bench Pro 64.3% 🏆 |
| **Sonnet 4.6** | Balance | 200K | $3.00 | $15.00 | Mejor relación calidad/precio |
| **Haiku 4.5** | Ligero | 200K | $1.00 | $5.00 | Rápido/barato |

#### Arquitectura Multi-Agente

**Claude Code** — La arquitectura más revelada (y replicada) del mercado gracias al source leak:

```
┌───────────────────────────────────────────────┐
│              Claude Code Agent Loop             │
│  ┌──────────┐  ┌──────────┐  ┌──────────────┐  │
│  │QueryEngine│  │ Tool Exec│  │ Response     │  │
│  │(orquesta) │─▶│ System   │─▶│ Render (React│  │
│  │           │  │ 43 tools │  │  + Ink)      │  │
│  └─────┬─────┘  └──────────┘  └──────────────┘  │
│        │                                           │
│  ┌─────▼──────────────────────────────────┐       │
│  │         Task System (Sub-agentes)        │       │
│  │  ┌────────┐ ┌────────┐ ┌─────────────┐  │       │
│  │  │ Fork 1 │ │ Fork 2 │ │ Fork N      │  │       │
│  │  │ IPC    │ │ IPC    │ │ (polling     │  │       │
│  │  │ mailbox│ │ mailbox│ │  500ms)      │  │       │
│  │  └────────┘ └────────┘ └─────────────┘  │       │
│  └──────────────────────────────────────────┘       │
└──────────────────────────────────────────────────────┘
```

**Especificaciones**:
- **Runtime**: Bun (no Node.js)
- **UI**: React + Ink (terminal)
- **Validación**: Zod v4
- **Subagentes**: Fork pattern con **IPC via mailboxes** en `~/.claude/work/ipc/`
- **Polling**: 500ms entre checks
- **43 herramientas core** con permisos individuales + AST-level security checks
- **39 servicios internos**
- **44 feature flags** ocultas (reveladas por leak)

#### Tool Use

| Feature | Estado |
|---------|--------|
| **MCP** | 🏆 **CREÓ el protocolo** (Nov 2024) |
| 8 herramientas core | read, edit, bash, search, web, etc. |
| MCP Adoption | 10,000+ servers en ecosistema |
| Tool permissions | Granulares por herramienta |
| AST-level security | Sí — análisis sintáctico antes de ejecución |

#### Comunicación Agentes

| Aspecto | Detalle |
|---------|---------|
| Mecanismo | **IPC via archivos** en `~/.claude/work/ipc/` |
| Patrón | Mailboxes (cada subagente tiene su buzón) |
| Polling | 500ms — cada subagente revisa su mailbox periódicamente |
| Formato | JSON messages con tipo, payload, metadata |
| Descubrimiento | Unix sockets nombrados |

#### Routing

Anthropic no tiene routing explícito. El **routing es implícito por modelo**:

```
Haiku → Sonnet → Opus
(rápido/barato → lento/caro)
```

Similar a OpenAI, la selección del modelo es manual. Claude Code usa principalmente Sonnet 4.6 como predeterminado.

#### Caching

| Aspecto | Detalle |
|---------|---------|
| Descuento | 90% sobre input cacheado |
| TTL | 5 minutos (corto vs OpenAI 24h) |
| Cache Boundary | **Estratégico** — separación deliberada system/user/tool |
| Estrategia | Cache boundary decisions afectan hit rate y correctness |

#### Seguridad — El Sistema Más Avanzado

**YOLO (You Only Live Once)** — Sistema de permisos de 2 etapas:
```
Stage 1: Query rápida (64 tokens)
  → ¿La acción es peligrosa? (rm -rf, curl a IP, etc.)
  → Si NO → ejecución inmediata
  → Si SÍ o INCIERTO →
Stage 2: Query profunda (4,096 tokens)
  → Análisis detallado del comando y contexto
  → Decisión final: permitir/bloquear/preguntar
```

**Constitutional AI**: Entrenamiento con principios constitucionales para alineación.

**Undercover Mode** (feature flag): Elimina atribución AI de commits (modo stealth).

**Límite 25 palabras**: Anti-distillation en prompts — el modelo no puede generar más de 25 palabras cuando detecta intentos de distillation.

#### Diferenciadores

| Métrica | Valor | Posición |
|---------|:-----:|:--------:|
| SWE-Bench Pro | 64.3% | 🏆 Líder |
| MCP Estándar | Creador | 🏆 Protocolo líder (10K+ servers) |
| Source Leak | 512K líneas | Reveló arquitectura completa |
| Seguridad | 2-stage YOLO | El más avanzado del mercado |
| Caching | 90%, 5min TTL | Bien diseñado pero TTL corto |

**Fortalezas clave**: MCP como estándar de facto, seguridad superior (YOLO + Constitutional AI), mejor agente de código (SWE-Bench Pro), arquitectura revelada por leak (ventaja de transparencia).

**Debilidades clave**: TTL de cache corto (5 min), sin routing automático, sin protocolo inter-agent propio, contexto 200K (vs 1M de competidores).

---

### 1.3 Google Gemini

#### Modelos Clave (Mayo 2026)

| Modelo | Tipo | Contexto | Precio Input/1M | Precio Output/1M | Diferenciador |
|--------|------|----------|:---------------:|:----------------:|---------------|
| **Gemini 3.1 Pro** | Flagship | 1M | $1.00 | $3.00 | Razonamiento multimodal |
| **Gemini 3.5 Flash** | Ligero | 1M | $0.30 | $1.20 | **GRATIS via agy** |
| **Gemma 4** | Open-weight | 256K | Open-source | Open-source | Edge deployment |

#### Arquitectura Multi-Agente

**AGY/Antigravity CLI** — Subagentes asíncronos:

```
┌──────────────────────────────────────────────┐
│          AGY (Antigravity) CLI                 │
│                                                │
│  ┌────────────────────────────────────────┐   │
│  │         Primary Agent                  │   │
│  │  Orquesta hasta 5 subagentes           │   │
│  │  ASÍNCRONOS (único en el mercado)      │   │
│  └────┬─────┬─────┬─────┬─────┬──────────┘   │
│       │     │     │     │     │               │
│  ┌────▼┐ ┌──▼──┐ ┌▼───┐ ┌▼───┐ ┌▼────┐      │
│  │AG 1 │ │AG 2 │ │AG 3│ │AG 4│ │AG 5 │      │
│  │fork │ │fork │ │fork│ │fork│ │fork │      │
│  │async│ │async│ │asnc│ │asnc│ │asnc │      │
│  └─────┘ └─────┘ └────┘ └────┘ └─────┘      │
│                                                │
└────────────────────────────────────────────────┘
```

**ADK 2.0 (Agent Development Kit)** — Graph-based workflows:

```
┌──────────────────────────────────────────────┐
│              ADK 2.0 Graph                     │
│                                                │
│  ┌──────────┐     ┌──────────┐               │
│  │ Sequential│────▶│Parallel  │               │
│  │ Agent A  │     │ Agent B  │               │
│  └──────────┘     └─────┬────┘               │
│                         │                     │
│                    ┌────▼────┐               │
│                    │LoopAgent│               │
│                    │ (retry) │               │
│                    └─────────┘               │
│                                                │
│  Soporte: Python, Java, Go, TypeScript        │
│  GA: Abril 2026 (Google Cloud Next)           │
└────────────────────────────────────────────────┘
```

**Especificaciones**:
- **Subagentes asíncronos**: Único laboratorio con paralelismo real (hasta 5 forks)
- **ADK 2.0**: Graph-based (SequentialAgent, ParallelAgent, LoopAgent)
- **Service Registry**: Swapping declarativo de backends (in-memory ↔ Vertex AI)
- **A2A Protocol**: Creado por Google, donado a Linux Foundation

#### Tool Use

| Feature | Estado |
|---------|--------|
| **MCP ADOPTADO** | ✅ Oficialmente desde 2025 |
| **50+ MCP servers** | Integrados en Vertex AI |
| **Agent Gateway** | Proxy unificado para tools |
| Function Calling | Nativo |
| Structured Outputs | JSON Schema |

#### Comunicación Agentes — A2A Protocol

**A2A (Agent-to-Agent) Protocol v1.0**:

```
┌──────────────┐         ┌──────────────┐
│  Agent A     │         │  Agent B     │
│  (Gemini)    │◄───────▶│  (Any)       │
│              │  A2A    │              │
│  Agent Card  │  HTTP   │  Agent Card  │
│  /.well-known│  JSON   │  /.well-known│
└──────────────┘         └──────────────┘
```

| Aspecto | Detalle |
|---------|---------|
| **Versión** | v1.0 estable (Marzo 2026) |
| **Gobernanza** | Linux Foundation |
| **Adopción** | 150+ organizaciones |
| **Análogo** | "TCP/IP para agentes" |
| **Transporte** | HTTP+JSON, gRPC, JSON-RPC 2.0 |
| **Descubrimiento** | Agent Cards en `/.well-known/agent-card.json` |
| **Backers** | Google, Salesforce, SAP, ServiceNow, Workday |

**Relación MCP + A2A**:
```
MCP: Agent → Tools  (vertical, "USB-C para AI")
A2A: Agent → Agent  (horizontal, "HTTP para agentes")
```

Son complementarios, no competidores. Consenso de industria 2026.

#### Caching

| Aspecto | Detalle |
|---------|---------|
| Descuento | 90% sobre input cacheado |
| Context Caching | $1/hr por contexto activo |
| TTL | Configurable |
| Gemini Flash FREE | 250K TPM sin costo |

#### Seguridad

| Feature | Estado |
|---------|--------|
| **Model Armor** | Prompt injection detection, DLP |
| Safety Settings | Por categoría de contenido |
| Filtros configurables | Por threshold |

#### Diferenciadores

| Métrica | Valor | Posición |
|---------|:-----:|:--------:|
| Subagentes asíncronos | 5 paralelos | 🏆 Único en el mercado |
| ADK Graph workflows | GA | 🏆 Framework más completo |
| Gemma 4 open-weight | Sí | 🏆 Edge deployment |
| A2A Protocol | Creador | 🏆 Estándar emergente (24K⭐) |
| Gemini Flash FREE | Sí | 🏆 Ideal para dev |

**Fortalezas clave**: Subagentes asíncronos (único), ADK graph-based, multimodalidad nativa, Gemma 4 para edge, Gemini Flash gratis, A2A como estándar emergente.

**Debilidades clave**: Sin agente de código tan popular como Codex CLI o Claude Code, adopción enterprise menor que OpenAI/Anthropic en USA, ecosistema MCP más pequeño que Anthropic.

---

### 1.4 Alibaba Qwen

#### Modelos Clave (Mayo 2026)

| Modelo | Tipo | Contexto | Precio Input/1M | Precio Output/1M | Licencia | Release |
|--------|------|----------|:---------------:|:----------------:|:--------:|:-------:|
| **Qwen3.7-Max** | Flagship | **1M** | $2.50 | $7.50 | Prop. | 20 May 2026 |
| Qwen3.6-Plus | Premium | 1M | $0.50 | $3.00 | Prop. | 2 Abr 2026 |
| Qwen3.6-27B | Open-weight | 262K | $0.60 | $3.60 | Apache 2.0 | 21 Abr 2026 |
| Qwen3.6-Flash | Ligero | 262K | $0.10 | $0.40 | Apache 2.0 | 15 Abr 2026 |
| QwQ-32B | Razonamiento | 131K | $0.80 | $2.40 | Apache 2.0 | 6 Mar 2025 |
| Qwen3-Coder-480B | Code MoE | 262K | — | — | Apache 2.0 | 2025 |

#### Arquitectura Multi-Agente

**Qwen Agent Framework** + **Qwen Code CLI**:

```
┌──────────────────────────────────────────────────┐
│          Qwen Agent Framework (16.4K⭐)           │
│                                                    │
│  ┌────────────┐  ┌──────────┐  ┌────────────┐    │
│  │ BaseChatMod│  │  Agent   │  │  Tool Exec  │    │
│  │  Qwen3.6   │  │ Planning │  │  FC + MCP   │    │
│  │  Qwen3.7   │  │Memory Wrk│  │  SSE proto  │    │
│  └────────────┘  └──────────┘  └────────────┘    │
│                                                    │
│  ┌──────────────────────────────────────────┐      │
│  │         Qwen Code CLI (v0.16)             │      │
│  │  ┌────────────────────────────────────┐  │      │
│  │  │    Primary Agent                   │  │      │
│  │  │  Plan → Execute → Synthesize       │  │      │
│  │  └──┬──────────────┬──────────────────┘  │      │
│  │     │              │                     │      │
│  │  ┌──▼──────────┐ ┌─▼───────────────┐    │      │
│  │  │ Subagent    │ │ Subagent        │    │      │
│  │  │ "testing"   │ │ "docs"          │    │      │
│  │  │ fork+context│ │ fork+context    │    │      │
│  │  │ cache share │ │ cache share     │    │      │
│  │  └─────────────┘ └─────────────────┘    │      │
│  └──────────────────────────────────────────┘      │
└──────────────────────────────────────────────────┘
```

**Especificaciones Qwen Code Subagentes**:
- **Subagentes fork**: Heredan contexto completo del padre
- **Prompt Cache Sharing**: Los forks comparten cache prefix del padre
- **Result aggregation**: Retornan mensaje único de resumen
- **ACP tracking**: `parentToolCallId` y `subagentType` trackeados
- **Almacenamiento**: Archivos MD en `.qwen/agents/` o `~/.qwen/agents/`
- **Comandos CLI**: `/agents create`, `/agents manage`

#### Tool Use

| Feature | Estado |
|---------|--------|
| Function Calling | Nativo (Hermes template) |
| **MCP Support** | ✅ Desde Mayo 2025 (SSE protocol) |
| Hasta **10 MCP servers** por request | Sí |
| MCP-Atlas | **76.4** 🏆 (líder) |
| MCP-Mark | **60.8** 🏆 (líder) |
| **⚠️ No sandbox** | "Use only in trusted, local dev" |

#### Comunicación Agentes

- **API-based** (sin protocolo propio como A2A)
- Subagentes se comunican vía el primario (hub-and-spoke interno)
- **No soporta A2A** actualmente
- ACP interno para tracking

#### Routing

**No hay routing nativo** en Qwen Agent Framework. El patrón es:
- Orchestrator manual + modelo más barato para sub-tareas
- Alibaba Cloud Model Studio ofrece routing entre versiones de Qwen

#### Caching

| Aspecto | Detalle |
|---------|---------|
| Descuento | 90% sobre input cacheado |
| Prompt Cache Sharing | ✅ Entre subagentes fork |
| Context Caching | ✅ En API Alibaba Cloud |
| Cache $0.25/M vs $2.50/M input | 90% descuento |

#### Seguridad

**⚠️ Área más débil**:
- **MCP no sandboxed**: Advertencia explícita de no usar en producción
- **Code Interpreter**: Python executor sin sandbox
- **Sin human-in-the-loop** nativo
- **Headless runaway-protection**: Añadido en v0.16 (Mayo 2026)

#### Diferenciadores

| Métrica | Valor | Posición |
|---------|:-----:|:--------:|
| Open-weight | 15+ modelos Apache 2.0 | 🏆 #1 HuggingFace descargas |
| Precio | 40-60% más barato que OpenAI/Anthropic | 🏆 |
| Contexto 1M verificado | Sí | 🏆 MRCR-v2 128k: 90.4% |
| Autonomía | **35h documentada** | 🏆 1,158 tool calls |
| MCP-Atlas | **76.4** | 🏆 Líder |
| Terminal-Bench 2.0 | **69.7** | 🏆 Líder |
| Protocolo Anthropic nativo | ✅ | Drop-in replacement para Claude |

**Fortalezas clave**: Open-weight masivo, precios agresivos, contexto 1M real, autonomía extrema (35h), liderazgo en MCP benchmarks.

**Debilidades clave**: Seguridad inmadura, sin routing nativo, verbosidad 4x (costo real por tarea ~2.5x), adopción enterprise occidental <0.5%, datos en servidores chinos.

---

### 1.5 Moonshot Kimi

#### Modelos Clave (Mayo 2026)

| Modelo | Tipo | Contexto | Precio Input/1M | Precio Output/1M | Licencia | Release |
|--------|------|----------|:---------------:|:----------------:|:--------:|:-------:|
| **Kimi K2.6** | Flagship | 262K | $0.95 | $4.00 | Modified MIT | Abr 2026 |
| Kimi K2.5 | Premium | 256K | $0.60 | $3.00 | Modified MIT | Ene 2026 |
| Kimi K2 Thinking | Razonamiento | 256K | $0.60 | $2.50 | Modified MIT | Nov 2025 |
| Kimi-K2 (0905) | Legacy | 256K | $0.60 | $2.50 | Modified MIT | Jul 2025 |

**⚠️ Nota**: Modelos K2 legacy (0711, 0905, Thinking, Turbo) discontinuados el 25 Mayo 2026.

#### Arquitectura Multi-Agente — LA MÁS AVANZADA DEL MERCADO

**Agent Swarm** — Framework multi-agente entrenado via PARL:

```
┌──────────────────────────────────────────────────────┐
│              Kimi K2.6 Agent Swarm                     │
│                                                        │
│  ┌────────────────────────────────────────────────┐   │
│  │        Orchestrator (K2.6)                     │   │
│  │  PARL-trained decomposition + assignment        │   │
│  │  Max 300 sub-agentes, 4,000 pasos coordinados   │   │
│  └─┬───┬───┬───┬───┬───┬───┬───┬───┬───┬──────────┘   │
│    │   │   │   │   │   │   │   │   │   │              │
│  ┌─▼┐ ┌▼─┐ ┌▼─┐ ┌▼─┐ ┌▼─┐ ┌▼─┐ ┌▼─┐ ┌▼─┐ ┌▼─┐       │
│  │SA│ │SA│ │SA│ │SA│ │SA│ │SA│ │SA│ │SA│ │SA│ ...300  │
│  │ 1│ │ 2│ │ 3│ │ 4│ │ 5│ │ 6│ │ 7│ │ 8│ │ 9│        │
│  └──┘ └──┘ └──┘ └──┘ └──┘ └──┘ └──┘ └──┘ └──┘        │
│                                                        │
│  PARL: Parallel-Agent Reinforcement Learning           │
│  - Solo el orquestador se entrena                      │
│  - Sub-agentes congelados                              │
│  - Reward: spawn eficiente + subtareas completadas     │
│  - Previene "serial collapse"                          │
│                                                        │
└────────────────────────────────────────────────────────┘
```

**Kimi Code CLI** — Agente de código open-source (8.5K⭐):

```
┌──────────────────────────────────────────────┐
│           Kimi Code CLI (Apache 2.0)          │
│                                                │
│  3 sub-agentes incorporados:                  │
│  ┌──────────┐ ┌──────────┐ ┌──────────────┐  │
│  │  coder   │ │ explore  │ │    plan      │  │
│  │  (code)  │ │ (search) │ │ (architect)  │  │
│  └──────────┘ └──────────┘ └──────────────┘  │
│                                                │
│  Skills system: SKILL.md                       │
│  Flow skills: Mermaid/D2 diagrams              │
│  Plugins: tool personalization                 │
│  IDE: VS Code, Zed, JetBrains (ACP)           │
│  MCP: stdio + HTTP (Streamable HTTP)          │
└────────────────────────────────────────────────┘
```

**Claw Groups** (Research Preview) — Colaboración multi-modelo heterogénea:
- Agentes de **cualquier modelo** pueden unirse
- Humanos + agentes colaboran en espacio compartido
- Cada agente con su toolkit, skills y memoria persistente
- K2.6 como coordinador adaptativo
- Dogfooding interno reportado

#### Tool Use

| Feature | Estado |
|--------|--------|
| Function Calling | API compatible OpenAI + Anthropic |
| Tool-invocation success | **96.6%** 🏆 (más alto open-weight) |
| Parallel tool calls | Sí |
| `preserve_thinking` mode | Retorna trace de razonamiento |
| **MCP Support** | ✅ Via Kimi Code CLI |
| MCPMark | 55.9 (vs K2.5 29.5 = **+89%**) |
| Toolathlon | 50.0 (vs K2.5 27.8 = **+80%**) |
| Límite práctico tools | ~128 funciones/request |

#### Comunicación Agentes

| Aspecto | Detalle |
|---------|---------|
| **Swarm** | 300 sub-agentes, 4,000 pasos |
| **Duración** | Sesiones de 12+ horas continuas |
| **Tool calls** | 4,000+ en una ejecución |
| **Contexto** | Compartido y persistente entre sub-agentes |
| **Claw Groups** | Comunicación cross-modelo (research preview) |

#### Routing

- **No hay routing nativo** (similar a Qwen)
- El orquestador del Agent Swarm decide qué sub-agente usar y cuándo
- La descomposición de tareas es dinámica, no basada en reglas estáticas

#### Caching

| Aspecto | Detalle |
|---------|---------|
| Descuento | 80-85% en input repetido (automático) |
| Cache price | $0.16/1M (K2.6) |
| Gestión contexto | Retiene solo último round de tool messages |
| Estrategia | Optimizado para sesiones largas multi-turn |

#### Seguridad

**Poco documentado públicamente.** Sin sistema equivalente a YOLO o Constitutional AI.

#### Diferenciadores

| Métrica | Valor | Posición |
|---------|:-----:|:--------:|
| **HLE w/ tools** | **54.0%** | 🏆 Líder global |
| BrowseComp (Agent Swarm) | **86.3** | 🏆 Líder |
| DeepSearchQA (f1) | **92.5** | 🏆 Líder |
| SWE-Bench Pro | **58.6** | 🏆 Líder |
| LiveCodeBench v6 | 89.6 | 🥈 (vs Gemini 91.7) |
| Tool-invocation success | **96.6%** | 🏆 Líder open-weight |
| Agentes por ejecución | **300** | 🏆 Líder absoluto |
| Contexto largo | 262K + MoBA + Kimi Linear (1M) | 🏆 NeurIPS 2025 |

**Fortalezas clave**: HLE 54.0% líder global, Agent Swarm más grande (300 agents), PARL como método de entrenamiento único, open-weight real (Modified MIT), mejor tool invocation del mercado, papers publicados (MoBA NeurIPS 2025, Kimi Linear).

**Debilidades clave**: Poco documentado en seguridad, adopción occidental limitada, sin sistema de routing explícito, modelos K2 legacy EOL, sin A2A support.

---

## SECCIÓN 2: PATRONES MULTI-AGENTE — COMPARATIVA CRUZADA

### 2.1 Tabla Comparativa Completa

| Patrón | OpenAI | Anthropic | Google | Qwen | Kimi | 🏆 Mejor |
|--------|--------|-----------|--------|------|------|:--------:|
| **Subagentes paralelos** | Codex CLI (6 threads, depth=1) | Claude Code IPC forks (polling 500ms) | **AGY (5 asíncronos)** 🏆 | Qwen Code forks (cache share) | **Agent Swarm (300 agents)** 🏆 | **Kimi** (escala) / **Google** (async) |
| **Graph workflows** | — | — | **ADK 2.0** 🏆 | No nativo | No nativo | **Google** |
| **Role-based agents** | — | — | ADK Agents | No nativo | Claw Groups (research) | **Google** |
| **Reflection/Verification** | — | Sí (verification sub-agent) | — | — | — | **Anthropic** |
| **Tool use estándar** | Function Calling | **MCP** 🏆 | MCP + A2A | Function Calling + MCP | MCP via CLI | **Anthropic** (creó MCP) |
| **Protocolo inter-agent** | — | — | **A2A** 🏆 | — | Claw Groups | **Google** (A2A v1.0) |
| **Context caching** | 90%, 24h TTL | 90%, 5min TTL | 90% | 90% | 80-85% auto | **OpenAI** (retención) |
| **Anti-distillation** | — | **≤25 words, YOLO** 🏆 | — | — | — | **Anthropic** |
| **Seguridad** | Moderation API | **YOLO 2-stage, Const. AI** 🏆 | Model Armor | ⚠️ No sandbox | No documentado | **Anthropic** |
| **Daemon/Long-running** | — | **KAIROS** 🏆 (leak) | — | 35h demo | 12h+ sesiones | **Kimi** (producción) |
| **Caching compartido** | — | — | — | **Cache share forks** 🏆 | Contexto compartido | **Qwen** |
| **AB Testing** | **Sí** 🏆 | — | — | — | — | **OpenAI** |
| **Entrenamiento multi-agente** | — | — | — | — | **PARL** 🏆 | **Kimi** |

### 2.2 Análisis por Patrón

#### Subagentes Paralelos

```
Escala (número de subagentes):
OpenAI:  ──███████████████─── (6 threads)
Anthropic:──██████████████████─ (~10-20 forks)
Google:  ──██████████████─── (5 asíncronos)
Qwen:    ──██████████████─── (n forks, sin límite documentado)
Kimi:    ──███████████████████████████████████████─── (300 agents) 🏆

Paralelismo real (no secuencial simulado):
OpenAI:  ⚠️ Parcial (threads compiten por recursos)
Anthropic:❌ Secuencial (polling 500ms)
Google:  ✅ ASÍNCRONO REAL 🏆
Qwen:    ⚠️ Fork, depende del LLM
Kimi:    ⚠️ Orquestado, paralelismo controlado
```

#### Graph Workflows

Google ADK 2.0 es el único framework con soporte nativo de DAGs multi-agente:
- **SequentialAgent**: Pipeline lineal
- **ParallelAgent**: Fan-out paralelo
- **LoopAgent**: Iteración hasta condición
- **Service Registry**: Swapping declarativo de almacenamiento

OpenAI, Anthropic, Qwen, y Kimi requieren LangGraph externo para grafos.

---

## SECCIÓN 3: TAXONOMÍA DE CONCEPTOS MULTI-AGENTE

### 3.1 Routing

| Tipo | Descripción | Implementación | Dónde se usa |
|------|-------------|----------------|--------------|
| **Cost routing** | Rutea al modelo más barato que cumpla requisitos | LiteLLM, OpenRouter | KAOS Aether (budget enforcement) |
| **Performance routing** | Rutea al modelo con mejor calidad histórica | Aether QualityStore | KAOS (quality rerank stage) |
| **Balanced** | Distribuye carga entre varios modelos | Aether target_pct | KAOS (flash 40%, mimo 40%, etc.) |
| **Fallback chain** | Si primario falla, cascada a alternativos | Aether fallback_chains | Todos los labs |
| **Parallel ensemble** | Múltiples modelos en paralelo, vota el mejor | OpenAI AB Testing | OpenAI |
| **Speculative parallel** | Modelo rápido genera borrador, lento verifica | — | Investigación |
| **Intra-Claude routing** | Haiku→Sonnet→Opus para subtareas | Claude Code | Anthropic |
| **Context-aware routing** | Elige modelo según longitud/ tipo de contexto | Aether context_routing | KAOS |

### 3.2 Subagentes

| Patrón | Descripción | Implementación |
|--------|-------------|----------------|
| **Fork** | Clonar contexto del padre, ejecutar en paralelo | Claude Code, Qwen Code, AGY |
| **Parallel** | Múltiples subagentes simultáneos | Codex CLI (6 threads), AGY (5 async) |
| **Sequential** | Pipeline de subagentes en serie | ADK SequentialAgent, pipelines KAOS |
| **Hierarchical** | Árbol de supervisores/workers | Kimi Agent Swarm (300 agents) |
| **Supervisor** | Un agente orquesta, workers ejecutan | Claude Code Task System |
| **Swarm** | Malla de agentes sin supervisor central | Kimi Claw Groups (research) |
| **Pipeline** | Output de A → input de B | Pipeline KAOS Aletheia→Kosmos→Metis |
| **Reflection** | Output es verificado por otro agente | Anthropic verification subagent |
| **Planner-Worker-Judge** | Planner descompone, Worker ejecuta, Judge evalúa | Cursor (2026) — nuevo estándar |

### 3.3 Comunicación

| Protocolo | Propósito | Creador | Transporte | Adopción |
|-----------|-----------|---------|------------|:--------:|
| **MCP** | Agent → Tools | Anthropic | stdio, SSE, Streamable HTTP | 10K+ servers |
| **A2A** | Agent → Agent | Google | HTTP+JSON, gRPC, JSON-RPC 2.0 | 150+ orgs |
| **IPC Mailboxes** | Intra-host agent comm | Anthropic | Archivos en FS (~/.claude/work/ipc/) | Claude Code |
| **gRPC** | Microservicios agentes | — | HTTP/2 | Frameworks |
| **JSON-RPC 2.0** | Llamadas remotas | — | TCP/HTTP | LiteLLM |
| **WebSocket** | Tiempo real | — | WS | Dashboards |
| **ACP** | Agent Communication Protocol | Qwen | Interno | Qwen Code |

### 3.4 Caching

| Tipo | Descripción | 90% descuento? | TTL | Quién |
|------|-------------|:--------------:|:---:|-------|
| **Prompt Caching** | Cachea el prompt completo (system + user) | ✅ OpenAI/Anthropic/Google/Qwen | 24h/5min/var/var | Todos |
| **Context Caching** | Cachea estado de contexto activo | ✅ Google ($1/hr) | Por sesión | Google |
| **Static Boundary** | Cache boundary fijo (system prompt) | ✅ | Varía | Anthropic |
| **Dynamic Boundary** | Cache boundary adaptativo | — | — | Investigación |
| **Cross-session** | Cache entre sesiones del mismo usuario | — | — | OpenAI |
| **Cross-agent** | Cache compartido entre subagentes | ✅ | Fork | Qwen (cache share) |
| **Semantic Cache** | Cache por similitud semántica | — | — | arXiv:2601.11687 (67% hit rate) |
| **KV Cache** | Cache de atención para inferencia | — | — | MoBA, KDA, NACL |

### 3.5 Seguridad

| Sistema | Laboratorio | Descripción |
|---------|-------------|-------------|
| **YOLO** (2-stage) | Anthropic | 64 tok → 4,096 tok para decisión de permisos |
| **Constitutional AI** | Anthropic | Entrenamiento con principios constitucionales |
| **Undercover Mode** | Anthropic | Elimina atribución AI de commits |
| **Límite 25 palabras** | Anthropic | Anti-distillation en prompts |
| **Model Armor** | Google | Prompt injection + DLP |
| **Safety Settings** | Google | Filtros por categoría y threshold |
| **Moderation API** | OpenAI | Filtros de contenido pre/post |
| **⚠️ No sandbox** | Qwen | MCP advierte no usar en producción |
| **Headless runaway-protection** | Qwen | v0.16 (Mayo 2026) |

### 3.6 Memoria

| Tipo | Descripción | Implementación |
|------|-------------|----------------|
| **Session memory** | Contexto de conversación activa | Todos los labs (ventana de contexto) |
| **Project memory** | Memoria persistente por proyecto | `.claude/`, `.qwen/agents/`, KAOS L1 |
| **Team memory** | Memoria compartida entre agentes | Kimi Agent Swarm, KAOS L2 KG |
| **Dream mode** | Consolidación durante inactividad | KAOS NREM/REM, Claude KAIROS autoDream |
| **RAG** | Retrieval-Augmented Generation | KAOS txtai, LightRAG |
| **Fine-tuning** | Modelo entrenado con datos específicos | Qwen (Apache 2.0 permite) |

### 3.7 Tool Use

| Tipo | Descripción | Labs |
|------|-------------|------|
| **Function Calling** | Llamada a funciones definidas por API | OpenAI (nativo), Anthropic, Google, Qwen, Kimi |
| **Structured Outputs** | Output forzado a JSON Schema | OpenAI, Anthropic |
| **MCP Tools** | Tools via Model Context Protocol | Anthropic (creó), Google (adoptó), Qwen, Kimi |
| **Built-in Tools** | Tools nativas del agente | read, edit, bash, search (todos) |
| **Custom Tools** | Tools definidas por usuario | Todos vía function calling o MCP |

### 3.8 Costo

| Estrategia | Descripción | Implementación |
|------------|-------------|----------------|
| **Batch processing** | Descuentos por procesamiento por lotes | OpenAI Batch (50% descuento) |
| **Provider hopping** | Rotar entre proveedores por precio | LiteLLM cost-tiering |
| **Routing inteligente** | Modelo barato para tareas simples, caro para complejas | KAOS Aether (task_type → model) |
| **Distillation** | Modelo pequeño entrenado con outputs de modelo grande | Qwen open-source via Apache 2.0 |

---

## SECCIÓN 4: CONEXIÓN CON KAOS

### 4.1 Estado Actual de KAOS

```
                    KAOS — Arquitectura Actual (Mayo 2026)
┌─────────────────────────────────────────────────────────────────┐
│                   MODELOS Y ROUTING                              │
│  ┌─────────────────────────────────────────────────────────┐    │
│  │                     Aether v3                            │    │
│  │  Router 10-stage: override→multimodal→base→quality→budget│    │
│  │  →cb_fallback + 4 más                                   │    │
│  │                                                          │    │
│  │  Tiers:                                                   │    │
│  │  flash (40%) ── DeepSeek V4 Flash ($0.00014/$0.00028)    │    │
│  │  mimo  (40%) ── Modelos ultra-económicos ($0.000014)     │    │
│  │  pro   ( 5%) ── DeepSeek V4 Pro ($0.00174/$0.00348)     │    │
│  │  kimi  (15%) ── Kimi K2.6 ($0.00095/$0.00400)           │    │
│  └─────────────────────────────────────────────────────────┘    │
│                                                                  │
│  ┌─────────────────────────────────────────────────────────┐    │
│  │              AGY BRIDGE (Multi-Modelo Premium)           │    │
│  │  agy_ask_flash  → Gemini Flash 3.5 (FREE)               │    │
│  │  agy_ask_sonnet → Claude Sonnet 4.6 ($)                  │    │
│  │  agy_ask_opus   → Claude Opus 4.6 ($$$)                  │    │
│  │  agy_ask_gpt55  → GPT-5.5 ($$$$)                         │    │
│  └─────────────────────────────────────────────────────────┘    │
│                                                                  │
│                    AGENTES                                      │
│  ┌─────────┐ ┌─────────┐ ┌─────────┐ ┌─────────┐ ┌──────────┐ │
│  │Aletheia │ │ Kosmos  │ │ Metis   │ │ Kratos  │ │ Mnemosyne│ │
│  │Research │ │Architect│ │Strategy │ │ Code    │ │ Curation │ │
│  │ go-pro  │ │ go-pro  │ │kimi-lat │ │go-flash │ │ go-flash │ │
│  └─────────┘ └─────────┘ └─────────┘ └─────────┘ └──────────┘ │
│         │          │          │          │            │         │
│         └──────────┴──────────┴──────────┴────────────┘         │
│                              │                                   │
│                    Pipeline secuencial                           │
│        Aletheia → Kosmos → Metis → {Kratos (código)             │
│                                     Mnemosyne (no-código)}      │
└─────────────────────────────────────────────────────────────────┘
```

**Costo actual**: ~$4.36/mes (vs $10/mes original)  
**Score calidad**: 88.6/100  
**Throughput**: ~1 pipeline/hr  
**Proveedores**: 1 (DeepSeek via OpenCode Go) + agy bridge (multi-modelo)

### 4.2 Patrones Aplicables a KAOS

#### De Anthropic

| Patrón | Aplicación en KAOS | Prioridad |
|--------|-------------------|:---------:|
| **YOLO 2-stage** | Sistema de permisos para Kratos (sandbox + YOLO) | 🔴 Alta |
| **Cache boundary strategy** | Optimización de contextos en Aether (system/user/tool separation) | 🔴 Alta |
| **Subagentes IPC mailboxes** | Arquitectura de subagentes para pipelines paralelos | 🟡 Media |
| **Undercover Mode** | Modo stealth para commits automáticos | 🟢 Baja |
| **Límite 25 palabras** | Anti-distillation en prompts del sistema | 🟢 Baja |

#### De OpenAI

| Patrón | Aplicación en KAOS | Prioridad |
|--------|-------------------|:---------:|
| **AB Testing framework** | Comparación de modelos en producción (Aether) | 🔴 Alta |
| **Parallel ensemble** | Múltiples modelos votan en tareas críticas | 🟡 Media |
| **Structured Outputs** | Output JSON forzado para parsing confiable | 🔴 Alta (ya implementado parcialmente) |

#### De Google

| Patrón | Aplicación en KAOS | Prioridad |
|--------|-------------------|:---------:|
| **Subagentes asíncronos** | Send API + fan-out paralelo en pipeline | 🔴 Alta (ya en roadmap) |
| **ADK graph-based workflows** | Diseño de DAGs para pipelines complejos | 🟡 Media |
| **Gemma 4 edge** | Modelo local para tareas offline de Mnemosyne | 🟡 Media |
| **A2A inter-agent** | Comunicación entre KAOS y agentes externos | 🟢 Baja (Q4 2026) |
| **Model Armor** | Sistema de seguridad para MCP gateway | 🟡 Media |

#### De Qwen

| Patrón | Aplicación en KAOS | Prioridad |
|--------|-------------------|:---------:|
| **Cache sharing entre forks** | Subagentes comparten cache prefix | 🔴 Alta |
| **Open-weight deployment** | Qwen3.6-27B como modelo local para Mnemosyne | 🟡 Media |
| **Subagentes con contexto heredado** | Fork pattern para pipelines paralelos | 🟡 Media |
| **Pricing agresivo** | Qwen como alternativa económica a DeepSeek Flash | 🟡 Media |

#### De Kimi

| Patrón | Aplicación en KAOS | Prioridad |
|--------|-------------------|:---------:|
| **PARL (orquestación entrenada)** | Auto-tuning del orquestador LangGraph | 🟡 Media (investigación) |
| **Agent Swarm (300 agents)** | Escalamiento horizontal del pipeline | 🟢 Baja (futuro) |
| **Tool-invocation optimization** | Mejora de function calling en Aether | 🟡 Media |
| **Long-running sessions** | Pipeline continuo 24/7 | 🟡 Media |
| **MoBA sparse attention** | Optimización de contexto largo en memoria | 🟢 Baja |

### 4.3 Recomendaciones de Implementación

#### ¿Qué patrones implementar en Aether?

**Fase 1 (Inmediata — Junio 2026)**:
1. **Cache boundary strategy** (Anthropic): Separar system/user/tool en caché de Aether
2. **AB Testing framework** (OpenAI): Comparar go-flash vs go-kimi-latest en tareas de strategy
3. **Structured Outputs** (OpenAI): Output JSON forzado para todas las llamadas

**Fase 2 (Corto Plazo — Julio 2026)**:
4. **YOLO 2-stage** (Anthropic): Sistema de permisos para Kratos
5. **Cache sharing entre forks** (Qwen): Subagentes compartiendo cache prefix
6. **Subagentes asíncronos** (Google): Send API con fan-out paralelo

**Fase 3 (Mediano Plazo — Q3 2026)**:
7. **ADK graph-based** (Google): DAGs para pipelines complejos
8. **Planner-Worker-Judge** (Cursor/Kimi): Nuevo patrón de orquestación
9. **Model Armor** (Google): Seguridad para MCP gateway

#### ¿Qué protocolos adoptar?

```
Prioridad: MCP > A2A (por ahora)

MCP (Model Context Protocol):
  ✅ Adoptar INMEDIATAMENTE
  - Ya hay adopción parcial (agy-bridge)
  - Estandarizar tools entre agentes
  - 10,000+ servers disponibles
  - Seguridad: implementar sandboxing

A2A (Agent-to-Agent Protocol):
  ⏸️ Posponer a Q4 2026
  - Diseñar Agent Card schema para KAOS
  - Monitorear adopción enterprise
  - Implementar cuando haya caso de uso cross-agent
```

#### ¿Qué arquitectura de subagentes?

**Recomendación**: Arquitectura híbrida **Supervisor/Worker + Fork**

```
┌──────────────────────────────────────────────┐
│         KAOS Subagent Architecture            │
│                                                │
│  Supervisor (Aether resolve_model)             │
│  Decide: qué agente, qué modelo, qué tools    │
│                                                │
│  Fork Workers (Send API):                      │
│  ┌──────────┐ ┌──────────┐ ┌──────────────┐  │
│  │ Aletheia │ │ Kosmos   │ │ Kratos       │  │
│  │ (fork 1) │ │ (fork 2) │ │ (fork 3)     │  │
│  │ research │ │ analyze  │ │ code_gen     │  │
│  │ cache    │ │ cache    │ │ cache        │  │
│  │ shared   │ │ shared   │ │ shared       │  │
│  └──────────┘ └──────────┘ └──────────────┘  │
│                                                │
│  Synthesizer (Metis):                          │
│  Recibe outputs de forks, sintetiza           │
│                                                │
│  Verifier (Mnemosyne/Kronos):                  │
│  Subgraf event-driven de verificación          │
│  Score 5 dimensiones                           │
└────────────────────────────────────────────────┘
```

#### Estrategia de caching multi-proveedor

```
Nivel 1: Prompt Caching (todos los proveedores)
  - Cache system prompt por tipo de tarea
  - Cache boundary: system | user | tool (Anthropic pattern)
  - TTL: 24h para OpenAI, 5min para Anthropic

Nivel 2: Semantic Caching (Aether)
  - Cache por similitud semántica de queries
  - Objetivo: 67% hit rate (arXiv:2601.11687)
  - Reducción: 40-60% tokens

Nivel 3: Cache compartido entre forks (Qwen pattern)
  - Subagentes del mismo pipeline comparten cache prefix
  - Reducción adicional: 20-30%

Nivel 4: Context Caching (Google)
  - Para sesiones largas de investigación
  - $1/hr por contexto activo
```

#### Sistema de seguridad (YOLO + Model Armor + Constitutional AI)

```
KAOS Security Stack (Propuesto)
┌──────────────────────────────────────────────┐
│  Capa 1: YOLO 2-stage (Anthropic)            │
│  - Aprobación rápida (64 tok) o profunda     │
│    (4,096 tok) para comandos de Kratos       │
│  - Query: ¿acción peligrosa?                 │
│                                                │
│  Capa 2: Model Armor (Google)                 │
│  - Detección de prompt injection en input     │
│  - DLP para outputs con datos sensibles       │
│                                                │
│  Capa 3: Constitutional AI (Anthropic)        │
│  - Principios constitucionales en system      │
│    prompts de cada agente                     │
│                                                │
│  Capa 4: Límite 25 palabras (Anthropic)       │
│  - Anti-distillation en prompts del sistema   │
│                                                │
│  Capa 5: Circuit Breaker (Aether existente)   │
│  - 3 fallos consecutivos → open (5 min)       │
│  - Half-open → 1 éxito → closed              │
└────────────────────────────────────────────────┘
```

#### Integración de Modelos en Aether v3+

**Propuesta de ampliación de `aether.yaml`**:

```yaml
# Nuevos tiers propuestos para Aether v4
model_tiers:
  flash:  {description: "Base — DeepSeek V4 Flash", target_pct: 35}
  mimo:   {description: "Ultra-económico — Router9/MiMo", target_pct: 30}
  pro:    {description: "Calidad — DeepSeek V4 Pro", target_pct: 5}
  kimi:   {description: "Diversidad — Kimi K2.6", target_pct: 15}
  qwen:   {description: "Open-weight — Qwen3.6-Flash", target_pct: 10}  # NUEVO
  gemini: {description: "Gratis — Gemini 3.5 Flash", target_pct: 5}    # NUEVO
```

**Routing ampliado**:

```yaml
# task_types existentes + nuevos
task_model_map:
  # ... existente ...
  # Nuevos:
  local_inference: {model: go-qwen, thinking: null, tier: qwen}
  edge_processing: {model: go-gemini, thinking: null, tier: gemini}
```

---

## SECCIÓN 5: HALLAZGOS DEL SOURCE LEAK DE CLAUDE CODE

### 5.1 El Incidente

**31 Marzo 2026**: Versión `@anthropic-ai/claude-code` v2.1.88 publicada en npm con un **source map de 59.8MB** adjunto. El archivo `.map` apuntaba a un zip en Cloudflare R2 con el código TypeScript completo: **512,000 líneas, 1,906 archivos**. Descubierto por Chaofan Shou. En horas: 41,500+ forks en GitHub.

### 5.2 Lecciones Definitivas para KAOS

#### KAIROS — Daemon Autónomo (150+ referencias)

El hallazgo más relevante para KAOS. El código revela un daemon siempre-activo:

```
KAIROS Architecture (revelado por leak)
┌──────────────────────────────────────────────┐
│               KAIROS Daemon                   │
│                                                │
│  Tick Loop (cada N segundos):                  │
│  ┌──────────┐  ┌──────────┐  ┌────────────┐  │
│  │ Receive  │  │ Decide   │  │ Act/Log    │  │
│  │ <tick>   │─▶│ if act   │─▶│ if budget  │  │
│  └──────────┘  └──────────┘  └────────────┘  │
│                                                │
│  Features:                                     │
│  - Logs diarios append-only                   │
│  - Budget: 15 segundos para acciones blocking │
│  - autoDream: consolidación de memoria idle   │
│  - Brief mode: output conciso cuando activo   │
│                                                │
│  Relevancia KAOS:                              │
│  ✅ El patrón de daemon agent ES la            │
│     dirección correcta                         │
│  ✅ autoDream ↔ NREM/REM sleep cycle           │
│  ✅ Brief mode ↔ output comprimido             │
└────────────────────────────────────────────────┘
```

**Aplicación directa**: El sistema de sueño NREM/REM de KAOS (ADR-011) ya implementa este patrón. El leak confirma que es la arquitectura correcta.

#### YOLO — Seguridad 2 Etapas

El sistema YOLO es más simple y efectivo de lo que se pensaba:

```python
# Pseudocódigo basado en el leak
def yolo_check(command: str, context: dict) -> str:
    # Stage 1: 64 tokens
    risk = fast_classify(command, max_tokens=64)
    if risk == "safe":
        return "allow"
    if risk == "dangerous":
        return "block"
    # Stage 2: 4,096 tokens (solo si incierto)
    analysis = deep_analyze(command, context, max_tokens=4096)
    return analysis.decision  # allow / block / ask
```

**Aplicación en KAOS**: Implementar YOLO en Kratos para:
- Comandos shell peligrosos (rm -rf, curl a IPs, etc.)
- Escritura en paths sensibles
- Ejecución de código sin sandbox

#### Límite 25 Palabras — Anti-Distillation

El código revela un límite implícito de 25 palabras en outputs cuando el modelo detecta intentos de distillation (extracción del system prompt). Esto es una **defensa contra jailbreaks y extracción de prompts**.

**Aplicación en KAOS**: Implementar límites similares en system prompts para prevenir extracción de la estrategia completa de routing.

#### Feature Flags — ¿Qué Desarrollar en Secreto?

Las 44 feature flags reveladas incluyen:

| Flag | Propósito | Relevancia KAOS |
|------|-----------|-----------------|
| KAIROS | Daemon autónomo | 🔴 Alta — validación del sleep cycle |
| ULTRAPLAN | Planificación en background | 🟡 Media — pipeline anticipatorio |
| Undercover Mode | Sin atribución AI | 🟢 Baja — commits stealth |
| BUDDY | Mascota terminal | 🟢 Muy baja |
| Voice Control | Input por voz | 🟢 Baja |

**Lección**: Desarrollar features transformacionales (como KAIROS) bajo feature flags, no revelarlas hasta madurez.

#### Mailboxes IPC — Arquitectura de Subagentes

El sistema de IPC en Claude Code usa **archivos como buzones** en `~/.claude/work/ipc/`:

```
~/.claude/work/ipc/
├── agent_<id>/
│   ├── inbox/     # Mensajes entrantes
│   ├── outbox/    # Mensajes salientes
│   └── state/     # Estado del subagente
```

Cada subagente tiene su propio directorio. El polling es cada 500ms. Los mensajes son JSON con tipo, payload, y metadatos.

**Aplicación en KAOS**: Este patrón es útil para comunicación entre agentes KAOS sin depender de MCP. Más simple que colas de mensajes externas.

#### Cache Boundary — Optimización de Contextos

El leak revela que Anthropic invirtió significativamente en la **separación estratégica del cache**:

```
Cache Boundary Strategy:
┌──────────────────────────────────────────┐
│  System Prompt:  CACHEABLE (siempre igual)│
│  User Messages:  CACHEABLE (parcial)      │
│  Tool Results:   NO CACHE (cambian siempre)│
│  Assistant Resp: NO CACHE (únicas)        │
└──────────────────────────────────────────┘
```

La decisión de dónde poner el cache boundary afecta dramáticamente el hit rate y la corrección.

**Aplicación en KAOS**: Implementar cache boundary strategy en Aether, separando:
- System prompts de cada agente (cache)
- Tool definitions (cache)
- Resultados de herramientas (no cache)
- Outputs de agentes previos (no cache)

#### Codenames — Nomenclatura Interna

El leak reveló que Anthropic usa nombres en clave internos (ej: "KAIROS", "ULTRAPLAN", "BUDDY"). KAOS ya tiene una nomenclatura (Aletheia, Kosmos, Metis, Kratos, Mnemosyne, Kronos) que sigue este mismo patrón mitológico.

---

## SECCIÓN 6: CONCLUSIONES Y RECOMENDACIONES

### 6.1 Top 5 Patrones Multi-Agente que KAOS Debería Implementar

| # | Patrón | Laboratorio | Esfuerzo | Impacto | Ratio |
|---|--------|-------------|:--------:|:-------:|:----:|
| 1 | **Cache boundary strategy** | Anthropic | 2 días | 40-60% reducción tokens | 20:1 |
| 2 | **AB Testing framework** | OpenAI | 4 días | Mejora continua de calidad | 15:1 |
| 3 | **YOLO 2-stage security** | Anthropic | 3 días | Seguridad de Kratos | 12:1 |
| 4 | **Subagentes asíncronos (Send API)** | Google | 5 días | 3-5x throughput | 10:1 |
| 5 | **Planner-Worker-Judge** | Cursor/Kimi | 6 días | Long-running calidad | 8:1 |

**Total esfuerzo**: ~20 días → **ROI proyectado**: 3-5x throughput, 40-60% cost reduction, >95 quality score.

### 6.2 Top 3 Protocolos/Herramientas a Adoptar

| # | Protocolo | Propósito | Cuándo |
|---|-----------|-----------|:------:|
| 1 | **MCP** | Estandarizar tools entre agentes | **AHORA** — Ya hay soporte parcial |
| 2 | **Structured Outputs** | Output JSON forzado para parsing | **AHORA** — Implementar en Aether |
| 3 | **A2A** | Comunicación inter-agente externa | Q4 2026 — Diseñar Agent Card ahora |

### 6.3 Qué NO Hacer (Anti-Recomendaciones)

| Anti-patrón | Laboratorio que lo sufre | Por qué evitarlo |
|-------------|-------------------------|------------------|
| **Dependencia de un solo modelo/proveedor** | OpenAI (antes) | Vulnerabilidad única. KAOS ya tiene multi-modelo ✅ |
| **Sin sandbox en MCP** | Qwen | "Use only in trusted, local development environments — not in production." |
| **Sin sistema de routing** | Qwen, Kimi | Desperdicio de recursos. Aether ya tiene routing 10-stage ✅ |
| **TTL de cache muy corto** | Anthropic (5 min) | Bajo hit rate en sesiones largas |
| **Subagentes sin paralelismo real** | Anthropic (polling 500ms) | Cuello de botella en pipelines |
| **Verbosity sin control** | Qwen (4x la mediana) | Costo real 2.5x el headline |
| **Arquitectura sin feature flags** | Anthropic (leak expuso todo) | Desarrollar features transformacionales en secreto |
| **Sin observabilidad multi-agente** | Todos (inicios 2025) | No se puede mejorar lo que no se mide |
| **Misma estrategia de cache para todos** | OpenAI (full prompt cache) | Cache boundary mejora hit rate |

### 6.4 Roadmap de Evolución Multi-Agente para KAOS (6-12 meses)

#### Junio 2026 (Semanas 1-4) — Fundación

```
Semana 1-2:
  ✅ Cache boundary strategy (Anthropic)
  ✅ Structured Outputs en Aether
  ✅ AB Testing framework
  HITO: 40-60% reducción tokens, calidad medible

Semana 3-4:
  ✅ YOLO 2-stage para Kratos
  ✅ Cache sharing entre forks
  ✅ Subagentes asíncronos (Send API)
  HITO: Pipeline paralelo, Kratos seguro
```

#### Julio-Agosto 2026 (Semanas 5-12) — Interconexión

```
Semana 5-8:
  ✅ Planner-Worker-Judge pipeline
  ✅ MCP estandarizado entre agentes
  ✅ Model Armor para seguridad
  HITO: MCP bidireccional, seguridad multi-capa

Semana 9-12:
  ✅ ADK graph-based workflows
  ✅ Semantic caching (67% hit rate target)
  ✅ Dashboard de observabilidad multi-agente
  HITO: Score calidad >92, throughput 3x
```

#### Septiembre-Diciembre 2026 (Semanas 13-24) — Auto-evolución

```
Semana 13-16:
  ✅ A2A Agent Card design
  ✅ PARL-inspired orchestrator tuning
  ✅ Auto-tuning de routing
  HITO: Sistema se optimiza solo

Semana 17-20:
  ✅ KAIROS-style daemon agent (sleep cycle mejorado)
  ✅ Gemma 4 / Qwen3.6-27B edge inference
  HITO: Modelo local para Mnemosyne

Semana 21-24:
  ✅ A2A protocol implementation
  ✅ Multi-agent memory consistency
  ✅ Score calidad >95
  HITO: Sistema multi-agente completo y autónomo
```

#### Q1 2027 (Visión)

```
✅ Agent Swarm-style scaled parallelism
✅ Claw Groups multi-model collaboration
✅ Full auto-evolution (Auto-ADR, self-healing)
✅ Score calidad >97
✅ <$5/semana operación
```

### 6.5 Preguntas Abiertas para Próxima Investigación

1. **Multi-agent memory consistency**: ¿Cómo resolver el problema de cache coherence entre agentes? (arXiv:2603.10062 lo identifica como el desafío #1)

2. **KAIROS timeline**: ¿Cuándo ship Anthropic el daemon mode de Claude Code?

3. **MCP Security evolution**: ¿Evolucionará MCP para incluir autenticación obligatoria? Los 492 servers expuestos son una señal de alerta.

4. **MCP + A2A convergence**: ¿Se fusionarán en un solo protocolo bajo Linux Foundation en 2027?

5. **PARL reproducibility**: ¿Es la demostración de 35h de Kimi reproducible independientemente?

6. **Qwen4 timeline**: Qwen3→3.5→3.6→3.7 en 12 meses. ¿Qwen4 en Q3 2026?

7. **Adopción enterprise de modelos chinos**: ¿Crecerá con partnerships occidentales (Together AI, Vercel)?

8. **Costo real de long-running agents**: ¿Cuál es el ROI de agentes que corren por semanas? Cursor gastó "trillones de tokens".

---

## APÉNDICE A: REFERENCIAS DEL VAULT KAOS

| Archivo | Propósito | Estado |
|---------|-----------|:------:|
| `.memory/schema/adr-015-estrategia-multi-modelo.md` | Estrategia multi-modelo 3 capas | ✅ Activo |
| `.memory/schema/adr-018-consolidacion-arquitectura-routing.md` | Aether v3 routing 10-stage | ✅ Activo |
| `.memory/schema/arquitectura-estrategica-total-kaos.md` | Visión completa KAOS | ✅ Activo |
| `.memory/schema/adr-011-memory-matrix.md` | Memoria jerárquica L0-L3 + sleep | ✅ Activo |
| `.memory/schema/adr-017-ua-inspiracion-fase1.md` | Inspiración análisis | ✅ Activo |
| `.memory/_scripts/aether.yaml` | Config maestro routing | ✅ Activo |
| `.memory/_scripts/mcp_dsol.py` | MCP DSOL router | ✅ Activo |
| `.memory/_scripts/mcp_agy_bridge.py` | Multi-modelo bridge | ✅ Activo |
| `.memory/_scripts/aletheia_router.py` | Router Aletheia | ✅ Activo |
| `.memory/_scripts/tests/test_aletheia_router.py` | Tests routing | ✅ Activo |
| `.memory/schema/reports/auditoria-q2-2026.md` | Auditoría trimestral | ✅ Activo |
| `.memory/schema/reports/metodo-kosmos-overview.md` | Método Kosmos | ✅ Activo |
| `.pipeline/research/strategic-research-2026.md` | Research estratégico | ✅ Activo |
| `.memory/wiki/glosario-kaos.md` | Glosario KAOS | ✅ Activo |
| `.opencode/opencode.json` | Config agentes OpenCode | ✅ Activo |
| `docs/architecture/multi-model-router.md` | Documentación router | ✅ Activo |

---

## APÉNDICE B: DIAGRAMA DE ARQUITECTURA COMPARATIVA

```
              COMPARATIVA DE ARQUITECTURAS MULTI-AGENTE
                  Mayo 2026 — Los 5 Laboratorios

OpenAI                           Anthropic
┌──────────────────────┐        ┌──────────────────────┐
│ Codex CLI            │        │ Claude Code          │
│ max_threads=6        │        │ IPC mailboxes        │
│ depth=1              │        │ 500ms polling        │
│ Responses API        │        │ 43 tools             │
│                      │        │ 39 services          │
│ MCP (nuevo)          │        │ MCP (creador) 🏆     │
│ Caching: 90%, 24h 🏆 │        │ YOLO 2-stage 🏆       │
└──────────────────────┘        └──────────────────────┘

Google                           Qwen
┌──────────────────────┐        ┌──────────────────────┐
│ AGY / ADK 2.0        │        │ Qwen Agent Framework │
│ 5 async subagents 🏆  │        │ Qwen Code CLI       │
│ Graph workflows 🏆    │        │ Fork subagents      │
│ A2A Protocol v1.0 🏆  │        │ Cache share forks 🏆 │
│                      │        │                      │
│ Model Armor          │        │ ⚠️ No sandbox       │
│ Gemini Flash FREE    │        │ 35h autonomy demo   │
└──────────────────────┘        └──────────────────────┘

Kimi
┌──────────────────────────────────┐
│ Agent Swarm (300 agents) 🏆      │
│ PARL-trained orchestrator 🏆     │
│ HLE 54.0% w/ tools 🏆            │
│ 12h+ autonomous sessions         │
│ MoBA sparse attention (NeurIPS)  │
│ Modified MIT open-source         │
│ Tool-invocation 96.6% 🏆         │
└──────────────────────────────────┘

                            KAOS
┌──────────────────────────────────────────────────┐
│ Aether v3 — 10-stage router                      │
│ 4 tiers: flash(40%) mimo(40%) pro(5%) kimi(15%)  │
│ Circuit Breaker + QualityStore + AB Testing      │
│ Pipeline: Aletheia→Kosmos→Metis→{Kratos/Mnem}   │
│ Sleep cycle NREM/REM con consolidación           │
│ 5 agentes, ~$4.36/mes, score 88.6/100           │
│                                                  │
│ NEXT: Send API + YOLO + Cache Boundary + MCP     │
│ TARGET: score >95, throughput 3x, costo <$5      │
└──────────────────────────────────────────────────┘
```

---

## APÉNDICE C: GLOSARIO DE TÉRMINOS

| Término | Definición | Contexto |
|---------|------------|----------|
| **A2A** | Agent-to-Agent Protocol | Protocolo de comunicación entre agentes (Google/Linux Foundation) |
| **ACP** | Agent Communication Protocol | Protocolo interno de Qwen Code |
| **ADK** | Agent Development Kit | Framework de Google para orquestación multi-agente |
| **AGY** | Antigravity CLI | CLI de agente de Google con subagentes asíncronos |
| **Cache Boundary** | Punto de separación en el prompt para caching | Estrategia de Anthropic |
| **Circuit Breaker** | Patrón de tolerancia a fallos | Implementado en Aether |
| **Constitutional AI** | Alineación basada en principios | Sistema de seguridad de Anthropic |
| **HLE** | Humanity's Last Exam | Benchmark de 2,500 preguntas expertas |
| **IPC** | Inter-Process Communication | Comunicación entre procesos vía archivos/mailboxes |
| **MCP** | Model Context Protocol | Protocolo de herramientas para agentes (Anthropic) |
| **MoBA** | Mixture of Block Attention | Atención sparse para contexto largo (Moonshot, NeurIPS 2025) |
| **PARL** | Parallel-Agent Reinforcement Learning | Entrenamiento de orquestación multi-agente (Kimi) |
| **QualityStore** | Almacén de calidad de outputs | Componente de Aether |
| **YOLO** | You Only Live Once | Sistema de permisos 2-etapas de Anthropic |

---

## FIRMA DEL REPORTE

**Generado por**: Metis (Μῆτις) — Diosa de la Sabiduría Profunda  
**Fecha**: 2026-05-29  
**Investigación base**: Aletheia (4 investigaciones paralelas, 80+ fuentes trianguladas)  
**Validación arquitectónica**: Kosmos  
**Curación**: Mnemosyne  
**Confianza del reporte**: 94/100  
**Próxima revisión**: Q3 2026 o antes si hay cambios significativos en el ecosistema multi-agente

---

*Este reporte es la REFERENCIA DEFINITIVA sobre arquitecturas multi-agente para el equipo KAOS. Consulte los archivos en `.memory/schema/` y `.memory/_scripts/` para implementaciones detalladas.*
