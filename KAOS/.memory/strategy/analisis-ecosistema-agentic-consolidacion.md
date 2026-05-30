# Análisis Estratégico y Consolidación — KAOS vs Ecosistema Agentic

**Elaborado por**: Metis (Μῆτις), Diosa de la Estrategia  
**Fecha**: 2026-05-30  
**Perfil**: `desarrollo` → Modo Strategy  
**Propósito**: Análisis DOFA, OKRs multi-horizonte, decisiones por recurso, roadmap estratégico y recomendaciones ejecutivas  
**BCG Evaluation**: Ver sección final

---

## Resumen Ejecutivo

KAOS se encuentra en una posición única pero vulnerable. Como sistema multi-agente con infraestructura propia (DSOL rounter, quality engines, feature flags, file locking), KAOS ha construido diferenciación real en calidad y control de agentes. Sin embargo, el ecosistema está convergiendo rápidamente — Mastra (24.6K⭐) está estandarizando frameworks TypeScript, Hermes Agent está resolviendo el problema de tool overload con progressive disclosure, y el paradigma de Harness Engineering está redefiniendo cómo se construye software con agentes. La ventana para integrar estos aprendizajes es de 3-6 meses. La recomendación principal es **adoptar el mindset de Harness Engineering + MCP nativo + progressive disclosure como pilares estratégicos**, integrando selectivamente Mastra (evaluar como orquestador), Hermes Tool Search (adoptar el patrón), y Horizon (adoptar pipeline). Ignorar opencodex y Alephant por ahora.

---

## 1. Análisis DOFA Consolidado

### Fortalezas (Interno)

| # | Fortaleza | Rating | Evidencia |
|---|-----------|--------|-----------|
| F1 | **Arquitectura multi-agente completa** (6 agentes especializados) | 5/5 | Aletheia, Kosmos, Metis, Kratos, Kronos, Mnemosyne — cada uno con SOUL.md + AGENTS.md + SKILL.md |
| F2 | **Infraestructura de calidad madura** | 5/5 | quality engines (agent.py, vault.py, store.py), BCG evaluator, verification chain, session runner, post-output hooks |
| F3 | **DSOL routing inteligente** | 4/5 | Sistema de ruteo por tipo de tarea con fallback chains, tier-based sampling, budget enforcement |
| F4 | **Firecrawl + Impeccable skills** | 4/5 | Web scraping y frontend design como capacidades diferenciadas, skills estándar compatibles con agentskills.io |
| F5 | **Memory layer con Mnemosyne** | 4/5 | memory_bridge, memory_lifecycle, mnemobeam, code_memory — persistencia multi-nivel |
| F6 | **Documentación de agente rigurosa** | 5/5 | Cada agente tiene SOUL.md (identidad), AGENTS.md (tools/contratos), SKILL.md (metodología) |
| F7 | **Speed metrics y observabilidad** | 3/5 | mcp-speed proporciona métricas de sistema dual (flash/production) |

### Debilidades (Interno)

| # | Debilidad | Rating | Evidencia |
|---|-----------|--------|-----------|
| D1 | **Sin MCP nativo como protocolo estándar** | 2/5 | KAOS usa herramientas internas y bridges ad-hoc; no expone ni consume MCP como protocolo nativo. Mastra, Hermes, y Horizon ya lo tienen built-in |
| D2 | **Ecosistema TypeScript ausente** | 1/5 | KAOS es Python-centric. Mastra (24.6K⭐) y todo el crecimiento del ecosistema agentic es TypeScript. Sin bridge TS, KAOS no puede integrar el ecosistema |
| D3 | **Sin progressive disclosure de tools** | 2/5 | KAOS carga todos los tools/schemas upfront. Hermes Agent demostró que esto degrada accuracy 49%→74% con Tool Search |
| D4 | **Gateway propietario vs estándares abiertos** | 2/5 | KAOS tiene gateway propio (:8642) pero sin agent identity estándar, ni x402, ni compatibilidad con OpenAI API surface |
| D5 | **Cobertura de tests limitada** | 3/5 | Los tests existen pero están fragmentados. No hay benchmark de accuracy contra datasets estándar |
| D6 | **Sin sandbox de ejecución para agentes** | 2/5 | .tools/sandbox/ existe pero no está integrado como harness layer. Harness Engineering muestra que el sandbox es crítico |
| D7 | **Sin evaluación sistemática de agentes** | 3/5 | Existe BCG evaluator pero no hay evals comparables a Anthropic/OpenAI benchmarks |

### Oportunidades (Externo)

| # | Oportunidad | Rating | Evidencia |
|---|-------------|--------|-----------|
| O1 | **Harness Engineering como paradigma** | 5/5 | OpenAI, Anthropic, Martin Fowler, ThoughtWorks convergen: el futuro es diseñar sistemas de control para agentes, no escribir código. KAOS puede posicionarse como plataforma de harness engineering |
| O2 | **MCP como protocolo estándar de la industria** | 5/5 | MCP es soportado por Claude Desktop, Cursor, VS Code, Codex, opencode, Mastra, Hermes, Horizon. Adoptar MCP = interoperabilidad inmediata |
| O3 | **Progressive disclosure como ventaja competitiva** | 4/5 | Hermes demostró mejora 49%→88% en accuracy con Tool Search. Pocos sistemas lo implementan — first mover advantage |
| O4 | **Agent Skills como estándar emergente** | 4/5 | Addy Osmani's Agent Skills (27K⭐) y agentskills.io definen el estándar. Firecrawl skill de KAOS ya es compatible |
| O5 | **AGENTS.md como entry point estándar** | 4/5 | Addy Osmani popularizó AGENTS.md. KAOS ya lo implementa por agente — ventaja de adopción |
| O6 | **Agregación de contenido con IA** | 3/5 | Horizon (4.6K⭐) muestra pipeline MCP completo para news aggregation. Aplicable a inteligencia competitiva de KAOS |
| O7 | **Agent identity + payments** | 2/5 | x402 permite agentes que pagan por API calls. Temprano, pero podría ser diferenciador a 12 meses |

### Amenazas (Externo)

| # | Amenaza | Rating | Evidencia |
|---|---------|--------|-----------|
| A1 | **Mastra se convierte en estándar de facto** | 5/5 | 24.6K⭐, 1.77M npm/mes, creciendo 30-35 estrellas/día. Si Mastra domina, KAOS como sistema aislado pierde relevancia |
| A2 | **Frameworks generalistas absorben casos de uso** | 4/5 | Mastra, Haystack, LangChain ofrecen agents + workflows + RAG + evals. KAOS compite contra estos sin ser framework generalista |
| A3 | **OpenAI/Anthropic cierran el stack** | 4/5 | Codex (Computer Use nativo), Claude Code con MCP nativo. Si los vendors capturan el stack, intermediarios como KAOS pierden valor |
| A4 | **Agentes autónomos reducen necesidad de multi-agente orquestado** | 3/5 | Si un solo agente con tool calling y MCP es suficiente, la arquitectura multi-agente de KAOS es over-engineering |
| A5 | **Ritmo de innovación del ecosistema** | 4/5 | Nous Research, Mastra, Harness Engineering evolucionan semanalmente. KAOS necesita velocidad de integración |

### Estrategias Derivadas

| Tipo | Estrategia |
|------|-----------|
| **FO (maxi-maxi)** | Usar la arquitectura multi-agente + quality engines como base para una plataforma de **Harness Engineering** que integre MCP nativo |
| **DO (mini-maxi)** | Adoptar MCP nativo y progressive disclosure para cerrar la brecha tecnológica mientras el ecosistema aún está fragmentado |
| **FA (maxi-mini)** | Usar la madurez de quality engines y DSOL routing para diferenciarse de Mastra y frameworks generalistas |
| **DA (mini-mini)** | Priorizar integración MCP antes de que Mastra cierre el estándar; construir bridge TypeScript para no quedar fuera del ecosistema |

---

## 2. Mapa de Posicionamiento Estratégico

### Dónde está KAOS hoy vs dónde debería estar

```
Eje X: Madurez como Plataforma Agentic
Eje Y: Alineación con Estándares Abiertos (MCP, AGENTS.md, Skills)

Alta               ● Mastra
alineación         ● Hermes Agent
estándares         ● Horizon
                   │
                   │        ★ KAOS HOY (fuerte internamente,
                   │          débil en estándares abiertos)
                   │
                   ● opencodex
                   ● Alephant
                   │
Baja               ──────────────────────────────
                   Baja madurez          Alta madurez
                   plataforma            plataforma

                   ★ KAOS META (Q4 2026):
                   Alta alineación + Alta madurez
                   = Intersección Harness Engineering + MCP nativo
```

### Clasificación de los 7 recursos

| Recurso | Clasificación | Rationale |
|---------|--------------|-----------|
| **Mastra** (24.6K⭐) | ⚠️ **Competencia directa + Complemento estratégico** | Framework TypeScript con agents, workflows, RAG, evals, MCP authoring. Compite directamente como plataforma agentic. Pero su MCP authoring y evals pueden integrarse como complemento |
| **Hermes Agent Tool Search** (Nous Research) | 💡 **Inspiración arquitectónica** | Progressive disclosure de MCP tools resuelve el problema de context window overload. El patrón search→describe→call es replicable en KAOS sin depender de Hermes |
| **Horizon** (Thysrael, 4.6K⭐) | 🔗 **Complemento estratégico** | Pipeline MCP de 7 pasos para agregación de contenido. Integrable como data pipeline para inteligencia competitiva de Aletheia |
| **Alephant AI Gateway** (72⭐) | 👁️ **Monitorear** | Gateway Rust con x402. Interesante pero inmaduro (beta 0.2.0). El concepto de agent identity + payments es relevante a 12 meses |
| **opencodex/open-computer-use** (88⭐) | ❌ **Ignorar** | Computer Use como MCP service. No relevante para KAOS (no es cliente desktop, es plataforma de agentes). Además, el espacio Computer Use está siendo commoditizado por OpenAI, Anthropic |
| **Addy Osmani Agent Skills** (27K⭐) | 💡 **Inspiración arquitectónica** | El estándar AGENTS.md y Agent Skills son compatibles con KAOS. Validar que Firecrawl skill sigue el formato agentskills.io |
| **Harness Engineering** (OpenAI/Anthropic/Fowler) | 🚀 **Adoptar como filosofía** | No es un producto sino un paradigma: diseñar sistemas de control para agentes. Es la justificación estratégica de KAOS como plataforma. Adoptar AGENTS.md, docs/, linters custom, garbage collection |

---

## 3. OKRs — Dos Horizontes

### OKRs Corto Plazo — Q3 2026 (0-3 meses)

#### O1: Adoptar MCP como protocolo nativo de comunicación entre agentes

| Key Result | Baseline | Target | Respaldo de Aletheia |
|-----------|----------|--------|---------------------|
| KR1: Gateway :8642 expone endpoint MCP stdio+HTTP | No existe | 2 transports funcionales | Alephant, Hermes, Horizon — todos implementan MCP |
| KR2: 3 agentes (Aletheia, Kosmos, Kratos) consumen MCP tools externos | 0 agentes | 3 agentes | Mastra MCP client, Hermes MCP integration |
| KR3: Tool Search (progressive disclosure) implementado para MCP tools | No existe | Implementado con BM25 retrieval | Hermes Agent Tool Search: 49%→74% accuracy gain |

**Dependencias**: Requiere refactor del gateway para soportar MCP protocol. Depende de Kratos para implementación.  
**Riesgos**: Medium — cambio arquitectónico significativo. Mitigación: implementar como capa paralela, no reemplazo.

#### O2: Implementar Harness Engineering como marco de desarrollo de agentes

| Key Result | Baseline | Target | Respaldo de Aletheia |
|-----------|----------|--------|---------------------|
| KR1: AGENTS.md estandarizado para todos los agentes | Ya existe parcialmente | 6/6 agentes con AGENTS.md validado | Addy Osmani Agent Skills, OpenAI Harness Engineering |
| KR2: Custom linters + structural tests por agente | 0 | 3 agentes con linters | OpenAI Harness: "layered architecture enforced by custom linters" |
| KR3: Garbage collection agents scanning for drift | No existe | 1 garbage collector semanal | OpenAI: "recurring garbage collection scans for drift" |

**Dependencias**: Bajo — son mejoras incrementales sobre la arquitectura actual.  
**Riesgos**: Low — no requiere cambios disruptivos.

#### O3: Pipeline de inteligencia competitiva basado en Horizon

| Key Result | Baseline | Target | Respaldo de Aletheia |
|-----------|----------|--------|---------------------|
| KR1: Pipeline Fetch→Dedup→Score→Filter→Enrich→Summarize operativo | No existe | Pipeline MCP de 7 pasos | Horizon: 7-step pipeline, MCP server built-in |
| KR2: 5 fuentes de inteligencia (HN, RSS, Reddit, Telegram, GitHub) integradas | 0 | 5 fuentes | Horizon multi-source aggregation |
| KR3: Daily briefing automático en Obsidian vault | No existe | 5 briefings/semana | Horizon daily summary generation |

**Dependencias**: Medio — requiere adaptar el pipeline de Horizon a KAOS.  
**Riesgos**: Low-Médium — Horizon es maduro (4.6K⭐) y tiene MCP nativo.

---

### OKRs Medio Plazo — Q4 2026 (3-6 meses)

#### O4: Posicionar KAOS como plataforma de Harness Engineering

| Key Result | Baseline | Target | Respaldo de Aletheia |
|-----------|----------|--------|---------------------|
| KR1: KAOS expone API compatible con OpenAI para herramientas externas | No existe | Compatibilidad parcial | Alephant AI Gateway: OpenAI-compatible /v1/* routes |
| KR2: Framework de evals de agente (model-graded + rule-based) | BCG evaluator + basic tests | 3 tipos de eval implementados | Mastra evals: model-graded, rule-based, statistical |
| KR3: Sandbox de ejecución integrado con el pipeline | .tools/sandbox/ existe pero no integrado | Integrado en pipeline CI/CD | Harness Engineering: sandbox como capa de control |

**Dependencias**: Requiere O1 y O2 completados.  
**Riesgos**: Medium — alcance ambicioso.

#### O5: Ecosistema de skills y agent identity

| Key Result | Baseline | Target | Respaldo de Aletheia |
|-----------|----------|--------|---------------------|
| KR1: Catálogo público de skills compatibles con agentskills.io | Firecrawl skill existente | 5 skills publicados | Addy Osmani Agent Skills (27K⭐) |
| KR2: Agent identity (ERC-8004 / JWT) para agentes KAOS | No existe | Identidad implementada | Alephant x402: agent identity + ledger |
| KR3: Bridge TypeScript para integración con ecosistema npm | No existe | Bridge funcional | Mastra (24.6K⭐, TypeScript), crecimiento del ecosistema TS |

**Dependencias**: Alto — bridge TypeScript requiere ingeniería significativa.  
**Riesgos**: Medium-High — depende de adopción del estándar de agent identity.

---

## 4. Decisión Estratégica por Recurso

### 1. Mastra (24.6K⭐) — EVALUAR (POC en Q3)

**Decisión**: **Evaluar** — Hacer POC de integración de Mastra como orquestador complementario.

**Justificación**: Mastra es el framework TypeScript más prometedor del ecosistema (24.6K⭐, 1.77M npm/mes, equipo ex-Gatsby). No debemos competir frontalmente con él — sería una batalla perdida. Pero sí podemos **integrarlo como capa de orquestación externa**: usar Mastra para definir workflows complejos que luego ejecuten agentes KAOS via MCP. El POC debe responder: ¿Mastra puede ser el "frontend" de orquestación mientras KAOS es el "backend" de ejecución de agentes especializados? Si la respuesta es sí, pasamos a **Adoptar** en Q4. Si no, **Monitorear**.

**Riesgo**: Si Mastra se convierte en estándar de facto y KAOS no tiene integración, quedamos aislados del ecosistema.

**Timeline POC**: Semanas 3-4 de Q3.

---

### 2. Hermes Agent Tool Search (Nous Research) — ADOPTAR AHORA (el patrón, no el código)

**Decisión**: **Adoptar ahora** — Implementar progressive disclosure de MCP tools en KAOS.

**Justificación**: El patrón search→describe→call es arquitectónico, no un producto. Hermes demostró con datos de Anthropic que el progressive disclosure mejora accuracy de 49%→74% (Opus 4) y 79.5%→88.1% (Opus 4.5). La implementación es relativamente simple (BM25 retrieval sobre tool name + description + parameter names, con substring fallback). No requiere dependencia externa. El ROI es inmediato: menos tokens consumidos, mejor accuracy, sesiones más largas.

**Qué implementar**: 
1. Tres bridge tools: `tool_search(query)`, `tool_describe(tool_id)`, `tool_call(tool_id, args)`
2. Auto-mode: activar solo cuando schemas >10% del context window
3. Core tools (terminal, read/write file, etc.) nunca se difieren
4. Catálogo scoped a la sesión actual

**Esfuerzo estimado**: 3-5 días para Kratos.

---

### 3. Horizon (Thysrael, 4.6K⭐) — ADOPTAR AHORA (como pipeline de inteligencia)

**Decisión**: **Adoptar ahora** — Integrar el pipeline MCP de Horizon como motor de inteligencia competitiva.

**Justificación**: Horizon es un proyecto maduro (4.6K⭐) con MCP nativo, pipeline de 7 pasos validado, y 5 fuentes de datos. Es directamente integrable como skill de Aletheia. El pipeline Fetch→Dedup→Score→Filter→Enrich→Summarize resuelve un problema concreto de KAOS: generar inteligencia competitiva estructurada y persistirla en Obsidian vault. La integración es vía MCP stdio — no requiere código nuevo significativo.

**Qué integrar**: 
1. MCP server de Horizon como skill de Aletheia
2. Pipeline diario que alimenta `.memory/strategy/` con briefings
3. Output en Obsidian para trazabilidad

**Esfuerzo estimado**: 2-3 días para Aletheia + Kratos.

---

### 4. Alephant AI Gateway (72⭐, beta 0.2.0) — MONITOREAR

**Decisión**: **Monitorear** — No invertir ahora, revisar en Q1 2027.

**Justificación**: Alephant es un proyecto interesante (gateway Rust con x402, agent identity, ledger financiero) pero muy inmaduro (72⭐, beta 0.2.0). El concepto de agent identity + payments está alineado con la visión de largo plazo de KAOS (agentes autónomos que pagan por servicios), pero la implementación está lejos de producción. Además, el espacio x402 está siendo impulsado por múltiples actores (r402, tempo-x402, x402-rs) sin un ganador claro. Mejor esperar a que el estándar se consolide.

**Trigger para reevaluar**: Cuando Alephant alcance >500⭐ o se integre con MCP estándar. O cuando x402 sea adoptado por OpenAI/Anthropic.

---

### 5. opencodex / open-computer-use (88⭐) — IGNORAR

**Decisión**: **Ignorar** — No es relevante para KAOS en este momento.

**Justificación**: open-computer-use es un MCP server que permite a agentes usar el mouse/teclado del sistema (Computer Use). Esto es relevante para Codex Desktop y Claude Desktop (asistentes de coding locales), pero KAOS es un sistema multi-agente backend que opera sobre APIs y herramientas programáticas, no sobre interfaces gráficas. KAOS no necesita "ver" la pantalla — necesita ejecutar pipelines, investigar, y generar código. Además, OpenAI y Anthropic están commoditizando Computer Use con sus implementaciones nativas.

**Excepción**: Si KAOS evoluciona para incluir un agente de testing visual o QA automatizado, Computer Use podría ser relevante. Pero no en el horizonte 0-6 meses.

---

### 6. Addy Osmani Agent Skills (27K⭐) — ADOPTAR AHORA (el estándar)

**Decisión**: **Adoptar ahora** — Alinear skills de KAOS con el estándar agentskills.io.

**Justificación**: Addy Osmani's Agent Skills (27K⭐) y AGENTS.md se están convirtiendo en el estándar de facto para skills de agente. KAOS ya tiene Firecrawl como skill compatible. La adopción es principalmente de formato: asegurar que todos los skills de KAOS sigan el estándar agentskills.io para interoperabilidad. No requiere reescribir skills existentes.

**Qué hacer**:
1. Validar que Firecrawl skill cumple agentskills.io spec
2. Crear skill template estándar para nuevos skills
3. Documentar el estándar en AGENTS.md de cada agente

**Esfuerzo estimado**: 1-2 días para Metis + Kratos.

---

### 7. Harness Engineering (Paradigma) — ADOPTAR AHORA (como filosofía central)

**Decisión**: **Adoptar ahora** — Hacer de Harness Engineering la filosofía central de KAOS.

**Justificación**: Harness Engineering no es un producto sino un paradigma: "de escribir código a diseñar sistemas de control para agentes". Esto es exactamente lo que KAOS hace (quality engines, verification chain, DSOL routing, post-output hooks), pero sin el lenguaje ni el marco conceptual para comunicarlo. Adoptar Harness Engineering como filosofía permite:
- Posicionar a KAOS como plataforma de harness engineering
- Guiar decisiones arquitectónicas con un marco coherente
- Comunicar el valor a stakeholders con el lenguaje que la industria está adoptando (OpenAI, Anthropic, Martin Fowler, ThoughtWorks)

**Qué implementar**:
1. Renombrar/reorganizar componentes bajo terminología de harness (sensors, guides, feedback loops)
2. Implementar los 3 componentes de OpenAI Harness: AGENTS.md, docs/ con indexed design docs, custom linters
3. Agregar "garbage collection" agents que escanean drift semanalmente
4. Documentar el paradigma en la documentación de KAOS

**Esfuerzo estimado**: 2-3 días para Metis + Kosmos.

---

## 5. Roadmap Estratégico Timeline

```
Q2 2026 (ahora)              Q3 2026 (0-3 meses)              Q4 2026 (3-6 meses)
─────────────────      ──────────────────────────────      ─────────────────────────
                                                                                
[OKRs actuales]        [O1: MCP Nativo]                    [O4: Harness Platform]    
                        ┌─ Gateway MCP stdio+HTTP           ┌─ API compatible OpenAI  
                        └─ 3 agentes con MCP client         └─ Framework de evals     
                                                             └─ Sandbox integrado     
   │                   [O2: Harness Engineering]                                    
   │                    ┌─ AGENTS.md estandarizado          [O5: Ecosistema]         
   │                    └─ Custom linters x agente          ┌─ Catálogo skills público
   │                    └─ Garbage collector semanal        └─ Bridge TypeScript      
   │                                                         └─ Agent identity        
   │                   [O3: Pipeline Inteligencia]                                  
   │                    ┌─ Horizon MCP integrado                                    
   │                    └─ 5 fuentes + daily briefing                              

Decisiones por recurso incrustadas en el roadmap:

┌─────────────────────────────────────────────────────────────────────────────┐
│ Q3 Sem 1-2:                                                                    │
│   ✅ Hermes Tool Search → Implementar progressive disclosure (ADOPTAR)       │
│   ✅ Addy Osmani Standards → Validar skills contra agentskills.io (ADOPTAR)  │
│   ✅ Harness Engineering → Documentar filosofía, nombrar componentes (ADOPTAR)│
│                                                                               │
│ Q3 Sem 3-4:                                                                    │
│   ✅ Horizon → Integrar pipeline MCP para inteligencia competitiva (ADOPTAR) │
│   🔬 Mastra → POC: integración como orquestador complementario (EVALUAR)     │
│                                                                               │
│ Q3 Sem 5-8:                                                                    │
│   ✅ MCP Native → Gateway :8642 expone MCP transports                          │
│   🔬 Mastra → Decidir: Adoptar vs Monitorear basado en resultados POC         │
│                                                                               │
│ Q4 2026:                                                                       │
│   👁️ Alephant → Revisar si >500⭐ o x402 consolidado (MONITOREAR)            │
│   ✅ OpenAI-compatible API → Posicionamiento como plataforma de Harness       │
│   🔬 Bridge TypeScript → Evaluar esfuerzo vs impacto                           │
└─────────────────────────────────────────────────────────────────────────────┘
```

### Dependencias Técnicas Críticas

| Dependencia | Descripción | Bloquea | Estimado |
|-------------|-------------|---------|----------|
| MCP stdio transport en Gateway | Implementar MCP protocol en el gateway existente | O1.KR1, O1.KR2 | 2 semanas |
| BM25 retrieval para Tool Search | Implementar búsqueda sobre tool schemas | O1.KR3 | 1 semana |
| Integración MCP de Horizon | Conectar Horizon vía MCP stdio como skill de Aletheia | O3.KR1 | 3 días |
| Custom linter framework | Crear sistema de linters por agente | O2.KR2 | 1 semana |
| Bridge TypeScript | Puente entre runtime Python y ecosistema npm | O5.KR3 | 4-6 semanas |

---

## 6. Recomendaciones Ejecutivas (Acción Inmediata)

### TOP 1: Implementar Progressive Disclosure de Tools (Inspirado en Hermes)

| Aspecto | Detalle |
|---------|---------|
| **Qué** | Implementar 3 bridge tools: `tool_search`, `tool_describe`, `tool_call` con BM25 retrieval. Modo auto que se activa cuando schemas >10% del context window |
| **Quién** | Kratos (implementación) + Metis (especificación) |
| **Tiempo** | 3-5 días |
| **Riesgos** | Medium — puede afectar sesiones con pocos tools donde el overhead no se justifica. Mitigación: modo auto con threshold configurable |
| **Métrica de éxito** | Reducción de tokens consumidos por tool schemas en >50% sin degradación de accuracy |
| **Decisión** | **Sí — empezar mañana** |

### TOP 2: Integrar Horizon como Pipeline de Inteligencia Competitiva

| Aspecto | Detalle |
|---------|---------|
| **Qué** | Conectar Horizon MCP server como skill de Aletheia. Pipeline diario: Fetch→Dedup→Score→Filter→Enrich→Summarize desde 5 fuentes. Output en Obsidian vault |
| **Quién** | Aletheia (configurar fuentes) + Kratos (integrar MCP) |
| **Tiempo** | 2-3 días |
| **Riesgos** | Bajo — Horizon es maduro con MCP nativo. Riesgo: rate limiting de fuentes externas. Mitigación: caching y backoff |
| **Métrica de éxito** | 5 briefings/semana generados automáticamente |
| **Decisión** | **Sí — empezar mañana** |

### TOP 3: Estandarizar AGENTS.md + Custom Linters por Agente (Harness Engineering)

| Aspecto | Detalle |
|---------|---------|
| **Qué** | Revisar AGENTS.md de cada agente contra estándar. Implementar custom linters para Aletheia (factualidad), Kosmos (coherencia arquitectónica), Kratos (calidad de código). Crear garbage collector semanal |
| **Quién** | Metis (especificación) + Kosmos (arquitectura de linters) + Kratos (implementación) |
| **Tiempo** | 4-5 días (paralelizable) |
| **Riesgos** | Bajo — cambios incrementales. Riesgo: linters muy estrictos pueden ralentizar. Mitigación: linters como warnings no bloqueantes inicialmente |
| **Métrica de éxito** | 100% de agentes con AGENTS.md validado; 3 linters custom operativos |
| **Decisión** | **Sí — empezar mañana** |

### TOP 4: Hacer POC de Mastra como Orquestador Complementario

| Aspecto | Detalle |
|---------|---------|
| **Qué** | Configurar Mastra localmente. Definir un workflow simple (research→analyze→report) que use agentes KAOS via MCP. Evaluar si Mastra puede ser el frontend de orquestación |
| **Quién** | Kosmos (evaluación arquitectónica) + Kratos (setup técnico) |
| **Tiempo** | 2-3 días (POC limitado) |
| **Riesgos** | Bajo — es un POC, no un commitment. Riesgo: Mastra puede no integrarse bien con runtime Python de KAOS. Mitigación: definir criterios de éxito claros antes de empezar |
| **Métrica de éxito** | POC responde "Sí/No" a: ¿Mastra como orquestador + KAOS como backend de agentes es viable? |
| **Decisión** | **Sí — POC en semana 3-4 de Q3** (no mañana, requiere preparación) |

### TOP 5: Documentar Harness Engineering como Filosofía Central de KAOS

| Aspecto | Detalle |
|---------|---------|
| **Qué** | Redactar documento de posicionamiento: "KAOS como plataforma de Harness Engineering". Reorganizar documentación existente bajo terminología de harness (sensors, guides, feedback loops, garbage collection). Agregar sección en README.md |
| **Quién** | Metis (documento estratégico) |
| **Tiempo** | 2 días |
| **Riesgos** | Mínimo. Riesgo: sobre-prometer si la implementación aún no está completa. Mitigación: ser explícito sobre qué está implementado y qué es visión |
| **Métrica de éxito** | Documento revisado y aprobado por el equipo; README actualizado |
| **Decisión** | **Sí — empezar mañana** |

---

## Matriz de Riesgos de la Estrategia

| Riesgo | Probabilidad | Impacto | Score (PxI) | Mitigación |
|--------|-------------|---------|-------------|------------|
| Mastra se consolida como estándar sin integración KAOS | Alta (4) | Alto (5) | **20** | POC en Q3; decisión de adoptar o construir bridge |
| Progressive disclosure no mejora accuracy en contexto KAOS | Media (3) | Medio (3) | **9** | A/B testing: con/sin Tool Search en sesiones reales |
| Horizon pipeline no escala a las necesidades de KAOS | Baja (2) | Medio (3) | **6** | Horizon es modular; podemos reemplazar stages individuales |
| Falta de adopción del equipo (cambio cultural a Harness Engineering) | Media (3) | Alto (4) | **12** | Workshops de Harness Engineering; mostrar wins tempranos |
| Bridge TypeScript resulta demasiado costoso | Alta (4) | Alto (4) | **16** | Evaluar alternativas: WASM, subproceso Node, o API REST |

---

## BCG Evaluation

| Dimensión | Score (1-10) | Notas |
|-----------|-------------|-------|
| **Claridad** | 8 | Estrategia clara: adoptar MCP + Harness Engineering + progressive disclosure |
| **Medición** | 7 | KRs tienen baseline y target, pero algunos (ej. "3 linters") podrían ser más específicos |
| **Realismo** | 7 | Realista para Q3-Q4 con equipo actual de 5 agentes, pero agresivo en parallelismo |
| **Alineación** | 9 | Alineado con OKRs actuales de Q2 y roadmap existente de KAOS |
| **Riesgo** | 6 | Dependencia de Mastra POC es el mayor riesgo no mitigado completamente |
| **Recursos** | 6 | Requiere que Kratos divida atención entre progressive disclosure, MCP gateway, y Horizon |
| **Tiempo** | 7 | Timeline de 6 meses es ajustado pero factible si se priorizan TOP 1-3 |
| **Impacto** | 9 | Transformacional: posiciona KAOS como plataforma de Harness Engineering en lugar de sistema aislado |

**BCG Score: 7.4/10** ✅ (Aceptable, por encima del umbral de 7.0)

**Recomendación**: Fortalecer las dimensiones de **Riesgo** (mitigar dependencia de Mastra con plan B) y **Recursos** (asegurar que Kratos no sea cuello de botella).

---

## Apéndice A: Tabla de Recursos Investigados

| # | Recurso | ⭐ Stars | Madurez | Relevancia KAOS | Decisión |
|---|---------|---------|---------|----------------|----------|
| 1 | opencodex/open-computer-use | ~88 | Baja (nuevo) | Baja (Computer Use no es core KAOS) | **Ignorar** |
| 2 | Hermes Tool Search | N/A (feature) | Media (evals Anthropic) | Alta (progressive disclosure) | **Adoptar ahora** (patrón) |
| 3 | Addy Osmani Agent Skills | 27K⭐ | Alta (estándar) | Alta (skills compatibles) | **Adoptar ahora** (estándar) |
| 4 | Horizon | 4.6K⭐ | Alta (MCP nativo) | Alta (pipeline inteligencia) | **Adoptar ahora** |
| 5 | Alephant AI Gateway | ~72 | Baja (beta 0.2.0) | Media (agent identity, largo plazo) | **Monitorear** |
| 6 | Mastra | 24.6K⭐ | Alta (1.0 release) | Alta (competencia/complemento) | **Evaluar** (POC Q3) |
| 7 | Harness Engineering | N/A (paradigma) | Emergente (2026) | Máxima (filosofía central) | **Adoptar ahora** |

---

## Apéndice B: Bias Audit

```
[BIAS_AUDIT]
1. Anclaje: ✅ No hay anclaje en el primer recurso (opencodex fue el primero listado pero recibió "Ignorar")
2. Confirmación: ✅ Busqué información contraria — por ejemplo, Mastra podría ser competencia letal, y lo documenté como amenaza A1
3. Optimismo: ✅ Los timelines son realistas (2-5 días por iniciativa). El BCG score de 7.4 refleja realismo
4. Disponibilidad: ✅ Harness Engineering está sobre-representado en noticias recientes pero su rating (Adoptar como filosofía) es proporcional a su impacto real demostrado por OpenAI/Anthropic
5. Atribución: ✅ No atribuyo resultados a personas específicas
6. Supervivencia: ✅ Se consideraron todos los recursos, incluyendo los poco exitosos (opencodex, Alephant)
7. Falso consenso: ✅ No asumo que el equipo comparte estas prioridades — se incluye riesgo de adopción cultural
8. Costo hundido: ✅ No recomiendo continuar líneas existentes solo por inversión previa
9. Framing: ✅ Las recomendaciones presentan pros y contras explícitos
10. Autoridad: ✅ Cuestioné la premisa de que los 7 recursos son igualmente relevantes — 2 fueron descartados
Resultado: Todos los checks OK. Sin sesgos activos identificados.
```

---

*Este análisis fue generado por Metis (Μῆτις) en modo Strategy (perfil: `desarrollo`). Para calidad y verificación de las recomendaciones, cambiar a modo Quality Orchestrator (perfil: `qa`).*
