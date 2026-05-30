# ADR-023: Framework de Agentes — Adoptar Patrones de Mastra sin Migrar

**Estado:** Propuesto  
**Fecha:** 2026-05-30  
**Contexto:** Decisión sobre adopción de Mastra (24.6K⭐, 1.77M npm/mes) como framework de agentes

## Contexto

KAOS tiene un stack de agentes **custom en Python** que ha evolucionado durante ~1 año:

- **6 agentes** (Aletheia, Kosmos, Kratos, Metis, Kronos, Mnemosyne) con skill-based routing, permisos granularizados, y ciclo de vida definido.
- **3 generaciones de routing** (DSOL → Ether → Aether), consolidado recientemente.
- **4 generaciones de memoria** (plano → Letta-inspired → LLM Wiki → Memory Matrix L0-L3).
- **30+ MCP servers**, sistema de calidad, pipeline DAG, kanban, telemetría.

**Mastra** (24.6K⭐, 1.77M descargas npm/mes) ofrece:

1. **Agents** con tools, memory, instructions, y model routing.
2. **Workflows** con `.then().branch().parallel()` — DSL declarativo para pipelines.
3. **4 tipos de memoria**: FIFO, semantic, working, vector-based.
4. **RAG** integrado con retrieval augmentado.
5. **Evals** nativos para evaluar outputs de agentes.
6. **MCP authoring** — crear y consumir MCP servers.
7. **Serverless deploy** — despliegue a Vercel, Cloudflare, etc.

La pregunta es: ¿migrar a Mastra o adoptar sus patrones en el stack existente?

## Opciones Consideradas

### Opción 1: Migración Completa a Mastra (TypeScript)

Reescribir KAOS agents en Mastra/TypeScript. Stack: Mastra Agents + Workflows + Memory + Evals.

- **Pros**: Framework unificado, 24.6K⭐, comunidad activa, evals nativos, serverless deploy, MCP authoring.
- **Cons**: **Reescritura completa** — meses de trabajo. Stack Python → TypeScript. Pérdida de 3 generaciones de refinamiento en routing (Aether). Pérdida de integración profunda con el vault `.memory/`. Riesgo de regresión en calidad (94.6/100 actual).

### Opción 2: Adoptar Patrones de Mastra en Stack Python (Seleccionada)

Extraer los patrones clave de Mastra e implementarlos en el stack Python existente:

- **Workflow DSL**: Patrón `.then().branch().parallel()` en Python con corrutinas.
- **Memory tipos**: FIFO (ya existe Working Memory), semantic (vector store txtai), working (scratchpad FIFO).
- **Evals nativos**: DeepEval ya integrado en Aether, extender para evolución continua.
- **MCP authoring**: Ya implementado vía Agno bridge (ADR-012).

- **Pros**: Sin reescritura, beneficio incremental, preserva inversión en Aether + vault + calidad, riesgo mínimo.
- **Cons**: No hay framework unificado, el código custom sigue siendo responsabilidad propia.

### Opción 3: Mastra como Orquestador Paralelo (Sidecar)

Correr Mastra en paralelo para tareas específicas (workflows serverless, evals externos) mientras KAOS mantiene su core.

- **Pros**: Beneficio de Mastra sin migración. Útil para tareas con deploy serverless.
- **Cons**: Dos sistemas paralelos = duplicación de lógica. Complejidad operativa. ¿Qué va en cada sistema?

### Opción 4: Status Quo

Mantener el stack actual sin cambios.

- **Pros**: Estabilidad, sin esfuerzo.
- **Cons**: Se pierden patrones valiosos de Mastra (workflow DSL, memoria semántica estructurada, evolución de calidad).

## Decisión

**Opción 2 — Adoptar patrones de Mastra en el stack Python existente.**

No se migra a Mastra. Se extraen e implementan 3 patrones específicos:

### Patrón 1: Workflow DSL (`.then().branch().parallel()`)

Implementar un DSL de workflows en Python sobre el pipeline DAG existente:

```python
# Inspirado en Mastra Workflow DSL
workflow = (
    Pipeline("research-analysis")
    .then(aletheia.investigate)
    .branch(
        lambda ctx: ctx.has_images,
        {
            True: kosmos.analyze_architecture,
            False: kratos.generate_code
        }
    )
    .parallel([
        mnemosyne.compile_knowledge,
        metis.strategic_analysis
    ])
    .then(kronos.orchestrate)
)
```

### Patrón 2: Cuatro Tipos de Memoria

| Tipo | Mastra | KAOS Actual | Acción |
|------|--------|-------------|--------|
| FIFO | Últimos N mensajes | Working Memory (scratchpad FIFO) | ✅ Ya existe |
| Semantic | Embeddings + retrieval | txtai vector store | ✅ Ya existe |
| Working | Estado persistente de agente | Core Memory (task + preferences) | 🔄 Formalizar |
| Vector-based | Memoria a largo plazo | Vault L0-L3 (compile-then-query) | 🔄 Mejorar retrieval |

### Patrón 3: Sistema de Evals Evolutivo

Mastra tiene evals nativos. KAOS ya tiene DeepEval + QualityStore. La mejora es:

- **Auto-evals periódicos**: ejecutar eval suite cada N llamadas por agente.
- **Eval-driven improvement**: cuando un score baja, gatillar revisión del agente.
- **Dashboard de evolución**: tendencias de calidad por agente a lo largo del tiempo.

## Consecuencias

### Positivas
+ **Sin reescritura**: preserva ~1 año de inversión en stack Python.
+ **Patrones valiosos**: workflow DSL mejora legibilidad de pipelines.
+ **Sin riesgo de regresión**: el core de KAOS no se modifica.
+ **Reversibilidad inmediata**: cada patrón se adopta independientemente.

### Negativas
- **No hay framework unificado**: el código custom sigue siendo mantenido.
- **Workflow DSL**: implementación desde cero en Python (~2-3 semanas).
- **Evals periódicos**: overhead de cómputo (~5-10% más llamadas LLM).

### Patrones que NO se adoptan de Mastra

| Patrón | Razón |
|--------|-------|
| Serverless deploy | KAOS es un sistema desktop + CI, no web |
| MCP authoring | Ya resuelto vía Agno bridge |
| RAG integrado | Ya resuelto vía txtai + vault compile-then-query |
| TypeScript runtime | Stack Python es mandatorio para integración con Aether |

## Referencias
- Mastra: 24.6K⭐, 1.77M npm/mes, 4 tipos de memoria, workflows, evals
- ADR-018: Consolidación Aether (routing, calidad, tracking)
- ADR-012: Integración DeerFlow + Agno (MCP bidireccional)
- ADR-001: Arquitectura de Memoria (vault L0-L3)
