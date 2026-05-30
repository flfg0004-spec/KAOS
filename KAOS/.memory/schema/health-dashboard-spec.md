# Health Score Dashboard — Specification

> Especificación del dashboard de salud automatizado para KAOS Harness.
> Define métricas, fuentes, frecuencia y formato de salida.
> Basado en ADR-024 (Harness Engineering, Práctica 3).

## Propósito

El Health Score Dashboard proporciona una vista unificada del estado de salud del sistema KAOS, combinando métricas de calidad del vault, calidad de outputs de agentes, éxito de pipelines, deuda técnica y rendimiento del sistema. Se genera automáticamente con frecuencia diaria y es la fuente de verdad para decisiones de calidad vinculantes.

## Metrics

| # | Metric | Source | Calculation | Frequency | Threshold |
|---|--------|--------|-------------|-----------|-----------|
| 1 | vault_quality | `lib/quality/vault.py` | % of vault entries with score ≥ 7 (9-dim vault eval, ADR-002) | daily | ≥ 80 |
| 2 | agent_output_quality | `lib/quality/agent.py` | avg score from `evaluate_agent_output()` over last 24h (5-dim eval, ADR-003) | daily | ≥ 75 |
| 3 | pipeline_success | `lib/quality/store.py` | % of recent pipeline runs successful (last 20 runs) | per-run | ≥ 90 |
| 4 | bridge_accuracy | `lib/bridge/ab_test.py` | correct_selection rate in A/B test (progressive disclosure) | daily | ≥ 85 |
| 5 | bridge_token_savings | `lib/bridge/ab_test.py` | avg token reduction vs full disclosure | daily | ≥ 40% |
| 6 | response_time | system / telemetry | avg ms per agent turn across all agents | per-session | ≤ 5000ms |
| 7 | tech_debt_count | `.memory/schema/tech-debt.md` | open tech debt issues (status=open) | weekly | ≤ 10 |
| 8 | gc_efficiency | `lib/garbage.py` | % of eligible files cleaned in last GC run | weekly | ≥ 80 |
| 9 | fever_score | `.memory/_scripts/tests/test_fever_benchmark.py` | FEVER Score = verified / total claims | daily | ≥ 0.70 |
| 10 | test_pass_rate | `pytest` runner | % of all tests passing in last run | per-run | ≥ 90 |

### Detalle de Métricas

#### 1. vault_quality
- **Fuente**: `lib/quality/vault.py` → `score_vault()` 
- **Dimensiones**: 9 (Completitud, Confianza, Conectividad, Frescura, Precisión factual, Legibilidad, Utilidad, Coherencia, Nivel)
- **Cálculo**: Promedio de scores de todos los documentos con frontmatter completo. % de entradas con score compuesto ≥ 7.0
- **Umbral crítico**: < 60 → alerta roja

#### 2. agent_output_quality
- **Fuente**: `lib/quality/agent.py` → `evaluate_agent_output()`
- **Dimensiones**: 5 (Veracidad, Coherencia, Completitud, Reproducibilidad, Utilidad)
- **Cálculo**: Promedio de scores de las últimas 24 horas, agregado por perfil (exploracion/desarrollo/produccion/auditoria/qa)
- **Umbral crítico**: < 50 → alerta roja

#### 3. pipeline_success
- **Fuente**: `lib/quality/store.py` → pipeline run history
- **Cálculo**: (runs exitosos / total runs) × 100 sobre las últimas 20 ejecuciones
- **Umbral crítico**: < 75 → alerta roja

#### 4. bridge_accuracy
- **Fuente**: `lib/bridge/ab_test.py`
- **Cálculo**: (selecciones correctas del modelo / total selecciones) × 100
- **Umbral crítico**: < 70 → alerta roja

#### 5. bridge_token_savings
- **Fuente**: `lib/bridge/ab_test.py`
- **Cálculo**: 100 - (tokens con progressive disclosure / tokens con full disclosure × 100)
- **Umbral crítico**: < 20% → alerta amarilla

#### 6. response_time
- **Fuente**: Telemetría del sistema (capturada por `mcp-speed` / `lib/telemetry.py`)
- **Cálculo**: Mediana móvil de tiempos de respuesta por turno de agente (ventana: 50 turnos)
- **Umbral crítico**: > 10000ms → alerta roja

#### 7. tech_debt_count
- **Fuente**: `.memory/schema/tech-debt.md`
- **Cálculo**: Conteo de entradas con status=open
- **Umbral crítico**: > 15 → alerta roja

#### 8. gc_efficiency
- **Fuente**: `lib/garbage.py` → `run_gc()` report
- **Cálculo**: (archivos limpiados / archivos elegibles) × 100
- **Umbral crítico**: < 60 → alerta roja

#### 9. fever_score
- **Fuente**: `.memory/_scripts/tests/test_fever_benchmark.py`
- **Cálculo**: claims verified / total claims (FEVER Score)
- **Umbral crítico**: < 0.60 → alerta roja

#### 10. test_pass_rate
- **Fuente**: pytest runner output
- **Cálculo**: (tests passed / total tests) × 100
- **Umbral crítico**: < 80 → alerta roja

## Output Format

El dashboard se genera como markdown en `.vault/quality/dashboard.md`.

### Estructura

```markdown
# 🏥 Health Score Dashboard

**Generated**: 2026-05-30T06:00:00Z
**Global Health Score**: 76.8/100  ✅
**Profile**: produccion (threshold: ≥ 80)

## Metrics

| Metric | Current | Threshold | Status | Trend |
|--------|:-------:|:---------:|:------:|:-----:|
| vault_quality | 82.3 | ≥ 80 | ✅ | ↑ |
| agent_output_quality | 74.1 | ≥ 75 | ⚠️ | → |
| pipeline_success | 95.0 | ≥ 90 | ✅ | ↑ |
| bridge_accuracy | 87.2 | ≥ 85 | ✅ | ↑ |
| bridge_token_savings | 45.3% | ≥ 40% | ✅ | → |
| response_time | 3200ms | ≤ 5000ms | ✅ | ↓ |
| tech_debt_count | 7 | ≤ 10 | ✅ | → |
| gc_efficiency | 85.0 | ≥ 80 | ✅ | ↑ |
| fever_score | 0.71 | ≥ 0.70 | ✅ | → |
| test_pass_rate | 96.8 | ≥ 90 | ✅ | → |

**Legend**: ✅ OK | ⚠️ Warning | ❌ Critical

## Sparklines (ASCII)

```
vault_quality:        ████████████████░░ 82.3
agent_output_quality: ███████████████░░░ 74.1
pipeline_success:     ██████████████████░ 95.0
bridge_accuracy:      █████████████████░░ 87.2
bridge_token_savings: ███████████████████ 45.3%
response_time:        ████████████████░░ 3200ms
tech_debt_count:      █████████████░░░░░ 7
gc_efficiency:        ██████████████████░ 85.0
fever_score:          ████████████████░░ 0.71
test_pass_rate:       ███████████████████ 96.8
```

Scale: each █ ≈ 5% (20 chars = 100%)

## Alerts

### ⚠️ Warnings
- **agent_output_quality** (74.1 < 75): La calidad de outputs de agentes está ligeramente por debajo del umbral. Revisar últimas 24h de outputs.

### ✅ All other metrics within thresholds

## Health Score Calculation

Global Health Score = weighted average of all metric scores (normalized 0-100):

```
component_score = min(current / threshold × 100, 100)

vault_quality:        min(82.3/80 × 100, 100) = 100.0 × 0.15 = 15.00
agent_output_quality: min(74.1/75 × 100, 100) =  98.8 × 0.15 = 14.82
pipeline_success:     min(95.0/90 × 100, 100) = 100.0 × 0.12 = 12.00
bridge_accuracy:      min(87.2/85 × 100, 100) = 100.0 × 0.10 = 10.00
bridge_token_savings: min(45.3/40 × 100, 100) = 100.0 × 0.10 = 10.00
response_time:        min(5000/3200 × 100,100)= 100.0 × 0.10 = 10.00
tech_debt_count:      min(10/7 × 100, 100)    = 100.0 × 0.10 = 10.00
gc_efficiency:        min(85.0/80 × 100, 100) = 100.0 × 0.08 =  8.00
fever_score:          min(0.71/0.70 × 100,100)= 100.0 × 0.05 =  5.00
test_pass_rate:       min(96.8/90 × 100, 100) = 100.0 × 0.05 =  5.00

Global = 15.00 + 14.82 + 12.00 + 10.00 + 10.00 + 10.00 + 10.00 + 8.00 + 5.00 + 5.00 = 99.82
→ Clamped to 100 max
```

Weights:
| Metric | Weight |
|--------|:------:|
| vault_quality | 0.15 |
| agent_output_quality | 0.15 |
| pipeline_success | 0.12 |
| bridge_accuracy | 0.10 |
| bridge_token_savings | 0.10 |
| response_time | 0.10 |
| tech_debt_count | 0.10 |
| gc_efficiency | 0.08 |
| fever_score | 0.05 |
| test_pass_rate | 0.05 |
| **Total** | **1.00** |

## Quality Gates (Vinculantes)

Según ADR-024 (Práctica 1), los siguientes gates **bloquean merge** a main:

| Gate | Condición | Excepción |
|------|-----------|-----------|
| Global Health Score | < 80 bloquea merge | `[skip-quality]` en commit msg |
| test_pass_rate | < 90 bloquea merge | `[skip-quality]` en commit msg |
| vault_quality | < 60 bloquea merge | Ninguna |

## Automation

### Generación
- **Frecuencia**: Diaria (06:00 UTC) vía GitHub Actions schedule
- **Trigger manual**: `py -3 .tools/quality_pipeline.py --dashboard`
- **Script**: `.tools/quality_pipeline.py` (por implementar)

### Reporte
- **Output**: `.vault/quality/dashboard.md`
- **Backup**: `.vault/quality/dashboard.history/` con timestamp ISO en filename
- **Retención**: Últimos 30 backups (rotación automática)

### Notificaciones
- Si Global Health Score < 80 → notificación a `#kaos-alerts` vía webhook
- Si cualquier métrica cruza umbral crítico → alerta inmediata

## Roles

- **Kosmos**: implementa el script de dashboard (`.tools/quality_pipeline.py`)
- **Metis**: mantiene esta especificación y revisa métricas mensualmente
- **Kratos**: integra con `lib/quality/store.py` para acceso a pipeline history
- **Aletheia**: provee datos de investigación para FEVER benchmark
- **Mnemosyne**: provee métricas de vault quality
- **Kronos**: provee métricas de pipeline speed y error rate

## Referencias

- ADR-024: Harness Engineering en KAOS (Práctica 3: Health Score Dashboard)
- ADR-002: Sistema de Scores (vault quality, 9 dimensiones)
- ADR-003: Protocolo de Verificación (agent output quality, 5 dimensiones)
- ADR-019: Quality Testing Strategy (FEVER benchmark, test suites)
- `lib/quality/`: Quality engines (agent.py, vault.py, store.py)
- `.memory/schema/tech-debt.md`: Tech debt register
