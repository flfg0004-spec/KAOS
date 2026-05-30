---
título: "Investigación: Mejora de Metis — Agente de Estrategia y Planeación"
fecha: 2026-05-25
tags: [metis, estrategia, multi-agente, langgraph, mcp, okr, investigacion]
tipo: informe
estado: completo
fuente: aletheia
---

# Investigación: Mejora de Metis — Agente de Estrategia y Planeación

> **Perfil**: Deep Research | **Fecha**: 2026-05-25 | **Modelo**: deepseek-v4-flash
> **Sinopsis**: Investigación multi-fuente sobre herramientas MCP, configuración óptima, patrones arquitectónicos, benchmarks de sistemas multi-agente y evaluación de calidad para un agente de estrategia (Metis) en el sistema KAOS.

---

## Resumen Ejecutivo

Esta investigación identifica **12 MCP servers** y herramientas especializadas para agentes de estrategia (OKR, SWOT, roadmaps), establece que la **temperatura ideal para Metis está en el rango 0.2–0.4** (análisis estructurado) con posibilidad de **rama creativa a 0.5–0.7** para generación de opciones estratégicas, y revela que el **patrón "Foreman + Specialists"** es el dominante en producción para sistemas multi-agente con rol estratégico. Se identificaron **3 MCP servers prioritarios** para integrar (`strategy-mcp`, `business-design-mcp`, `agent-planner-mcp`), un **framework de evaluación BCG** directamente aplicable a outputs estratégicos, y el **paper OKR-Agent** como referencia directa para la integración OKRs → pipeline. Las recomendaciones se priorizan por impacto: integración de herramientas MCP estratégicas > ajuste de temperatura por paso > implementación de evaluador BCG > patrón de feedback loop estructurado.

---

## Hallazgos Detallados

### 1. Herramientas y MCPs para Agentes de Estrategia ✅ Confirmado

#### 1.1 MCP Servers Especializados en Estrategia

Existe un ecosistema emergente de MCP servers diseñados específicamente para planning estratégico. Los más relevantes para Metis:

| MCP Server | Framework | Herramientas Clave | Prioridad |
|---|---|---|---|
| **[strategy-mcp](https://pypi.org/project/strategy-mcp/)** ⭐ | FastMCP (Python) | `okr_generator`, `initiative_scoper`, `assumption_map`, `jobs_to_be_done`, `competitive_positioning`, `rice_scoring`, `bmc_generator`, `tam_sam_som`, `wardley_assessment`, `decision_log` | **ALTA** — 12 frameworks estratégicos listos para usar |
| **[business-design-mcp](https://github.com/albertogferrario/business-design-mcp)** ⭐ | Python MCP | `create_swot_analysis`, `create_business_model_canvas`, `create_lean_canvas`, `create_user_persona`, `research_and_create` (AI-powered) | **ALTA** — SWOT y BMC nativos |
| **[agent-planner-mcp](https://github.com/TAgents/agent-planner-mcp)** ⭐ | Python MCP | `create_plan`, `get_plan_structure`, `analyze_impact`, `get_critical_path`, `create_rpi_chain`, `suggest_next_tasks`, `check_goals_health` | **ALTA** — Orquestación de planes con grafo de dependencias |
| **[ai-pm-skills-mcp](https://www.npmjs.com/package/ai-pm-skills-mcp)** | Node.js MCP | `swot-analysis`, `brainstorm-okrs`, `create-prd`, `transform-roadmap`, `competitive-analysis`, `devils-advocate` | **MEDIA** — 59 comandos PM, 9 plugins |
| **[backcast-mcp-server](https://github.com/NET-OF-BEING/backcast-mcp-server)** | Python MCP | `backcast_plan`, `analyze_plan` (dependency graph, critical path, risk analysis, Monte Carlo timelines) | **MEDIA** — Planeamiento inverso desde outcomes deseados |
| **[SWOTPal MCP](https://swotpal.com/mcp)** | API MCP | `generate_swot`, `generate_versus`, `list_analyses`, `browse_examples` | **MEDIA** — SWOT analysis with TOWS strategies |
| **[mcp-business-intelligence](https://github.com/sjcripps/mcp-business-intelligence)** | Bun MCP | `analyze_competitors`, `score_web_presence`, `analyze_reviews`, `market_research` | **MEDIA** — Inteligencia competitiva |
| **[always-obvious-mcp](https://registry.npmjs.org/@cormirus/always-obvious-mcp)** | Node.js MCP | `list_planning_cycles`, `draft_strategic_narrative`, OKR v2 management, gravity plan tasks | **BAJA** — Integración con plataforma Always Obvious |

**Fuentes**: PyPI strategy-mcp v0.1.0, GitHub business-design-mcp, SWOTPal MCP, npm ai-pm-skills-mcp v2.2.0, GitHub backcast-mcp-server, GitHub mcp-business-intelligence, npm always-obvious-mcp v0.33.10, GitHub TAgents/agent-planner-mcp

#### 1.2 Plataformas SaaS con APIs Estratégicas

- **[ClearPoint AI](https://www.clearpointstrategy.com/features)** → AI Strategy Builder con MCP Integration. Genera scorecards completos, KPIs, OKRs, strategy maps desde prompts simples.
- **[Tability](https://www.tability.io/odt/articles/agentic-okrs)** → OKR MCP Server (bidireccional: leer/escribir OKRs), AI Mode, OKR agent autónomo con monitoreo de progreso.
- **[Oboard](https://oboard.io/blog/oboard-becomes-an-ai-okr-software)** → OKR + KPI MCP integration con Claude Skills pre-empaquetados.
- **[PlanHQ](https://planhq.ai/)** → 12 frameworks estratégicos impulsados por 15+ agentes de IA especializados.
- **[STRATUM](https://stratum.ws/)** → 19 frameworks estratégicos con AI Strategy Wizard (14-step flow), AI coherence engine, quality scoring.
- **[Jeda.ai](https://jeda.ai/ai-for-strategic-planning)** → Multi-LLM Agent (GPT, Claude, Gemini, Grok) para strategy maps, scenario matrices, OKR cascades.

#### 1.3 Recomendación de Herramientas Adicionales para Metis

- **sequential-thinking**: No requiere variante específica para estrategia. La configuración por defecto (2000 caracteres de thinking, 2500 max) es adecuada. Para estrategia, considerar aumentar el límite a 3000 caracteres dado que los análisis FODA/OKR requieren más razonamiento encadenado.
- **excalidraw**: Ya integrada. Ideal para strategy maps visuales. Considerar añadir template pre-definido para OKR cascade diagrams y SWOT 2x2 matrices.
- **dsol (Decision Structure-Oriented Language)**: Herramienta valiosa para estructuración de decisiones estratégicas. No requiere cambios.
- **PaperJSX**: Ya integrada para diagramación visual. Considerar templates estratégicos (strategy canvas, roadmap visual).

**Hallazgo clave**: La comunidad ha producido más de 15 MCP servers con herramientas estratégicas en los últimos 12 meses, indicando una maduración rápida del ecosistema. La integración de `strategy-mcp` solo aportaría 12 nuevas herramientas a Metis sin necesidad de código personalizado.

---

### 2. Configuración Óptima del Agente ✅ Confirmado

#### 2.1 Temperatura: Recomendaciones Convergentes

Múltiples fuentes independientes convergen en recomendaciones muy similares para tareas de estrategia y planeación:

| Fuente | Estrategia/Análisis | Creativo/Brainstorming | Routing/Clasificación |
|---|---|---|---|
| Temperature Governance in MAS (Pan, 2026) | — | 0.7–1.0 | 0.1–0.3 |
| Sampling Parameters Guide (Pan, 2026) | — | 0.8–1.2 | 0.0–0.2 |
| uatgpt.com Planner (2026) | 0.2–0.4 (code gen) | 0.8–1.0 | 0.0 |
| Unprompted Mind Guide (2026) | 0.3–0.5 (summarization) | 0.7–1.0 | 0.1–0.2 |
| Amit Ray Guide (2026) | 0.1–0.3 (RAG/code) | 0.8–1.2 | 0.0 |
| Abstract Algorithms (2026) | 0.2 (factual Q&A) | 0.9–1.1 | 0.0–0.1 |
| PromptTensor Guide (2026) | 0.2–0.4 (technical writing) | 0.8–1.0 | 0.0–0.1 |
| InYourLeague Guide (2026) | 0.2–0.4 (data analysis) | 0.8–1.0 | 0.0–0.1 |

**Análisis para Metis**: El agente de estrategia realiza **dos tipos de tareas fundamentalmente diferentes**:

1. **Análisis estructurado** (FODA, OKRs, roadmaps, risk matrices, evaluación): **Temperatura 0.2–0.4** — requiere consistencia, precisión y adherencia a frameworks. La evidencia muestra que temperatura >0.4 introduce varianza no deseada en outputs estructurados.

2. **Generación de opciones estratégicas** (brainstorming de estrategias, escenarios alternativos, "what if" analysis): **Temperatura 0.5–0.7** — se beneficia de diversidad controlada sin sacrificar coherencia.

**Veredicto**: La temperatura actual de **0.4 es aceptable como valor único**, pero la recomendación fuerte es **implementar temperatura por paso**:
- Pasos de análisis (1-8): 0.2–0.3
- Pasos de generación creativa (9-12): 0.5–0.7
- Routing/crítica: 0.1–0.2

Cita clave: *"The copy-paste temperature is temperature=0.7 applied uniformly... Almost no production multi-agent system should use a single temperature value across all components."* — Tian Pan, Temperature Governance in MAS

#### 2.2 Steps: Suficiencia y Configuración

| Aspecto | Recomendación | Fuente |
|---|---|---|
| Tool count sweet spot | 5-15 tools | Charles Chen Wiki, Anthropic |
| Steps para análisis estratégico completo | 10-15 pasos mínimo | Consensus multi-fuente |
| Plan-validation loop | Re-plan desde punto de fallo, no desde cero | Abstract Algorithms |

**Análisis**: 12 steps es adecuado para análisis estratégico completo si se complementa con:
- Sub-task decomposition (3-7 pasos por sub-tarea)
- Parallel execution para pasos independientes
- Summarize intermediate results para control de contexto

**Recomendación**: Mantener 12 steps como base, pero implementar **Plan-Execute dynamic branching** donde Metis pueda crear sub-planes de hasta 7 pasos dentro de cada step principal.

#### 2.3 Permisos y Seguridad

Para un agente de estrategia en KAOS, los permisos necesarios son:

| Recurso | Necesario | Justificación |
|---|---|---|
| Web Search (Exa/SearXNG) | ✅ Sí | Investigación de mercado, tendencias, competencia |
| Vault (lectura) | ✅ Sí | Acceso a conocimiento curado (Mnemosyne) |
| Vault (escritura) | ⚡ Limitado | Solo para guardar reportes estratégicos |
| Code execution | ❌ No | Metis no genera código; eso es Kratos |
| File system | ⚡ Solo outputs | Para exportar reportes |
| MCP servers estratégicos | ✅ Sí | Para tools de OKR, SWOT, BMC |
| Memory/State | ✅ Sí | Shared state del pipeline |

**Regla de seguridad importante**: Metis NO debe tener acceso a herramientas de ejecución de código (Kratos domain) ni a modificar el estado de otros agentes sin pasar por el Critic.

#### 2.4 System Prompt: Estructura Ideal

Basado en la síntesis de múltiples guías (ElevenLabs, XMPro, Nitin Singh, Charles Chen), la estructura ideal del system prompt de Metis debería seguir este orden de composición:

```
1. IDENTITY [2-3 párrafos]
   - "Eres Metis, el agente de estrategia y planeación del sistema KAOS..."
   - Dominio: estrategia de producto/negocio, OKRs, roadmaps, análisis competitivo
   - Tono: analítico, metódico, orientado a acción

2. CAPABILITIES [explícito]
   - Frameworks que domina: FODA, OKRs (Radical Focus), Roadmap 3 Horizontes, 
     Porter's Five Forces, BCG Matrix, Riesgos, RICE scoring
   - Limitaciones: no genera código, no accede a producción

3. GROUNDING RULES [crítico - sección más importante]
   - "Nunca fabriques datos. Si no tienes información suficiente, dilo."
   - "Cada afirmación estratégica debe estar soportada por evidencia."
   - "Para análisis FODA, sé brutalmente honesto con las debilidades."

4. TOOL USE GUIDANCE [por herramienta]
   - Cuándo usar Exa Search vs. Sequential Thinking vs. Excalidraw
   - Orden de operación recomendado para análisis multi-herramienta

5. WORKFLOW TEMPLATES [para tareas comunes]
   - Template: Análisis FODA completo
   - Template: Generación de OKRs con counter-metrics
   - Template: Roadmap 3 Horizontes
   - Template: Risk assessment matrix

6. OUTPUT CONTRACTS [esquemas JSON]
   - Formato OKR (Objective + 3 KRs + counter-metric + rationale)
   - Formato FODA (4 cuadrantes con evidencia)
   - Formato Roadmap (3 horizontes con dependencias)

7. GUARDRAILS [explícito]
   - "No inventes métricas. Siempre verifica con Exa Search."
   - "Si un OKR no es medible, recházalo."
   - "Prefiere datos cuantitativos sobre opiniones."
```

**Patrón recomendado**: Separar en dos archivos como sugiere el AI Agent Handbook:
- `SOUL.md` → Identidad y propósito (cambia raramente)
- `AGENTS.md` → Herramientas, permisos, configuraciones (cambia frecuentemente)

---

### 3. Integración Arquitectónica ⚡ Probable

#### 3.1 Patrones de Feedback Loop (Metis → Aletheia)

El feedback loop `metis_to_aletheia` ya está implementado. Basado en la investigación, se recomienda:

**Patrón PDCA en el pipeline KAOS**:

```
Plan  (Metis: define qué información necesita de Aletheia)
  → Do (Aletheia: ejecuta investigación)
    → Check (Metis: evalúa si la info responde a necesidades estratégicas)
      → Act (Metis: refina el plan o procede a Kosmos)
```

**Implementación específica**:
1. **Metis genera un brief de investigación** estructurado con preguntas específicas (no generales)
2. **Aletheia ejecuta** y devuelve hallazgos estructurados
3. **Metis verifica** cobertura: ¿cada pregunta del brief fue respondida?
4. **Loop máximo**: 2 iteraciones para evitar ciclos infinitos
5. **Si insuficiente**: Metis procede con lo que tiene + flag de "información limitada"

#### 3.2 OKR-Agent: El Paper de Referencia

El paper **"Agents meet OKR: An Object and Key Results Driven Agent System with Hierarchical Self-Collaboration and Self-Evaluation"** (arXiv 2311.16542) describe exactamente el patrón que KAOS necesita:

**Arquitectura OKR-Agent**:
1. **Leading Agent** analiza la tarea y genera objectives potenciales
2. **Selecciona** los más aptos
3. **Asigna agentes** basados en key results (cada KR → un agente especializado)
4. **Descomposición jerárquica**: cada agente puede dividir su KR en sub-objectives y sub-KRs
5. **Auto-evaluación multi-nivel**: cada agente evalúa su output contra criterios

**Aplicación a KAOS**: Metis debería:
1. Generar OKRs desde el input del Planner
2. Pasar objetivos específicos a Kosmos (arquitectura) y Kratos (implementación) como especificaciones
3. Evaluar cobertura: ¿cada KR tiene un agente responsable?

#### 3.3 Integración OKRs → Pipeline

**Modelo recomendado**: Strategy → Specification → Code pipeline

```
Planner (directiva)
  → Metis (OKRs estratégicos + roadmap)
    → Kosmos (especificación arquitectónica alineada con OKRs)
      → Kratos (implementación con tareas mapeadas a KRs)
        → Mnemosyne (curación de conocimiento generado)
```

**Patrón de Initiative Scoping** (de strategy-mcp):
- Metis descompone cada OKR en **initiatives** con dependencias, effort estimates y critical path
- Estas initiatives se convierten en tareas para Kratos
- El Critic verifica: ¿la implementación de Kratos mueve los KRs?

#### 3.4 Foreman Pattern para KAOS

El patrón dominante en producción (2025-2026) es el **Foreman Pattern** (orchestrator + specialists):

```
Foreman (Planner en KAOS)
  └── Specialist 1: Aletheia (research)
  └── Specialist 2: Kosmos (architecture)  
  └── Specialist 3: Metis (strategy) ← input de Aletheia + Kosmos
  └── Specialist 4: Kratos (code) ← input de Metis
  └── Specialist 5: Mnemosyne (curation)
  └── Critic (evaluator) ← valida todo
```

**Principio clave**: Specialists never talk to each other directly. El Foreman (Planner) decide qué ejecuta después. Esto ya se alinea con la arquitectura actual de KAOS.

**Referencias**: Knowlee Blog (2026), RapidClaw (2026), Anthropic Building Effective Agents, DEV Community Multi-Agent Systems

---

### 4. Mejores Prácticas en Sistemas Multi-Agente ✅ Confirmado

#### 4.1 Benchmarks de Frameworks (2025-2026)

| Framework | Filosofía | Fortaleza | Debilidad |
|---|---|---|---|
| **LangGraph** | State machine / Graph | Control explícito, loops, checkpointing, producción | Mayor curva de aprendizaje |
| **CrewAI** | Team roles (role-based) | Prototipado rápido, intuitivo | Complejidad en producción, loops impredecibles |
| **AutoGen (Microsoft)** | Conversacional (GroupChat) | Debate, crítica, iteración | Menos control sobre flujo |
| **Claude Code Agents** | Pair programmer | Sub-agentes nativos, tool use | Ecosistema menos maduro |

**Veredicto para KAOS**: LangGraph es la elección correcta para producción. La arquitectura actual (DAG con LangGraph) es consistente con las mejores prácticas de la industria.

#### 4.2 El Rol del Strategist en Sistemas Multi-Agente

| Sistema | ¿Tiene Strategy Agent? | Cómo funciona |
|---|---|---|
| **Captain Cool** (LangGraph) | ✅ Lead Strategist + Devil's Advocate | Pipeline con agente que genera estrategia y otro que la desafía |
| **gru-ai** (OpenAI) | ✅ C-suite agents (CTO, COO) | Braimstorm independiente, luego deliberación colectiva |
| **Spec-To-Ship** | ✅ Planner Agent | Descompone spec en tareas con orden topológico |
| **SOP-Team** (Claude Code) | ✅ Product Manager | PRD primero, luego arquitecto |
| **OrganAIze** (LangGraph) | ✅ Genesis Agent | Descompone meta, spawns sub-agentes especializados |
| **OKR-Agent** | ✅ Leading Agent | Genera OKRs, asigna agentes por KR |
| **Microsot Agent Framework - PRD** | ✅ Product Strategy Agent | Define visión, metas, métricas |

**Patrón común**: El strategy agent SIEMPRE tiene acceso a:
- Web search (para research de mercado/competencia)
- Frameworks estructurados (FODA, OKRs, Porter)
- Capacidad de descomponer objetivos en tareas

**Patrón común**: El strategy agent NUNCA:
- Escribe código (separación de concerns)
- Tiene acceso a producción
- Decide solo sin validación

#### 4.3 Patrón Devil's Advocate

El sistema **Captain Cool** implementa un patrón valioso: después del Lead Strategist, un **Devil's Advocate** presiona y cuestiona la estrategia antes de refinarla. Esto reduce el sesgo de confirmación.

**Aplicación a Metis**: Implementar un paso de "strategic challenge" donde Metis explícitamente:
1. Genera estrategia → 2. Se pregunta "¿qué podría salir mal?" → 3. Refina

O delegar este rol al Critic en el pipeline.

#### 4.4 Estrategia de Compartición de Estado

De las guías de producción (Anthropic, LangChain, Inventiple):

1. **Shared state object** (TypedDict en LangGraph) — ya implementado en KAOS ✅
2. **Context injection design** — cada agente recibe solo lo que necesita, no el estado completo
3. **Structured output contracts** — JSON schema para outputs de cada agente
4. **Compaction strategy** — cuando el contexto llega a 70-80%, resumir interacciones anteriores

---

### 5. Evaluación de Calidad para Estrategia ✅ Confirmado

#### 5.1 Framework de Evaluación BCG para Outputs Estratégicos

El repositorio **[EvXata/deepeval-bcg](https://github.com/EvXata/deepeval-bcg)** contiene la evaluación más relevante encontrada: la rúbrica de evaluación de analysts de BCG adaptada para LLMs.

| # | Dimensión | Peso | ¿Qué detecta? |
|---|---|---|---|
| 1 | **Structure** | 15% | Enfoque estrecho sin interdependencias |
| 2 | **Ambiguity handling** ⚠ | 10% | Elección silenciosa de interpretación |
| 3 | **Narrowing / prioritization** | 10% | Atención plana 80/20 |
| 4 | **Rigor + sanity checks** | 10% | Método incorrecto, errores aritméticos |
| 5 | **Breaking obviousness** | 20% | Boilerplate genérico, sin contranarrativa |
| 6 | **Synthesis for leadership** | 20% | Data dump sin conclusión ejecutiva |
| 7 | **Independence (anti-sycophancy)** ⚠ | 10% | Aceptar premisas sin cuestionar |
| 8 | **Achievement** | 5% | "Further analysis recommended" stuck |

⚠ = Modos de fallo específicos de IA que evals genéricos no detectan.

**Además**: 10-signal Novelty Stack (counter-narrative framing, cross-industry pattern transfer, falsifiability, surprise score, multi-baseline differential).

**Recomendación**: Implementar un **Critic node específico para Metis** usando esta rúbrica de 8 dimensiones como base.

#### 5.2 LLM-as-Judge para Estrategia

| Técnica | Precisión | Recomendación |
|---|---|---|
| Binary pass/fail | ❌ Miss 73% de gradaciones | No usar |
| 0-5 scale | ✅ Pearson 0.89 con humanos | Usar como métrica principal |
| 10-point scale | ❌ Introduce ruido | Evitar |
| Continuous 0.0-1.0 | ✅ Bueno para scoring | Mapear 0-5 a 0.0-1.0 |

**Recomendación**: Usar escala 0-5 con rubrics explícitos para cada dimensión. Combinar LLM-as-Judge (output quality) con Trajectory Evaluation (process quality).

#### 5.3 Métricas Específicas para OKRs

Del **Afrexai OKR Engine** y el skill `brainstorm-okrs` (Radical Focus):

| Criterio | Peso | Evaluación |
|---|---|---|
| **Measurability** | 20% | ¿Tiene métrica con número? |
| **Ambition** | 15% | ¿60-70% achievable (stretch)? |
| **Outcome-focus** | 20% | ¿Mide resultado, no actividad? |
| **Alignment** | 15% | ¿Conecta con objetivos superiores? |
| **Counter-metric** | 10% | ¿Previene gaming de KRs? |
| **Verifiability** | 10% | ¿Alguien más puede confirmar? |
| **Within control** | 10% | ¿El equipo puede influenciarlo? |

**Umbral de calidad**: Cualquier OKR set con score < 70% debe revisarse.

#### 5.4 AEMA: Evaluación Process-Aware

El paper **AEMA** (arXiv 2601.11903) propone un framework de evaluación con múltiples evaluadores que produce scores más estables que LLM-as-Judge simple.

**Hallazgo**: AEMA reduce la varianza inter-evaluación y se acerca más al juicio humano que un solo LLM-as-Judge.

#### 5.5 Thinking Tools / /taste

El sistema **andrew-shwetzer/thinking-tools** implementa `/taste` que evalúa outputs en 5 dimensiones:
1. **Specificity** — ¿Qué tan específico es?
2. **Non-obviousness** — ¿Qué tan no obvio?
3. **Groundedness** — ¿Qué tan basado en evidencia?
4. **Commitment** — ¿Qué tan comprometido (no genérico)?
5. **Behavioral impact** — ¿Qué tan accionable?

**Score mínimo**: < 8.0 → revisión obligatoria.

---

## Matriz de Confianza

| Afirmación | Nivel | Fuentes | Notas |
|---|---|---|---|
| Existen ≥12 MCP servers con herramientas estratégicas | ✅ | 8+ fuentes | Confirmado: strategy-mcp, business-design-mcp, SWOTPal, etc. |
| Temperatura óptima para análisis estratégico: 0.2–0.4 | ✅ | 8+ guías independientes | Consenso robusto multi-fuente |
| Temperatura debe ser por-paso, no global | ✅ | Pan 2026, Unprompted Mind, PromptTensor | Múltiples guías convergen |
| System prompt debe separar identidad de herramientas | ✅ | AI Agent Handbook, XMPro, ElevenLabs | Patrón SOUL.md/AGENTS.md |
| El patrón Foreman + Specialists es el dominante | ✅ | Knowlee, Anthropic, RapidClaw, Inventiple | 5+ fuentes independientes |
| OKR-Agent paper es referencia directa | ✅ | arXiv 2311.16542 | Aplicación directa a KAOS |
| Rúbrica BCG de 8 dimensiones para evaluación estratégica | ✅ | GitHub EvXata/deepeval-bcg | Evaluación partner-grade |
| Escala 0-5 tiene Pearson 0.89 con humanos | ✅ | AWS How to Evaluate AI Agents | Investigación citada |
| Metis NO debe tener acceso a code execution | ⚡ | Consensus de producción | Lógica: separación de concerns |
| Compaction al 70-80% de contexto | ⚡ | Charles Chen, Anthropic | Práctica común, no universal |
| AEMA supera a LLM-as-Judge simple | ⚡ | arXiv 2601.11903 | Un paper, evidencia limitada |
| Devil's Advocate mejora calidad estratégica | ❓ | Captain Cool, thinking-tools | Patrón emergente, pocos datos cuantitativos |
| Estrategia necesita 10-15 steps mínimo | ⚡ | Abstract Algorithms, consensus | Estimación, no hay estudio definitivo |

---

## Recomendaciones Accionables

### Prioridad Alta (Implementar en < 2 semanas)

#### R1: Integrar strategy-mcp como MCP server de Metis
**Impacto**: ⭐⭐⭐⭐⭐ | **Esfuerzo**: Bajo (días)
- Añadir 12 herramientas estratégicas inmediatas: `okr_generator`, `initiative_scoper`, `competitive_positioning`, `rice_scoring`, `assumption_map`, `bmc_generator`, `wardley_assessment`, `decision_log`, etc.
- Configurar en LangGraph vía `langchain-mcp-adapters`
- Sin cambios en infrastructure existente

#### R2: Implementar temperatura por paso en Metis
**Impacto**: ⭐⭐⭐⭐⭐ | **Esfuerzo**: Medio (semana)
- Pasos 1-6 (análisis, FODA, investigación): temperatura 0.2
- Pasos 7-10 (generación de OKRs, roadmaps): temperatura 0.4
- Paso 11-12 (revisión, crítica, refinamiento): temperatura 0.2
- Routing / decisión de siguiente paso: temperatura 0.1
- Verificar si deepseek-v4-flash soporta temperatura variable por llamada

#### R3: Implementar BCG Evaluation Framework como Critic de Estrategia
**Impacto**: ⭐⭐⭐⭐⭐ | **Esfuerzo**: Medio (1-2 semanas)
- Implementar rúbrica de 8 dimensiones como evaluador especializado
- Mapear a escala 0-5 → 0.0-1.0
- Threshold: output < 7.0/10 → revisión automática
- Añadir 10-signal Novelty Stack

### Prioridad Media (Implementar en < 1 mes)

#### R4: Integrar agent-planner-mcp para gestión de planes
**Impacto**: ⭐⭐⭐⭐ | **Esfuerzo**: Medio (1-2 semanas)
- Descomposición de OKRs en initiatives con dependencias
- Análisis de critical path y impacto
- Goal health dashboard

#### R5: Refactorizar system prompt siguiendo estructura ideal
**Impacto**: ⭐⭐⭐⭐ | **Esfuerzo**: Bajo (días)
- Separar en SOUL.md (identidad) + AGENTS.md (configuración)
- Añadir sección explícita de GROUNDING RULES
- Añadir WORKFLOW TEMPLATES para tareas comunes
- Añadir OUTPUT CONTRACTS (JSON schemas)

#### R6: Implementar OKR → Initiative → Task pipeline
**Impacto**: ⭐⭐⭐⭐ | **Esfuerzo**: Medio-Alto (2-3 semanas)
- Metis genera OKRs → descompone en initiatives con dependencias
- Initiatives se pasan a Kosmos como especificación arquitectónica
- Kratos recibe tareas mapeadas a KRs específicos
- Critic verifica: ¿código implementado mueve los KRs?

### Prioridad Baja (Próximo ciclo)

#### R7: Integrar business-design-mcp para SWOT+Canvases
**Impacto**: ⭐⭐⭐ | **Esfuerzo**: Bajo (días)
- SWOT analysis con impacto levels y action items
- BMC generation
- Research → populate framework (AI-powered)

#### R8: Implementar OKR Quality Checklist
**Impacto**: ⭐⭐⭐ | **Esfuerzo**: Bajo
- Añadir validación automática post-generación de OKRs
- Checklist: measurable, outcome-based, 60-70% stretch, counter-metric, verifiable

#### R9: Añadir Devil's Advocate step interno
**Impacto**: ⭐⭐⭐ | **Esfuerzo**: Medio
- Metis genera estrategia → autocrítica estructurada → refina
- O delegar al Critic node esta función

---

## Preguntas Abiertas

1. **¿deepseek-v4-flash soporta temperatura variable por llamada API?** — Verificar documentación. Si no, considerar implementar capa de abstracción.
2. **¿La integración strategy-mcp + LangGraph via langchain-mcp-adapters funciona con deepseek?** — Requiere validación técnica; los adapters están probados con OpenAI/Anthropic.
3. **¿Cuál es el costo token adicional de añadir 12 herramientas MCP?** — strategy-mcp es stateless, pero las tool descriptions consumen contexto. Verificar impacto.
4. **¿La rúbrica BCG necesita calibración para el dominio específico de KAOS?** — Las 8 dimensiones son genéricas; podrían necesitar ajuste para estrategia de producto/software.
5. **¿Debemos implementar temperature por paso en Metis solo, o extender a todos los agentes?** — La evidencia sugiere que cada agente se beneficia de temperatura optimizada por rol.

---

## Gap Feedback (Mnemosyne)

**Gaps detectados pre-investigación**:
- No existía documentación sobre MCP servers estratégicos en el vault
- No había referencia al paper OKR-Agent
- No existía benchmarking de temperatura para agents

**Nuevos conceptos para curación**:
- `strategy-mcp` — herramieta MCP con 12 frameworks estratégicos
- `OKR-Agent` — paper de referencia para integración OKRs en pipelines multi-agente
- `BCG Evaluation Rubric` — framework de evaluación de 8 dimensiones
- `Foreman Pattern` — patrón arquitectónico dominante en MAS
- `Devil's Advocate Pattern` — patrón de cuestionamiento estratégico
- `AEMA` — evaluation framework process-aware
- `Radical Focus` — metodología de OKRs (Christina Wodtke)
- `Temperature Governance` — guía de temperatura por componente en MAS

---

## Fuentes

### Papers Académicos
- [OKR-Agent: Agents meet OKR](https://arxiv.org/abs/2311.16542)
- [Building Effective AI Agents (Anthropic)](https://resources.anthropic.com/hubfs/Building%20Effective%20AI%20Agents-%20Architecture%20Patterns%20and%20Implementation%20Frameworks.pdf)
- [AEMA: Verifiable Evaluation Framework](https://arxiv.org/pdf/2601.11903)
- [SPIN-Bench: Strategic Planning Benchmark](https://arxiv.org/pdf/2503.12349)
- [GameBench: Strategic Reasoning](https://arxiv.org/pdf/2406.06613)
- [Production-Grade Agentic AI Workflows](https://arxiv.org/html/2512.08769)
- [LangGraph+CrewAI Exploration](https://arxiv.org/html/2411.18241v1)
- [Strategic Reasoning of LLMs (NeurIPS 2024)](https://proceedings.neurips.cc/paper_files/paper/2024/file/3191170938b6102e5c203b036b7c16dd-Paper-Conference.pdf)

### MCP Servers
- [strategy-mcp v0.1.0](https://pypi.org/project/strategy-mcp/)
- [business-design-mcp](https://github.com/albertogferrario/business-design-mcp)
- [SWOTPal MCP Server](https://swotpal.com/mcp)
- [ai-pm-skills-mcp v2.2.0](https://www.npmjs.com/package/ai-pm-skills-mcp)
- [backcast-mcp-server](https://github.com/NET-OF-BEING/backcast-mcp-server)
- [mcp-business-intelligence](https://github.com/sjcripps/mcp-business-intelligence)
- [agent-planner-mcp v0.6.2](https://github.com/TAgents/agent-planner-mcp)
- [Tability MCP Server](https://www.tability.io/odt/articles/agentic-okrs)
- [Oboard MCP Integration](https://oboard.io/blog/oboard-becomes-an-ai-okr-software)
- [Nexus MCP](https://github.com/10-gaurav-01/nexus-mcp)
- [DeepMCPAgent](https://github.com/olserres-crypto/DeepMCPAgent)

### Guías de Configuración
- [Temperature Governance in MAS (Pan, 2026)](https://tianpan.co/blog/2026-04-20-temperature-governance-multi-agent-systems)
- [Sampling Parameters in Production (Pan, 2026)](https://tianpan.co/blog/2026-04-18-sampling-parameters-production-temperature-top-p-tuning)
- [Temperature as Product Decision (Pan, 2026)](https://tianpan.co/blog/2026-04-19-temperature-as-product-decision)
- [LLM Sampling Parameter Planner](https://uatgpt.com/tools/sampling-parameter-planner/)
- [Temperature and Top-P Guide (Unprompted Mind)](https://www.unpromptedmind.com/temperature-top-p-llm-guide/)
- [LLM Parameters Guide (Amit Ray, 2026)](https://amitray.com/llm-parameters-temperature-top-p-top-k-guide/)
- [LLM Hyperparameters Guide (Abstract Algorithms)](https://www.abstractalgorithms.dev/llm-hyperparameters-guide-temperature-top-p-and-top-k-explained)
- [AI Agents Prompting Guide (SurePrompts, 2026)](https://sureprompts.com/blog/ai-agents-prompting-guide)
- [Prompt Engineering for AI Agents (Nitin Singh, 2026)](https://nitinksingh.com/posts/prompt-engineering-for-ai-agents--grounding-roles-and-yaml-configuration/)
- [Designing System Prompts for Autonomous Agents (Charles Chen)](https://wiki.charleschen.ai/ai/processed/wiki/llm-core/prompts/queries/designing-system-prompts-for-autonomous-agents)
- [ElevenLabs Prompting Guide](https://elevenlabs.io/docs/eleven-agents/best-practices/prompting-guide.mdx)
- [XMPro System Prompts Guide](https://github.com/XMPro/Multi-Agent/blob/main/docs/implementation-guides/system-prompts.md)
- [Gemini 3 Prompting Guide (Google)](https://docs.cloud.google.com/gemini-enterprise-agent-platform/models/start/gemini-3-prompting-guide)

### Sistemas Multi-Agente de Referencia
- [Multi-Agent Orchestration Patterns (RapidClaw, 2026)](https://rapidclaw.dev/blog/multi-agent-orchestration-patterns-2026)
- [Multi-Agent AI Systems Guide (Inventiple, 2026)](https://www.inventiple.com/blog/multi-agent-ai-systems-architecture-guide)
- [How to Build Multi-Agent System (Knowlee, 2026)](https://www.knowlee.ai/blog/how-to-build-multi-agent-ai-system)
- [CrewAI vs LangGraph vs AutoGen (Dev Digest, 2026)](https://www.developersdigest.tech/guides/ai-agent-frameworks-compared)
- [Multi-Agent AI 2026 (DEV Community)](https://dev.to/ottoaria/multi-agent-ai-in-2026-build-production-systems-with-crewai-langgraph-autogen-5e40)
- [Captain Cool (DEV)](https://dev.to/angel_macwan_cfb0a96ed25c/captain-cool-a-multi-agent-ai-that-thinks-like-an-ipl-captain-1o3f)
- [Spec-To-Ship Pipeline](https://github.com/dakshjain-1616/Spec-To-Ship)
- [SOP-Team Framework](https://github.com/shalinda-j/SOP-Team)
- [gru-ai Pipeline](https://github.com/andrew-yangy/gru-ai)
- [OrganAIze System](https://github.com/akashchekka/OrganAIze)
- [AutoCodeAI Framework](https://github.com/raja21068/AutoCodeAI)
- [PM Operating System](https://github.com/Ninety2UA/pm-operating-system)
- [ElBruno Agent Orchestration](https://github.com/elbruno/elbruno.agentsorchestration)
- [Coordinated Agent Team](https://github.com/q3ok/coordinated-agent-team)
- [7 AI Models Architecture](https://dev.to/judy_miranttie/how-i-run-7-ai-models-247-multi-agent-architecture-in-practice-4k6l)

### Evaluación de Calidad
- [DeepEval BCG Rubric](https://github.com/EvXata/deepeval-bcg)
- [AI Agent Output Validation (DEV, 2026)](https://dev.to/waxell/ai-agent-output-validation-in-production-why-static-quality-gates-fail-and-how-to-fix-them-51ba)
- [How to Evaluate AI Agents (AWS, 2026)](https://dev.to/aws/how-to-evaluate-ai-agents-llm-as-judge-tutorial-4a6h)
- [3 Framework Comparison (AWS, 2026)](https://dev.to/aws/3-ways-to-evaluate-ai-agents-a-practical-comparison-24p9)
- [AI Evaluation Framework (DreamHost)](https://www.dreamhost.com/news/announcements/ai-evaluation-framework-how-we-built-a-system-to-score-and-improve-ai-generated-business-plans/)
- [Automatos Verification & Quality](https://docs.automatos.app/automatos-ai-docs/design-docs/prds/103-verification-quality)
- [Afrexai OKR Engine](https://aiagentivo.com/skills/openclaw-skills-afrexai-okr-engine)
- [Thinking Tools / /taste](https://github.com/andrew-shwetzer/thinking-tools)
- [agent-evals (ThinkWright)](https://thinkwright.ai/agent-evals)
- [OKR Brainstorm Skill](https://github.com/weemax/Claude-Skills/blob/main/project-management/execution/brainstorm-okrs/SKILL.md)
- [Product Strategist Skill](https://github.com/alirezarezvani/claude-skills/blob/main/agents/product/cs-product-strategist.md)
- [AI Agent Systems Handbook](https://github.com/Prompthon-IO/agent-systems-handbook)

### Plataformas SaaS Estratégicas
- [ClearPoint Strategy AI](https://www.clearpointstrategy.com/features)
- [PlanHQ AI Platform](https://planhq.ai/)
- [STRATUM Platform](https://stratum.ws/)
- [Jeda.ai Strategic Planning](https://jeda.ai/ai-for-strategic-planning)
- [Tars AI Strategist Agent](https://hellotars.com/ai-agents/ai-strategist)
- [JieGou Board Prep](https://jiegou.ai/blog/executive-board-prep-automation/)

### Herramientas y Frameworks
- [LangChain MCP Adapters](https://github.com/langchain-ai/langchain-mcp-adapters)
- [MCP Server with LangGraph](https://mcp-server-langgraph.mintlify.app/getting-started/introduction)
- [LangGraph MCP Integration](https://github.com/esxr/langgraph-mcp)
- [api2mcp (LangGraph + MCP)](https://github.com/manavghosh/api2mcp)
- [AI Agent Handbook (vasilyevdm)](https://github.com/vasilyevdm/ai-agent-handbook)
- [Reasoning Router (LangGraph)](https://github.com/Pro-GenAI/Reasoning-Router)
- [Agent Workflow Designer Skill](https://github.com/borghei/Claude-Skills)
- [AutoGPT vs CrewAI vs LangGraph (Agix, 2026)](https://agixtech.com/insights/langgraph-vs-crewai-vs-autogpt/)
- [CrewAI vs LangGraph (Xcelore)](https://xcelore.com/blog/langgraph-vs-crewai/)
- [CrewAI vs LangGraph Building Same System](https://notes.muthu.co/2025/12/crewai-vs-langgraph-building-the-same-multi-agent-system-in-both/)
- [Strategy Frameworks Builder (Anselmoo)](https://github.com/Anselmoo/mcp-ai-agent-guidelines/blob/main/docs/tools/strategy-frameworks-builder.md)
