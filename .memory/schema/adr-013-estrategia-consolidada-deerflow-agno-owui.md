# ADR-013: Estrategia Consolidada — DeerFlow + Agno + Open Web UI + KAOS

## Estado
Aceptado

## Contexto

KAOS ha implementado exitosamente la integración DeerFlow + Agno (ADR-012) en modo mock, con 4 puentes funcionales y smoke test verificado (Ruta A, 6/6 PASS). Sin embargo, la arquitectura actual tiene 3 gaps estratégicos:

1. **Open Web UI (139K⭐)** no está integrado — KAOS carece de chat UI humana, gestión de sesiones multi-usuario, RAG documental y tool calling visual.
2. **MCPO Bridge** estaba planificado para conectar OWUI con KAOS, pero Agno Gateway ya provee MCP server nativo — hay superposición.
3. **3 runtimes separados** (KAOS + DeerFlow + OWUI) sin un plan claro de convergencia — riesgo de complejidad operativa.

Este ADR consolida las 3 tecnologías en una estrategia unificada, respondiendo 5 preguntas arquitectónicas clave.

## Decisiones Arquitectónicas

### Q1: ¿DeerFlow + Agno reemplazan o complementan MCPO Bridge?

**Decisión: Opción B — Ambos, con responsabilidades separadas**

```
Agno Gateway (MCP Server, puerto 8010)
  └── Expone tools KAOS al mundo externo (research, analyze, strategize)
  └── Protocolo MCP bidireccional (consume tools externas + expone propias)
  └── Target: desarrolladores, sistemas CI/CD, agentes externos

MCPO Bridge (MCP stdio→HTTP, puerto 9090)
  └── Conecta Open Web UI con MCP servers locales
  └── Traduce MCP stdio (OpenCode) → HTTP (OWUI)
  └── Target: Open Web UI, chat UI para humanos
```

**Justificación:**
- MCPO Bridge es específico para el stack OpenCode + OWUI — no es reemplazable por Agno.
- Agno es para interoperabilidad externa (sistemas que hablan MCP).
- Eliminar MCPO crearía un gap: OWUI necesita HTTP, no stdio.
- DeerFlow PR #1845 (MCP nativo) no está mergeado — seguir monitoreando.

**Riesgo mitigado:** Superposición de MCP servers. Se resuelve con puertos diferentes y dominios de responsabilidad distintos.

### Q2: ¿Cómo se integra DeerFlow Sandbox con el plan OWUI?

**Decisión: DeerFlow Sandbox como tool dentro de OWUI vía MCP, no como provider LLM**

```
Open Web UI (chat UI)
  └── Llama al provider LLM (OpenCode API)
  └── Tools disponibles via MCPO Bridge → MCP servers en OpenCode:
        ├── hermes-gateway (MCP server, ya configurado en opencode.json)
        ├── deerflow-sandbox → ejecución aislada de código
        └── kaos-tools (via Agno Gateway)
```

**Justificación:**
- DeerFlow Sandbox como **provider LLM** no tiene sentido — OWUI soporta OpenAI-compatible API, no DeerFlow nativo.
- DeerFlow Sandbox como **tool** sí es valioso — permite a usuarios de OWUI ejecutar código Python aislado desde el chat.
- Hermes ya está configurado como MCP server en OpenCode (`hermes-gateway` en `opencode.json`).
- La cadena es: OWUI → MCPO Bridge → OpenCode MCP → DeerFlow Sandbox (HTTP).

### Q3: ¿Memory Bridge con Open Web UI RAG?

**Decisión: Opción A+ — 3 stores separados pero con bridge OWUI→KAOS**

| Store | Contenido | Propietario | Estrategia |
|-------|-----------|-------------|------------|
| sqlite-vec (L0-L3) | Memoria episódica de agentes, Hebbian edges, Sleep Cycle | KAOS | Source of truth de agentes |
| ChromaDB (OWUI) | RAG documental, embeddings de documentos | OWUI | RAG para humanos |
| DeerFlow (100 facts) | Cache de trabajo plano | DeerFlow | Cache temporal |

**Bridge adicional (nuevo):** Open Web UI → KAOS Memory Bridge
- OWUI ChromaDB exporta embeddings de documentos relevantes a KAOS L0
- Mnemosyne Sleep Cycle los consolida durante curaduría nocturna
- Flujo: documentos en OWUI → ChromaDB → export nocturno → raw/ → Sleep Cycle → L1→L2

**Justificación:**
- Unificar en ChromaDB (Opción B) requeriría migrar sqlite-vec — riesgo alto, 0 beneficio.
- Unificar en sqlite-vec (Opción C) requeriría que OWUI lo soporte — no es compatible.
- Opción A+ añade un bridge nocturno unidireccional OWUI→KAOS, mínimo esfuerzo.
- DeerFlow sigue siendo cache plano — no hay planes de migrar a embeddings vectoriales (RFC #1898 sin avances).

### Q4: Memory Bridge con Open Web UI — ¿unificación o separación?

*(Renumerada de Q3, respuesta completa arriba)*

### Q5: Riesgos nuevos con DeerFlow + Agno

| Riesgo | Probabilidad | Impacto | Mitigación |
|--------|-------------|---------|------------|
| DeerFlow ByteDance — riesgo geopolítico | Baja-Media | Alto | Fork interno del repo, Agno como backup, licencia Apache 2.0 permite fork |
| PR #1845 sin mergear (MCP nativo DeerFlow) | Alta | Medio | Agno Gateway es permanente hasta que mergee; monitorear semanalmente |
| 3 runtimes separados (complejidad operativa) | Alta | Medio | Docker Compose unificado (track nuevo F), healthchecks automáticos, logging centralizado (LangFuse) |
| DeerFlow dependencies rotas en futuro | Media | Medio | Mock mode garantiza degradación gradual, smoke tests en CI |
| Agno mantenimiento si proyecto se estanca | Baja | Bajo | Agno es liviano (< 500 líneas en nuestra implementación), fácil de reemplazar |

## Mapa de Componentes Actualizado

### Estado Actual (Post ADR-012)

```
KAOS Orchestrator (LangGraph)
  ├── DeerFlowBridge (mock mode) → DeerFlowClient (LangGraph adapter)
  ├── AgnoGateway (mock mode) → MCP tools
  ├── MemoryBridge (mock mode) → sync KAOS↔DeerFlow
  ├── Hermes Bridge → Telegram
  └── 22 MCP servers en OpenCode

FALTANTE:
  ✗ Open Web UI (no implementado)
  ✗ MCPO Bridge (no implementado, pendiente de decisión)
  ✗ DeerFlow → OWUI integración
  ✗ Orchestrator no referencia DeerFlow/Agno todavía
```

### Estado Target (Post ADR-013)

```
                    ┌──────────────────────────────────┐
                    │    OPEN WEB UI (Docker)           │
                    │  Chat UI, RAG, Sesiones, Tools    │
                    │  Provider: OpenCode API           │
                    └──────────┬───────────────────────┘
                               │ HTTP (MCPO Bridge)
                    ┌──────────▼───────────────────────┐
                    │    MCPO BRIDGE (stdio→HTTP)       │
                    │  Puerto 9090                      │
                    │  Conecta OWUI ↔ OpenCode MCP      │
                    └──────────┬───────────────────────┘
                               │ stdio
                    ┌──────────▼───────────────────────┐
                    │    OPENCODE MCP ECOSYSTEM         │
                    │  22 servers, incluyendo:          │
                    │  ├── hermes-gateway (MCP)         │
                    │  ├── kaos-tools (via Agno:8010)   │
                    │  └── deerflow-sandbox (via HTTP)  │
                    └──────────┬───────────────────────┘
                               │
          ┌────────────────────┼────────────────────┐
          │                    │                    │
┌─────────▼────────┐ ┌────────▼───────┐ ┌─────────▼────────┐
│  KAOS ORCHESTRATOR│ │DEERFLOW RUNTIME│ │  AGNO GATEWAY    │
│  LangGraph DAG    │ │Sandbox Docker  │ │  MCP Server:8010 │
│  5 agentes        │ │Sub-agentes     │ │  Exposición       │
│  Memory L0-L3     │ │100 facts cache │ │  externa          │
│  Quality 94.6/100 │ │6 canales IM    │ │                   │
└─────────┬────────┘ └────────────────┘ └───────────────────┘
          │
┌─────────▼────────┐
│  MEMORY BRIDGE   │
│  KAOS↔DeerFlow   │
│  KAOS↔OWUI (new) │
└──────────────────┘
```

## Timeline Consolidado (Semanas 1-10)

### Semana 1-2: Fundación (Track A original + merge DeerFlow en orchestrator)

```
┌─────────────────────────────────────────────────────────┐
│ SEMANA 1-2                                              │
│                                                         │
│ [A1] OWUI Deploy: Docker + configuración OpenCode API   │
│ [A2] DeerFlow → Orchestrator: integrar DeerFlowBridge   │
│      como nodo en el DAG LangGraph (ruta código)         │
│ [A3] Agno → Orchestrator: integrar AgnoGateway.start()  │
│      en inicialización del sistema                       │
│ [A4] Smoke tests actualizados (Ruta A + OWUI health)    │
│                                                         │
│ Dependencias: Docker, deerflow package (pip install)    │
│ Entregables: OWUI running, pipeline con DeerFlow node   │
└─────────────────────────────────────────────────────────┘
```

### Semana 3-4: Bridges (Track B + memoria OWUI)

```
┌─────────────────────────────────────────────────────────┐
│ SEMANA 3-4                                              │
│                                                         │
│ [B1] MCPO Bridge: implementar MCP stdio→HTTP proxy     │
│      Puerto 9090, traducción de tool calls              │
│ [B2] OWUI → KAOS Memory Bridge: export nocturno        │
│      ChromaDB → raw/ → Sleep Cycle                      │
│ [B3] DeerFlow Sandbox como tool en OWUI (via MCPO)     │
│ [B4] Test de integración: OWUI→MCPO→DeerFlow sandbox   │
│                                                         │
│ Dependencias: OWUI running (sem 1-2)                   │
│ Entregables: MCPO Bridge funcional, bridge de memoria   │
└─────────────────────────────────────────────────────────┘
```

### Semana 5-6: Hermes + Profiles (Track C + Agno live)

```
┌─────────────────────────────────────────────────────────┐
│ SEMANA 5-6                                              │
│                                                         │
│ [C1] Hermes API: extender config.yaml para OWUI         │
│ [C2] Profiles: mapear perfiles KAOS → OWUI workspaces   │
│ [C3] Agno Gateway LIVE (modo real, no mock):            │
│      pip install agno, AgentOS con enable_mcp_server    │
│ [C4] DeerFlowClient LIVE (modo real, no mock):          │
│      pip install deerflow, sub-agentes activos          │
│                                                         │
│ Dependencias: DeerFlow package, Agno package            │
│ Entregables: Hermes+OWUI integrados, modo real activo   │
└─────────────────────────────────────────────────────────┘
```

### Semana 7-8: Observabilidad (Track D + quality)

```
┌─────────────────────────────────────────────────────────┐
│ SEMANA 7-8                                              │
│                                                         │
│ [D1] LangFuse: tracing para OWUI + DeerFlow + KAOS     │
│ [D2] DeerFlowQualityReport → LangFuse dataset           │
│ [D3] KAOS evaluator (kosmos_evaluator_node) → LangFuse  │
│ [D4] Dashboard de calidad unificado (3 sistemas)        │
│                                                         │
│ Dependencias: modo real activo (sem 5-6)                │
│ Entregables: LangFuse tracing, dashboard calidad        │
└─────────────────────────────────────────────────────────┘
```

### Semana 9-10: Dashboard + Hardening (Track E + Track F new)

```
┌─────────────────────────────────────────────────────────┐
│ SEMANA 9-10                                             │
│                                                         │
│ [E1] Dashboard Unificado: health de 3 sistemas          │
│ [E2] Docker Compose: KAOS + OWUI + DeerFlow + Agno      │
│      docker-compose.yml con healthchecks                 │
│ [E3] Hardening: timeouts, retries, circuit breakers     │
│ [E4] Documentación final + ADR-013 completado           │
│                                                         │
│ Dependencias: tracks anteriores                          │
│ Entregables: Docker Compose, dashboard, docs            │
└─────────────────────────────────────────────────────────┘
```

### Nuevos Tracks vs Originales

| Track | Original (5 tracks) | Consolidado (7 tracks) | Cambio |
|-------|---------------------|------------------------|--------|
| A: OWUI Deploy | Sem 1-2 | Sem 1-2 | +DeerFlow/Agno en orchestrator |
| B: MCPO Bridge | Sem 3-4 | Sem 3-4 | +Memoria OWUI→KAOS |
| C: Hermes+Profiles | Sem 5-6 | Sem 5-6 | +Agno/DeerFlow LIVE mode |
| D: LangFuse | Sem 7-8 | Sem 7-8 | +3 sistemas tracing |
| E: Dashboard | Sem 9-10 | Sem 9-10 | Unchanged |
| **F: Docker Compose** | ✗ Nuevo | Sem 9-10 | Unificar 3 runtimes |
| **G: Orquestación** | ✗ Nuevo | Sem 1-2 | DeerFlow/Agno como nodos |

### Dependencias entre Tracks

```
Sem 1-2 [A+G] ──→ Sem 3-4 [B] ──→ Sem 5-6 [C] ──→ Sem 7-8 [D] ──→ Sem 9-10 [E+F]
                                                                           ↑
                                                             DeerFlow PR #1845 ┘
                                                             (si se mergea a tiempo)
```

## Matriz de Riesgos Actualizada

| # | Riesgo | Prob | Impacto | Score | Mitigación |
|---|--------|------|---------|-------|------------|
| R1 | DeerFlow ByteDance — riesgo geopolítico/licencia | 30% | 9/10 | 2.7 | Fork interno, Agno como backup |
| R2 | PR #1845 no mergeado (MCP DeerFlow nativo) | 85% | 7/10 | 5.95 | Agno Gateway permanente, monitoreo semanal |
| R3 | 3 runtimes: complejidad operativa | 70% | 6/10 | 4.2 | Docker Compose (Track F), healthchecks |
| R4 | OWUI consume recursos significativos (Docker) | 60% | 4/10 | 2.4 | Límites de memoria en docker-compose |
| R5 | Memory Bridge OWUI→KAOS: conflictos de embedding | 40% | 5/10 | 2.0 | Bridge nocturno unidireccional, no sync bidireccional |
| R6 | DeerFlow 69.5K⭐ → mantenimiento caótico (issues) | 50% | 5/10 | 2.5 | Usar subset estable (sandbox + sub-agentes) |
| R7 | OpenCode API rate limits con OWUI multi-usuario | 40% | 6/10 | 2.4 | Caching de respuestas, cola de requests |
| R8 | Agno proyecto puede estancarse | 20% | 3/10 | 0.6 | Gateway propio es <500 líneas, reemplazable |

### Comparación con ADR-012

Los riesgos de ADR-012 se mantienen (R1-R3 originales) y se añaden:

| Riesgo Nuevo | Origen | Prioridad |
|-------------|--------|-----------|
| R3 (3 runtimes) | Complejidad operativa | ALTA |
| R4 (OWUI recursos) | OWUI en Docker | MEDIA |
| R5 (Memory conflict) | Embeddings dispares | MEDIA |
| R7 (Rate limits) | OpenCode API | MEDIA |

## Recomendación Ejecutiva

**Iniciar Semana 1 inmediatamente.** La integración DeerFlow+Agno en mock mode está lista y testeada. El siguiente paso crítico es integrar DeerFlowBridge como nodo del orquestador LangGraph (Track G) y desplegar OWUI en Docker (Track A). Estos dos tracks son independientes y pueden ejecutarse en paralelo.

**No eliminar MCPO Bridge.** Agno Gateway y MCPO Bridge tienen dominios diferentes — uno para exposición externa MCP-to-MCP, otro para conectar OWUI con el ecosistema OpenCode. Mantener ambos evita crear un gap de integración.

**No unificar vector stores.** 3 stores separados (sqlite-vec, ChromaDB, DeerFlow cache) con bridges unidireccionales nocturnos es el balance óptimo entre simplicidad y funcionalidad. Unificar requeriría migraciones riesgosas sin beneficio tangible.

**Costo total estimado:** ~60 horas-hombre distribuidas en 10 semanas, asumiendo 1-2 personas.

## ADRs Afectados

- ADR-012: Se extiende — DeerFlow/Agno ahora son nodos del orquestador, no solo puentes independientes
- ADR-010: LangGraph Orchestrator gana 2 nuevos nodos (deerflow, agno_gateway)
- ADR-005: sqlite-vec se mantiene como L0, Opción A+ añade bridge nocturno OWUI→KAOS
- ADR-011: Memory Matrix L0-L3 se extiende con OWUI ChromaDB como fuente de ingesta nocturna
- **Nuevo**: Este ADR-013 reemplaza el plan OWUI de 5 tracks con uno de 7 tracks consolidado

## Referencias

- DeerFlow 2.0: https://github.com/bytedance/deer-flow
- Agno MCP: https://docs.agno.com/tools/mcp/overview
- Open Web UI: https://github.com/open-webui/open-webui
- OpenCode MCP: https://opencode.ai/docs/mcp
- ADR-012: Integración DeerFlow + Agno
- ADR-010: DSOL + LangGraph Orchestrator
- ADR-005: Vector Store (sqlite-vec)
