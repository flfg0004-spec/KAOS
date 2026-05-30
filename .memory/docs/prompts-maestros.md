# Prompts Maestros de KAOS

> **Documentación de los 10 prompts más importantes del sistema multi-agente KAOS**
> Fecha: 2026-05-29 | Sprint: S2 | Elaborado por: Metis (vía QW8)

---

## Ranking por frecuencia de uso

| # | Nombre | Agente | Propósito | Uso/semana | Cacheable |
|---|--------|--------|-----------|:----------:|:---------:|
| 1 | Aletheia — System Prompt (SKILL) | Aletheia | Investigación multi-fuente con triangulación y matriz de confianza | ~120 | ✅ |
| 2 | Kratos — System Prompt (SKILL) | Kratos | Generación, depuración y revisión de código con memoria experiencial | ~80 | ✅ |
| 3 | Kosmos — System Prompt (SKILL) | Kosmos | Análisis arquitectónico, diagramas C4 y ADRs | ~50 | ✅ |
| 4 | Metis — System Prompt (SKILL) | Metis | Estrategia, OKRs, roadmaps, modelos de negocio | ~40 | ✅ |
| 5 | Mnemosyne — System Prompt (SKILL) | Mnemosyne | Curación de conocimiento, wikilinks, calidad del vault | ~30 | ✅ |
| 6 | Kronos — SOUL Identity | Kronos | Orquestación de pipelines, routing adaptativo y recuperación | ~25 | ✅ |
| 7 | Metis — SOUL Dual Mode | Metis | Identidad estratégica con sesgos, branching, dual role Strategy/Quality | ~25 | ✅ |
| 8 | Mnemosyne-Curator — System Prompt (SKILL) | Mnemosyne (ext.) | Scoring multidimensional, síntesis automática, knowledge levels | ~15 | ✅ |
| 9 | Kronos — Methodology 6-Step Cycle | Kronos | Pipeline lifecycle: Plan→Decompose→Route→Execute→Monitor→Learn | ~25 | ✅ |
| 10 | Workspace Dispatch — Mission Prompt | Hermes/Workspace | Descomposición de misiones en tareas con workers auto-verificados | ~15 | ❌ |

---

## Detalle por prompt

### 1. Aletheia — System Prompt (SKILL)

- **Agente**: Aletheia (Ἀλήθεια) — Investigación
- **Archivo**: `.opencode/skills/aletheia/SKILL.md` — Línea 10
- **Propósito**: Define la identidad central de Aletheia como agente de investigación. Establece el pipeline de 3 fases (Scope → Research → Synthesis), la metodología de triangulación (mínimo 3 fuentes), los perfiles de pipeline (flash/standard/deep/massive/estratégico), y el contrato de output con matriz de confianza.
- **Uso estimado**: ~120 veces/semana (es el agente más invocado del sistema)
- **Fragmento**:
  ```
  Eres Aletheia, agente de investigacion de KAOS. Tu rol es investigar en multiples fuentes, verificar hechos, y producir reportes estructurados con matriz de confianza.
  ```
- **Optimización Cache Boundary 7+13**:
  - **Secciones estáticas**: Identidad (4%), metodología 3 fases (30%), perfiles de pipeline (12%), reglas (5%), output esperado (8%) → ~59% del prompt
  - **Secciones dinámicas**: Herramientas por perfil (15%), contexto de investigación (20%), fuentes específicas (6%) → ~41% del prompt
  - **Estrategia**: Las secciones 1-3 (Identidad + Metodología F1+F2) son ~100% estáticas y pueden cachearse con Boundary 13. La Fase 3 y 4 son semi-dinámicas según el perfil de pipeline.
  - **Tokens ahorrables**: ~350 tokens estáticos por invocación → ~42,000 tokens/semana (120 llamadas × 350)
  - **Recomendación**: Cache estático de identidad+fases (Boundary 13); perfil y herramientas se resuelven dinámicamente.

---

### 2. Kratos — System Prompt (SKILL)

- **Agente**: Kratos (Κράτος) — Código
- **Archivo**: `.opencode/skills/kratos/SKILL.md` — Línea 9
- **Propósito**: Define a Kratos como agente de código con marco PRGII (Plan→Retrieve→Generate→Iterate→Ingest) y memoria experiencial CodeExperience. Establece el sistema de captura de errores con triple fusión (FTS5 + vector + AST) y contextual bandit para ajuste de confianza.
- **Uso estimado**: ~80 veces/semana (segundo agente más invocado)
- **Fragmento**:
  ```
  Eres Kratos, agente de codigo de KAOS. Tu rol es generar, depurar, revisar y testear codigo usando memoria experiencial estructurada (CodeExperience). Cada error que encuentres debe ser capturado para que el sistema aprenda.
  ```
- **Optimización Cache Boundary 7+13**:
  - **Secciones estáticas**: Identidad (5%), metodología PRGII (35%), captura de errores (10%), output esperado (8%) → ~58% del prompt
  - **Secciones dinámicas**: Contexto de tarea (20%), errores identificados (12%), historial de iteraciones (10%) → ~42% del prompt
  - **Estrategia**: PRGII es pseudo-estático (el número de iteraciones varía, pero la estructura no). Ideal para Boundary 13.
  - **Tokens ahorrables**: ~280 tokens estáticos por invocación → ~22,400 tokens/semana
  - **Recomendación**: Cachear metodología PRGII completa con Boundary 13 (se repite cada ~3 ciclos de pipeline).

---

### 3. Kosmos — System Prompt (SKILL)

- **Agente**: Kosmos (Κόσμος) — Arquitectura
- **Archivo**: `.opencode/skills/kosmos/SKILL.md` — Línea 8
- **Propósito**: Define a Kosmos como agente de arquitectura. Establece la metodología de análisis: escaneo con Depwire, modelado C4 con Structurizr, visualización con Excalidraw, documentación de ADRs y validación cruzada con ADRs existentes (001-011). Incluye el rol de verificador técnico para calidad cross-agente.
- **Uso estimado**: ~50 veces/semana
- **Fragmento**:
  ```
  Eres Kosmos, agente de arquitectura de KAOS. Tu rol es analizar codigo y sistemas, producir diagramas C4, y documentar decisiones arquitectonicas en ADRs.
  ```
- **Optimización Cache Boundary 7+13**:
  - **Secciones estáticas**: Identidad (6%), metodología 6 pasos (40%), formato de entrega (15%) → ~61% del prompt
  - **Secciones dinámicas**: Herramientas por contexto (10%), referencias a ADRs específicos (12%), system audit (17%) → ~39% del prompt
  - **Estrategia**: Los 6 pasos de metodología + formato de entrega no cambian entre invocaciones. Cache perfecto para Boundary 13.
  - **Tokens ahorrables**: ~300 tokens estáticos por invocación → ~15,000 tokens/semana
  - **Recomendación**: Cache estático con Boundary 13; la sección de "Herramientas disponibles" puede ser dinámica según disponibilidad.

---

### 4. Metis — System Prompt (SKILL)

- **Agente**: Metis (Μῆτις) — Estrategia
- **Archivo**: `.opencode/skills/metis/SKILL.md` — Línea 13
- **Propósito**: Define la metodología estratégica de 7 fases (Diagnosticar→Investigar→Estructurar→Diseñar→Modelar→Validar→Comunicar). Incluye frameworks FODA, OKRs, RICE, Business Model Canvas, Wardley, TAM/SAM/SOM, y el modo Quality Orchestrator con auditoría completa.
- **Uso estimado**: ~40 veces/semana (combinando Strategy + Quality)
- **Fragmento**:
  ```
  Eres Metis, agente de estrategia de KAOS. Tu rol es analizar situaciones, definir OKRs, crear roadmaps, modelar modelos de negocio, y producir reportes ejecutivos usando frameworks estratégicos (strategy-mcp, strategy-extras, exa-search). Cada entrega debe incluir diagnóstico, formulación, validación y comunicación.
  ```
- **Optimización Cache Boundary 7+13**:
  - **Secciones estáticas**: Identidad (3%), metodología 7 fases detallada (45%), frameworks estratégicos (20%), formatos de entrega (8%) → ~76% del prompt
  - **Secciones dinámicas**: Quality Orchestration Mode (~20%), perfiles de evaluación (4%) → ~24% del prompt
  - **Estrategia**: Por ser el prompt más largo (~613 líneas en total), la optimización es crítica. La metodología 7 fases es el payload estático más grande del sistema.
  - **Tokens ahorrables**: ~1,200 tokens estáticos por invocación → ~48,000 tokens/semana
  - **Recomendación**: **ALTA PRIORIDAD** — Cachear las primeras 5 fases completas (estáticas) con Boundary 7. La Fase 6 (Validar) y 7 (Comunicar) son semi-dinámicas. Modo Quality Orchestrator debe cargarse condicionalmente.

---

### 5. Mnemosyne — System Prompt (SKILL)

- **Agente**: Mnemosyne (Μνημοσύνη) — Memoria
- **Archivo**: `.opencode/skills/mnemosyne/SKILL.md` — Línea 9
- **Propósito**: Define la identidad de Mnemosyne como guardiana de la memoria, con 14 fases de curación + Gap Query API. Establece el ciclo completo: Ingest→Tag→Link→Dedup→Quality→Compress→Index→Lint→Graph→Gaps→Cross-Ref→Lifecycle→Dashboard→Report.
- **Uso estimado**: ~30 veces/semana
- **Fragmento**:
  ```
  Eres Mnemosyne, guardiana de la memoria de KAOS. Tu rol es curar el conocimiento del vault: deduplicar, enlazar, indexar, taggear, analizar el grafo, y consolidar. Tambien sirves como pre-memoria para Aletheia.
  ```
- **Optimización Cache Boundary 7+13**:
  - **Secciones estáticas**: Identidad (5%), metodología 14 fases (50%), Gap Query API (10%), output esperado (8%) → ~73% del prompt
  - **Secciones dinámicas**: Herramientas por fase (10%), contexto de pipeline (10%), resultados de curación previa (7%) → ~27% del prompt
  - **Estrategia**: Las 14 fases son una secuencia fija. Ideal para Boundary 13 ya que se ejecuta en pipeline.
  - **Tokens ahorrables**: ~250 tokens estáticos por invocación → ~7,500 tokens/semana
  - **Recomendación**: Cache completo de la metodología con Boundary 13; solo resolver herramientas dinámicamente.

---

### 6. Kronos — SOUL Identity

- **Agente**: Kronos (Κρόνος) — Orquestación
- **Archivo**: `.opencode/agents/kronos/SOUL.md` — Líneas 1-5
- **Propósito**: Define la identidad central de Kronos como orquestador de pipelines. Establece sus core values (Speed, Observability, Parallelism, Cost-efficiency, Auto-discovery), boundaries (qué NO hace), dependencias del sistema, guardrails y perfiles de pipeline (rápido/balanceado/crítico).
- **Uso estimado**: ~25 veces/semana (se carga en cada pipeline que Kronos orquesta)
- **Fragmento**:
  ```
  Eres **Kronos** (Κρόνος), el titán del tiempo, el orden y los ciclos. En el panteón KAOS eres el **Orquestador** — el arquitecto de pipelines, el tejedor de flujos multi-agente, el guardián de la velocidad y la resiliencia del sistema.
  ```
- **Optimización Cache Boundary 7+13**:
  - **Secciones estáticas**: Identidad (6%), Core Values (15%), Boundaries (30%), Dependencies (10%), Guardrails (12%), Mode Switching (5%) → ~78% del prompt
  - **Secciones dinámicas**: Tool Guidance (10%), dependencias específicas de pipeline (12%) → ~22% del prompt
  - **Estrategia**: Kronos necesita cargar su identidad en cada pipeline. Ideal para Boundary 13 (ciclo de pipeline).
  - **Tokens ahorrables**: ~500 tokens estáticos por invocación → ~12,500 tokens/semana
  - **Recomendación**: Cache completo con Boundary 13. Identity + Values + Boundaries + Guardrails son 100% estáticos.

---

### 7. Metis — SOUL Dual Mode

- **Agente**: Metis (Μῆτις) — Estrategia/Calidad
- **Archivo**: `.opencode/agents/metis/SOUL.md` — Líneas 1-96
- **Propósito**: Define la identidad profunda de Metis con auto-detección de sesgos cognitivos (10 sesgos), Creative Branching Protocol, y el sistema de Dual Mode (Strategy ↔ Quality Orchestrator). Incluye grounding rules y la metodología de cambio de modo semántico.
- **Uso estimado**: ~25 veces/semana
- **Fragmento**:
  ```
  Eres **Metis** (Μῆτις), la titánide de la sabiduría, el consejo y la estrategia. Tu propósito es analizar situaciones complejas, diseñar estrategias accionables y guiar la toma de decisiones con inteligencia y previsión.
  ```
- **Optimización Cache Boundary 7+13**:
  - **Secciones estáticas**: Identidad (6%), Grounding Rules (12%), auto-detección de sesgos (25%), Creative Branching (15%), Guardrails (8%) → ~66% del prompt
  - **Secciones dinámicas**: Dual Role (15%), Mode Switching tables (12%), tool guidance por modo (7%) → ~34% del prompt
  - **Estrategia**: Los sesgos cognitivos y branching protocol son siempre iguales. La sección de Dual Mode se carga según el perfil activo.
  - **Tokens ahorrables**: ~400 tokens estáticos por invocación → ~10,000 tokens/semana
  - **Recomendación**: Cache identidad + sesgos + branching con Boundary 7. Dual Mode sections cargar condicionalmente según `eval-profile.yaml`.

---

### 8. Mnemosyne-Curator — System Prompt (SKILL)

- **Agente**: Mnemosyne-Curator (extensión de Mnemosyne)
- **Archivo**: `.opencode/skills/mnemosyne-curator/SKILL.md` — Línea 11
- **Propósito**: Define el sistema de scoring multidimensional para el vault (8 métricas con pesos fijos), 6 knowledge levels (RAW→ROUGH→DRAFT→REVIEW→CURATED→CANONICAL), y el pipeline extendido de curación con síntesis automática para documentos con score < 60. Incluye guardrails de seguridad (backup, dry-run, diff ratio).
- **Uso estimado**: ~15 veces/semana
- **Fragmento**:
  ```
  Eres Mnemosyne-Curator, extensión de Mnemosyne especializada en curaduría profunda de conocimiento. Tu función es aplicar scoring multidimensional a cada documento del vault usando 8 métricas con pesos fijos, asignar knowledge levels (RAW → CANONICAL), y ejecutar síntesis automática para documentos con score menor a 60.
  ```
- **Optimización Cache Boundary 7+13**:
  - **Secciones estáticas**: Identidad (5%), Knowledge Scoring (8 métricas + pesos, 35%), Knowledge Levels (20%), guardrails (15%) → ~75% del prompt
  - **Secciones dinámicas**: Metodología pipeline extendido (15%), resultados de scoring previo (10%) → ~25% del prompt
  - **Estrategia**: Las 8 métricas con pesos fijos son 100% estáticas. Los knowledge levels son estáticos. Ideal para cache prolongado.
  - **Tokens ahorrables**: ~350 tokens estáticos por invocación → ~5,250 tokens/semana
  - **Recomendación**: Cache completo con Boundary 13 (solo se invoca ~15 veces/semana pero el payload es denso).

---

### 9. Kronos — Methodology 6-Step Cycle

- **Agente**: Kronos (Κρόνος) — Orquestación
- **Archivo**: `.opencode/agents/kronos/methodology.md` — Líneas 1-278
- **Propósito**: Define el ciclo completo de orquestación de pipelines Kronos (6 pasos: Plan→Decompose→Route→Execute→Monitor→Learn). Incluye la estrategia de cache Boundary 7+13, los patrones de paralelismo (FORK/JOIN/CONDITIONAL/RACE), pipeline lifecycle states, esquema de Pipeline State, orchestration templates, y matriz de recuperación de errores.
- **Uso estimado**: ~25 veces/semana (se carga con cada pipeline orquestado)
- **Fragmento**:
  ```
  Cada pipeline orquestado sigue este ciclo iterativo. Un ciclo completo se ejecuta por cada "misión" o "sesión de trabajo".
  ```
- **Optimización Cache Boundary 7+13**:
  - **Secciones estáticas**: 6-Step Cycle completo (30%), Boundary 7+13 cache strategy (10%), Pipeline Lifecycle States (8%), Pipeline State Schema (15%), Error Recovery Matrix (15%) → ~78% del prompt
  - **Secciones dinámicas**: Orchestration Templates (15%), métricas específicas (7%) → ~22% del prompt
  - **Estrategia**: Este es un documento de **metodología**, no un prompt de identidad. Su carga es bajo demanda cuando Kronos necesita la referencia. Sin embargo, el 6-Step Cycle es el corazón del pipeline.
  - **Tokens ahorrables**: ~800 tokens estáticos por invocación → ~20,000 tokens/semana
  - **Recomendación**: **ALTA PRIORIDAD** — Cachear los Steps 1-6 completos + Boundary strategy + Error Recovery con Boundary 13. Los orchestration templates (Research Pipeline, Code Gen Pipeline, Quality Audit Pipeline) pueden cargarse condicionalmente.

---

### 10. Workspace Dispatch — Mission Prompt

- **Agente**: Hermes/Workspace (Workspace Dispatch Skill)
- **Archivo**: `.workspace/skills/workspace-dispatch/SKILL.md` — Líneas 9, 58-73
- **Propósito**: Define el prompt de misión para workers autónomos. Establece el flujo de descomposición (2-6 tareas con criterios de salida verificables por shell), el dispatch loop con retry (max 3), y el formato de worker prompt que incluye exit criteria, working directory y reglas de auto-verificación.
- **Uso estimado**: ~15 veces/semana
- **Fragmento**:
  ```
  You are an autonomous mission orchestrator. Decompose work into tasks, spawn one worker per task, verify output, chain to the next — no user intervention needed.
  ```
- **Optimización Cache Boundary 7+13**:
  - **⚠️ NO CACHEABLE**: Este prompt es dinámico por naturaleza — cada misión tiene tareas, descripciones y exit criteria diferentes. El worker prompt se construye en tiempo real con contexto de la misión actual.
  - **Secciones estáticas**: Flujo base (20%), reglas de descomposición (15%), tipos de tarea (10%) → ~45% del prompt base
  - **Secciones dinámicas**: Para cada misión: descripción de tarea (30%), exit criteria (30%), errores previos en retry (15%) → ~55% del prompt
  - **Estrategia**: No aplica Boundary 7+13 por ser altamente dinámico. Sin embargo, el Worker Prompt Template (líneas 58-73) es un template reutilizable que podría cachearse a nivel de aplicación.
  - **Tokens ahorrables**: ~0 (no cacheable directamente). El template del worker prompt (~180 tokens) podría cachearse si se abstrae como plantilla.
  - **Recomendación**: Extraer el template del worker prompt a un archivo estático para cache parcial. El contenido dinámico es inherente al modelo de misión.

---

## Resumen de Optimización Agregada

| Métrica | Valor |
|---------|-------|
| Tokens ahorrables por semana (suma) | ~182,650 tokens |
| Equivalencia en costo API (DeepSeek Flash) | ~$0.37/semana (input: $2/M tok) |
| Promedio de sección estática por prompt | ~67% |
| Promedio de ahorro por invocación | ~463 tokens |
| Prompts candidatos a Boundary 13 (ciclo) | 6 (Aletheia, Kratos, Kosmos, Mnemosyne, Kronos SOUL, Mnemosyne-Curator) |
| Prompts candidatos a Boundary 7 (días) | 2 (Metis SKILL, Metis SOUL) |
| Prompts no cacheables | 1 (Workspace Dispatch) |

## Recomendaciones Estratégicas

1. **Priorizar cache de Metis SKILL** (líder en ahorro): ~48,000 tokens/semana con Boundary 7
2. **Implementar Boundary 13 para pipelines repetitivos**: Kronos SOUL + Methodology juntos ahorrarían ~32,500 tokens/semana
3. **Extraer templates estáticos de Workspace Dispatch**: El Worker Prompt Template puede cachearse como bloque fijo
4. **Monitorear hit rate**: Si cache hit rate < 30%, revisar segmentación estático/dinámico
5. **No sobre-segmentar**: Prompts < 200 tokens estáticos no justifican overhead de cache management

---

*Documento generado por Metis en BUILD mode — QW8: Documentar 10 prompts más usados*
