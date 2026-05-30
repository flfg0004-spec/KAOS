---
status: Aceptado
date: 2026-05-30
authors: Kosmos (Arquitectura), Kratos (Implementación), Metis (Estrategia)
historial:
  - 2026-05-30: ADR-011 creado — Kratos 2.0 Production Pipeline
  - 2026-05-01: ADR-009 actualizado — Kratos 2.0 Alpha fundacional
  - 2026-04-15: ADR-009 creado — Arquitectura base Kratos con PRGII y RSCB-MC
---

# ADR-011: Kratos 2.0 Production — Pipeline Paralelo Multi-Lenguaje con Feature Flags

## Contexto

Kratos v1 (desplegado desde ADR-009, Abril 2026) probó la arquitectura PRGII con memoria experiencial (CodeExperience, RSCB-MC, sqlite-vec) y estableció el pipeline base de 7 quality gates secuenciales. La implementación actual corre en producción con 66 tests, 0 regresiones, y un score compuesto de calidad de 7.8/10. Sin embargo, el análisis arquitectónico reveló 11 items de deuda técnica (17h estimadas) y 3 riesgos estructurales que bloquean la evolución a multi-lenguaje (Rust/TypeScript/Go).

El pipeline secuencial `evaluate()` ejecuta 8 gates Python en serie (~3-5s por invocación), duplicado en `evaluate_parallel()` (~1-2s con 4 workers). El CircuitBreaker es global (instancia única en `_KRATOS_CIRCUIT_BREAKER`) sin namespacing por operación. Los 17 feature flags existen sin convención de namespacing (mezclan `snake_case` con `use_` inconsistente). Y la función `_kratos_node_v2()` es un stub `NotImplementedError` — la arquitectura prometida de pipeline paralelo v2 no existe.

Metis diseñó el plan estratégico-táctico H3 con 8 semanas divididas en 4 tracks paralelos: Core Pipeline con self-healing (H3-A, 3 semanas), Technical Debt con refactor de gates y namespacing (H3-B, 2 semanas), MCP Server + Streaming (H3-C, 3 semanas), y Dashboard + Auto-evolution (H3-D, 3 semanas). Este ADR formaliza la arquitectura objetivo para Kratos 2.0 Production, documenta el estado actual de cada componente, y establece los criterios GO/NO-GO para el flip v1→v2.

Este ADR no reemplaza ADR-009 — lo extiende. ADR-009 describe la arquitectura del agente (memoria experiencial, PRGII, RSCB-MC). Este ADR describe el pipeline de calidad, el sistema de feature flags, la telemetría, los contratos cross-agent, y el plan de migración v1→v2.

## Decisión

### Principios arquitectónicos

1. **Strangler Fig pattern** — pipeline híbrido v1/v2 conviviendo durante 8 semanas. `kratos_node()` delega a `_kratos_node_impl` (v1) por defecto (flag `use_new_agent_executor` = false). Cuando se flipa a true, `_kratos_node_v2()` activa el pipeline paralelo multi-lenguaje.

2. **Feature flags para todo** — granularidad máxima: cada nuevo componente, gate, lenguaje, y comportamiento tiene su propio flag con default false. El pipeline completo puede operar sin cambios en prod hasta que cada flag se flipa individualmente.

3. **Default false, zero impacto** — toda funcionalidad nueva nace desactivada. Un deploy de Kratos 2.0 Production en un entorno existente produce exactamente el mismo comportamiento que antes de deployar.

4. **Backward compatibility** — `KratosDecision` hereda de `str` para que `"complete" == KratosDecision.COMPLETE` sea verdadero. La serialización JSON produce strings planos. Todos los consumidores existentes (orquestador, dashboard, Mnemosyne) funcionan sin cambios.

5. **Nunca crashear** — todos los gates, bridges, y procesos están envueltos en `try/except` con score neutral (5.0/10) como fallback. Una excepción en un gate multi-lang no detiene el pipeline.

### Componentes del sistema

| Componente | Archivo | Propósito | Feature Flag |
|---|---|---|---|
| **Kratos node (router)** | `lib/agent_nodes/kratos.py` | Router v1/v2 según flag | `use_new_agent_executor` |
| **Kratos v1 impl** | `lib/agent_nodes/kratos.py` `_kratos_node_impl()` | Pipeline PRGII legacy (314 líneas) | — (default) |
| **Kratos v2 stub** | `lib/agent_nodes/kratos.py` `_kratos_node_v2()` | `NotImplementedError` hasta H3-A | `use_new_agent_executor` |
| **Quality gates** | `lib/quality_gate.py` | 8 gates Python + 3 multi-lang × 3 lenguajes (612 líneas) | `use_kratos_v2` |
| **Parallel executor** | `lib/quality_gate.py` `evaluate_parallel()` | ThreadPoolExecutor con max_workers=4 | `use_parallel_gates` |
| **Early exit** | `lib/quality_gate.py` (en evaluate_parallel) | Cortocircuito si syntax falla | `use_early_exit` |
| **Multi-lang syntax** | `lib/quality_gate.py` `gate_syntax_multi()` | tree-sitter para Rust/TS/Go | `use_rust_gates`, `use_ts_gates`, `use_go_gates` |
| **Multi-lang compilation** | `lib/quality_gate.py` `gate_compilation_multi()` | rustc/tsc/go vet sobre tempfiles | `use_rust_gates`, `use_ts_gates`, `use_go_gates` |
| **Multi-lang lint** | `lib/quality_gate.py` `gate_lint_multi()` | clippy/eslint/golint sobre tempfiles | `use_rust_gates`, `use_ts_gates`, `use_go_gates` |
| **Real coverage** | `lib/quality_gate.py` `gate_coverage()` | pytest --cov cuando flag activo | `use_real_coverage` |
| **Real mypy** | `lib/quality_gate.py` `gate_types()` | mypy --strict cuando flag activo | `use_real_mypy` |
| **KratosDecision** | `lib/kratos_decision.py` | Enum str-heritable (5 valores, 37 líneas) | — (siempre activo) |
| **Telemetría** | `lib/kratos_telemetry.py` | CSV con file-locking + CircuitBreaker (239 líneas) | `use_kratos_telemetry` |
| **Circuit Breaker** | `lib/kratos_telemetry.py` | 3-failure threshold, 300s recovery | `use_circuit_breaker` |
| **Dashboard** | `lib/kratos_dashboard.py` | Widget CLI (52 líneas) | — (sin flag) |
| **Contrato Metis→Kratos** | `lib/kratos_contract.py` | TypedDict con 5+ campos nuevos (67 líneas) | — (siempre activo) |
| **Feature flags** | `lib/feature_flags.py` | 17 flags Kratos + 17 flags sistema (127 líneas) | — (core) |
| **Bash hook** | `lib/kratos_hook.py` | Captura de errores vía monkey-patch CodeMemory | — (opt-in context manager) |
| **OPA bridge** | `lib/opa_bridge.py` | Governance check en post-processing | — (fallback abierto) |
| **Agent executor** | `lib/agent_executor.py` | Delegación a kratos_node canónico | — (siempre) |

### Feature flags

| Flag | Default | Grupo | Creado | Descripción |
|---|---|---|---|---|
| `use_kratos_v2` | false | H3-A | Alpha | Activa el pipeline v2 completo |
| `use_kratos_telemetry` | false | H3-A | Alpha | Graba invocaciones a CSV |
| `use_real_coverage` | false | H3-C | Alpha | pytest --cov real |
| `use_real_mypy` | false | H3-C | Alpha | mypy --strict real |
| `use_parallel_gates` | false | H3-B | Alpha | ThreadPoolExecutor en gates |
| `use_early_exit` | false | H3-B | Alpha | Cortocircuito en syntax fail |
| `use_circuit_breaker` | false | H3-A | Alpha | CircuitBreaker en LLM critic |
| `use_rust_gates` | false | H3-D | Alpha | Gates para Rust |
| `use_ts_gates` | false | H3-D | Alpha | Gates para TypeScript |
| `use_go_gates` | false | H3-D | Alpha | Gates para Go |
| `use_new_agent_executor` | false | H3-A | Alpha | Router v1→v2 |
| `use_knowledge_tour` | true | Sistema | — | Tour de conocimiento |
| `use_incremental_analysis` | true | Sistema | — | Análisis incremental |
| `use_enhanced_parallelism` | true | Sistema | — | Paralelismo mejorado |
| `use_unified_circuit_breaker` | false | Sistema | — | CircuitBreaker unificado |
| `use_dag_verification` | false | Sistema | — | Verificación DAG |
| `use_event_coordination` | false | Sistema | — | Coordinación de eventos |
| `use_new_quality_engine` | false | Sistema | — | Motor de calidad v2 |
| `use_domain_mapper` | true | Sistema | — | Mapeo de dominio |
| `use_markmap_mindmaps` | true | Sistema | — | Mapas mentales |
| `use_kroki_diagrams` | true | Sistema | — | Diagramas Kroki |
| `use_plotly_dashboard` | true | Sistema | — | Dashboard Plotly |
| `use_cytoscape_graph` | true | Sistema | — | Grafos Cytoscape |
| `use_pdf_reports` | true | Sistema | — | Reportes PDF |
| `use_knowledge_scorer` | true | Sistema | — | Scorer de conocimiento |
| `use_knowledge_synthesis` | true | Sistema | — | Síntesis de conocimiento |
| `use_curation_pipeline` | true | Sistema | — | Pipeline de curación |

*Nota:* Los flags del sistema existen en `DEFAULT_FLAGS` pero son gestionados por otros equipos. Kratos solo gestiona los 11 flags del grupo Kratos.

### Pipeline flow (Strangler Fig)

```
state → kratos_node(state)
         │
         ├─ use_new_agent_executor = false ──→ _kratos_node_impl(state) [v1]
         │                                      │
         │                                      ├─ LLM Direct = true  → PRGII loop
         │                                      └─ LLM Direct = false → prompt dump
         │
         └─ use_new_agent_executor = true ───→ _kratos_node_v2(state) [v2]
                                                  │
                                                  └─ (H3-A) Parallel pipeline
                                                       │
                                                       ├─ quality_gate.evaluate_parallel()
                                                       │   ├─ use_parallel_gates → ThreadPoolExecutor
                                                       │   ├─ use_early_exit → cortocircuito syntax
                                                       │   └─ use_rust/ts/go_gates → multi-lang routing
                                                       │
                                                       ├─ kratos_telemetry.record_invocation()
                                                       │   └─ use_circuit_breaker → LLM critic protegido
                                                       │
                                                       ├─ kratos_contract.validate_metis_to_kratos()
                                                       │
                                                       └─ kratos_dashboard.render_dashboard()
```

### Criterios de routing multi-lenguaje

El pipeline actual detecta el lenguaje vía `lib/lang_utils.detect_code_language()` y enruta a uno de dos sub-pipelines:

1. **Python** (8 gates): `syntax → compilation → lint → types → structure → security → coverage → style`, con pesos composición. Si syntax falla, se ejecuta early exit con todos los gates pero score fallido.

2. **Rust/TypeScript/Go** (3 gates): `syntax_multi → compilation_multi → lint_multi`. Score compuesto es promedio simple. Cada gate verifica su flag de lenguaje (`use_rust_gates`, `use_ts_gates`, `use_go_gates`) y el toolchain disponible — si no encuentra el tool, retorna score neutral (5.0).

## Consecuencias

### Positivas

1. **66 tests, 0 regresiones** — el suite completo pasa sin cambios tras deploy de la arquitectura. Ningún test existente requirió modificación.

2. **Rollback granular <30s** — cada componente tiene su feature flag. Si el pipeline paralelo v2 falla, se flipea `use_new_agent_executor` a false y se restaura el comportamiento v1 inmediatamente. Sin redeploy, sin code revert.

3. **Multi-lenguaje ready** — Rust/TypeScript/Go tienen gates de syntax, compilation y lint con toolchain detection. Para activarlos en un entorno, solo se flipean `use_rust_gates`, `use_ts_gates`, `use_go_gates`.

4. **CircuitBreaker protege LLM critic** — el critic review (agente LLM que revisa el código generado) está envuelto en `_KRATOS_CIRCUIT_BREAKER` con threshold de 3 fallos y recovery de 300s. Si el modelo critic falla repetidamente, el circuito se abre y el pipeline continúa sin critic review (graceful degradation).

5. **Telemetría con file-locking** — `record_invocation()` usa `file_lock.py` (portalocker) para escritura thread-safe a CSV. La telemetría incluye timestamp, decisión, quality score, lenguaje, flags activos, duración e iteración.

6. **Backward compatibility vía herencia de str** — `KratosDecision(str, Enum)` permite que los consumidores existentes (orquestador en LangGraph, Mnemosyne, dashboard) comparen contra strings planos sin cambios.

7. **Contratos cross-agent robustos** — `MetisToKratos` y `AletheiaToKratos` tienen `validate_*()` functions que nunca crashean. Si reciben un string en vez de dict, retornan defaults seguros.

### Negativas

1. **17+ flags = complejidad de configuración** — cada nuevo desarrollador debe entender el sistema de flags para saber por qué un componente no se activa. La matriz de combinaciones posibles es 2^17 (~131K) — aunque en la práctica solo 4 combinaciones son relevantes (dev, staging, prod-canary, prod-full).

2. **Deuda técnica v1 no se paga hasta flip v2** — el pipeline secuencial v1 (`_kratos_node_impl`) mantiene código legacy: 80 líneas duplicadas entre `evaluate()` y `evaluate_parallel()`, `gate_coverage()` que no mide coverage real cuando `use_real_coverage` es false, y `gate_syntax_multi()` que no verifica el feature flag antes de ejecutarse.

3. **`_kratos_node_v2` es NotImplementedError** — hasta H3-A (semana 3), el flag `use_new_agent_executor` no se puede activar porque no hay implementación v2 real.

4. **`evaluate_parallel()` duplica `evaluate()`** — del análisis arquitectónico: 80 líneas de lógica duplicada entre los dos métodos. La función `evaluate_parallel()` reimplementa el flujo completo en vez de paralelizar `evaluate()`.

5. **CircuitBreaker global** — la instancia `_KRATOS_CIRCUIT_BREAKER` es singleton a nivel de módulo. No hay CircuitBreaker por operación (syntax/lint/types/compilation tienen el mismo breaker global). Esto significa que un fallo en syntax abre el circuito para todos.

6. **Dashboard sin feature flag** — `kratos_dashboard.py` se importa directamente sin verificar flag. En entornos donde la telemetría está desactivada, el dashboard muestra datos vacíos.

### Riesgos

| Riesgo | Probabilidad | Impacto | Mitigación |
|---|---|---|---|
| **Strangler Fig muy largo** — v1/v2 conviven 8 semanas, duplicando mantenimiento | Media | Alto | CI/CD automatiza deploy de flags. H3-A prioriza Core Pipeline. Si en semana 4 no hay avance suficiente, se corta alcance de H3-C/D |
| **17 flags nunca se flipean** — equipos olvidan activar flags y el sistema opera en modo "default false" indefinidamente | Alta | Medio | Metis programa OKRs de flip por sprint. Dashboard muestra % de flags activos. Koans verifica que flags sin usar se reporten semanalmente |
| **Multi-lang gates sin toolchain** — rustc/tsc/go no instalados en CI, gates retornan score neutral y el multi-lang testing es ineficaz | Alta | Medio | `_detect_toolchain()` retorna neutral si tool no existe. CI template (`ci-multi-lang.yml`) instala toolchains condicionalmente vía feature flags |
| **OPA governance fail-open** — si OPA server no responde, governance retorna `{"allowed": True}` por defecto (fail-open en vez de fail-closed) | Baja | Alto | ADR-003 documenta esta decisión explícita: en desarrollo, fail-open permite iterar sin OPA. En producción, fail-open es riesgo de seguridad. Mitigación: entorno staging activa OPA validation pre-deploy |

## Alternativas consideradas

| Alternativa | Razón para rechazar |
|---|---|
| **Rewrite completo v2 en una rama** (sin Strangler Fig) | Riesgo de big-bang deployment. Sin rollback granular. Forzaba a parar desarrollo durante 8 semanas. |
| **Feature flags como variables de entorno únicamente** | Sin namespacing, 17 flags en un solo JSON env son imposibles de gestionar. Sin jerarquía, no se puede activar "todos los flags de multi-lang" con una sola variable. |
| **Un solo pipeline para todos los lenguajes** | Python, Rust, TS y Go tienen paradigmas de lint/compi distintos. Un pipeline genérico sería demasiado abstracto y frágil (como `evaluate()` que mezcla Python con multi-lang en un solo if/else). |
| **Reemplazar file-locking con SQLite para telemetría** | Más robusto pero añade dependencia (sqlite3 para telemetría) y complejidad de schema. CSV con file-locking es suficiente para <1000 invocaciones/día (volumen esperado de Kratos). |
| **CircuitBreaker con Redis** | Global. La telemetría es local al proceso. Redis añade latencia innecesaria para un breaker que protege una sola instancia. |
| **Pausar deuda técnica y construir v2 desde cero** | La deuda técnica (17h estimadas) es manejable. Ignorarla ahora significaría arrastrarla a v2 y multiplicarla cuando el pipeline paralelo se active. H3-B la aborda explícitamente. |

## Plan de implementación H3

### H3-A: Core Pipeline + Self-Healing [3 semanas, S1-S3]

| Semana | Entregable | Dependencias |
|---|---|---|
| S1 | `_kratos_node_v2()` implementado con pipeline paralelo real | Feature flags existentes |
| S2 | Self-healing: CircuitBreaker por operación (syntax/lint/types), retry con backoff | S1 |
| S3 | Telemetría en tiempo real + auto-reporte de salud del pipeline | S2 |

**Costos estimados:**
- S1: 6h (implementación pipeline paralelo)
- S2: 4h (CircuitBreaker namespaced + retry)
- S3: 3h (telemetría real-time + health report)

**Criterio de éxito:** `evaluate(content)` en paralelo completa en <1.2s promedio (vs ~3.5s secuencial).

### H3-B: Technical Debt [2 semanas, S4-S5]

| Semana | Entregable | Items de deuda |
|---|---|---|
| S4 | Refactor gates + namespacing de flags | Items #1, #2, #3, #5, #7, #8, #11 |
| S5 | Tests multi-lang + caching | Items #4, #6, #9, #10 |

**Items de deuda a resolver:**
1. CircuitBreaker global → namespaced (4h)
2. 50 flags sin namespacing → kratos_* prefijo (3h)
3. 80 líneas duplicadas evaluate/evaluate_parallel → DRY (2h)
4. OPA governance fail-open → fail-closed configurable (2h)
5. `gate_coverage` real no mide coverage real → fix (2h)
6. `gate_syntax_multi` no verifica feature flag → fix (1h)
7. Early exit corre syntax secuencialmente → paralelo (1h)
8. `record()` acepta decision pero no la usa → fix (1h)
9. `_detect_toolchain()` sin cache → memoize (0.5h)
10. Tests faltantes gate_lint_multi TS/Go → add (0.5h)
11. Dashboard sin feature flag → add (0.25h)

**Criterio de éxito:** Health score sube de 7.8 a ≥8.5. Deuda técnica < 5 items restantes.

### H3-C: MCP Server + Streaming [3 semanas, S6-S8]

| Semana | Entregable | Dependencias |
|---|---|---|
| S6 | MCP server para quality_gate (gates como herramientas remotas) | H3-B |
| S7 | Streaming de resultados de gates (sse/mcp streaming) | S6 |
| S8 | Integración con el dashboard en tiempo real | S7, H3-D dashboard |

**Criterio de éxito:** MCP server responde a `tools/call` para cada gate en <200ms.

### H3-D: Dashboard + Auto-evolution [3 semanas, S6-S8, paralelo a H3-C]

| Semana | Entregable | Dependencias |
|---|---|---|
| S6 | Dashboard CLI con feature flag + métricas en tiempo real | H3-B (namespacing) |
| S7 | Auto-evolution: Kratos modifica sus propios gates vía quality score feedback | H3-A (pipeline) |
| S8 | Reportes de evolución + closed-loop: el dashboard recomienda flips de flags | S7 |

**Criterio de éxito:** Dashboard reporta salud del pipeline + últimas 10 invocaciones en <50ms.

## Criterios GO/NO-GO para flip v2

El flip de `use_new_agent_executor` a true (activar pipeline v2 en producción) requiere **todos** los siguientes criterios:

| # | Criterio | Medición | Target |
|---|---|---|---|
| 1 | `_kratos_node_v2()` implementado | `py -3 -c "from lib.agent_nodes.kratos import _kratos_node_v2; assert callable(_kratos_node_v2)"` | No lanza `NotImplementedError` |
| 2 | Pipeline paralelo funcional | Test end-to-end con `use_new_agent_executor=true` | `evaluate_parallel()` completa 8 gates Python en <1.2s |
| 3 | Multi-lang operativo | Tests multi-lang con flags activos | `evaluate("fn main(){}", language="rust")` retorna composite real |
| 4 | Telemetría funcional | `record_invocation()` con flag activo | Archivo CSV se crea y `telemetry_summary()` retorna datos correctos |
| 5 | CircuitBreaker por operación | Stress test: 10 fallos consecutivos en lint | Sólo lint se abre, otros gates continúan |
| 6 | Health score ≥ 8.5 | Depwire health score | Composite ≥ 8.5/10 |
| 7 | Deuda técnica ≤ 5 items | Depwire debt inventory | Sólo items menores restantes |
| 8 | 66 tests + 0 regresiones | `py -3 -m pytest .memory/_scripts/tests/ -v --no-header` | 66 passed, 0 failed |
| 9 | Rollback probado | Flip flag a false en staging | Comportamiento idéntico a pre-deploy |
| 10 | Dashboard operativo | `show_dashboard()` en entorno con telemetría | Muestra datos sin errores |

**Proceso GO:** Metis valida checklist → Kosmos firma ADR amend → Kratos flipa flag en staging → 48h canary → flip en producción.

**Proceso NO-GO:** Cualquier criterio rojo → Kosmos documenta gap en ADR amend → Metis ajusta plan H3 → próxima evaluación en 2 semanas.

## Deuda técnica aceptada (para H3-B)

| # | Item | Archivo | Esfuerzo | Prioridad | H3 Track |
|---|---|---|---|---|---|
| 1 | CircuitBreaker global — instancia única compartida | `kratos.py` línea 26 | 4h | Crítica | H3-B S4 |
| 2 | 50 flags sin namespacing consistente | `feature_flags.py` | 3h | Alta | H3-B S4 |
| 3 | 80 líneas duplicadas evaluate/evaluate_parallel | `quality_gate.py` | 2h | Alta | H3-B S4 |
| 4 | OPA governance fail-open (no verifica servidor) | `kratos.py` línea 42-47 | 2h | Media | H3-B S5 |
| 5 | gate_coverage real no ejecuta pytest --cov correctamente | `quality_gate.py` línea 210-240 | 2h | Media | H3-B S4 |
| 6 | gate_syntax_multi no verifica feature flag primero | `quality_gate.py` línea 243-265 | 1h | Media | H3-B S5 |
| 7 | Early exit corre syntax secuencialmente en evaluate_parallel | `quality_gate.py` línea 453-479 | 1h | Baja | H3-B S4 |
| 8 | record_invocation() acepta parámetro decision pero no lo registra en flags_active | `kratos_telemetry.py` línea 134-168 | 1h | Baja | H3-B S4 |
| 9 | _detect_toolchain() ejecuta shutil.which() sin cache | `quality_gate.py` línea 31-33 | 0.5h | Baja | H3-B S5 |
| 10 | Faltan tests para gate_lint_multi en TypeScript y Go | `tests/test_kratos_e2e.py` | 0.5h | Baja | H3-B S5 |
| 11 | Dashboard no tiene feature flag de protección | `kratos_dashboard.py` | 0.25h | Baja | H3-B S4 |

**Total estimado:** 17 horas

## Referencias

- ADR-009: Arquitectura del Code Agent Kratos (PRGII, RSCB-MC, CodeExperience, sqlite-vec)
- ADR-003: Zonas de Autonomía y Protocolo de Verificación (OPA fail-open governance)
- ADR-002: Sistema de Scores (Calidad y Veracidad)
- [Fowler 2004] Strangler Fig Application pattern — martinfowler.com/bliki/StranglerFigApplication.html
- [Nygard 2018] Circuit Breaker pattern — Release It! 2nd Edition (Pragmatic Programmers)
- [Humble & Farley 2010] Feature Toggles — Continuous Delivery (Addison-Wesley)
- [KAOS Internal] H3 Strategic-Tactical Plan (Metis, 2026-05-28)
- [KAOS Internal] Kratos 2.0 Alpha Analysis (Kosmos, 2026-05-25) — score 7.8/10, 11 debt items
- [KAOS Internal] Depwire health score: `py -3 .tools/depwire.py .memory/_scripts/lib/` (score compuesto 7.8)
