# ARQUITECTURA ESTRATÉGICA TOTAL DE KAOS

## *El sistema multi-agente evolutivo definitivo*

> **Documento**: `.memory/schema/arquitectura-estrategica-total-kaos.md`
> **Agente**: Metis (Μῆτις) — Diosa de la Sabiduría Profunda
> **Fecha**: 2026-05-25
> **Perfil**: Producción 🔴
> **Score objetivo**: >95/100

---

## Resumen Ejecutivo

KAOS se encuentra en una encrucijada evolutiva. El pipeline lineal Aletheia→Kosmos→Metis→Mnemosyne funciona, los puentes DeerFlow+Agno están en mock mode (6/6 smoke tests PASS), la memoria L0-L3 con 3,610 chunks y sleep cycle está operativa, y el score compuesto de calidad alcanza 88.6/100. Sin embargo, **el sistema actual no escala, no es paralelo, no es auto-evolutivo y no se comunica con el exterior**.

Esta arquitectura estratégica total define el salto cualitativo: de un pipeline secuencial de 5 agentes a un **sistema multi-agente evolutivo con paralelismo dinámico (Send API), memoria federada híbrida (txtai + KG), auto-mejora (Auto-ADR, Auto-tuning), calidad estructural (>95/100) y MCP bidireccional como protocolo universal de comunicación**.

**Palancas de cambio clave**: (1) Activar LangGraph Send API, (2) Migrar L0 a txtai, (3) Configurar Agno real, (4) Implementar Auto-ADR, (5) Score engine post-hoc.

**Recomendación**: Ejecutar en 3 oleadas paralelas de 4 semanas cada una. Costo estimado: ~120 horas-hombre.

---

## PARTE 1: VISIÓN DEL SISTEMA FINAL

### 1.1 La Experiencia KAOS en Estado Óptimo

KAOS opera como un **organismo cognitivo distribuido** donde 5 agentes especializados cooperan en tiempo real, compartiendo memoria federada, comunicándose vía MCP bidireccional y evolucionando su propia arquitectura sin intervención humana para decisiones rutinarias.

**Escenario típico — 2026-Q3:**

El humano escribe: *"Investiga el estado del arte en agentes MCP con memoria procedural, diseñame una arquitectura, y genera el código de un prototipo."*

1. **Aletheia** recibe la tarea y, en paralelo con Kosmos (Send API), lanza 4 búsquedas simultáneas (arXiv, web, GitHub, RSS). En 45 segundos tiene 12 fuentes relevantes. Destila en raw/.
2. **Kosmos** lee raw/ mientras Aletheia aún busca. Propone 3 diseños arquitectónicos con C4. Genera ADR borrador.
3. **Metis** evalúa los 3 diseños contra OKRs del sistema. Puntúa, recomienda el óptimo.
4. **Kratos** toma la arquitectura seleccionada y genera el prototipo (1,200 líneas Python) usando CodeExperience DB (FTS5+vec0+AST) para patrones previos. Sandbox Docker ejecuta y testea. 3 errores detectados y corregidos automáticamente.
5. **Mnemosyne** consolida todo: actualiza conceptos wiki, crea wikilinks, ejecuta sleep NREM→REM. Score de calidad: 97/100.

**Tiempo total**: ~8 minutos. **Sin intervención humana.**

### 1.2 Arquitectura Final

```
                     ┌──────────────────────────────────────────┐
                     │           HUMAN INTERFACE LAYER           │
                     │  OpenCode CLI  │  Open Web UI  │  Hermes │
                     └──────────────────┬───────────────────────┘
                                        │ MCP / A2A
                     ┌──────────────────▼───────────────────────┐
                     │         AGNO MCP GATEWAY (REAL)           │
                     │  - MCP Server bidireccional :8010         │
                     │  - Expone: research, analyze, strategize  │
                     │  - Consume: 22 MCP servers externos       │
                     │  - Rate limiting, auth, logging            │
                     └──────────────────┬───────────────────────┘
                                        │ MCP
                     ┌──────────────────▼───────────────────────┐
                     │       LANGGRAPH ORCHESTRATOR v1.0+        │
                     │  ┌──────────────────────────────────┐    │
                     │  │  Send API — Parallel Fan-out      │    │
                     │  │  ├── Aletheia (Research)         │    │
                     │  │  ├── Kosmos (Architecture)       │    │
                     │  │  ├── Metis (Strategy)            │    │
                     │  │  ├── Kratos (Code)               │    │
                     │  │  └── Mnemosyne (Curation)        │    │
                     │  │  Send API con with_parallel=True  │    │
                     │  │  Checkpointing SQLite (WAL)       │    │
                     │  │  Evaluator-Optimizer loop (max 3) │    │
                     │  └──────────────────────────────────┘    │
                     │  ┌──────────────────────────────────┐    │
                     │  │ VERIFICATION SUBGRAPH             │    │
                     │  │  - Event-driven verification      │    │
                     │  │  - Subscribe a todos los outputs  │    │
                     │  │  - Score 5 dimensiones continuo   │    │
                     │  └──────────────────────────────────┘    │
                     └──────────────────┬───────────────────────┘
                                        │
           ┌────────────────────────────┼────────────────────────┐
           │                            │                        │
┌──────────▼──────────┐  ┌─────────────▼──────────┐  ┌─────────▼──────────┐
│   MEMORIA FEDERADA   │  │    SANDBOX DOCKER       │  │  SISTEMA AUTO-EVO   │
│ ┌──────────────────┐ │  │ kaos-sandbox (read-only)│  │ Auto-ADR Generator  │
│ │ L0: txtai híbrido│ │  │ Kratos ejecuta aquí     │  │ Auto-tuning DSOL    │
│ │ (bm25+vector 384d)│ │  │ Sin red, Python aislado │  │ Self-healing graph  │
│ │ 50-80MB RAM      │ │  │                         │  │ Budget optimizer    │
│ ├──────────────────┤ │  └─────────────────────────┘  └─────────────────────┘
│ │ L1: CodeExp DB   │ │
│ │ FTS5+vec0+AST    │ │
│ │ Hebbian edges    │ │
│ ├──────────────────┤ │
│ │ L2: Knowledge G. │ │
│ │ 106 conceptos    │ │
│ │ wikilinks vivos  │ │
│ ├──────────────────┤ │
│ │ L3: Schema+ADRs  │ │
│ │ Patrones sleep   │ │
│ └──────────────────┘ │
└───────────────────────┘
```

### 1.3 Cómo fluye el conocimiento

```
INPUT (humano)
  → LangGraph Send API descompone tarea
  → Fan-out paralelo:
      ├── Aletheia busca en web + papers
      ├── Kosmos analiza código existente
      └── Kratos consulta CodeExperience DB
  → Fan-in con síntesis (Metis)
  → Kratos genera código (sandbox)
  → Mnemosyne consolida en memoria
  → Verificación subgraph evalúa calidad
  → Auto-ADR decide si crear nuevo ADR
  → Output al humano
  → Sleep cycle nocturno:
      NREM: clustering + destilación L0→L1
      REM: síntesis cross-dominio L1→L2→L3
      Forgetting: decaimiento natural
```

### 1.4 Auto-evolución

| Mecanismo | Trigger | Acción |
|-----------|---------|--------|
| **Auto-ADR** | Score < 80 en 3 ejecuciones consecutivas | Kosmos genera ADR propuesta |
| **Auto-tuning DSOL** | Cache hit rate < 20% | Ajusta prompts, thinking mode, budget |
| **Self-healing graph** | Nodo falla > 2 veces seguidas | Reconexión con backoff |
| **Budget optimizer** | Costo semanal excede umbral | Reduce thinking en tareas simples |

---

## PARTE 2: PRINCIPIOS RECTORES

1. **La memoria es el centro del sistema** — todo lo demás es ejecución. Toda inversión en memoria tiene prioridad sobre features de agente.

2. **La calidad no se delega — se diseña estructuralmente**. Verificación asíncrona como subgraph separado, no en línea.

3. **El sandbox no es opcional** — es la base de la seguridad. Todo código de Kratos en sandbox.

4. **Un sistema que no se mide, no se puede mejorar**. Timeseries de calidad desde el día 1.

5. **La complejidad solo se justifica si reduce complejidad futura**. txtai colapsa 3 stacks en 1. Send API colapsa DeerFlow + CrewAI en 0 dependencias.

6. **La velocidad es función del riesgo controlado**. Hitos de verificación NO negociables entre oleadas.

7. **El humano es el arquitecto final** — el sistema es su instrumento. Auto-ADR propone, humano aprueba.

---

## PARTE 3: MAPA ESTRATÉGICO — Dimensiones de Evolución

| Dimensión | Estado Actual | Estado Objetivo | Palanca | Esfuerzo |
|-----------|--------------|-----------------|---------|----------|
| Memoria L0 | sqlite-vec 3,610 chunks | txtai híbrido, ~50-80MB RAM, <5ms | Migrar a txtai | 3-5 días |
| Pipeline | Secuencial | Send API paralelo | with_parallel=True | 5-8 días |
| Verificación | Cadena lineal | Subgraph event-driven | Rediseñar | 3-5 días |
| Interconexión | Agno mock | Agno real MCP bidireccional | Configurar | 2h |
| Calidad | Score 88.6, sin timeseries | Score >95 continuo + trending | Score engine | 3-5 días |
| Auto-evolución | No existe | Auto-ADR + Auto-tuning + Self-healing | Implementar | 6-10 días |

---

## PARTE 4: TEORÍA DEL CAMBIO

### Puntos de Apalancamiento

| # | Palanca | Esfuerzo | Impacto | Ratio |
|---|---------|----------|---------|-------|
| P1 | Activar Send API | 2 días | 3x-5x throughput | 10:1 |
| P2 | Verificación asíncrona | 4 días | Desbloquea Send API | 8:1 |
| P3 | Migrar L0 a txtai | 3 días | Colapsa 3 stacks en 1 | 7:1 |
| P4 | Agno real | 2 horas | MCP bidireccional | 20:1 |
| P5 | Score engine post-hoc | 2 días | Timeseries + mejora | 5:1 |
| P6 | Auto-ADR detector | 6 días | Auto-evolución | 4:1 |

### Cuellos de Botella

| # | Cuello | ¿Qué se atasca? | Desbloqueo |
|---|--------|-----------------|------------|
| B1 | Verificación no DAG-ready | Send API bloqueado | Subgraph event-driven |
| B2 | DSOL ↔ LangGraph sin contrato | Costos impredecibles | Implementar routing |
| B3 | txtai no migrado | 3 stacks paralelos | Migración directa |
| B4 | Sin timeseries calidad | No hay mejora medible | Score engine |

---

## PARTE 5: PLAN DE EJECUCIÓN ACELERADO

### Oleada 1: Fundación (S1-S4)

```
S1-S2:
  [1A] Verificación asíncrona (subgraph) ←──┐ paralelo
  [1B] DSOL→LangGraph integración          ─┘
  HITO H1: Smoke test paralelo + verificación

S3-S4:
  [1C] Send API activation
  [1D] txtai migración L0
  HITO H2: Fan-out 3 agentes, txtai <5ms
```

### Oleada 2: Interconexión (S5-S8)

```
S5-S6:
  [2A] Agno real · [2B] Memoria federada · [2C] Calidad estructural
  HITO H3: MCP bidireccional + score continuo
S7-S8:
  [2D] Observabilidad · [2E] Telegram+Slack
  HITO H4: Dashboard 7d tendencias
```

### Oleada 3: Auto-evolución (S9-S12)

```
S9-S10:
  [3A] Auto-ADR · [3B] Auto-tuning DSOL
  HITO H5: Sistema propone mejoras sin humano
S11-S12:
  [3C] Self-healing · [3D] Docker Compose unificado
  HITO H6-H7: Score >95/100, 7 días sin intervención
```

---

## PARTE 6: MATRIZ DE RIESGOS TOTAL

### Riesgos Críticos (severidad >3.0)
- **AD1** (3.5) — Humano no adopta el sistema
- **C1** (3.6) — Costo de API se dispara con paralelismo

### Riesgos Altos (severidad 2.0-3.0)
- **AR1** (2.7) — Send API corrompe estado del pipeline
- **AR3** (2.25) — Verificación pierde outputs por race conditions
- **AR4** (2.8) — Hebbian edges incompatibles con txtai
- **AD2** (3.2) — Alertas ignoradas → degradación silenciosa
- **AD3** (2.7) — Complejidad de 3 oleadas abruma
- **EV1** (2.4) — Auto-ADR contradictorio con ADRs existentes
- **EV4** (2.45) — Self-healing esconde bugs
- **S2** (1.35) — MCP Gateway sin autenticación

---

## PARTE 7: DECISIONES ABIERTAS

| Decisión | Recomendación |
|----------|---------------|
| txtai ¿reemplazo total o capa dual? | **Reemplazo total** — migrar 100 chunks, validar, luego todo |
| MCPO Bridge o Agno directo? | **Agno directo** primero |
| Hermes ¿solo Telegram o más canales? | **Telegram + Slack** |
| Auto-ADR ¿aprobación o autónomo? | **Híbrido**: críticos requieren aprobación |
| Score ¿gatekeeper duro o blando? | **Blando**: <80 alerta, <60 bloquea |

---

## PARTE 8: MÉTRICAS DE SALUD

| Métrica | Actual | Target | Alerta |
|---------|--------|--------|--------|
| M1: Score compuesto | 88.6 | >95 | <80 🟡 <60 🔴 |
| M2: Cache hit rate | 2.7% | >60% | <20% 🟡 <10% 🔴 |
| M3: Tiempo pipeline | ~10min | <5min | >15min 🟡 |
| M4: Broken wikilinks | 0 | 0 | >0 🔴 |
| M5: Costo semanal | ~$30 | <$5 | >$5 🟡 |
| M6: Throughput | ~1/h | >3/h | <1/h 🟡 |
| M7: Fragmentación memoria | N/A | <0.2 | >0.5 🟡 |

---

*Documento generado por Metis el 2026-05-25.*
*Score de confianza: 92/100. Perfil: Producción 🔴.*
