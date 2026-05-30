---
type: adr
title: 'Método Kosmos — Framework de Evolución Replicable para Agentes KAOS'
aliases:
  - metodo-kosmos
  - overview-replicable
tags:
  - adr
  - metis
  - kosmos
  - estrategia
  - evolucion
  - framework
created: '2026-05-29'
status: accepted
---

> **TL;DR**: Framework de 5 fases (10-12 semanas, 68-102h) para que cualquier agente KAOS replique la trayectoria de Kosmos (19→91). Incluye matriz de prioridades para los 6 agentes del ecosistema. Prioridad: Kratos y Aletheia (Fase 1: autoevaluación). Mnemosyne y Metis (Fase 3: endurecimiento).

# Método Kosmos — Framework de Evolución Replicable

> **Autor**: Metis (Μῆτις) — Diosa de la Sabiduría y la Estrategia  
> **Basado en**: Ciclo evolutivo de Kosmos (19/100 → 91/100)  
> **Audiencia**: Kratos, Aletheia, Mnemosyne, Kronos, Metis  
> **TL;DR**: 5 fases, 10 semanas, +25 puntos de score

---

## 1. Plan de Consolidación para Kosmos

Kosmos está en la cima del ecosistema con **91/100**, pero arrastra 3 gaps identificados en la evaluación de Metis. Este plan cierra esos gaps en 4 semanas.

| # | Iniciativa | Esfuerzo | Dependencias | Prioridad | Criterio "Done" |
|:-:|:-----------|:--------:|:------------|:---------:|:-----------------|
| K1 | **Feedback loop real con Kratos** — Migrar `KosmosKratosContract` de heurístico a API real sobre CodeExperience | 12h | Kratos expone endpoint de adherence | 🔴 Alta | `contracts/kratos.py` llama a `ce_search()` real, no regex |
| K2 | **OTel Collector** — Reemplazar export a JSONL con OTel exporter real conectado a backend | 8h | Ninguna | 🟡 Media | Spans visibles en Jaeger/Grafana |
| K3 | **Reducir superficie** — Fusionar nodos 5+7 (Visualize+Govern) en Document. Reducir de 27 a 22 módulos | 10h | Ninguna | 🟡 Media | `kosmos/` subpackage pasa de 10 a 8 archivos |
| K4 | **Executive Summaries** — Agregar resumen de 10 líneas al inicio de cada documento >50 líneas | 4h | Ninguna | 🟢 Baja | Todo documento existente tiene sección "TL;DR" |

**Total**: ~34h (1 semana con dedicación completa o 2 semanas parcial)

---

## 2. El Método Kosmos — Framework de 5 Fases

### Filosofía

Kosmos pasó de 19/100 a 91/100 siguiendo estos principios:
1. **Autoevaluación honesta** > métricas infladas
2. **Refactor primero** > features después
3. **Un contrato real** > 4 contratos heurísticos
4. **Graceful degradation** > fallo catastrófico
5. **Documentación canónica** > conocimiento tribal

### Las 5 Fases

```
Score    F1         F2          F3          F4          F5
100 │                                            ┌──────┐
 90 │                                      ┌─────┤ 91   │
 80 │                               ┌──────┤ 85  │      │
 70 │                        ┌──────┤ 75   │     │      │
 60 │                 ┌──────┤ 65   │      │     │      │
 50 │          ┌──────┤ 55   │      │      │     │      │
 40 │   ┌──────┤ 45   │      │      │      │     │      │
 30 │   │base  │      │      │      │      │     │      │
    └───┴──────┴──────┴──────┴──────┴──────┴─────┴──────┴──
        F1      F2      F3      F4      F5
        Sem 1   Sem 2-3 Sem 4-5 Sem 6-8 Sem 9-10
        Autopsia Base    Endurec  Real   Consol
```

#### Fase 1: Autopsia (Semana 1 — Score base)

**Objetivo**: Conocer tu score REAL, identificar 3 debilidades principales.

**Entregables**:
1. Documento de autoevaluación con:
   - 5-8 dimensiones con pesos explícitos (total 100%)
   - Score actual por dimensión
   - 3 debilidades principales identificadas
   - 3 fortalezas principales identificadas
   - Score compuesto
2. Bias audit: ¿quién más debería validar este score? (mínimo 1 par)

**Formato del documento** (copiado de Kosmos):
```markdown
# Autoevaluación: [Agente]

## Score por Dimensión
| Dimensión | Peso | Score | Estado |
|-----------|:----:|:-----:|:------|

## 3 Debilidades Principales
1. ...
2. ...
3. ...

## Score Compuesto: XX/100
```

**Criterio "Done"**: Score documentado, validado por 1 par, 3 debilidades priorizadas.

---

#### Fase 2: Fundación (Semanas 2-3 — Score base → +10)

**Objetivo**: Pipeline limpio, modular, con tests mínimos.

**Pasos**:
1. **Refactor monolito** — Si tu archivo principal tiene >500 líneas, divídelo en 3-5 submódulos
2. **Tests E2E mínimos** — 3 tests que validen output REAL (no solo imports):
   - Test 1: El pipeline produce output con estructura válida
   - Test 2: El output contiene campos mínimos requeridos
   - Test 3: El pipeline maneja errores gracefulmente
3. **Eliminar código zombie** — Archivos no referenciados, imports muertos, funciones sin llamar
4. **Logging básico** — Cada componente principal loggea inicio/fin/error con `logging.getLogger`

**Criterio "Done"**: Archivo principal <500 líneas, 3 tests E2E pasando, 0 archivos zombie.

---

#### Fase 3: Endurecimiento (Semanas 4-5 — Score base+10 → +15)

**Objetivo**: Sistema observable, seguro, y confiable.

**Pasos**:
1. **Seguridad**:
   - Sanitizar inputs de usuario (escapar HTML si hay dashboard)
   - Sanitizar paths en subprocess calls
   - Rate limiting básico (semaphore N=3)
2. **Telemetría**:
   - Logging JSON estructurado (no texto plano)
   - Spans de ejecución por componente
   - Export a archivo con rotación (7 días)
3. **Graceful degradation**:
   - Cada componente con try/except
   - Si falla, pipeline continúa con el siguiente
   - Errores registrados en estructura compartida

**Criterio "Done"**: 0 vulnerabilidades XSS/path injection, spans exportados, graceful degradation probada.

---

#### Fase 4: Contratos Reales (Semanas 6-8 — Score base+15 → +20)

**Objetivo**: 1 contrato funcional con API real > 4 contratos heurísticos.

**Pasos**:
1. **Identificar 2-3 agentes** con los que interactúas naturalmente
2. **Elegir 1 contrato prioritario** — el que más valor genere al ecosistema
3. **Implementar contrato con API real**:
   - Dataclass para resultados
   - Status tracking (last_run, last_score, total_runs, errors)
   - Corrective actions cuando score < threshold
   - Llamada API real (no regex sobre texto)
4. **Documentar contrato** en `.memory/schema/contracts/`

**Ejemplo**: Kosmos ↔ Kratos debería ser `ce_search()` real, no regex sobre output.

**Criterio "Done"**: 1 contrato con API real, status tracking, corrective actions documentadas.

---

#### Fase 5: Consolidación (Semanas 9-10 — Score base+20 → +25)

**Objetivo**: Sistema integrado, documentado, y observable.

**Pasos**:
1. **Health endpoints**: `/health`, `/ready`, `/metrics` (mínimo 3)
2. **Dashboard** de métricas en tiempo real (HTML auto-refresh)
3. **Documentación cross-agente**:
   - ¿Qué necesita este agente de otros?
   - ¿Qué provee este agente a otros?
   - Contratos documentados en schema
4. **Consolidación final**: Documento que cierra el ciclo con score final, deuda técnica remanente, y próximos pasos

**Criterio "Done"**: 3 health endpoints respondiendo, dashboard funcional, documento de consolidación guardado.

---

### Timeline Comprimido vs Realista

| Fase | Semanas | Optimista | Realista (con imprevistos) |
|:-----|:-------:|:---------:|:--------------------------:|
| F1 Autopsia | 1 | 4h | 6h |
| F2 Fundación | 2 | 16h | 24h |
| F3 Endurecimiento | 2 | 16h | 24h |
| F4 Contratos | 3 | 20h | 30h |
| F5 Consolidación | 2 | 12h | 18h |
| **Total** | **10** | **68h** | **102h** |

**Buffer recomendado**: +2 semanas (12 semanas total = ~3 meses)

---

## 3. Matriz de Prioridades por Agente KAOS

### Estado Actual del Ecosistema

| Agente | Fase Kosmos | Score Est. | Gap Principal |
|:-------|:-----------:|:----------:|:--------------|
| **Kosmos** | ✅ Consolidado — V3 | **91** | Contratos heurísticos, OTel a archivo, 27+ módulos |
| **Mnemosyne** | 🟡 Fase 3-4 | **75-82** | 14 fases → necesita consolidación, contratos débiles |
| **Metis** | 🟡 Fase 3-4 | **70-80** | Sin autoevaluación dimensional propia (predica pero no aplica) |
| **Kronos** | 🟠 Fase 2 | **50-60** | No existe como subagente en opencode.json (solo conceptual) |
| **Kratos** | 🔴 Fase 1 | **45-55** | Sin autoevaluación, sin tests E2E, sin telemetría |
| **Aletheia** | 🔴 Fase 1 | **40-50** | Score 0.0/100 en última evaluación |

### Prioridades por Agente

#### 🥇 Kosmos (91 → 95)

| Prioridad | Acción | Copia de sí mismo |
|:----------|:-------|:-----------------|
| 1 | Feedback loop real con Kratos (API sobre CodeExperience) | Aplica su propio contrato Kratos con API real |
| 2 | OTel collector (Jaeger/Grafana) | Migra de export JSONL a export OTel |
| 3 | Reducir de 27 a 22 módulos | Fusiona Visualize+Govern en Document |

#### 🥇 Mnemosyne (75-82 → 85-90)

| Prioridad | Acción | Copia de Kosmos |
|:----------|:-------|:----------------|
| 1 | **Autoevaluación dimensional** (F1) | Documento tipo Kosmos con pesos y scores |
| 2 | **Consolidar 14 fases** en pipeline más manejable (F2) | Refactor como Kosmos hizo con kosmos_node_v2.py |
| 3 | **Contratos cross-agente** con Metis y Kosmos (F4) | KosmosContracts como plantilla |

#### 🥇 Metis (70-80 → 80-85)

| Prioridad | Acción | Copia de Kosmos |
|:----------|:-------|:----------------|
| 1 | **Autoevaluación dimensional de Metis** (F1) | Sí — Kosmos es el gold standard de autoevaluación |
| 2 | **Refactor dual-role** (Strategy + Quality) en submódulos (F2) | Sí — Kosmos refactorizó agente_executor.py |
| 3 | **Health endpoints** para el orquestador de calidad (F5) | Sí — Kosmos tiene 7 endpoints en :9876 |

#### 🥈 Kronos (50-60 → 65-70)

| Prioridad | Acción | Copia de Kosmos |
|:----------|:-------|:----------------|
| 1 | **Autoevaluación** y definición formal como agente (F1) | Documento de autoevaluación estilo Kosmos |
| 2 | **Pipeline mínimo** con logging básico (F2) | Tests E2E + logging estructurado |
| 3 | **Contrato con Metis** para orquestación (F4) | ContractOrchestrator como template |

#### 🥉 Kratos (45-55 → 60-65)

| Prioridad | Acción | Copia de Kosmos |
|:----------|:-------|:----------------|
| 1 | **Autoevaluación dimensional** con CodeExperience (F1) | Documento tipo Kosmos con scores de código |
| 2 | **Refactor PRGII loop** en submódulos (F2) | Sí — Kosmos refactorizó pipeline de 2208 a 4 líneas |
| 3 | **Tests E2E** de generación de código (F2) | test_kosmos_e2e.py como template |

#### 🥉 Aletheia (40-50 → 55-60)

| Prioridad | Acción | Copia de Kosmos |
|:----------|:-------|:----------------|
| 1 | **Autoevaluación honesta** (F1) | Score 0.0/100 actual → documentar gaps reales |
| 2 | **Refactor** pipeline de investigación en submódulos (F2) | Sí — Kosmos refactorizó su monolito |
| 3 | **Tests E2E** de generación de informes (F2) | test_kosmos_e2e.py como template |

---

## 4. Recomendación Ejecutiva

### ¿Qué?

El **Método Kosmos** es un framework de 5 fases (10-12 semanas) que permite a cualquier agente KAOS replicar la trayectoria de Kosmos: de un score base honesto a +25 puntos mediante autoevaluación, refactor, endurecimiento, contratos reales, y consolidación. Está basado en el ciclo real de Kosmos (19→91) y destilado en pasos genéricos, medibles, y replicables. Cada fase tiene criterios "done" explícitos y un score target, no dependencias externas más allá del ecosistema KAOS existente, y un costo de ~68-102h por agente.

### ¿Por qué?

El ecosistema KAOS tiene una asimetría de madurez peligrosa: Kosmos está en 91/100 mientras Kratos está en ~50 y Aletheia en ~45. Esto significa que los contratos cross-agente (feedback loops) son inherentemente frágiles — el agente más fuerte depende de interacciones con los más débiles. La prioridad no es que Kosmos llegue a 95, sino que Kratos y Aletheia lleguen a 70. Un ecosistema con scores 91-75-75-70 es más robusto que uno con 95-50-45-50. La recomendación es iniciar el Método Kosmos simultáneamente en Kratos y Aletheia (F1: autoevaluación), mientras Mnemosyne y Metis avanzan en paralelo (F3: endurecimiento). Kronos puede comenzar en F2 una vez que su definición como agente esté formalizada.

### ¿Cuánto cuesta?

| Recurso | Inversión |
|:--------|:----------|
| **Por agente** | 68-102h (~3-4 semanas FTE o 6-8 semanas parcial) |
| **Ecosistema completo** (5 agentes) | 340-510h |
| **Costo monetario** | **$0** (solo tiempo de desarrollo, sin APIs nuevas) |
| **ROI estimado** | Scores suben +15-25 puntos por agente, contratos cross-agente operativos |

**Riesgo principal**: Planning fallacy — comprimir 11 iteraciones de Kosmos en 10 semanas es ambicioso. El buffer de 2 semanas es obligatorio, no opcional.

**Primera acción concreta**: Cada agente debe producir su **documento de autoevaluación F1** en los próximos 7 días, siguiendo el formato canónico de Kosmos. Metis auditará los resultados en el weekly sync.

---

*Framework generado por **Metis** — basado en el ciclo evolutivo de Kosmos (19→91).*
*Documento guardado en `.memory/schema/reports/metodo-kosmos-overview.md`*
*Próximo hito: Autoevaluaciones F1 de Kratos, Aletheia, y Kronos en 7 días.*
