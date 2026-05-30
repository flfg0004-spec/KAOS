# ADR-019: Quality Testing Strategy

## Estado
Aceptado

## Contexto
KAOS comenzó con solo 10 tests (Aletheia integration). Tras la implementación de FEVER Benchmark y E2E Router→Score Store, ahora cuenta con 32 tests efectivos en 3 suites. Es necesario formalizar la estrategia de testing para garantizar calidad reproducible.

Datos actuales:
- **Aletheia Integration** (`test_aletheia_integration.py`): 10 tests — validación de pipeline de investigación, prompts, salidas, score store
- **FEVER Benchmark** (`test_fever_benchmark.py`): 17 claims parametrizadas + 1 test de reporte — verificación factual contra vault wiki con FEVER Score ≥ 0.70
- **E2E Router→Score** (`test_e2e_router_score.py`): 4 tests — integración crítica entre router de Aletheia y score store persistente
- **Total**: 32 checks, todos pasando. FEVER Score actual: 0.71 (12 verified / 17 claims)

## Decisión
Adoptar una estrategia de testing en 3 capas:

### Capa 1: Tests Unitarios
- Pruebas de módulos individuales (agent_tools, score_store, validación)
- Sin dependencias externas (monkey-patch DB_PATH, mock HTTP calls)
- Cobertura: funciones puras, validación de formato, edge cases

### Capa 2: Tests de Integración
- Pipeline Aletheia → `validate_aletheia_output` → score_store save
- Router con tópicos vacíos, outputs malformados, secciones faltantes
- Verificación de persistencia (history, average)
- Tests existentes: `test_aletheia_integration.py` (10 tests) + `test_e2e_router_score.py` (4 tests)

### Capa 3: Benchmark Factual (FEVER)
- Verificación de claims contra el ground truth del vault wiki
- Score mínimo: 0.70 (FEVER Score = verified / total)
- 17 claims actuales cubriendo: Hermes Agent (5), Kanban (2), Router (1), Agentes (3), Qualidad (1), Cron (1), API Server (1), ntfy (1), Webhook (1), WhatsApp (1)
- Herramientas: regex con `re.IGNORECASE | re.MULTILINE` para FEVER v1
- A futuro: `sentence-transformers` para FEVER v2 (matching semántico)

## Estrategia de Aislamiento
- **DB_PATH**: monkey-patched con `tempfile.mkdtemp()` en cada test E2E (fixture autouse)
- **sys.exit()**: EVITAR en módulos bajo test — usar return codes o excepciones
- **sys.path**: `insert(0, ..)` al inicio de cada test file para resolución de imports
- **Variables de entorno**: `KAOS_TESTING=1`, `LLM_DIRECT_ENABLED=false` en tests de integración

## Tests Existentes

### test_aletheia_integration.py (10 tests)

Verifica el pipeline completo de Aletheia: desde la construcción del prompt hasta la persistencia de scores.

| # | Test | Propósito |
|---|------|-----------|
| 1 | `test_aletheia_node_returns_dict` | `aletheia_node()` retorna dict con claves `aletheia_output` y `aletheia_prompt` |
| 2 | `test_aletheia_prompt_contains_topic` | El prompt generado incluye el topic específico pasado en el estado |
| 3 | `test_aletheia_prompt_has_methodology` | El prompt contiene "research" o "investigación" indicando metodología |
| 4 | `test_aletheia_empty_topic` | Topic vacío no crasha — retorna output aunque sea mínimo |
| 5 | `test_validation_good_output` | Output con 5 secciones (Resumen, Hallazgos, Análisis, Conclusiones, Recomendaciones) + fuentes → `valid=True`, score ≥ 0.6 |
| 6 | `test_validation_empty_output` | Output vacío → `valid=False`, score = 0.0 |
| 7 | `test_validation_no_sources` | Output sin URLs ni wikilinks → `valid=False`, warning "Sin URLs de fuentes" |
| 8 | `test_validation_missing_sections` | Output con solo 1 sección → `valid=False`, ≥ 3 secciones faltantes |
| 9 | `test_validation_minimal_pass` | Output mínimo con las 5 secciones y contenido suficiente → pasa con score ≥ 0.6 |
| 10 | `test_validation_persists_score` | Validación con topic persiste el score en el store — history crece después de validar |

### test_fever_benchmark.py (17 claims + 1 report)

Mide la verificabilidad factual del vault wiki. Cada claim se parametriza como tupla `(claim, expected_score, source_pattern, description)` y se evalúa contra todo el vault. Incluye un test de reporte agregado que calcula el FEVER Score global.

| ID | Claim | Esperado | Real (vault) | Patrón |
|----|-------|----------|--------------|--------|
| GW-01 | Hermes Agent v0.15.2 corre en puerto 8642 | 1.0 | Verificado | `gateway.*8642` |
| GW-02 | El dashboard de Hermes corre en puerto 9119 | 1.0 | Verificado | `dashboard.*9119` |
| GW-03 | Hermes Agent usa MiMo como proveedor primario | 1.0 | Verificado | `primary.*MiMo\|mimo-v2\.5-pro` |
| GW-04 | Hermes Agent usa DeepSeek como proveedor primario | 0.5 | Insuficiente — vault no permite refutar vía regex | `primary.*MiMo\|mimo-v2\.5-pro` |
| GW-05 | El gateway timeout de Hermes es 300 segundos | 0.5 | Insuficiente — timeout config está en config.yaml, no en vault wiki | `gateway_timeout.*1800` |
| KN-01 | Hermes Agent incluye kanban dispatch como feature | 1.0 | Verificado | `kanban.*dispatch\|kanban_dispatch` |
| KN-02 | Kanban dispatcher tiene fallback a cola local JSON | 1.0 | Verificado | `Cola local JSON\|cola.*local` |
| RT-01 | Hermes Router tiene fallback a Telegram API directa | 1.0 | Verificado | `Router fallback\|fallback.*Telegram` |
| AG-01 | Aletheia, Kosmos y Metis son agentes del ecosistema KAOS | 1.0 | Verificado | `Aletheia\|Kosmos\|Metis` |
| AG-02 | Aletheia no puede editar archivos (edit: deny) | 1.0 | Verificado | `Aletheia.*edit.*deny\|edit deny` |
| AG-03 | Kosmos tiene acceso al MCP exa-search | 0.5 | Insuficiente — ausencia no es refutación vía regex | `Kosmos.*exa-search` |
| QL-01 | El score de calidad del sistema KAOS es 76.8/100 | 1.0 | Verificado | `Score actual.*76\.8\|76\.8/100` |
| CR-01 | KAOS utiliza Windows Task Scheduler para tareas programadas | 1.0 | Verificado | `Task Scheduler\|install_schedule` |
| AP-01 | Hermes Agent sirve como API server de mensajería | 1.0 | Verificado | `gateway.*mensajería` |
| NT-01 | KAOS usa ntfy.sh para notificaciones push | 0.5 | Insuficiente — sin referencia directa en vault wiki | `ntfy\|ntfy\.sh` |
| WH-01 | KAOS usa webhooks para comunicación bidireccional | 1.0 | Verificado | `webhook` |
| WA-01 | KAOS tiene un bridge de WhatsApp para mensajería entrante | 0.5 | Insuficiente — sin referencia en vault wiki | `whatsapp\|baileys` |

**FEVER Score actual**: 12/17 = **0.71** (12 verified, 0 refuted, 5 insufficient). Vault: 80+ archivos `.md`.

El test `test_fever_report()` calcula el score global: recorre todos los claims, clasifica en verified/refuted/insufficient, y asegura que `fever_score >= 0.70`. Falla si el vault queda desactualizado respecto a las features implementadas.

### test_e2e_router_score.py (4 tests)

Valida el flujo crítico de integración: `validate_aletheia_output()` → score store persistente con base de datos aislada.

| # | Test | Propósito |
|---|------|-----------|
| 1 | `test_validate_good_output` | Output bien formado (5 secciones + fuentes) → `valid=True`, score ≥ 0.8 |
| 2 | `test_validate_bad_output` | Output incompleto (solo 1 sección, sin fuentes) → `valid=False`, score < 0.5 |
| 3 | `test_score_store_save_and_retrieve` | Guarda score via `store.save()` y lo recupera con `store.history()` — verifica `topic`, `valid`, `score` |
| 4 | `test_e2e_full_flow` | Flujo completo: validar → guardar → recuperar por topic → verificar `average(days=30) > 0.0` |

**Aislamiento**: fixture autouse `_patch_db_path` crea `tempfile.mkdtemp()` y reemplaza `store.DB_PATH` con un archivo temporal `test.db`. El directorio se elimina con `shutil.rmtree()` al finalizar cada test.

## Tests Futuros Planificados

| Agente | Tipo | Prioridad |
|--------|------|-----------|
| Kosmos | Unitario + Integración | P1 |
| Kratos | CodeExperience + ciclos PRGII | P2 |
| Metis | OKR validation + strategy coherence | P2 |
| Mnemosyne | Curation pipeline + vault quality | P3 |
| Kronos | Pipeline recovery + error routing | P3 |

## Herramientas
- **pytest** (v9.x) — test runner con plugins: cov, xdist, rerunfailures, repeat, asyncio, langsmith
- **regex** — FEVER v1: matching literal con `re.IGNORECASE | re.MULTILINE`
- **sentence-transformers** — FEVER v2 (planificado): embeddings semánticos + cosine similarity
- **monkeypatch / pytest fixtures** — aislamiento de DB_PATH, variables de entorno
- **tempfile / shutil** — limpieza de BD temporales post-test

## Consecuencias

### Positivas
+ FEVER Score asegura que el vault wiki está sincronizado con las features implementadas
+ Tests E2E verifican el flujo crítico Router→Score sin necesidad de Hermes Gateway
+ Aislamiento de base de datos evita contaminación entre tests y producción
+ 3 capas permiten identificar rápidamente si un fallo es unitario, de integración o de benchmark
+ 17 claims FEVER cubren todos los agentes visibles del ecosistema

### Negativas
- FEVER v1 con regex es frágil — cambios de formato en vault pueden romper tests sin cambio real de veracidad
- Sin sentence-transformers aún, no hay matching semántico contra afirmaciones parafraseadas (GW-04, GW-05, AG-03 son claims "insuficientes" por límite del regex)
- Los tests E2E requieren estructura de secciones específica en el output de Aletheia

### Riesgos y Mitigaciones

| Riesgo | Probabilidad | Impacto | Mitigación |
|--------|-------------|---------|------------|
| FEVER regex fragile | Alta | Bajo | Migrar a sentence-transformers en v2 |
| DB_PATH leaks | Baja | Alto | Fixture autouse con tmpdir + cleanup |
| Tests lentos | Media | Medio | pytest-xdist para paralelización |
| Dependencia de vault | Alta | Medio | FEVER 0.7 absorbe cambios menores; threshold al 70% da margen |

## Alternativas Consideradas

### Alternativa A: Solo tests unitarios (sin FEVER ni E2E)
- ❌ Sin verificación factual del vault wiki
- ❌ Sin validación del flujo Router→Score Store
- ❌ Sin detección de desincronización entre docs y features
- ✅ Tests más rápidos, sin dependencia del vault

### Alternativa B: FEVER v2 desde el inicio (sentence-transformers)
- ❌ Dependencia heavy (torch + transformers + modelos ~500MB)
- ❌ Tiempo de inferencia alto para 17+ claims
- ✅ Matching semántico real, tolerante a paráfrasis
- ✅ Sin falsos "insufficient" por límites de regex

### Alternativa C: Un solo archivo de test monolítico
- ❌ Sin separación de capas — fallo de benchmark oculta fallo unitario
- ❌ Difícil depuración
- ✅ Un solo runner, sin dispersión

## ADRs Relacionados
- **ADR-002**: Sistema de Scores (quality thresholds)
- **ADR-003**: Protocolo de Verificación (cross-agent)
- **ADR-011**: Hermes Integration Strategy (dependencia de gateway para tests)

## Referencias
- `test_aletheia_integration.py`: 10 tests, pipeline Aletheia → validación → score store
- `test_fever_benchmark.py`: 17 claims + 1 report, FEVER Score 0.71
- `test_e2e_router_score.py`: 4 tests, Router→Score Store con aislamiento DB
- `.memory/_scripts/lib/aletheia_score_store.py`: Score store persistence (DB SQLite)
- `.memory/_scripts/lib/agent_tools.py`: `validate_aletheia_output()` — core de validación
