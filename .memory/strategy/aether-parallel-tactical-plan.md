# Aether — Plan Táctico Paralelo (F0 + F1)

> **Elaborado por**: Metis (Μῆτις), Diosa de la Estrategia  
> **Fecha**: 2026-05-29  
> **Decisión**: Proceder con F0 (Quick Wins) + F1 (Corto Plazo)  
> **Restricciones**: Kronos postergado · Aether sigue siendo biblioteca · Sin nuevo agente de routing · Control solo sugiere cambios  
> **Principio rector**: Máximo paralelismo — 3 tracks, 3 agents, 3 personas trabajando simultáneamente

---

## PARTE 1: Mapa de Dependencias

```
LEGEND:
  ──→  Dependencia dura (debe esperar)
  - - →  Dependencia suave (puede empezar antes de que termine)
  [N]  Número de tarea
  ═══  Límite entre F0 y F1

F0 ────────────────────────────────────────────────────────────────────

  [1] inline sampling fix ──────────── independiente
  [2] budget_enforcement flag ──────── independiente
  [3] langfuse_enabled flag ────────── independiente
  [4] deepeval_enabled flag ────────── independiente
  [5] EtherJudge→EvalPipeline ──────── independiente (solo lee ambos)
  [6] sampling 10%→50% ─────────────── independiente
  [7] hot-reload reload_config() ───── independiente

F1 ────────────────────────────────────────────────────────────────────

  [8] Dashboard CLI unificado ──────── independiente (solo lee data sources)
  [9] Budget proactivo alertas ──────── - - → [8] (comparte UI/CLI)
 [10] env.py detección entorno ─────── independiente (archivo nuevo)
 [11] Router9 en fallback chains ───── independiente (solo aether.yaml + router9.py)
 [12] Sampling adaptativo por tier ─── - - → [6] (mismo archivo: client.py)
                                        - - → [3] (observability.py sampling)

ÁRBOL DE PARALELISMO (día 1):

  Track A                   Track B                   Track C
  ────────                  ────────                  ────────
  [2] budget flag           [1] inline fix            [8] dashboard CLI
  [3] langfuse flag         [5] EtherJudge connect    [9] budget alerts
  [4] deepeval flag         [6] sampling 50%          [11] Router9 chains
  [7] hot-reload            [12] sampling adaptativo  [10] env.py
  [10] env.py            

  TODAS INDEPENDIENTES → paralelismo puro desde el día 1

  Dependencias suaves (no bloquean):
  - [9] usa CLI de [8] → pueden diseñarse juntos, implementarse separados
  - [12] comparte lógica con [6] → mismo developer idealmente, o coordinar interfaz
```

**Conclusión**: No hay dependencias duras entre ninguna tarea de F0 y F1. **Las 12 tareas pueden ejecutarse en paralelo desde el día 1.** Las únicas dependencias suaves son entre tareas que tocan archivos similares y se benefician de un mismo desarrollador, pero ninguna bloquea.

---

## PARTE 2: Asignación por Track

### Track A — Infraestructura (Config, YAML, Flags, Hot-Reload, Entorno)

**Desarrollador**: Infraestructura / DevOps  
**Archivos**: `aether.yaml`, `config_loader.py`, `config.py`, `__init__.py`, `env.py` (nuevo)

| # | Tarea | Esfuerzo | Archivos | Cambio Específico | Criterio "Done" |
|---|-------|----------|----------|-------------------|-----------------|
| A1 | `ether_budget_enforcement: true` | 🟢 5 min | `aether.yaml:108` | `ether_budget_enforcement: false` → `true` | `aether.yaml` line 108 cambia a `true` |
| A2 | `ether_langfuse_enabled: true` | 🟢 5 min | `aether.yaml:109` | `ether_langfuse_enabled: false` → `true` | `aether.yaml` line 109 cambia a `true` |
| A3 | `ether_deepeval_enabled: true` | 🟢 5 min | `aether.yaml:110` | `ether_deepeval_enabled: false` → `true` | `aether.yaml` line 110 cambia a `true` |
| A4 | Hot-reload: exponer `reload_config()` | 🟡 30 min | `config_loader.py:161-163`, `__init__.py`, `cli.py` | 1. Mejorar `reload_config()` para que también reinicie singleton de config.py 2. Exponer en `__init__.py` 3. Agregar comando `aether reload` en `cli.py` | `reload_config()` disponible públicamente; `python -m lib.aether.cli reload` funciona |
| A5 | `env.py` — detección de entorno | 🟢 20 min | `lib/aether/env.py` (nuevo) | Archivo nuevo con `detect_environment()` que lee `KAOS_ENV`, `HOSTNAME`, `.env`; exporta `is_dev()`, `is_prod()`, `is_test()` | `from lib.aether.env import is_dev; assert isinstance(is_dev(), bool)` |

**Entregable Track A**: Configuración completa, flags activados, hot-reload funcional, detección de entorno operativa.

---

### Track B — Calidad (Eval Pipeline, EtherJudge, QualityStore, Sampling)

**Desarrollador**: ML / Calidad / Evaluación  
**Archivos**: `client.py`, `eval.py`, `judge/__init__.py`, `quality_store.py`, `observability.py`

| # | Tarea | Esfuerzo | Archivos | Cambio Específico | Criterio "Done" |
|---|-------|----------|----------|-------------------|-----------------|
| B1 | Eliminar inline sampling contaminado | 🟢 10 min | `client.py:202-218` | Eliminar el bloque `if success: ... qs.record(... scores={"correctness": 7.0, "coherence": 7.0} ...)` que escribe scores 7.0 falsos en QualityStore | `client.py` ya no tiene `qs.record(... 7.0 ...)` — ni siquiera importa `QualityStore` ni `random` |
| B2 | Conectar EtherJudge al EvalPipeline | 🟡 1-2 hr | `eval.py:143-180`, `judge/__init__.py:242-303` | En `eval.py:_eval_with_llm_judge()`, reemplazar el prompt manual con `EtherJudge.evaluate()`. Integrar también `EtherJudge.evaluate_batch()` en `run_batch_eval()` | `EvalPipeline._eval_with_llm_judge()` usa `EtherJudge(prompt, response, task_type)` en vez de construir su propio prompt |
| B3 | Aumentar sampling QualityStore 10%→50% | 🟢 2 min | `client.py:206` | `if random.random() < 0.1:` → `if random.random() < 0.5:` | `client.py` line 206 cambia `0.1` → `0.5` |
| B4 | Sampling adaptativo por tier de tarea | 🟡 45 min | `client.py:203-218`, `observability.py:30-35` | Reemplazar sampling fijo en `client.py` con lógica que consulte tier de la tarea: flash=10%, pro=50%, kimi=80%, mimo=30%. Mover configuración a `SAMPLE_RATES` en `observability.py` | `client.py` llama `_should_sample(model, tier)` de `observability.py` en vez de `random.random() < 0.1` |

**Entregable Track B**: Datos de calidad limpios, EtherJudge integrado en pipeline de evaluación, sampling 50% con adaptación por tier.

---

### Track C — Proveedores (Router9, Budget, Dashboard)

**Desarrollador**: Backend / Routing / Full-stack  
**Archivos**: `cli.py`, `tracker.py`, `aether.yaml`, `router.py`, `providers/router9.py`, `providers/__init__.py`, `ether_dashboard.py`

| # | Tarea | Esfuerzo | Archivos | Cambio Específico | Criterio "Done" |
|---|-------|----------|----------|-------------------|-----------------|
| C1 | Dashboard CLI unificado | 🟡 2-3 hr | `cli.py`, `ether_dashboard.py`, `tracker.py` | 1. Agregar comando `aether dashboard` que muestre en 4 paneles: (a) Resumen tokens+costos, (b) Calidad por modelo, (c) Circuit Breaker, (d) Budget con barras. 2. Integrar datos de `QualityStore.get_summary()`. 3. Agregar flag `--watch` para auto-refresh cada 5s | `python -m lib.aether.cli dashboard` muestra 4 paneles con datos en vivo |
| C2 | Budget proactivo con alertas 80% | 🟡 1 hr | `tracker.py:256-287`, `cli.py`, `mcp_ether.py` | 1. Mejorar `check_budget()` para que emita warning estructurado por tier 2. Agregar `get_budget_alerts()` separado 3. Integrar alertas en dashboard CLI (panel rojo si >80%) 4. Agregar flag `--alert-only` para monitoreo | `tracker.check_budget()` retorna `{"status": "warning", "alerts": ["⚠️ flash: $2.50/$3.00 (83.3%)"]}` |
| C3 | Integrar Router9 en fallback chains | 🟢 30 min | `aether.yaml:91-98`, `router.py:219-232`, `providers/__init__.py` | 1. Agregar `router9-default` y `router9-minimax` como último eslabón en las fallback chains de `aether.yaml` 2. Registrar modelos Router9 en `router.py` para que CB los reconozca 3. Inicializar `providers/__init__.py` con registro básico | `resolve_model(task_type="general")` incluye router9 models en última instancia de fallback |

**Entregable Track C**: Dashboard funcional con 4 paneles, alertas de budget al 80%, Router9 integrado como fallback ultra-económico.

---

## PARTE 3: Cronograma Paralelo (Días 1-10)

| Día | Track A (Infraestructura) | Track B (Calidad) | Track C (Proveedores) |
|-----|--------------------------|-------------------|----------------------|
| **1** | `aether.yaml`: activar flags [A1, A2, A3] (15 min) | `client.py`: eliminar inline sampling [B1] (10 min) | `cli.py`: esqueleto dashboard — leer tracker + CB + QS [C1] (2 hr) |
| **1** | `config_loader.py`: mejorar `reload_config()` [A4] (30 min) | `client.py`: aumentar sampling 10→50% [B3] (2 min) | — |
| **1** | — | — | `tracker.py`: mejorar `check_budget()` alertas [C2] (1 hr) |
| **2** | `config_loader.py`: probar hot-reload ciclo completo [A4] (30 min) | `judge/__init__`: revisar interfaz `EtherJudge.evaluate()` [B2] (30 min) | `aether.yaml`: agregar Router9 a fallback chains [C3] (15 min) |
| **2** | `__init__.py`: exportar `reload_config` (5 min) | `eval.py`: mapear dónde integrar EtherJudge [B2] (30 min) | `router.py`: validar que Router9 no rompe CB [C3] (15 min) |
| **2** | — | — | Dashboard: panel calidad desde QS [C1] (1 hr) |
| **3** | `cli.py`: agregar comando `aether reload` [A4] (15 min) | `eval.py`: reemplazar `_eval_with_llm_judge` con `EtherJudge` [B2] (1 hr) | Dashboard: panel budget con barras + alertas [C1+C2] (1 hr) |
| **3** | `env.py`: crear archivo nuevo con detección [A5] (20 min) | Probar que `EvalPipeline.evaluate_session()` funciona con EtherJudge (30 min) | `providers/__init__.py`: inicializar registro [C3] (15 min) |
| **4** | **INTEGRACIÓN**: Validar que flags + hot-reload + env funcionan juntos | `client.py`: implementar sampling adaptativo [B4] (45 min) | **INTEGRACIÓN**: Dashboard completo — 4 paneles, flag `--watch` |
| **4** | — | — | Probar budget alertas con datos reales |
| **5** | Tests Track A | Tests Track B | Tests Track C |
| **5** | `py -3 -m pytest ... test_aether_config.py -v` | `py -3 -m pytest ... test_aether_judge.py test_aether_smoke.py -v` | `py -3 -m pytest ... test_aether_router.py -v` |
| **6** | **INTEGRACIÓN CRUZADA**: Track A + B (hot-reload afecta config que usa calidad) | Track B + C (QualityStore alimenta dashboard) | Track A + C (flags afectan budget enforcement) |
| **6** | Arreglar conflictos de merge si los hay | Validar sampling adaptativo con dashboard | Validar alertas con hot-reload |
| **7** | **PRUEBAS GENERALES**: Suite completa | Suite completa | Suite completa |
| **7** | `py -3 -m pytest .memory/_scripts/tests/test_aether_*.py -v --no-header` | — | — |
| **8** | **FIXES**: Bugs encontrados en pruebas | Fixes | Fixes |
| **9** | **DOCUMENTACIÓN RESUMEN**: Qué cambió, cómo revertir | Documentación | Documentación |
| **10** | **ENTREGA**: Release candidate | RC | RC |

---

## PARTE 4: Riesgos del Paralelismo

### 4.1 Conflictos de Merge (2 tracks tocando el mismo archivo)

| Archivo | Track A | Track B | Track C | Riesgo | Mitigación |
|---------|---------|---------|---------|--------|------------|
| `client.py` | — | B1 (eliminar sampling 7.0) + B3 (0.1→0.5) + B4 (sampling adaptativo) | — | 🟡 **ALTO**: B1 elimina el bloque, B3 cambia la misma línea, B4 reemplaza toda la lógica | **Secuenciar B**: B1 primero, luego B4 directamente (incluye el cambio de tasa), B3 se vuelve innecesario. O un solo developer hace B1+B3+B4 en orden. |
| `aether.yaml` | A1, A2, A3 (3 flags en líneas 108-110) | — | C3 (fallback chains líneas 91-98) | 🟢 **BAJO**: Secciones diferentes del archivo | Sin riesgo real — YAML sections independientes |
| `eval.py` | — | B2 (reemplazar `_eval_with_llm_judge`) | — | Ninguno | Solo Track B |
| `tracker.py` | — | — | C2 (mejorar `check_budget`) | Ninguno | Solo Track C |
| `cli.py` | A4 (comando `reload`) | — | C1 (dashboard 4 paneles) | 🟢 **BAJO**: Comandos diferentes | `reload` es un subcomando nuevo; `dashboard` es otro. Namespace separado. |

**Zona crítica**: `client.py` línea 206. **Solución**: Asignar B1+B3+B4 al mismo developer y ejecutar en este orden:
1. B1: Eliminar inline sampling contaminado (borra el bloque `if success: ... qs.record(...)`)
2. B4: Sampling adaptativo por tier (agrega nuevo bloque que reemplaza la funcionalidad)
3. B3: Se vuelve redundante porque B4 ya implementa sampling configurable por tier. Cancelar B3.

### 4.2 Dependencias No Detectadas

| Riesgo | Impacto | Probabilidad | Mitigación |
|--------|---------|-------------|------------|
| `reload_config()` no reinicia `config.py` flags | Flags activados por YAML no toman efecto | 🟡 Media | Test de integración: cambiar flag en YAML, llamar `reload_config()`, verificar que `config.ETHER_BUDGET_ENFORCEMENT` cambió |
| `EtherJudge` usa `agent_llm_call()` que a su vez llama `resolve_model()` que puede causar loop infinito | Stack overflow | 🟠 Alta | `EtherJudge` debe pasar `model_override` explícito (ej. `go-pro`) y NO llamar a `resolve_model()` indirectamente. Revisar que `agent_llm_call` no use router |
| Dashboard CLI importa QualityStore que hace I/O lento | Dashboard tarda >1s en cargar | 🟡 Media | Cachear summary de QS con TTL de 30s; no leer archivo en cada refresh |
| Router9 no está disponible (localhost:20128) | Fallback chains intentan conectar y fallan | 🟡 Media | Router9 debe estar en fallback chain como **último** eslabón, y `agent_llm_call()` debe tener timeout rápido |

### 4.3 Pruebas que se Rompen por Cambios Concurrentes

| Test | Riesgo | Mitigación |
|------|--------|------------|
| `test_aether_smoke.py::test_resolve_default()` espera `go-gemini-flash` (line 53) | Si fallback chains cambian, resultado puede diferir | No cambiar, es correcto |
| `test_aether_config.py::test_router_circuit_breaker_states()` | Independiente | Ninguno |
| `test_aether_judge.py` | Depende de que EtherJudge funcione post-cambio B2 | Ejecutar test antes y después |
| `test_aether_smoke.py::test_quality_store()` | Registra datos de prueba que contaminan QS | Usar `KAOS_TESTING=1` que fuerza `_load()` a retornar vacío |

---

## PARTE 5: Verificación y Criterios de Aceptación

### Tarea A1: `ether_budget_enforcement: true`

| Aspecto | Detalle |
|---------|---------|
| **Test** | `diff aether.yaml | grep budget_enforcement` debe mostrar `true` |
| **Validación** | `py -3 -c "from lib.aether.config import ETHER_BUDGET_ENFORCEMENT; assert ETHER_BUDGET_ENFORCEMENT == True"` |
| **No-rompe** | `py -3 -m pytest .memory/_scripts/tests/test_aether_config.py::test_router_budgets_includes_kimi -v --no-header` |
| **Rollback** | `git checkout .memory/_scripts/aether.yaml` o editar línea 108 a `false` |

### Tarea A2: `ether_langfuse_enabled: true`

| Aspecto | Detalle |
|---------|---------|
| **Test** | `py -3 -c "from lib.aether.config import ETHER_LANGFUSE_ENABLED; assert ETHER_LANGFUSE_ENABLED == True"` |
| **Validación** | Observability carga LangFuse client (puede fallar si no hay servidor, pero no debe crashear) |
| **No-rompe** | `py -3 -m pytest .memory/_scripts/tests/test_aether_smoke.py::test_timer -v --no-header` |
| **Rollback** | Editar línea 109 a `false` |

### Tarea A3: `ether_deepeval_enabled: true`

| Aspecto | Detalle |
|---------|---------|
| **Test** | `py -3 -c "from lib.aether.config import ETHER_DEEPEVAL_ENABLED; assert ETHER_DEEPEVAL_ENABLED == True"` |
| **Validación** | `py -3 -m pytest .memory/_scripts/tests/test_aether_config.py -v --no-header` |
| **No-rompe** | Suite completa de tests |
| **Rollback** | Editar línea 110 a `false` |

### Tarea A4: Hot-reload `reload_config()`

| Aspecto | Detalle |
|---------|---------|
| **Test** | `py -3 -c "from lib.aether.config_loader import reload_config, get_config; c1 = get_config(); reload_config(); c2 = get_config(); assert c1 is not c2"` |
| **Validación** | Modificar flag en YAML, llamar `reload_config()`, verificar que `config.FLAG` cambió |
| **No-rompe** | `py -3 -m pytest .memory/_scripts/tests/test_aether_config.py::test_aether_env_fallback -v --no-header` |
| **Rollback** | `git checkout .memory/_scripts/lib/aether/config_loader.py` |

### Tarea A5: `env.py`

| Aspecto | Detalle |
|---------|---------|
| **Test** | `py -3 -c "from lib.aether.env import detect_environment, is_dev; env = detect_environment(); assert env in ('dev', 'prod', 'test')"` |
| **Validación** | `KAOS_ENV=prod py -3 -c "from lib.aether.env import is_prod; assert is_prod()"` |
| **No-rompe** | No hay código existente que importe `env.py` — no hay riesgo |
| **Rollback** | Eliminar `lib/aether/env.py` |

### Tarea B1: Eliminar inline sampling contaminado

| Aspecto | Detalle |
|---------|---------|
| **Test** | `grep -n "7.0" .memory/_scripts/lib/aether/client.py` debe retornar solo falsos positivos (no el bloque de sampling) |
| **Validación** | `grep -n "quality_store" .memory/_scripts/lib/aether/client.py` no debe aparecer |
| **No-rompe** | `py -3 -m pytest .memory/_scripts/tests/test_aether_smoke.py .memory/_scripts/tests/test_aether_config.py -v --no-header` |
| **Rollback** | `git checkout .memory/_scripts/lib/aether/client.py` |

### Tarea B2: Conectar EtherJudge al EvalPipeline

| Aspecto | Detalle |
|---------|---------|
| **Test** | `py -3 -c "from lib.aether.eval import EvalPipeline; p = EvalPipeline(); print('OK')"` |
| **Validación** | `py -3 -m pytest .memory/_scripts/tests/test_aether_judge.py -v --no-header` (debe pasar) |
| **No-rompe** | `py -3 -m pytest .memory/_scripts/tests/test_aether_smoke.py::test_quality_store -v --no-header` |
| **Rollback** | `git checkout .memory/_scripts/lib/aether/eval.py` |

### Tarea B3: Aumentar sampling 10%→50% (⚠️ Se cancela si B4 se implementa)

| Aspecto | Detalle |
|---------|---------|
| **Test** | `grep -n "0.1" .memory/_scripts/lib/aether/client.py | grep random` debe retornar vacío |
| **Validación** | La línea es ahora `0.5` |
| **No-rompe** | `py -3 -c "from lib.aether.client import chat; print('OK')"` |
| **Rollback** | Revertir línea 206 |

> **⚠️ NOTA**: Si B4 (sampling adaptativo) se implementa, B3 es redundante. En ese caso, marcar B3 como `cancelled` y solo hacer B4.

### Tarea B4: Sampling adaptativo por tier

| Aspecto | Detalle |
|---------|---------|
| **Test** | `py -3 -c "from lib.aether.observability import _should_sample; r = [_should_sample('go-flash') for _ in range(1000); pct = sum(r)/10; assert 5 < pct < 20"` (flash debe ser ~10%) |
| **Validación** | Dashboard muestra tasas de sampling por tier |
| **No-rompe** | `py -3 -m pytest .memory/_scripts/tests/test_aether_smoke.py -v --no-header` |
| **Rollback** | `git checkout .memory/_scripts/lib/aether/client.py .memory/_scripts/lib/aether/observability.py` |

### Tarea C1: Dashboard CLI unificado

| Aspecto | Detalle |
|---------|---------|
| **Test** | `py -3 -m lib.aether.cli dashboard --help` retorna código 0 |
| **Validación** | `py -3 -m lib.aether.cli dashboard` muestra 4 paneles con datos |
| **No-rompe** | `py -3 -m lib.aether.cli status` y `costs` deben seguir funcionando |
| **Rollback** | `git checkout .memory/_scripts/lib/aether/cli.py` |

### Tarea C2: Budget proactivo con alertas

| Aspecto | Detalle |
|---------|---------|
| **Test** | `py -3 -c "from lib.aether.tracker import EtherTracker; t = EtherTracker(); r = t.check_budget(); assert 'status' in r"` |
| **Validación** | Dashboard muestra barras verdes/amarillas/rojas según % usado |
| **No-rompe** | `py -3 -m pytest .memory/_scripts/tests/test_aether_config.py::test_aether_tracker -v --no-header` |
| **Rollback** | `git checkout .memory/_scripts/lib/aether/tracker.py` |

### Tarea C3: Router9 en fallback chains

| Aspecto | Detalle |
|---------|---------|
| **Test** | `grep -n "router9" .memory/_scripts/aether.yaml` debe mostrar al menos 2 líneas en `fallback_chains` |
| **Validación** | `py -3 -c "from lib.aether.router import resolve_model; r = resolve_model(task_type='general')"` no debe crashear |
| **No-rompe** | `py -3 -m pytest .memory/_scripts/tests/test_aether_router.py -v --no-header` |
| **Rollback** | Restaurar fallback_chains en `aether.yaml` |

---

## PARTE 6: Estimación de Tiempo Real

### Días-Calendario vs Días-Hombre

```
Métrica                    Días-Hombre    Días-Calendario (3 tracks)
─────────────────────────  ────────────   ──────────────────────────
Track A (5 tareas)          ~1.5 días      1.5 días (1 persona)
Track B (4 tareas)          ~2.5 días      2.5 días (1 persona)
Track C (3 tareas)          ~4.0 días      4.0 días (1 persona)

Implementación pura         ~8.0 días      4.0 días (3 personas)
Integración + Tests         ~3.0 días      1.5 días (2 personas)
Fixes + Documentación       ~2.0 días      1.0 día  (2 personas)

TOTAL                       ~13.0 días     6.5 días calendario
```

### Desglose Realista

| Fase | Días Calendario | Gantt |
|------|----------------|-------|
| **F0 Quick Wins** (A1-A4, B1, B3) | **Día 1** | ████░░░░ |
| **F1 + resto F0** (A5, B2, B4, C1-C3) | **Días 2-4** | ░░██████░░ |
| **Integración** | **Días 5-6** | ░░░░░░████ |
| **Fixes + Release** | **Días 7-8** | ░░░░░░░░██ |

### Velocidad por Track (horas reales)

```
Track A:  1.5 hr trabajo → 1.5 días calendario (holgura: 0)
Track B:  2.5 hr trabajo → 2.5 días calendario (holgura: 0)
Track C:  4.0 hr trabajo → 4.0 días calendario (holgura: 0)

⚠️ Track C es el cuello de botella: dashboard lleva 2-3 hr.
→ Si se necesita acelerar, dividir C1 en:
   - C1a: esqueleto + panel tokens/costos (1 hr) → día 1
   - C1b: panel calidad + CB + budget (1 hr) → día 2
   - C1c: flag --watch + alertas (1 hr) → día 3
```

### Recomendación

| Factor | Recomendación |
|--------|--------------|
| **Orden de inicio** | Todos los tracks empiezan el día 1 simultáneamente |
| **Sprint planning** | 1 semana (5 días hábiles) para F0 + F1 completo |
| **Daily sync** | 5 min — solo conflictos de merge y bloqueos |
| **Revisión cruzada** | Día 4: Track A revisa código de Track B; Track B revisa Track C; Track C revisa Track A |
| **Buffer** | Días 6-8 para imprevistos (estimación: ~1.5 días de buffer sobre 6.5) |

---

## ANEXO: Comandos de Verificación Rápida

```bash
# Suite completa de tests Aether
py -3 -m pytest .memory/_scripts/tests/test_aether_config.py .memory/_scripts/tests/test_aether_smoke.py .memory/_scripts/tests/test_aether_router.py .memory/_scripts/tests/test_aether_judge.py -v --no-header

# Smoke test rápido (15s)
py -3 -m pytest .memory/_scripts/tests/test_aether_smoke.py -v --no-header

# Validar que flags están activos
py -3 -c "
from lib.aether.config import ETHER_BUDGET_ENFORCEMENT, ETHER_LANGFUSE_ENABLED, ETHER_DEEPEVAL_ENABLED
print(f'budget_enforcement={ETHER_BUDGET_ENFORCEMENT}')
print(f'langfuse_enabled={ETHER_LANGFUSE_ENABLED}')
print(f'deepeval_enabled={ETHER_DEEPEVAL_ENABLED}')
assert all([ETHER_BUDGET_ENFORCEMENT, ETHER_LANGFUSE_ENABLED, ETHER_DEEPEVAL_ENABLED])
print('✅ All flags active')
"

# Validar que no hay inline sampling contaminado
grep -n "7.0" .memory/_scripts/lib/aether/client.py || echo "✅ No 7.0 found"

# Validar hot-reload
py -3 -c "
from lib.aether.config_loader import reload_config, get_config
c1 = get_config()
reload_config()
c2 = get_config()
assert c1 is not c2, 'reload_config() debe crear nueva instancia'
print('✅ Hot-reload OK')
"

# Validar dashboard
py -3 -m lib.aether.cli dashboard --help >nul 2>&1 && echo "✅ Dashboard CLI exists" || echo "❌ Dashboard missing"

# Validar budget alerts
py -3 -c "
from lib.aether.tracker import EtherTracker
t = EtherTracker()
r = t.check_budget()
print(f'Budget status: {r[\"status\"]}')
print(f'Alerts: {r[\"alerts\"]}')
assert 'status' in r
print('✅ Budget check OK')
"

# Validar Router9 registered
grep -q "router9" .memory/_scripts/aether.yaml && echo "✅ Router9 in YAML" || echo "❌ Router9 not in YAML"

# Validar env.py
py -3 -c "
from lib.aether.env import detect_environment, is_dev
env = detect_environment()
print(f'Environment: {env}')
assert env in ('dev', 'prod', 'test')
print('✅ env.py OK')
"

# Lint
py -3 -m flake8 .memory/_scripts/lib/aether/

# Type check
py -3 -m mypy .memory/_scripts/lib/aether/
```
