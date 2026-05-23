---
type: investigation
agent: aletheia
date: 2026-05-19
confidence: media
status: complete
tags: [memoria-persistente, agentes-ia, langgraph, crewai, autogen, openai-assistants]
---

# Investigación: Modelos de Agentes con Memoria Persistente

## Pregunta Central
¿Cómo se comparan las implementaciones actuales de memoria persistente en los frameworks de agentes de IA más utilizados en 2026 (LangGraph, CrewAI, AutoGen/Microsoft Agent Framework, OpenAI Agents SDK)?

## Sub-preguntas
1. ¿Qué mecanismos de memoria ofrece cada framework (corto/largo plazo, entre sesiones)?
2. ¿Cómo se implementa técnicamente la persistencia (checkpointers, bases de datos vectoriales, almacenamiento externo)?
3. ¿Cuáles son las diferencias arquitectónicas clave en el modelo de estado?
4. ¿Qué limitaciones y casos de uso favorecen a cada framework?
5. ¿Cuál es el estado actual de desarrollo y la trayectoria de cada framework?

## Metodología Aplicada
- **Herramientas**: Web Search, Firecrawl, documentación oficial, GitHub
- **Alcance temporal**: Diciembre 2025 – Mayo 2026
- **Idiomas**: Inglés
- **Fuentes consultadas**: 15+ (documentación oficial, comparativas técnicas, artículos de análisis, repositorios GitHub, benchmarks independientes)

---

## Hallazgos Detallados

### 1. LangGraph — El estándar de producción para memoria persistente

LangGraph (LangChain, v1.0+ desde finales de 2025) modela los agentes como **máquinas de estado** con tres primitivas: nodos (funciones que procesan estado), aristas (transiciones, incluyendo routing condicional) y un esquema de estado tipado. Su sistema de memoria es el más maduro y con dos capas diferenciadas:

#### a) Checkpointers (memoria a corto plazo / por hilo)
- Cada ejecución de nodo genera un **checkpoint** automático — una instantánea completa del estado del grafo.
- Organizados por `thread_id`: dos conversaciones con distinto `thread_id` están completamente aisladas.
- Backends disponibles:
  - `InMemorySaver`: solo para debugging (TODO en RAM, se pierde al reiniciar).
  - `SqliteSaver`: persistencia local ligera.
  - `PostgresSaver` / `AsyncPostgresSaver`: producción, con connection pooling, concurrencia, transacciones.
  - `MongoDBSaver` / `RedisStore`: alternativas para producción.
- Permite **Time Travel**: inspeccionar cualquier checkpoint pasado, reproducir desde él o bifurcar (fork) la ejecución.
- Permite **durable execution**: si un worker muere, la siguiente petición retoma desde el último checkpoint completado.
- **Durability modes**: `sync` (checkpoint antes de cada paso — más seguro), `async` (en background — más rápido), `exit` (solo al finalizar — más rápido aún).

#### b) Store (memoria a largo plazo / entre hilos)
- Interfaz `BaseStore` — almacén clave-valor organizado por **namespaces** (tuplas de strings).
- Operaciones explícitas: `store.put()` para guardar hechos; `store.search()` para recuperar con búsqueda semántica.
- La memoria persiste **entre sesiones y entre usuarios** — no está atada a un thread.
- Backends: `InMemoryStore` (dev), `PostgresStore`, `MongoDBStore`, `RedisStore`.
- `PostgresStore` soporta **búsqueda por similitud vectorial** (semantic search) si se configura un embedding.
- El Store se inyecta automáticamente en las funciones nodo a través del objeto `Runtime` — no requiere cableado manual.

#### c) Integración con LangSmith
- Observabilidad nativa: trazado de cada paso, visualización del grafo, evaluación de rendimiento.
- Cumplimiento HIPAA/SOC2 disponible.

**Casos de uso ideales**: Workflows complejos multi-paso, procesos que duran horas/días, sistemas que requieren intervención humana, industrias reguladas.

**Limitaciones**: Curva de aprendizaje alta (2-4 semanas), overhead de serialización en cada checkpoint, mayor complejidad inicial.

---

### 2. CrewAI — Memoria unificada con análisis por LLM

CrewAI (2022+ estrellas GitHub) ofrece un **sistema de memoria unificado** recién rediseñado (PR #4420, febrero 2026). Reemplaza los 4 tipos separados (corto/largo plazo, entidad, contextual) con una única clase `Memory`.

#### a) Arquitectura de la memoria unificada
- Una API: `remember()`, `recall()`, `forget()`.
- En el guardado, el **LLM analiza el contenido** e infiere: ámbito (scope), categorías, importancia, metadatos (entidades, fechas, temas).
- En la recuperación, un `RecallFlow` multi-paso evalúa la complejidad de la consulta y profundiza cuando la confianza es baja.
- **Composite scoring**: blend de similitud semántica (50%), recencia (30%) e importancia (20%) — no solo distancia vectorial.
- `remember_many()` es **no bloqueante**: guarda en background mientras el agente continúa.

#### b) Storage backend
- **Default**: LanceDB, almacenado en `./.crewai/memory`.
- **Custom**: implementar el protocolo `StorageBackend` — permite conectar FAISS, Qdrant, PostgreSQL, etc.
- Soporte para PostgreSQL en desarrollo (PR #2892, cerrado como stale; pendiente de reestructuración).

#### c) Consolidación automática
- Al guardar, si la similitud con registros existentes supera `consolidation_threshold` (0.85 por defecto), el LLM decide si fusionar, actualizar o insertar.
- Evita duplicados y mantiene la base de conocimiento limpia.

#### d) Scopes jerárquicos
- Las memorias se organizan en un árbol de scopes (ej: `/`, `/project/alpha`, `/agent/researcher/findings`).
- Si no se especifica scope, el LLM lo infiere del contenido y del árbol existente.

**Casos de uso ideales**: Prototipado rápido, equipos multi-agente con roles (investigador, escritor, revisor), workflows lineales.

**Limitaciones**: SQLite como backend por defecto se vuelve cuello de botella en alta concurrencia; no tiene aislamiento multi-usuario nativo (requiere Mem0); la observabilidad es limitada comparada con LangSmith.

---

### 3. AutoGen (v0.4+) / Microsoft Agent Framework 1.0 — Estado serializable con memoria de protocolo

AutoGen de Microsoft ha tenido una transición significativa. El repositorio original (`microsoft/autogen`) entró en **modo mantenimiento** a favor del **Microsoft Agent Framework 1.0 GA** (anunciado el 3 de abril de 2026), que unifica AutoGen y Semantic Kernel en un solo SDK.

#### a) AutoGen v0.4 (AgentChat)
- Define un **protocolo `Memory`** con métodos: `query()`, `update_context()`, `add()`, `clear()`, `close()`.
- `ListMemory`: implementación simple basada en lista, cronológica, predecible.
- `ChromaDBVectorMemory`: memoria vectorial persistente con ChromaDB — búsqueda por similitud, umbral de score.
- La memoria se pasa como parámetro al `AssistantAgent`: `memory=[chroma_user_memory]`.
- **Save/Load State**: `save_state()` y `load_state()` en agentes, equipos (teams) y condiciones de terminación.
- El estado se serializa a JSON y puede persistirse en disco o base de datos.
- `BufferedChatCompletionContext`: limita el historial enviado al modelo para controlar tokens.

#### b) Microsoft Agent Framework 1.0 (Abril 2026)
- **AgentSession**: para estado de conversación persistente (similar al Store de LangGraph).
- **GraphFlow**: control de flujo explícito (paralelo a LangGraph).
- Soporte nativo de MCP (Model Context Protocol) para herramientas estandarizadas.
- Integración con Azure Monitor para observabilidad.
- Soporte .NET nativo para escalado horizontal.

**Casos de uso ideales**: Equipos Azure-native, sistemas que requieren interoperabilidad de protocolos, refinamiento iterativo.

**Limitaciones**: AutoGen v0.2/0.4 está en modo mantenimiento; el nuevo Agent Framework 1.0 tiene riesgo de estabilidad de API durante la migración; el modelo conversacional puede ser impredecible en costos y rutas de ejecución.

---

### 4. OpenAI Assistants API → Responses API — Memoria gestionada por el servidor (en transición)

OpenAI está migrando de la Assistants API (stateful, server-side) a la **Responses API** (stateless, client-side). La fecha límite para Assistants es el **26 de agosto de 2026** (febrero 2027 para Azure).

#### a) Assistants API (legado)
- **Threads**: contenedores de mensajes almacenados en servidores de OpenAI.
- Límite: 100,000 mensajes por thread.
- Retención: inicialmente 30-60 días; posteriormente indefinido hasta borrado manual.
- Truncación automática del contexto cuando excede la ventana del modelo.
- Vector Stores adjuntos a threads para búsqueda semántica (File Search).
- **Sin checkpointing local, sin time-travel debugging, sin control de residencia de datos.**

#### b) Responses API + Conversations API (nuevo estándar)
- **Stateless por defecto**: el cliente envía el historial completo en cada petición.
- **Conversations API**: almacenamiento server-side opcional (equivalente a Threads pero más flexible).
- Los items de la conversación pueden ser mensajes, tool calls, tool outputs y otros tipos de datos.
- `previous_response_id` para continuidad de contexto sin estado server-side.
- Nuevas capacidades: deep research, MCP, computer use.
- 40-80% mejora en cache utilization vs Assistants API.

**Casos de uso ideales**: Stack OpenAI-native, prototipado rápido, workflows simples de handoff.

**Limitaciones**: Lock-in a OpenAI (sin Claude, Gemini ni modelos open-source); sin checkpointing local; sin control de residencia de datos; no apto para workflows largos o que requieran durable execution.

---

### 5. Comparativa transversal

| Dimensión | LangGraph | CrewAI | AutoGen / MAF 1.0 | OpenAI (Assistants → Responses) |
|-----------|-----------|--------|-------------------|-------------------------------|
| **Modelo mental** | Grafo de estados (nodos + aristas) | Equipos con roles | Agentes conversacionales | Agentes con handoffs |
| **Memoria corto plazo** | Checkpointers (SQLite, Postgres, Redis) | LanceDB / ChromaDB | ListMemory / ChromaDB | Threads (server-side) |
| **Memoria largo plazo** | Store (Postgres, MongoDB) — cross-thread | Memory unificada con LLM scoring | Save/Load State (JSON) | Vector Stores (server-side) |
| **Time-travel debugging** | ✅ Completo (checkpoint rewind) | ❌ Parcial (event log) | ❌ No disponible | ❌ No disponible |
| **Durable execution** | ✅ Nativo (crash recovery) | ❌ Limitado | ❌ Limitado | ❌ No disponible |
| **Human-in-the-loop** | ✅ Nativo (interrupt/resume) | ❌ Via callbacks | ❌ UserProxy pattern | ❌ Guardrails (limitado) |
| **Multi-provider LLM** | ✅ 100+ (via LangChain) | ✅ Todos (via LiteLLM) | ✅ Todos | ❌ Solo OpenAI |
| **Persistencia local** | ✅ Total (datos del usuario) | ✅ Parcial (LanceDB local) | ✅ Parcial (JSON/chromadb) | ❌ Solo server-side |
| **Observabilidad** | LangSmith (best-in-class) | Dashboard Enterprise | Azure Monitor | Dashboard OpenAI |
| **Curva de aprendizaje** | Alta (2-4 semanas) | Baja (horas) | Media | Baja-Media |
| **Estado en 2026** | Muy activo | Muy activo | MAF 1.0 GA (abril 2026) | En transición (Agosto 2026 deadline) |
| **Producción a escala** | LinkedIn, Uber, Klarna, Replit | Varios (menos conocidos) | Azure-native | Startup-friendly |

---

### 6. Integraciones externas de memoria

- **Mem0** (ECAI 2025, arXiv:2504.19413): benchmark líder en LoCoMo (92.5), LongMemEval (94.4) con ~6,900 tokens/query. Se integra con los 4 frameworks como proveedor externo. Resuelve el aislamiento multi-usuario que CrewAI no tiene nativamente.
- **Mem0 nuevo algoritmo (abril 2026)**: +29.6 puntos en razonamiento temporal, +23.1 en multi-hop. Extracción single-pass jerárquica + retrieval multi-señal (semántica + BM25 + entidades).
- **Benchmarks estándar**: LoCoMo (1,540 preguntas), LongMemEval (500 preguntas), BEAM (1M y 10M tokens) — definen el campo para comparar arquitecturas de memoria.

---

### 7. Tendencias y convergencia (2026)

1. **Convergencia de protocolos**: El landscape se está unificando en torno a MCP (Model Context Protocol) y A2A (Agent2Agent). OpenAgents es el único con soporte nativo de ambos; CrewAI añadió A2A; LangGraph y MAF 1.0 están incorporando MCP.
2. **Frameworks híbridos**: Varios equipos usan LangGraph como orquestador principal con CrewAI crews o AutoGen conversations como nodos dentro del grafo.
3. **Del estado server-side al cliente**: OpenAI abandonando Assistants API (stateful server-side) en favor de Responses API (stateless client-side) marca una tendencia hacia mayor control del desarrollador sobre los datos.
4. **Memoria como servicio externo**: Mem0 y Zep están emergiendo como capas de memoria independientes del framework, desacoplando la persistencia de la orquestación de agentes.
5. **Simplificación de APIs**: CrewAI unificó 4 tipos de memoria en 1; LangGraph separó claramente Checkpointer vs Store; AutoGen introdujo el protocolo Memory.

---

## Matriz de Confianza

| Afirmación | Confianza | Fuentes | Notas |
|------------|-----------|---------|-------|
| LangGraph tiene el sistema de memoria más maduro y completo | Alta | Documentación oficial, 6+ comparativas, casos de producción (LinkedIn, Uber, Klarna) | Consistente entre todas las fuentes |
| CrewAI unificó su sistema de memoria en febrero 2026 | Alta | PR #4420 del repositorio oficial, documentación oficial | Cambio reciente pero bien documentado |
| AutoGen está en modo mantenimiento; MAF 1.0 es el sucesor | Alta | Múltiples comparativas (JobsByCulture, paperclipped, TURION.AI), anuncio oficial de Microsoft | Fuentes independientes confirman |
| OpenAI Assistants API será deprecada el 26 agosto 2026 | Alta | Documentación oficial de OpenAI, APIScout | Fecha límite confirmada |
| CrewAI no tiene aislamiento multi-usuario nativo | Alta | Documentación de Mem0, issues de GitHub, análisis de producción | Confirmado por múltiples fuentes |
| CrewAI tiene cuello de botella con SQLite en alta concurrencia | Media | Análisis de terceros (Paperclipped), PR #2892 | Fuente única con análisis técnico |
| LangGraph y CrewAI se pueden combinar en producción | Alta | Varios casos reportados (Thinking Company, TURION.AI) | Patrón emergente documentado |
| AutoGen v0.4 soporta save/load state nativo | Alta | Documentación oficial de AutoGen | Bien documentado |

---

## Conclusiones

1. **No hay un "mejor" framework universal** — la elección depende del caso de uso: LangGraph para producción con estado durable, CrewAI para prototipado rápido con roles, MAF 1.0 para entornos Azure, OpenAI SDK para stacks OpenAI-native.

2. **LangGraph es el líder técnico en memoria persistente** por su sistema de dos capas (Checkpointer + Store), soporte de time-travel debugging, durable execution y observabilidad con LangSmith.

3. **La memoria está evolucionando de ser una característica del framework a un servicio externo** — Mem0 y Zep están desacoplando la capa de memoria, permitiendo elegir el mejor motor independientemente del framework de orquestación.

4. **OpenAI está en una transición crítica**: la migración de Assistants a Responses API (agosto 2026) es un cambio arquitectónico profundo que requiere replanificar sistemas existentes.

5. **AutoGen como framework independiente está en su fase final**; el futuro es Microsoft Agent Framework 1.0, que unifica lo mejor de AutoGen y Semantic Kernel.

---

## Investigación Pendiente

- Benchmarks cuantitativos propios con cargas de trabajo reales para cada framework.
- Evaluación de latencia y costo de checkpointing en LangGraph a escala (>1000 hilos concurrentes).
- Análisis de la integración Mem0 + cada framework en producción (no solo documentación).
- Seguimiento de la migración OpenAI Assistants → Responses API en equipos reales.
- Evaluación del nuevo Microsoft Agent Framework 1.0 tras su GA (abril 2026) — aún pocos reports de producción.

---

## Fuentes

- [LangGraph Documentation: Persistence](https://langchain-ai.github.io/langgraph/how-tos/persistence/) — confianza: alta
- [LangGraph: Checkpointers Reference](https://reference.langchain.com/python/langgraph/checkpoints) — confianza: alta
- [LangGraph: Persistence and Memory (DeepWiki)](https://deepwiki.com/langchain-ai/langgraph/4-persistence-and-memory) — confianza: alta
- [LangGraph Long-Term Memory with Store (AI Workshack)](https://aiworkshack.com/tools/langgraph/langgraph-long-term-memory-using-store-for-persistent-cross-thread-knowledge.html) — confianza: media
- [LangGraph Persistence and Thread Models (learnwithparam)](https://www.learnwithparam.com/blog/langgraph-persistence-thread-models-production) — confianza: alta
- [CrewAI Documentation: Memory](https://docs.crewai.com/en/concepts/memory) — confianza: alta
- [CrewAI Memory System PR #4420](https://github.com/crewAIInc/crewAI/pull/4420) — confianza: alta
- [CrewAI Memory and Knowledge Systems (DeepWiki)](https://deepwiki.com/crewAIInc/crewAI/7-memory-and-knowledge-systems) — confianza: alta
- [CrewAI Memory Production Setup with Mem0](https://mem0.ai/blog/crewai-memory-production-setup-with-mem0) — confianza: alta
- [AutoGen Documentation: Memory](https://microsoft.github.io/autogen/0.4.9/user-guide/agentchat-user-guide/memory.html) — confianza: alta
- [AutoGen: Managing State](https://microsoft.github.io/autogen/0.4.8/user-guide/agentchat-user-guide/tutorial/state.html) — confianza: alta
- [AutoGen v0.2 to v0.4 Migration Guide](https://microsoft.github.io/autogen/0.5.5/user-guide/agentchat-user-guide/migration-guide.html) — confianza: alta
- [OpenAI: Assistants API Deep Dive](https://developers.openai.com/api/docs/assistants/deep-dive) — confianza: alta
- [OpenAI: Assistants Migration Guide](https://platform.openai.com/docs/assistants/migration) — confianza: alta
- [OpenAI Responses API vs Assistants 2026 (APIScout)](https://apiscout.dev/blog/openai-responses-api-vs-assistants-api-migration-2026) — confianza: media
- [AI Agent Frameworks Compared 2026 (JobsByCulture)](https://jobsbyculture.com/blog/ai-agent-frameworks-compared-2026) — confianza: media
- [LangGraph vs CrewAI vs OpenAI Agents SDK 2026 (FRE|Nxt)](https://www.frenxt.com/compare/langgraph-vs-crewai-vs-openai-agents-sdk) — confianza: media
- [AI Agent Frameworks Compared 2026 (Paperclipped)](https://www.paperclipped.de/en/blog/ai-agent-frameworks/) — confianza: media
- [State of AI Agent Memory 2026 (Mem0)](https://mem0.ai/blog/state-of-ai-agent-memory-2026) — confianza: media
- [LangGraph vs AutoGen vs CrewAI 2026 (Thinking Company)](https://thinking.inc/en/blue-ocean/comparisons/langgraph-vs-autogen-vs-crewai/) — confianza: media
- [LangGraph vs CrewAI vs AutoGen 2026 (TURION.AI)](https://turion.ai/blog/langgraph-vs-crewai-vs-autogen-comparison-2026/) — confianza: media
- [CrewAI vs LangGraph vs AutoGen 2026 (FutureAGI)](https://futureagi.com/blog/crewai-vs-langgraph-vs-autogen-2026/) — confianza: media
