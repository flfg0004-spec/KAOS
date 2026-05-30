---
title: Metis↔Kronos Boundary
type: boundary
scope: agent-boundary
status: active
created: 2026-05-29
updated: 2026-05-29
---

# Metis ↔ Kronos Boundary Matrix

Definición formal del límite de responsabilidad entre Metis (estrategia, calidad estratégica)
y Kronos (orquestación de pipelines, routing, scheduling).

## Cadena de valor

```
  Metis (qué/cuándo/por qué)
    │
    ▼
  Kronos (cómo/ruting/recuperación)
    │
    ▼
  Pipeline (ejecución)
```

Metis define la estrategia y la calidad del output. Kronos asegura que el pipeline
entregue ese output de forma fiable, rápida y recuperable.

---

## Matriz de Decisión

| Dimensión | Propietario | Rationale |
|-----------|-------------|-----------|
| Calidad de PIPELINE (routing adaptativo, scheduling, errores) | **Kronos** | Tiene `lifecycle_*`, `quality_*`, `gaps_*` — herramientas de infraestructura |
| Calidad de OUTPUT estratégico (BCG eval, reportes semanales) | **Metis** | Tiene `strategy-mcp`, `strategy-extras`, `agy-bridge` — frameworks y modelos |
| Velocidad del sistema (speed metrics) | **Kronos** | Monitorea pipeline throughput con `mcp-speed_*` |
| Evaluación de velocidad vs. calidad | **Metis + Kronos** | Kronos provee métrica, Metis evalúa impacto estratégico |
| Verificación cruzada post-output | **Metis** | Quality Orchestrator Mode — smoke/functional/audit sessions |
| Recuperación de errores en pipeline | **Kronos** | `lifecycle_*` tools para restart, fallback, circuit breaker |
| Detección de gaps de conocimiento | **Metis** (identifica), **Kronos** (routing a Aletheia) | Gap Detection es estratégico; el routing es pipeline |
| OKRs y roadmaps | **Metis** | `strategy-mcp` okr_generator, roadmap tools |
| Scheduling de tests | **Kronos** | Pipeline orchestration — `lifecycle_*` session scheduling |
| Dashboard de calidad estratégica | **Metis** | BCG scores, health scores — populate dashboard.py |
| Dashboard de pipeline operacional | **Kronos** | Speed metrics, error rates, uptime |

---

## Reglas

1. **Si el problema es "el sistema está funcionando correctamente"** → Kronos.
   Evalúa health del pipeline, speed, tasas de error, scheduling.

2. **Si el problema es "la calidad del output estratégico"** → Metis.
   Evalúa BCG score, alineación con OKRs, verificación cruzada.

3. **Si un test falla en pipeline** → Kronos lo detecta y lo reporta.
   Metis evalúa el impacto estratégico del fallo y decide si reprogramar.

4. **Metis NO toca routing ni scheduling** — esas son responsabilidad de Kronos.
   Kronos tiene `lifecycle_*` y `txtai_*` para gestionar el pipeline.

5. **Kronos NO evalúa calidad de contenido estratégico** — esa es responsabilidad de Metis.
   Metis tiene `strategy-mcp_*` y `agy-bridge_*` para evaluación estratégica.

---

## Guardrails

| Guardrail | Descripción |
|-----------|-------------|
| Metis no debe invocar `lifecycle_*` tools de Kronos | Metis no tiene permiso `lifecycle_*` en opencode.json. La separación es técnica y de policy. |
| Kronos no debe generar OKRs ni roadmaps | Kronos no tiene `strategy-mcp` ni `strategy-extras` en su tool set. No posee los frameworks necesarios. |
| Metis no debe alterar scheduling del pipeline | Kronos gestiona los ciclos de pipeline via `lifecycle_*` y `quality_*`. |
| Kronos no debe ejecutar BCG evaluation | BCG eval es estratégico (8 dimensiones de calidad de output) — es competencia de Metis. |
| Ambos pueden leer `mcp-speed_*` | Speed metrics son shared: Kronos monitorea pipeline, Metis monitorea calidad vs velocidad. |
| Ambos pueden usar `mcp-dsol_*` | DSOL routing es compartido: Kronos lo usa para routing adaptativo, Metis para selección de modelo. |

---

## Tool Overlap Analysis

Basado en `opencode.json` (líneas 168-239):

### Metis tools (11)
`agy-bridge_*`, `exa-search_*`, `excalidraw_*`, `mcp-dsol_*`, `mcp-obsidian-cli_*`,
`mcp-speed_*`, `paperjsx_*`, `sequential-thinking_*`, `strategy-extras_*`,
`strategy-mcp_*`, `vault_*`

### Kronos tools (10)
`vault_*`, `sequential-thinking_*`, `knowledge-graph_*`, `strategy-mcp_*`,
`txtai_*`, `quality_*`, `gaps_*`, `lifecycle_*`, `mcp-speed_*`, `mcp-dsol_*`

### Shared (4)
| Tool | Metis uso | Kronos uso |
|------|-----------|------------|
| `vault_*` | Lectura/escritura de reportes estratégicos | Acceso a pipeline state, logs |
| `sequential-thinking_*` | Descomposición de problemas estratégicos | Debug de pipeline failures |
| `mcp-speed_*` | Monitoreo de velocidad vs calidad estratégica | Monitoreo de pipeline throughput |
| `mcp-dsol_*` | Resolución dinámica de modelos | Routing adaptativo de workers |

### Exclusive to Metis (7)
`agy-bridge_*`, `exa-search_*`, `excalidraw_*`, `mcp-obsidian-cli_*`,
`paperjsx_*`, `strategy-extras_*`, `strategy-mcp_*`

### Exclusive to Kronos (6)
`knowledge-graph_*`, `txtai_*`, `quality_*`, `gaps_*`, `lifecycle_*`

---

## Referencias

- `opencode.json` líneas 168-204 (Metis config) y 206-238 (Kronos config)
- `.memory/wiki/entities/metis.md` — identidad y capacidades de Metis
- `.opencode/agents/metis/AGENTS.md` — tool use guidance de Metis
