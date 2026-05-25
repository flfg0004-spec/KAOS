# ADR-012: Integracion KAOS + DeerFlow + Agno

## Estado
Aceptado

## Contexto
KAOS necesita cerrar 3 gaps criticos: (1) ejecucion aislada de codigo via sandbox, (2) multiples canales IM (actualmente solo Telegram via Hermes), (3) exposicion como MCP server para interoperabilidad externa.

La investigacion de Aletheia (11 frameworks, 78+ fuentes) y la estrategia de Metis identificaron a DeerFlow 2.0 (ByteDance, 69.5K⭐) y Agno (40K⭐) como los complementos ideales:

- **DeerFlow**: sandbox Docker aislado, sub-agentes dinamicos, 6 canales IM nativos, Docker Compose production-ready
- **Agno**: unico framework con MCP bidireccional (consume y expone), util mientras DeerFlow no mergee su PR #1845 (MCP Server)

## Decision
Adoptar una arquitectura de 3 capas donde cada framework aporta su mejor pieza:

| Capa | Framework | Rol |
|------|-----------|-----|
| **Orquestador** | KAOS (LangGraph) | Pipeline DAG, memoria L0-L3, calidad 94.6/100, compile-then-query |
| **Runtime** | DeerFlow | Sandbox Docker, sub-agentes, 6 canales IM, Docker Compose |
| **MCP Gateway** | Agno AgentOS | Exposicion MCP bidireccional (hasta PR #1845) |

### Decisiones Arquitectonicas (P1-P7)

**P1 — Secuencial vs paralelo:** PARALELO. Sandbox, IM, MCP Gateway y Memory Bridge son ortogonales y se implementan simultaneamente.

**P2 — Contrato KAOS↔DeerFlow:** DUAL. `DeerFlowClient.chat()` in-process (~2ms) como primario para tareas de razonamiento. MCP/HTTP hacia Sandbox Docker (~50ms) para ejecucion de codigo aislado.

**P3 — Memory Bridge:** ASIMETRICO. KAOS (L0-L3 con Hebbian + Sleep Cycle) es source of truth. DeerFlow (100 facts planos sin embeddings) es cache de trabajo. Sync unidireccional por hora: KAOS push top-100 facts comprimidos a DeerFlow.

**P4 — Agno timing:** RUTA A desde dia 1. PR #1845 de DeerFlow no esta mergeado. Agno AgentOS con `enable_mcp_server=True` es la unica forma de exponer KAOS como MCP server hoy.

**P5 — Pipeline:** FASE A mantiene pipeline secuencial con delegacion a DeerFlow. FASE B migra a LangGraph Send API para paralelismo real.

**P6 — Kratos sandbox:** NO migrar. Kratos mantiene ejecucion local con CodeExperience, FTS5, AST matching, RSCB-MC bandit, Hebbian edges. Sandbox solo para codigo aislado.

**P7 — Calidad:** HIBRIDA. KAOS evalua en 5 dimensiones (post-hoc). DeerFlow produce `DeerFlowQualityReport` (JSON) por tarea ejecutada.

### Arquitectura

```
                    ┌──────────────────────────────────────┐
                    │         IM Canales (DeerFlow)         │
                    │  Telegram | Slack | Feishu | CLI     │
                    └──────────────┬───────────────────────┘
                                   │
              ┌────────────────────▼──────────────────────┐
              │         AGNO MCP GATEWAY                   │
              │  enable_mcp_server=True → /mcp endpoint   │
              │  Expone: kaos_research, kaos_analyze, ... │
              └────────────────────┬──────────────────────┘
                                   │ MCP
              ┌────────────────────▼──────────────────────┐
              │          KAOS ORCHESTRATOR                 │
              │  ┌──────────────────────────────────┐     │
              │  │  LangGraph DAG (5 agentes)        │     │
              │  │  ├── Aletheia → Kosmos → Metis   │     │
              │  │  ├── Kratos (local + sandbox)    │     │
              │  │  └── Mnemosyne (curation+memory) │     │
              │  └──────────────────────────────────┘     │
              │  ┌──────────────────────────────────┐     │
              │  │  Memory L0-L3 + Sleep Cycle       │     │
              │  │  Quality System 94.6/100          │     │
              │  └──────────────────────────────────┘     │
              └────────────────────┬──────────────────────┘
                                   │ DeerFlowClient (in-process)
              ┌────────────────────▼──────────────────────┐
              │         DEERFLOW RUNTIME                   │
              │  ┌──────────────────────────────────┐     │
              │  │  Lead Agent → Sub-agentes         │     │
              │  │  Sandbox Docker (AioSandbox)      │     │
              │  │  Skills progresivos (SKILL.md)    │     │
              │  │  Memory cache (100 facts planos)   │     │
              │  │  LangSmith + Langfuse tracing     │     │
              │  └──────────────────────────────────┘     │
              └──────────────────────────────────────────┘
```

### Puentes

**Puente 1 — DeerFlowBridge (`lib/deerflow_bridge.py`):**
```python
class DeerFlowBridge:
    async def execute(self, task: dict) -> dict
        if task.type == 'code_execution':    return await self._via_sandbox(task)
        else:                                return await self._via_client(task)
```

**Puente 2 — Agno MCP Gateway (`lib/agno_gateway.py`):**
```python
class AgnoGateway:
    def start(self): agentos.enable_mcp_server = True; agentos.run()
    # Expone: kaos_research, kaos_analyze, kaos_strategize
```

**Puente 3 — Memory Bridge (`lib/memory_bridge.py`):**
```python
class MemoryBridge:
    async def push_to_deerflow(self):  # top-100 facts L1 → DeerFlow
    async def pull_from_deerflow(self):  # DeerFlow facts → L0 raw
```

## Consecuencias

### Positivas
+ Sandbox Docker permite ejecucion segura de codigo (gap critico cerrado)
+ 6 canales IM nativos (vs solo Telegram actualmente)
+ MCP Gateway para interoperabilidad con cualquier sistema MCP-compatible
+ Contrato dual optimiza latencia (in-process) + seguridad (sandbox)
+ Memoria asimetrica mantiene a KAOS como source of truth
+ Kratos preserva CodeExperience + bandit + Hebbian

### Negativas
- Dependencia de 2 frameworks externos (DeerFlow + Agno)
- PR #1845 no mergeado → Agno como MCP Gateway permanente hasta que DeerFlow lo implemente
- Memory Bridge requiere mantenimiento de sync (push por hora)
- Costo operativo adicional (3 runtimes vs 1 actual)
- Complejidad de debugging cuando la cadena cruza 3 sistemas

### Neutrales
- Agno puede ser deprecado si PR #1845 se mergea y DeerFlow expone MCP nativo
- Memory Bridge puede escalar a sincronia completa cuando DeerFlow adopte embeddings vectoriales (RFC #1898)
- Pipeline secuencial se mantiene en Fase A, se migra a Send API en Fase B

### ADRs Afectados
- ADR-001: No se modifica (memoria KAOS sigue siendo L0-L3)
- ADR-005: Vector Store (sqlite-vec) se mantiene como L0, Qdrant se evalua en ADR-013
- ADR-010: LangGraph Orchestrator se extiende con DeerFlowBridge como nodo
- ADR-011: Memory Matrix L0-L3 se mantiene, Memory Bridge sincroniza con DeerFlow externamente

## Referencias
- DeerFlow 2.0: https://github.com/bytedance/deer-flow
- Agno MCP Bidireccional: https://docs.agno.com/tools/mcp/overview
- PR #1845 (DeerFlow MCP Server): https://github.com/bytedance/deer-flow/pull/1845
- LangGraph Send API: https://docs.langchain.com/oss/python/langgraph/use-graph-api
- ADR-010: DSOL + LangGraph Orchestrator
- ADR-011: Memory Matrix L0-L3
- Hallazgos Aletheia: Investigacion 11 frameworks, 78+ fuentes
- Estrategia Metis: Analisis 3 rutas (A→B→C), OKRs, riesgos
