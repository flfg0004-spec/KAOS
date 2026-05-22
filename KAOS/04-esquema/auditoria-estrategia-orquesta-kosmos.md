---
type: audit
title: 'Auditoría Arquitectónica: Estrategia Orquesta + Code Agent + Hermes'
aliases:
- auditoria-estrategia-orquesta-kosmos
tags:
- audit
- architecture
- strategy
- code-agent
- langgraph
- hermes
- adr-review
created: 2026-05-21
modified: '2026-05-21'
confidence: media
status: draft
agent: kosmos
---

# Auditoría Arquitectónica: Estrategia Orquesta DAG + Code Agent + Hermes

> **Verificador**: Kosmos (Agente de Arquitectura)
> **Documento auditado**: `schema/estrategia-orquesta-agentes-hermes-strategy.md`
> **ADRs de referencia**: ADR-001 a ADR-008
> **Perfil de evaluación**: Producción 🔴 (umbral mínimo compuesto: 80)

---

## Resumen Ejecutivo

La estrategia de Metis para evolucionar KAOS hacia un sistema multi-agente DAG con Code Agent, LangGraph Orchestrator y Hermes Gateway es **arquitectónicamente sólida en su visión general pero tiene 3 issues críticos que deben resolverse antes de la implementación**. La propuesta se basa en investigación profunda (78+ fuentes), reconoce correctamente las limitaciones del pipeline lineal actual, y propone una secuencia de implementación pragmática (Code Agent → LangGraph → Hermes).

**Veredicto: APROBADA CON CONDICIONES** — 6 condiciones obligatorias para proceder.

---

## Score Arquitectónico por Dimensión

| Dimensión | Score (1-10) | Justificación |
|-----------|:---:|---|
| **Consistencia** (vs ADRs) | 6.5 | 3 conflictos directos con ADRs existentes (003, 004, 008); 1 inconsistencia con ADR-005 (status Propuesta); 1 con ADR-006 (superposición no resuelta) |
| **Cohesión** (entre componentes) | 7.5 | Code Agent y LangGraph se integran bien; Hermes introduce fricción (doble máquina de estado con Kanban + LangGraph); SleepGate se superpone con ADR-006 sin resolver |
| **Viabilidad técnica** | 7.0 | Plan semanal realista; MVP-first bien; pero Hermes como proceso externo + Kanban + LangGraph = 3 sistemas nuevos simultáneos en H1 |
| **Seguridad arquitectónica** | 6.0 | 🔴 Hermes es dependencia externa (Nous Research) sin plan de contingencia si el proyecto cambia; verificación cruzada (ADR-003) se rompe con DAG; costos LLM escalan sin mitigación clara |
| **Escalabilidad** | 8.5 | La dirección DAG + paralelismo + memoria jerárquica es correcta para escalar; diseño reconoce límites y propone soluciones progresivas |
| **Completitud** | 7.0 | Estrategia buena para H1 (semanal); H2-H3 más vagos; falta detalle en los ADRs propuestos (009-012); falta plan de migración de datos/memoria |
| ****Score compuesto** | **7.1** | Por debajo del umbral de producción (80/100) pero aceptable para perfil desarrollo 🟡 (70/100) |

---

## Componentes Aprobados y Rechazados

| Componente | Veredicto | Condiciones |
|-----------|-----------|-------------|
| **Code Agent** (5º agente) | ✅ **APROBADO** | Sin condiciones. MVP secuencial (FTS5 → PRGII → Bandit) es correcto. |
| **LangGraph Orchestrator** | ✅ **APROBADO CON CONDICIONES** | Ver Issues 🔴C1 (verificación), 🔴C3 (DSOL), 🟡M4 (autonomía) |
| **Hermes Gateway** | ⚠️ **APROBACIÓN CONDICIONAL** | Ver Issues 🔴C2 (dependencia externa), 🟡M5 (doble máquina de estado) |
| **SleepGate / Agenternal** | ✅ **APROBADO CON CONDICIONES** | Ver Issues 🟡M1 (jerarquía), 🟡M3 (ADR-006), 🟡M2 (ADR-005) |
| **A2A + MCP** | ✅ **APROBADO** | Sin condiciones. MCP ya es estándar en KAOS; A2A es futuro. |

---

## Issues Encontrados

### 🔴 Críticos (Deben resolverse antes de implementar)

#### 🔴 C1: Topología de verificación cruzada rota por migración a DAG
**Componente**: LangGraph Orchestrator
**ADR violado**: ADR-003 (Protocolo de Verificación Cruzada)
**Severidad**: Crítica
**Descripción**: ADR-003 define una cadena triangular de verificación (Aletheia→Kosmos→Metis→Aletheia). LangGraph cambia la topología de ejecución a DAG, donde los flujos pueden ser paralelos, condicionales o dinámicos. Con 5+ agentes (Code Agent, Hermes), el triángulo se convierte en pentágono. La verificación cruzada no está diseñada para topología DAG.
**Riesgo**: Outputs no verificados pasan a producción. Calidad del sistema no garantizada.
**Mitigación requerida**: Rediseñar la verificación como un **subgrafo separado en LangGraph** (no acoplado a la topología de ejecución). El verificador debe ser un nodo independiente que subscribe a outputs, no parte del flujo lineal.

#### 🔴 C2: Hermes como dependencia externa — conflicto con principio de mínimas dependencias
**Componente**: Hermes Gateway
**ADR violado**: ADR-008 (Plugin Decision — principio de mínimas dependencias externas)
**Severidad**: Crítica
**Descripción**: ADR-008 establece explícitamente que KAOS minimiza dependencias externas (rechazó supermemory, background-agents por esta razón). Hermes (Nous Research) es un proyecto open source externo. La propia estrategia lo reconoce como riesgo A5 ("cambio de dirección o mantenimiento"). Si Hermes cambia su API, roadmap o modelo de negocio, KAOS queda bloqueado en su capa de comunicación externa.
**Riesgo**: KAOS pierde autonomía operativa. Gateway deja de funcionar si Hermes cambia.
**Mitigación requerida**: (a) Formalizar exención a ADR-008 mediante nuevo ADR que justifique el valor de Hermes vs el riesgo. (b) Containerizar Hermes (Docker) con resource limits. (c) Definir interfaz abstracta de Gateway para poder reemplazar Hermes si es necesario. (d) Contingencia: plan B si Hermes desaparece.

#### 🔴 C3: Conflicto de routing — DSOL (ADR-004) vs LangGraph Orchestrator
**Componente**: LangGraph Orchestrator + DSOL
**ADR violado**: ADR-004 (DeepSeek Optimization Layer)
**Severidad**: Crítica
**Descripción**: ADR-004 define DSOL como capa de routing que decide qué tareas van a Flash vs Pro según complejidad. LangGraph también define routing condicional entre agentes. Ambas capas deciden "routing" pero en niveles diferentes (modelo vs agente). Sin integración explícita, pueden contradecirse (e.g., DSOL manda tarea simple a Flash, pero LangGraph la routea a un agente Pro-heavy).
**Riesgo**: Token budget duplicado, costos impredecibles, conflictos de scheduling.
**Mitigación requerida**: Integración explícita LangGraph ↔ DSOL. Definir quién es el source of truth para routing. Propuesta: LangGraph decide QUÉ agente ejecuta, DSOL decide CÓMO (qué modelo, qué thinking mode, qué budget). Crear ADR de integración.

---

### 🟡 Medios (Deben planearse antes de H1)

#### 🟡 M1: Desajuste de jerarquía de memoria — ADR-001 (3 niveles) vs Estrategia (L0-L3)
**Componente**: Memoria jerárquica (SleepGate/Agenternal)
**ADR afectado**: ADR-001 (Sistema de Memoria)
**Severidad**: Media
**Descripción**: ADR-001 define 3 niveles de memoria: Core (volátil) → Working (volátil) → Archival (persistente). La estrategia propone L0→L3 (4 niveles) vía SleepGate/Agenternal. No hay documento de correspondencia entre ambos modelos.
**Riesgo**: Confusión en documentación, gaps en cobertura de memoria, inconsistencias en implementación.
**Mitigación**: Crear documento de mapping ADR-001 → L0-L3 antes de implementar SleepGate. Posible correspondencia: Core≈L0, Working≈L1, Archival≈L2-L3.

#### 🟡 M2: ADR-005 (Vector Store) en estado "Propuesta" — la estrategia lo trata como implementado
**Componente**: Infraestructura de memoria
**ADR afectado**: ADR-005 (Vector Store)
**Severidad**: Media
**Descripción**: La estrategia lista sqlite-vec como "existente: 161 páginas, 3610 chunks". Sin embargo, ADR-005 está en estado **Propuesta — Pendiente de implementación cuando vault supere 100 páginas**. No hay registro de que se haya aceptado formalmente ni implementado.
**Riesgo**: La estrategia construye sobre una base que no está formalmente aceptada.
**Mitigación**: Formalizar aceptación de ADR-005 (cambiar estado a Aceptada). Verificar que sqlite-vec está realmente operativo (no solo los chunks, sino el pipeline de indexación y búsqueda).

#### 🟡 M3: Sleep cycles (Agenternal/SleepGate) extienden ADR-006 sin deprecación formal
**Componente**: SleepGate / Agenternal
**ADR afectado**: ADR-006 (Sleep-Time Compute)
**Severidad**: Media
**Descripción**: ADR-006 define "Consolidación programada" (script diario simple). La estrategia propone Agenternal/SleepGate con NREM/REM cycles, compresión 2M:1, DBSCAN clustering, etc. — una evolución significativa. Sin embargo, el strategy no menciona que ADR-006 quedaría superseded.
**Riesgo**: Dos estrategias de consolidación compitiendo en documentación.
**Mitigación**: Formalizar que ADR-006 queda reemplazado por el nuevo enfoque. Agregar condición en ADR-006: "Reemplazado por ADR-013 (Sleep Gate Architecture)" cuando se cree.

#### 🟡 M4: Zonas de autonomía (ADR-003) vs principio de "orquestador nunca ejecuta trabajo"
**Componente**: LangGraph Orchestrator
**ADR afectado**: ADR-003 (Zonas de Autonomía)
**Severidad**: Media
**Descripción**: ADR-003 establece que los agentes escriben directamente al vault en zonas de baja autonomía (auto). LangGraph propone que el orquestador "descompone, delega, monitorea, sintetiza". Si el orquestador se vuelve el despachador central, los agentes podrían perder su capacidad de escritura directa autónoma.
**Riesgo**: Agentes bloqueados esperando al orquestador para operaciones simples (escritura de log, actualización de conceptos).
**Mitigación**: Mantener escritura directa al vault para operaciones de baja criticidad (log, wiki/concepts). El orquestador solo media en tareas multi-agente complejas. Documentar esta separación.

#### 🟡 M5: Hermes Kanban introduce una segunda máquina de estado paralela a LangGraph Checkpointing
**Componente**: Hermes Gateway + LangGraph
**Severidad**: Media
**Descripción**: LangGraph tiene su propia máquina de estado (checkpointing, nodos, edges). Hermes Kanban introduce otra con estados (created→todo→ready→running→done). Ambas máquinas de estado coexisten y deben sincronizarse. Sin un protocolo de sincronización, el estado puede divergir (Kanban dice "running" pero LangGraph checkpoint está en "error").
**Riesgo**: Visibilidad inconsistente del estado de las tareas. Dificultad para depurar fallos.
**Mitigación**: Diseñar protocolo de sincronización Kanban ↔ LangGraph. Definir quién es source of truth. Propuesta: LangGraph es source of truth del execution state; Kanban refleja fielmente, no decide. Kanban es la vista externa, LangGraph la interna.

---

### 🟢 Bajos (Documentar y monitorear)

#### 🟢 G1: Skill de Code Agent no detallado
**Componente**: Code Agent
**Severidad**: Baja
**Descripción**: La estrategia menciona crear skill "code" en S1 pero no describe su contenido, metodología ni MCPs específicos. El plan dice "tools:[vault,sequential-thinking,git,excalidraw]" pero esto no es un skill completo.
**Mitigación**: Kosmos debe diseñar el skill Code Agent como parte de ADR-009. Incluir metodología APEX-EM PRGII adaptada, ejemplos de prompts, y lista completa de tools.

#### 🟢 G2: Mnemosyne — rol no actualizado explícitamente
**Componente**: Mnemosyne
**Severidad**: Baja
**Descripción**: En el diagrama de arquitectura objetivo, Mnemosyne aparece como "6o" agente al final del DAG. La estrategia no detalla cómo cambia su rol actual (curador + consolidación programada) bajo el nuevo esquema con LangGraph y SleepGate.
**Mitigación**: Incluir en ADR-010 o ADR-013 la nueva definición de rol de Mnemosyne bajo el DAG.

#### 🟢 G3: ADR-007 ya lista 19 MCPs, la estrategia menciona 18 desactualizados
**Componente**: Infraestructura
**Severidad**: Baja
**Descripción**: La estrategia dice "18 MCPs activos" pero ADR-007 y opencode.json muestran 19 (incluyendo obsidian REST API). Diferencia menor pero indica que la estrategia no se actualizó con el estado post-ADR-007.
**Mitigación**: Actualizar la estrategia a 19 MCPs.

---

## ADRs Afectados y Acciones Requeridas

| ADR | Estado Actual | Acción Requerida | Prioridad |
|-----|:---:|---|:---:|
| **ADR-001** (Sistema de Memoria) | Aceptada | **Modificar**: Agregar mapping de 3 niveles a L0-L3. No contradice pero necesita extensión. | Alta |
| **ADR-002** (Scores + Aislamiento) | Aceptada | **Sin cambios**: Scores compatibles con DAG. Aislamiento se mantiene. | — |
| **ADR-003** (Verificación + Autonomía) | Aceptada | **Modificar CRÍTICO**: Rediseñar verificación para topología DAG. Verificar zonas de autonomía bajo orquestador. | 🔴 Urgente |
| **ADR-004** (DSOL) | Aceptada | **Modificar CRÍTICO**: Integración LangGraph-DSOL. Definir quién routea qué. | 🔴 Urgente |
| **ADR-005** (Vector Store) | **Propuesta** | **Aceptar formalmente**. Cambiar estado a Aceptada. Verificar implementación sqlite-vec. | Alta |
| **ADR-006** (Sleep-Time Compute) | Aceptada | **Marcar como "Reemplazado por ADR-013"**. La estrategia va más allá de lo que ADR-006 contempla. | Media |
| **ADR-007** (Optimización) | Aceptada | **Sin cambios**. Agregar nota de que Code Agent necesitará sus propios MCPs. | Baja |
| **ADR-008** (Plugin Decision) | Aceptada | **Modificar**: Agregar exención para Hermes Gateway (dependencia externa justificada). O crear ADR separado. | Alta |
| **ADR-009** (Code Agent) | **Nuevo** | Crear en S1. Skill, arquitectura, PRGII adaptado, tools. | Alta |
| **ADR-010** (LangGraph Orchestration) | **Nuevo** | Crear en S2. Topología DAG, integración DSOL, checkpointing, verificación DAG. | Alta |
| **ADR-011** (Hermes Integration) | **Nuevo** | Crear en S3. Protocolo Kanban↔LangGraph, mitigación dependencia, interfaz abstracta. | Alta |
| **ADR-012** (APEX-EM Memory) | **Nuevo** | Crear en S4. Arquitectura de memoria procedural, FTS5 + AST + DAG. | Media |
| **ADR-013** (Sleep Gate) | **Nuevo** | Crear en M2. Jerarquía L0-L3, NREM/REM, mapping ADR-001. | Media |

---

## Validación Detallada Contra Cada ADR

### ADR-001: Sistema de Memoria
| Aspecto | Evaluación |
|---------|-----------|
| ¿Contradice? | ❌ No contradice. La jerarquía L0-L3 de la estrategia es extensión natural de Core/Working/Archival. |
| ¿Extiende? | ✅ Sí. SleepGate+Agenternal añade consolidación biológica (NREM/REM) que no estaba en ADR-001. |
| ¿Riesgo? | 🟡 M1: Falta mapping explícito entre modelos. |
| **Veredicto** | Compatible. Requiere documento de mapping. |

### ADR-002: Sistema de Scores + Aislamiento
| Aspecto | Evaluación |
|---------|-----------|
| ¿Contradice? | ❌ No. Sistema de scores con 5 dimensiones sigue siendo válido en DAG. |
| ¿Extiende? | ✅ El Code Agent necesitará perfil de evaluación nuevo ("code") en eval-profile.yaml. |
| ¿Riesgo? | Ninguno. Scores son ortogonales a la topología de orquestación. |
| **Veredicto** | Compatible. Agregar perfil "code" a eval-profile.yaml. |

### ADR-003: Verificación Cruzada + Zonas de Autonomía
| Aspecto | Evaluación |
|---------|-----------|
| ¿Contradice? | 🔴 **SÍ, CRÍTICO**. El triángulo de verificación (A→K→M→A) no funciona en DAG con 5+ agentes y flujos paralelos/condicionales. |
| ¿Extiende? | La verificación DAG sería una extensión, pero debe rediseñarse desde cero. |
| ¿Riesgo? | 🔴 C1: Verificación no operable bajo DAG. 🟡 M4: Autonomía de escritura vs orquestador central. |
| **Veredicto** | **Requiere modificación urgente antes de migrar a DAG.** |

### ADR-004: DeepSeek Optimization Layer
| Aspecto | Evaluación |
|---------|-----------|
| ¿Contradice? | 🔴 **SÍ, CRÍTICO**. DSOL routea entre Flash/Pro; LangGraph también routea entre agentes. Sin integración, hay doble routing. |
| ¿Extiende? | Podría integrarse si se definen límites claros: LangGraph routea agentes, DSOL optimiza llamadas. |
| ¿Riesgo? | 🔴 C3: Token budget duplicado, costos impredecibles. |
| **Veredicto** | **Requiere diseño de integración antes de implementar LangGraph.** |

### ADR-005: Vector Store
| Aspecto | Evaluación |
|---------|-----------|
| ¿Contradice? | ❌ No. La estrategia asume sqlite-vec como existente, que es lo que ADR-005 propone. |
| ¿Problema? | 🟡 M2: ADR-005 es "Propuesta", no "Aceptada". La estrategia trata como implementado algo que está en estado pendiente. |
| ¿Riesgo? | Si ADR-005 no se acepta formalmente, la base de la estrategia para memoria vectorial no está validada. |
| **Veredicto** | **Aceptar ADR-005 formalmente. Verificar implementación real.** |

### ADR-006: Sleep-Time Compute
| Aspecto | Evaluación |
|---------|-----------|
| ¿Contradice? | ❌ No contradice, pero **supersede** (va mucho más allá). ADR-006 define consolidación programada simple; la estrategia propone NREM/REM, 2M:1 compression, DBSCAN. |
| ¿Riesgo? | 🟡 M3: Dos estrategias de consolidación coexistiendo sin jerarquía formal. |
| **Veredicto** | **Marcar ADR-006 como "Reemplazado por ADR-013".** |

### ADR-007: Optimización de Arquitectura
| Aspecto | Evaluación |
|---------|-----------|
| ¿Contradice? | ❌ No. Per-Agent MCP restriction es compatible con nuevo Code Agent y Hermes. |
| ¿Extiende? | ✅ Code Agent necesitará MCPs específicos. Hermes Gateway añadirá capa de red. |
| ¿Riesgo? | 🟢 G3: Estrategia dice 18 MCPs, hay 19. Diferencia menor. |
| **Veredicto** | Compatible. Code Agent tools: vault, sequential-thinking, git, excalidraw, knowledge-graph, txtai. |

### ADR-008: Plugin Decision
| Aspecto | Evaluación |
|---------|-----------|
| ¿Contradice? | 🔴 **SÍ, CRÍTICO**. ADR-008 rechaza dependencias externas; Hermes es dependencia externa (Nous Research). |
| ¿Justificable? | Sí, si se formaliza exención. Hermes ofrece Kanban + multi-plataforma que KAOS no puede construir internamente en H1-H2. |
| ¿Riesgo? | 🔴 C2: Si Hermes cambia, KAOS pierde su gateway. |
| **Veredicto** | **Requiere ADR de exención formal + plan de contingencia.** |

---

## Recomendaciones Ordenadas por Prioridad

### Imprescindibles (antes de implementar cualquier cosa)

1. **[🔴] Rediseñar verificación cruzada para DAG** — La verificación no puede ser un flujo lineal incrustado en el DAG. Debe ser un subgrafo separado que subscribe a outputs vía eventos y verifica asíncronamente. Esto desconecta la topología de verificación de la topología de ejecución.
   - **Costo**: ~3 días de diseño
   - **Beneficio**: Verificación funcional bajo cualquier topología
   - **Dueño**: Kosmos

2. **[🔴] Integrar DSOL con LangGraph** — Definir contrato: LangGraph decide el *agente*, DSOL decide el *modelo* (Flash/Pro) y *thinking mode*. LangGraph lleva token budget tracking; DSOL optimiza el consumo dentro de ese budget.
   - **Costo**: ~2 días de diseño, integración en librería compartida
   - **Beneficio**: Sin costos sorpresa ni routing conflictivo
   - **Dueño**: Kosmos

3. **[🔴] Formalizar exención ADR-008 para Hermes** — Crear ADR que documente: (a) por qué Hermes justifica ser excepción, (b) interfaz abstracta de Gateway para reemplazo futuro, (c) plan de contingencia si Hermes desaparece.
   - **Costo**: ~1 día
   - **Beneficio**: Riesgo de dependencia externa documentado y mitigado
   - **Dueño**: Kosmos + Metis

### Altas (antes de H2)

4. **[🟡] Aceptar formalmente ADR-005** — Cambiar estado de "Propuesta" a "Aceptada". Verificar que sqlite-vec pipeline (indexación + búsqueda) está operativo. Si no, completar implementación.
   - **Costo**: ~1 día si ya está implementado
   - **Beneficio**: Base sólida para la estrategia de memoria

5. **[🟡] Crear documento de mapping ADR-001 → L0-L3** — Correspondencia entre Core/Working/Archival y los niveles propuestos por SleepGate. Definir qué vive en cada nivel y cómo se promueve/demueve información.
   - **Costo**: ~1 día
   - **Beneficio**: Sin ambigüedad en jerarquía de memoria

6. **[🟡] Deprecar ADR-006 formalmente** — Agregar nota de "Reemplazado por ADR-013" y crear el nuevo ADR de SleepGate.
   - **Costo**: ~0.5 día
   - **Beneficio**: Una sola fuente de verdad para consolidación

### Medias (durante H1)

7. **[🟡] Diseñar protocolo Kanban ↔ LangGraph** — Quién es source of truth del estado de tareas. Definir ciclo de vida y mapping de estados.
   - **Costo**: ~1 día
   - **Beneficio**: Sin divergencia de estado entre las dos máquinas de estado

8. **[🟡] Actualizar zonas de autonomía (ADR-003) para DAG** — Confirmar que agentes mantienen escritura directa al vault para operaciones de baja criticidad, incluso bajo orquestador. Documentar qué operaciones pasan por el orquestador y cuáles no.
   - **Costo**: ~1 día
   - **Beneficio**: Agentes no bloqueados por el orquestador

### Bajas (durante implementación)

9. **[🟢] Diseñar skill de Code Agent** — Metodología APEX-EM PRGII adaptada a KAOS, lista de MCPs, ejemplos de prompts, flujo de trabajo.
   - **Costo**: ~2 días
   - **Beneficio**: Code Agent productivo desde S1

10. **[🟢] Actualizar rol de Mnemosyne** — Definir si sigue siendo el 6º agente curador o su rol cambia con SleepGate.
    - **Costo**: ~0.5 día
    - **Beneficio**: Claridad en responsabilidades

---

## Veredicto Final

```
╔══════════════════════════════════════════════════════════════╗
║                                                              ║
║         🟡 APROBADA CON CONDICIONES                          ║
║                                                              ║
║  Score compuesto: 7.1 / 10                                   ║
║  Umbral producción (🔴): 80 ❌ (por debajo)                  ║
║  Umbral desarrollo (🟡): 70 ✅ (aceptable)                   ║
║                                                              ║
║  Condiciones para APROBACIÓN TOTAL:                          ║
║  1. 🔴 Rediseñar verificación cruzada para DAG (ADR-003)     ║
║  2. 🔴 Integrar DSOL con LangGraph (ADR-004)                 ║
║  3. 🔴 Formalizar exención ADR-008 para Hermes               ║
║  4. 🟡 Aceptar formalmente ADR-005                           ║
║  5. 🟡 Mapear jerarquía ADR-001 → L0-L3                     ║
║  6. 🟡 Deprecar ADR-006 formalmente                          ║
║                                                              ║
║  Sin estas 6 condiciones, la implementación introduce        ║
║  riesgos arquitectónicos que pueden comprometer la           ║
║  integridad del sistema.                                     ║
║                                                              ║
╚══════════════════════════════════════════════════════════════╝
```

### Notas finales de Kosmos

La estrategia de Metis es **la dirección correcta**. KAOS necesita evolucionar del pipeline lineal al DAG, necesita un Code Agent, y necesita una puerta al mundo exterior. La investigación base (78+ fuentes) es sólida, el roadmap es realista, y los OKRs son medibles.

Sin embargo, como arquitecto, mi deber es señalar que:

1. **No se puede copiar-pegar un patrón de verificación triangular en una topología DAG.** La verificación debe ser un sistema de eventos, no un flujo lineal. Es el issue más subestimado de esta estrategia.

2. **Tres sistemas nuevos (Code Agent + LangGraph + Hermes) en paralelo es ambicioso.** La estrategia lo reconoce y propone secuenciación, pero incluso la secuencia implica tocar los 3 en H1. Sugiero considerar dividir en 2 fases: H1a (S1-S4) solo Code Agent + LangGraph wrapper, H1b (M2) Hermes.

3. **Hermes es el componente más riesgoso.** Su valor (Kanban + multi-plataforma) es real, pero la dependencia externa es un costo arquitectónico que debe pagarse explícitamente, no asumirse. Si Hermes no existiera, ¿construiríamos un gateway propio o pospondríamos la feature? Esa respuesta define si vale la pena.

4. **Mnemosyne no debe ser relegada.** En el diagrama de la estrategia, Mnemosyne aparece como un "6o" agente al final, casi un appendage. Su rol de curadora y consolidadora es más importante que nunca con múltiples agentes generando más datos. SleepGate es su evolución natural, no un sistema separado.

---

## Referencias Cruzadas

| Documento | Relación |
|-----------|----------|
| `schema/estrategia-orquesta-agentes-hermes-strategy.md` | Estrategia auditada |
| `schema/adr-001-sistema-memoria.md` a `adr-008-plugin-decision.md` | ADRs de referencia |
| `schema/KAOS.md` | Reglas del vault |
| `schema/eval-profile.yaml` | Perfiles de evaluación |
| `opencode/opencode.json` | Configuración actual de agentes y MCPs |
| `schema/health-report.md` | Salud del vault al momento de la auditoría |

---

*Auditoría realizada por Kosmos el 2026-05-21.*
*Perfil: producción (veracidad 80%, umbral compuesto 80/100).*
*Score compuesto ponderado: 71/100 — APROBADA CON CONDICIONES.*
*Próxima revisión: 2026-05-28 (post-semana 1) o cuando las 6 condiciones estén resueltas.*
