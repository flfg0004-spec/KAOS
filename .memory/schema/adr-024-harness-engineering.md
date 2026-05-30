# ADR-024: Harness Engineering en KAOS

**Estado:** Propuesto  
**Fecha:** 2026-05-30  
**Contexto:** Integración del paradigma Harness Engineering (AHE: Auto-Evolving Harness) en KAOS

## Contexto

La investigación de Aletheia sobre **Harness Engineering** reveló un paradigma para sistemas de agentes que formaliza prácticas que KAOS ya implementa parcialmente:

1. **AGENTS.md como contrato**: KAOS ya tiene AGENTS.md con comandos de verificación y estructura.
2. **docs/ actualizada**: KAOS tiene `.memory/schema/` con ADRs y documentación.
3. **Linters custom**: KAOS tiene flake8, mypy, ruff, bandit, safety.
4. **Garbage collection semanal**: KAOS tiene scripts de limpieza pero no GC formalizado.
5. **Papers de referencia**: OpenAI, Martin Fowler sobre agentes y arquitectura evolutiva.

**Gaps identificados** entre Harness Engineering y KAOS:

1. **AHE (Auto-Evolving Harness)**: KAOS no tiene un sistema formal de auto-evolución — las mejoras arquitectónicas son reactivas, no proactivas.
2. **Garbage Collection formal**: No hay GC programado ni métricas de salud de archivos.
3. **Quality Gates en pipeline**: Los gates existen pero no son vinculantes (no bloquean el pipeline si fallan).
4. **Harness SDK**: KAOS no tiene un SDK de harness — las herramientas de verificación están dispersas.
5. **Auto-repair**: KAOS no tiene mecanismos de auto-reparación cuando detecta degradación.

## Opciones Consideradas

### Opción 1: Implementación Completa del Paradigma AHE

Auto-Evolving Harness: sistema que monitorea, evalúa, y auto-repara la arquitectura basado en métricas de salud.

- **Pros**: Formalización completa, auto-curación, reducción de deuda técnica sistémica.
- **Cons**: Esfuerzo significativo (~4-6 semanas), riesgo de falsos positivos, complejidad operativa alta.

### Opción 2: Implementación Incremental — Harness Lite (Seleccionada)

Implementar 5 prácticas de Harness Engineering con priorización, dejando AHE para fase 2.

- **Pros**: Bajo riesgo, resultados rápidos, cada práctica es independiente.
- **Cons**: No hay auto-evolución formal, algunas mejoras son manuales.

### Opción 3: Status Quo

KAOS ya implementa varias prácticas del paradigma.

- **Pros**: Sin esfuerzo.
- **Cons**: Gaps persisten, no hay formalización, GC no ocurre.

## Decisión

**Opción 2 — Harness Lite: 5 prácticas incrementales.**

### Práctica 1: Quality Gates Vinculantes

Actualmente, los quality gates (flake8, mypy, pytest) se ejecutan pero **no bloquean** el pipeline. Cambiar:

- **Pipeline**: Agregar `fail-fast` a quality gates en `.github/workflows/quality.yml`.
- **Umbral**: Health score < 80 bloquea merge a main.
- **Excepción**: `[skip-quality]` en commit message para emergencias.

### Práctica 2: Garbage Collection Formalizado

- **Trigger**: Semanal (domingo 02:00 UTC) vía GitHub Actions schedule.
- **Qué limpia**: 
  - Archivos en `.memory/raw/` con más de 60 días sin referencias en wiki/.
  - Cachés temporales en `.memory/cache/` con más de 7 días.
  - Logs de pipeline con más de 30 días.
  - Archivos huérfanos (sin wikilinks entrantes) en wiki/.
- **Reporte**: genera `.memory/schema/orphan-report.md` antes de limpiar.

### Práctica 3: Health Score Dashboard Automatizado

- **Frecuencia**: Diaria.
- **Métricas**: 
  - Vault quality (9 dimensiones, ADR-002)
  - Agent output quality (5 dimensiones, ADR-003)
  - Pipeline success rate
  - Tiempo medio de respuesta por agente
  - Deuda técnica estimada
- **Output**: Dashboard en `.vault/quality/dashboard.md` actualizado automáticamente.

### Práctica 4: AGENTS.md como Manifiesto de Harness

Formalizar AGENTS.md como el manifiesto único del harness:

```markdown
# Harness: KAOS Agent System

## Verification Commands
- Tests:    py -3 -m pytest ... (existente)
- Lint:     py -3 -m flake8 ... (existente)
- Types:    py -3 -m mypy ... (existente)
- Quality:  py -3 .tools/quality_pipeline.py (NUEVO)

## Health Thresholds
- Min health score: 80/100
- Max debt ratio: 20%
- Max orphan files: 10

## Lifecycle
- GC: Domingo 02:00 UTC
- Quality audit: Diario 06:00 UTC
- Architecture review: Mensual (Kosmos)
```

### Práctica 5: Registro de Deuda Técnica Sistémica

Crear un registro de deuda técnica en `.memory/schema/tech-debt.md` con:

- **Formato**: Issue, impacto, categoría, fecha de detección, fecha objetivo de resolución.
- **Trigger**: Cada vez que Kosmos detecta un antipatrón, se registra automáticamente.
- **Revisión**: Mensual por Metis para priorizar resolución.

## Consecuencias

### Positivas
+ **Calidad vinculante**: health score < 80 bloquea deploys.
+ **Higiene del vault**: GC semanal elimina archivos huérfanos.
+ **Visibilidad**: dashboard diario de salud.
+ **Deuda rastreada**: registro formal con revisión mensual.
+ **Bajo esfuerzo**: ~1-2 semanas para implementar las 5 prácticas.

### Negativas
- **Falsos positivos en quality gates**: posible bloqueo de cambios urgentes.
- **GC agresivo**: posible pérdida de archivos referenciados indirectamente.
- **Overhead de dashboard**: ~10-15 min/día de cómputo para métricas.

### Gaps que persisten (para fase 2)

| Gap | Impacto | Posible solución |
|-----|---------|-----------------|
| Auto-evolución (AHE) | Alto | Sistema de monitoreo + auto-repair |
| Harness SDK | Medio | SDK Python unificado para verificación |
| Auto-repair | Alto | Auto-fix de low-hanging issues (lint, tipos) |
| Benchmark histórico | Bajo | Time-series de health score en QualityStore |

## Referencias
- Harness Engineering: OpenAI papers, Martin Fowler, auto-evolving harness
- AGENTS.md standard (Addy Osmani): 27K⭐, estándar de facto
- ADR-003: Protocolo de Verificación Cruzada
- ADR-019: Quality Testing Strategy
- `.github/workflows/quality.yml`: quality gates existentes
