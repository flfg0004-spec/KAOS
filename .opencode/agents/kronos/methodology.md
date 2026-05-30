# Kronos: Methodology — The Orchestration Framework

## The Kronos Cycle (6-Step)

Cada pipeline orquestado sigue este ciclo iterativo. Un ciclo completo se ejecuta por cada "misión" o "sesión de trabajo".

### Step 1: Plan
**Propósito**: Recibir la intención de la tarea y determinar el alcance del pipeline.

**Input**: Intención del usuario o tarea delegada por otro agente.

**Actividades**:
1. Parsear la intención: ¿qué se necesita ejecutar?
2. Identificar el tipo de pipeline: `research`, `architecture`, `code_gen`, `strategy`, `memory`, `quality`, `mixed`
3. Determinar el perfil: `rapido`, `balanceado`, `critico`
4. Estimar el grafo de dependencias inicial
5. Verificar prerequisites: ¿los agentes necesarios están disponibles?

**Output**: `PipelinePlan` — documento JSON con alcance, tipo, perfil y dependencias.

### Step 2: Decompose
**Propósito**: Descomponer la tarea en unidades atómicas orquestables.

**Actividades**:
1. Descomponer la tarea en sub-tareas independientes
2. Identificar dependencias entre sub-tareas (grafo DAG)
3. Asignar cada sub-tarea al agente apropiado según SKILL:
   - `research` → Aletheia
   - `architecture` → Kosmos
   - `code` → Kratos
   - `strategy` → Metis
   - `curation` → Mnemosyne
4. Marcar tareas paralelizables (fork) y puntos de sincronización (join)
5. Identificar tareas condicionales (solo ejecutar si condición se cumple)

**Output**: `TaskDAG` — DAG de tareas con dependencias, asignaciones y tipo de paralelismo.

### Step 3: Route
**Propósito**: Resolver el routing óptimo para cada tarea — qué modelo, qué proveedor, qué cache.

**Actividades**:
1. **Model Resolution**: Para cada tarea, consultar DSOL:
   - `dsol_resolve_model(task_type, agent)` → determinar modelo óptimo
   - Considerar: costo, calidad, disponibilidad
2. **Cache Check**: Para tareas repetitivas, verificar cache (Boundary 7+13):
   - Boundary 7: Cache de 7 días para resultados de investigación que no han cambiado
   - Boundary 13: Cache de 13 ciclos para resultados de pipeline repetitivos
3. **Provider Selection**: Elegir proveedor según perfil:
   - `rapido`: Priorizar velocidad (Groq, Gemini Flash)
   - `balanceado`: Balance costo/calidad (DeepSeek Flash)
   - `critico`: Priorizar calidad (DeepSeek Pro, GPT-55)
4. **Cost Budgeting**: Verificar que la tarea no exceda el budget del perfil actual

**Output**: `RoutePlan` — plano detallado con modelo, proveedor, y estrategia de cache para cada tarea.

### Step 4: Execute
**Propósito**: Ejecutar el DAG de tareas con paralelismo controlado.

**Actividades**:
1. **Topological Sort**: Ordenar el DAG respetando dependencias
2. **Parallel Execution**: Ejecutar tareas independientes en paralelo (fork)
3. **Synchronization**: Esperar joins antes de continuar (barrier)
4. **Conditional Branches**: Evaluar condiciones en tiempo real y bifurcar según resultado
5. **Error Handling**: Aplicar política de errores en cada tarea

**Patrones de Paralelismo**:

```
FORK: Tareas A y B son independientes → ejecutar simultáneamente
JOIN: Tareas A y B deben completarse antes de C → barrier
CONDITIONAL: Si resultado de A > umbral → ejecutar B; si no → ejecutar C
RACE: Ejecutar A y B simultáneamente, usar el primer resultado disponible
SEQUENTIAL: A → B → C (sin paralelismo posible)
```

**Políticas de Error**:

| Estrategia | Cuándo usarla | Configuración default |
|------------|---------------|----------------------|
| **Retry** | Errores transitorios (timeout, rate limit) | 3 intentos, backoff exponencial (1s, 2s, 4s) |
| **Circuit Breaker** | Errores persistentes en un agente/proveedor | 5 fallos en 60s → open circuit → 30s cooldown |
| **Fallback** | Cuando un agente/proveedor no está disponible | Proveedor secundario o modelo más barato |
| **Fail-Fast** | Errores críticos donde no tiene sentido reintentar | Sin retry, error inmediato con diagnóstico |

**Output**: `ExecutionResult` — resultados de cada tarea con métricas de tiempo, éxito/fallo y metadatos.

### Step 5: Monitor
**Propósito**: Colectar métricas de la ejecución para el dashboard y la retroalimentación.

**Actividades**:
1. **Speed Metrics**: Capturar throughput, latencia por tarea, tiempo total del pipeline
2. **Error Metrics**: Registrar tasa de error, tipos de error, circuit breaker events
3. **Cost Metrics**: Tokens consumidos por modelo, costo estimado por tarea
4. **Quality Metrics**: Scores de calidad de output por agente
5. **Dashboard Update**: Actualizar visualización operacional con métricas en tiempo real

**Métricas Clave**:

| Métrica | Descripción | Target |
|---------|-------------|--------|
| Pipeline Throughput | Tareas completadas por hora | ≥ 10/hr |
| P50 Latency | Mediana de tiempo por tarea | ≤ 30s |
| Error Rate | % de tareas fallidas sobre total | ≤ 5% |
| Cache Hit Rate | % de tareas servidas de cache | ≥ 30% |
| Cost Per Pipeline | Costo estimado de API por pipeline | ≤ $0.05 |
| Time-to-Commit | Tiempo desde intención hasta commit | ≤ 5min |

**Output**: `PipelineMetrics` — JSON estructurado con todas las métricas del pipeline.

### Step 6: Learn
**Propósito**: Cerrar el ciclo de retroalimentación — mejorar el próximo Plan basado en métricas de ejecución.

**Actividades**:
1. **Anomaly Detection**: Identificar tareas con latencia o tasa de error fuera de rango
2. **Bottleneck Analysis**: ¿Qué tarea fue el cuello de botella? ¿Por qué?
3. **Routing Optimization**: ¿El modelo seleccionado fue el correcto? ¿Debe ajustarse?
4. **Cache Invalidation**: ¿Algún resultado en cache debe invalidarse?
5. **Feedback to Plan**: Las métricas alimentan el próximo ciclo de Plan:
   - Ajustar perfiles de routing
   - Actualizar umbrales de circuit breaker
   - Refinar descomposición de tareas similares

**Output**: `LearningReport` — recomendaciones para el próximo ciclo.

## Cache Strategy: Boundary 7+13

Kronos implementa un sistema de cache con dos boundaries temporales:

### Boundary 7 — Cache de Contenido (7 días)
- **Propósito**: Resultados de investigación, análisis arquitectónicos, reportes estratégicos
- **Duración**: 7 días desde la última actualización del contenido fuente
- **Invalidación**: Cuando el contenido fuente cambia (detectado por hash)
- **Uso típico**: Aletheia research results, Kosmos architecture analysis, Metis strategy reports

### Boundary 13 — Cache de Pipeline (13 ciclos)
- **Propósito**: Resultados de pipeline repetitivos, configuraciones, rutas de ejecución
- **Duración**: 13 ciclos de pipeline desde la última ejecución exitosa
- **Invalidación**: FIFO — cuando se alcanzan 13 entradas, la más antigua se elimina
- **Uso típico**: Route plans, task DAGs, model resolutions, errores conocidos

### Cache Hit/Miss Protocol
```
1. Task arrives → check Boundary 13 cache first
2. If hit and task is pipeline-level → serve from cache, skip executive
3. If miss → check Boundary 7 cache
4. If hit and content is still valid (hash match) → serve from cache
5. If miss → execute task fresh, store result in both caches
```

## Pipeline Lifecycle States

Cada pipeline pasa por estos estados, registrados en el Pipeline State:

```
CREATED → PLANNED → DECOMPOSED → ROUTED → EXECUTING → [COMPLETED | FAILED | PARTIAL] → MONITORED → LEARNED → ARCHIVED
```

| State | Descripción |
|-------|-------------|
| CREATED | Pipeline creado, aún sin planificar |
| PLANNED | Pipeline planificado, DAG inicial generado |
| DECOMPOSED | Tareas descompuestas y asignadas |
| ROUTED | Routing resuelto para todas las tareas |
| EXECUTING | Ejecución en curso |
| COMPLETED | Todas las tareas completadas exitosamente |
| FAILED | Error crítico, pipeline detenido |
| PARTIAL | Algunas tareas fallaron, otras se completaron |
| MONITORED | Métricas colectadas y registradas |
| LEARNED | Ciclo de aprendizaje completado |
| ARCHIVED | Pipeline cerrado, estado persistido |

## Pipeline State Schema

```json
{
  "pipeline_id": "uuid",
  "type": "research | architecture | code_gen | strategy | memory | quality | mixed",
  "profile": "rapido | balanceado | critico",
  "state": "CREATED | PLANNED | ... | ARCHIVED",
  "created_at": "ISO8601",
  "completed_at": "ISO8601 | null",
  "dag": {
    "tasks": [
      {
        "id": "uuid",
        "agent": "aletheia | kosmos | kratos | metis | mnemosyne",
        "type": "research | architecture | code | strategy | curation",
        "dependencies": ["task_id_1", "task_id_2"],
        "parallel_group": "group_name | null",
        "conditional": {
          "depends_on": "task_id",
          "condition": "result.value > threshold"
        },
        "status": "pending | running | completed | failed | skipped | cached"
      }
    ]
  },
  "route_plan": {
    "model_resolutions": {},
    "cache_hits": [],
    "provider_selections": {}
  },
  "execution": {
    "started_at": "ISO8601",
    "tasks_completed": 0,
    "tasks_failed": 0,
    "tasks_cached": 0,
    "total_duration_ms": 0
  },
  "metrics": {
    "throughput": 0.0,
    "p50_latency_ms": 0,
    "error_rate": 0.0,
    "cache_hit_rate": 0.0,
    "estimated_cost": 0.0
  },
  "learning": {
    "anomalies": [],
    "bottlenecks": [],
    "recommendations": []
  }
}
```

## Orchestration Templates

### Template: Research Pipeline (Aletheia → Kosmos → Metis → Mnemosyne)
```
1. Plan: Investigación multi-fuente
2. Decompose: 
   ├── Fork: Aletheia (web_search + scholar_search)
   ├── Join → Kosmos (architecture analysis)
   ├── Fork: Metis (strategy synthesis) + Kosmos (ADR generation)
   └── Join → Mnemosyne (curation + storage)
3. Route: research→DSOL, architecture→DeepSeek Pro, strategy→GPT-55
4. Execute: Parallel Aletheia, sequential Kosmos→Metis+Mnemosyne
5. Monitor: Track speed, quality scores, cache hits
6. Learn: Ajustar routing para futuras investigaciones similares
```

### Template: Code Generation Pipeline (Kratos + Kosmos + Mnemosyne)
```
1. Plan: Feature development con code review
2. Decompose:
   ├── Fork: Kratos (code_gen) + Kosmos (architecture validation)
   ├── Join → Kratos (code_review + test_gen)
   └── Mnemosyne (memory capture of new code experience)
3. Route: code→DeepSeek Flash, architecture→DeepSeek Pro
4. Execute: Parallel generation + validation, sequential review
5. Monitor: Time-to-commit, test pass rate
6. Learn: Actualizar CodeExperience con nuevos patrones
```

### Template: Quality Audit Pipeline (Cross-Agent)
```
1. Plan: Auditar calidad de outputs recientes
2. Decompose:
   ├── Aletheia: verificar fuentes de últimas 5 investigaciones
   ├── Kosmos: verificar ADRs contra código implementado
   ├── Metis: Quality Orchestrator mode → verificación cruzada
   └── Mnemosyne: health check del vault
3. Route: Cada tarea al modelo más barato que cumpla requisitos
4. Execute: Todas en paralelo
5. Monitor: Dashboard de calidad, alertas si scores bajan de umbral
6. Learn: Identificar patrones de degradación de calidad
```

## Error Recovery Matrix

| Error | Detección | Acción Inmediata | Escalamiento |
|-------|-----------|-----------------|--------------|
| Timeout en tarea | Latencia > 3σ de baseline | Retry con backoff (1s, 2s, 4s) | Si 3 retrys fallan → fallback a otro proveedor |
| Rate limit | HTTP 429 / MCP error | Retry con backoff + jitter | Si persiste > 60s → circuit breaker |
| Model unavailable | DSOL retorna error | Fallback al siguiente mejor modelo | Reportar a dashboard |
| Agent unavailable | MCP connection error | Reintentar conexión 3 veces | Si persiste → abortar pipeline, notificar |
| Corrupt data | Validation schema fails | Re-ejecutar tarea fresh (no cache) | Si persiste → marcar como FAILED con diagnóstico |
| Circuit breaker open | CB monitorea tasa de error > 30% | No ejecutar tareas en ese agente/proveedor por 30s | Si persiste > 3 ciclos → escalar a Metis |
| Partial failure | Algunas tareas fallaron, otras no | Continuar con tareas independientes | Reportar en results y learning |
