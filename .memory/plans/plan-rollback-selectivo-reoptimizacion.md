---
type: strategic-plan
agent: metis
date: 2026-05-28
status: ready-for-execution
commit: d195855
phase: rollback+reoptimize
---

# Plan Estratégico: Rollback Selectivo + Re-optimización Controlada

## Resumen Ejecutivo

KAOS tiene **219 archivos .py modificados** en el working tree (vs HEAD `d195855`), producto de Ruff format + optimizaciones masivas (SQLite pool, vectorización, crystallize, hebbian, catch blocks). Se reportan errores en agents y herramientas, algunos pre-existentes. Este plan revierte **solo código** (`.py`), preserva todas las configs de seguridad/CI, y re-aplica optimizaciones en 6 fases secuenciales con verificación obligatoria después de cada paso.

**Hallazgos clave del diagnóstico:**
- **219 .py modificados** (todos ` M`) + **9 agent_nodes nuevos** (`AM`) → revertir/eliminar
- **0 .ts/.tsx modificados** → la fase TypeScript no tiene nada que revertir (archivos están en `.workspace/` que es untracked)
- **Configs preservadas**: `.env.template`, `SECURITY.md`, `.gitignore`, `.pre-commit-config.yaml` (untracked), `.ruff.toml` (untracked), `.github/workflows/*`
- **Tests**: todos en `.memory/_scripts/tests/` — usar `python -m pytest` desde ese directorio
- **No hay logs de error** en el sistema — los errores deben diagnosticarse ejecutando tests base

---

## Análisis Situacional

### Estado actual del repositorio

| Métrica | Valor |
|---------|-------|
| HEAD | `d195855` (security: sanitize API keys) |
| Archivos .py modificados | 219 |
| Archivos .py nuevos (agent_nodes) | 9 |
| Archivos .py eliminados | 4 |
| Archivos .ts/.tsx modificados | 0 |
| Archivos .ts/.tsx en `.workspace/` | Todos untracked (nuevos) |
| Configs a preservar (modificadas) | 3 (`.env.template`, `SECURITY.md`, `.gitignore`) |
| Configs a preservar (untracked) | 3 (`.pre-commit-config.yaml`, `.ruff.toml`, `scripts/freeze-deps.py`) |

### Riesgos identificados

| Riesgo | Probabilidad | Impacto | Mitigación |
|--------|-------------|---------|------------|
| Rollback rompe dependencias entre .py y configs | Baja | Medio | Las configs preservadas no importan .py directamente |
| agent_nodes huérfanos referenciados desde configs | Media | Alto | Verificar imports rotos en Fase 1 |
| Tests base fallan por errores pre-existentes | Alta | Alto | Documentar failures, NO continuar hasta entender causa |
| Re-optimización reintroduce bugs | Media | Alto | Verificación después de CADA paso, revertir si falla |
| Los tests no cubren todos los módulos optimizados | Alta | Medio | Usar smoke test como gate, no solo tests unitarios |

---

## Estrategia Propuesta

**Visión**: Restaurar código a estado HEAD limpio, diagnosticar errores base, y re-aplicar optimizaciones incrementalmente con garantía de que cada paso no rompe nada.

---

## Plan de Ejecución

### Fase 0: Rollback Selectivo (código .py solamente)

**Objetivo**: Revertir los 219 archivos .py a HEAD, eliminar agent_nodes (nuevos), restaurar .py eliminados. Preservar TODAS las configs.

**Comandos exactos** (ejecutar desde `C:\Users\LeonX\Documents\KAOS` en PowerShell):

```powershell
# ===== FASE 0.1: Respaldos de seguridad =====
# Stash con mensaje descriptivo de las configs a preservar
git stash push -m "BACKUP-configs-antes-del-rollback" -- `
  '.env.template' 'SECURITY.md' '.gitignore' `
  '.github/workflows/ci.yml' '.github/workflows/pipeline.yml' `
  '.agents/mcp_config.json' '.memory/schema/eval-profile.yaml'

# ===== FASE 0.2: Revertir .py modificados (excluyendo agent_nodes) =====
# Restaurar todos los .py modificados a HEAD
git diff --name-only HEAD -- '*.py' | Where-Object { 
  $_ -notmatch '^\.memory/_scripts/lib/agent_nodes/' 
} | ForEach-Object { 
  Write-Host "Restaurando: $_"
  git checkout HEAD -- $_ 
}

# ===== FASE 0.3: Eliminar agent_nodes (nuevos, no existen en HEAD) =====
if (Test-Path '.memory/_scripts/lib/agent_nodes') {
  Write-Host "Eliminando agent_nodes (archivos nuevos)..."
  git rm -r --cached '.memory/_scripts/lib/agent_nodes/' 2>$null
  Remove-Item -Recurse -Force '.memory/_scripts/lib/agent_nodes/'
}

# ===== FASE 0.4: Restaurar .py eliminados =====
$deletedPyFiles = @(
  '.memory/_archive/lib/obsidian.py'
  '.memory/_archive/tools/weekly_report.py'
  '.memory/_scripts/lib/obsidian.py'
  'owui/pipelines/kaos_dashboard.py'
)
foreach ($f in $deletedPyFiles) {
  if (-not (Test-Path $f)) {
    Write-Host "Restaurando eliminado: $f"
    git checkout HEAD -- $f
  }
}

# ===== FASE 0.5: Restaurar configs desde stash =====
git stash pop

# ===== FASE 0.6: Verificar resultado del rollback =====
Write-Host "=== VERIFICACIÓN DEL ROLLBACK ==="
Write-Host "Archivos .py modificados restantes:"
git diff --name-only HEAD -- '*.py' | Measure-Object | Select-Object -ExpandProperty Count
Write-Host "Archivos .py nuevos (no debería haber):"
git ls-files --others --exclude-standard -- '*.py'
Write-Host "Estado general:"
git status --short
```

**Verificación Fase 0**: Deben quedar CERO archivos .py modificados. Solo deben aparecer configs y archivos no-code.

---

### Fase 0.5: Snapshot de Línea Base

**Objetivo**: Antes de cualquier optimización, hacer un commit snapshot del estado "limpio" para poder revertir fácilmente si algo sale mal durante la re-optimización.

```powershell
# ===== SNAPSHOT: Estado base post-rollback =====
git add -A
git commit -m "snapshot: estado base post-rollback — código HEAD limpio, configs preservadas"

# Verificar que el commit contiene solo configs (no .py optimizados)
git diff --name-only HEAD~1..HEAD -- '*.py'
# Debe mostrar solo los 4 archivos .py eliminados restaurados, y tal vez los stashed
```

> **Nota**: Si no quieres commitear, usa `git stash` con tag:
> ```powershell
> git stash push -m "SNAPSHOT-BASE-post-rollback-$(Get-Date -Format yyyyMMdd-HHmm)"
> ```

---

### Fase 1: Diagnóstico de Errores Pre-existentes

**Objetivo**: Ejecutar la batería de tests base para identificar QUÉ está roto ANTES de re-optimizar. Esto establece la línea base contra la cual mediremos si una optimización rompe algo.

```powershell
# ===== DIAGNÓSTICO BASE =====
cd .memory\_scripts

# Test 1: Config + Lint (tests más básicos, sin dependencias externas)
Write-Host "=== TEST: Config + Lint ==="
$env:PYTHONPATH = "."; python -m pytest tests/test_config.py tests/test_lint.py -v --tb=short 2>&1 | Tee-Object -FilePath "../../.memory/_pipeline/diagnostico-base-1.txt"

# Test 2: Smoke test E2E (valida que el pipeline DAG build ea correcto)
Write-Host "=== TEST: E2E Smoke ==="
$env:PYTHONPATH = "."; python -m pytest tests/test_e2e_smoke.py -v --tb=short 2>&1 | Tee-Object -FilePath "../../.memory/_pipeline/diagnostico-base-2.txt"

# Test 3: Tests unitarios críticos (los módulos que vamos a optimizar)
Write-Host "=== TEST: Módulos a optimizar (baseline) ==="
$env:PYTHONPATH = "."; python -m pytest `
  tests/test_pipeline.py `
  tests/test_contradictions.py `
  tests/test_wikilinks.py `
  tests/test_crystallize.py `
  tests/test_hebbian_memory.py `
  tests/test_vectorstore.py `
  -v --tb=short 2>&1 | Tee-Object -FilePath "../../.memory/_pipeline/diagnostico-base-3.txt"

# Test 4: Suite completa (fast only, sin slow tests)
Write-Host "=== TEST: Suite rápida completa ==="
$env:PYTHONPATH = "."; python tests/run.py --fast 2>&1 | Tee-Object -FilePath "../../.memory/_pipeline/diagnostico-base-4.txt"

cd ../..
```

**Criterio de aceptación para Fase 1**: Documentar TODOS los failures pre-existentes en `.memory/_pipeline/diagnostico-base.md`. NO intentar arreglarlos ahora — solo conocerlos para no confundirlos con regresiones de optimización.

```powershell
# Generar reporte de diagnóstico
@"
# Diagnóstico Base Pre-Optimización
- Fecha: $(Get-Date)
- HEAD: $(git rev-parse HEAD)

## Failures pre-existentes identificados
| Test | Error | Pre-existente? |
|------|-------|----------------|
| ...  | ...   | Sí/No          |

## Línea base
- Tests pasados: X
- Tests fallados: Y
- Tests saltados: Z
"@ | Out-File -FilePath ".memory/_pipeline/diagnostico-base.md" -Encoding utf8
```

---

### Fase 2: Re-aplicar Optimización #1 — SQLite Pool

**Objetivo**: Agregar connection pooling a SQLite en archivos críticos del pipeline. Solo los archivos pipeline-core.

**Archivos a modificar** (basado en diff analysis):
- `.memory/_scripts/lib/vectorstore.py` — pool de conexiones SQLite
- `.memory/_scripts/lib/code_memory.py` — pool en memory persistence
- `.memory/_scripts/lib/pipeline.py` — pool en pipeline DAG

**Comandos**:
```powershell
cd .memory\_scripts

# Aplicar cambios de SQLite pool...
# [EDITAR los archivos específicos con las optimizaciones]

# Verificar
$env:PYTHONPATH = "."; python -m pytest tests/test_pipeline.py tests/test_memory_persistence.py -v --tb=short
```

**GATE**: Si `test_pipeline.py` o `test_memory_persistence.py` fallan (y no fallaban en baseline) → REVERTIR inmediatamente:
```powershell
git checkout HEAD -- lib/vectorstore.py lib/code_memory.py lib/pipeline.py
Write-Host "FASE 2 REVERTIDA — SQLite pool introdujo regresión"
```
Y SALTAR a Fase 3.

---

### Fase 3: Re-aplicar Optimización #2 — Vectorización

**Objetivo**: Optimizar contradictions + wikilinks (los que tienen tests).

**Archivos a modificar**:
- `.memory/_scripts/lib/contradictions.py`
- `.memory/_scripts/lib/wikilinks.py`

**Comandos**:
```powershell
cd .memory\_scripts

# [EDITAR contradictions.py y wikilinks.py con optimizaciones de vectorización]

# Verificar
$env:PYTHONPATH = "."; python -m pytest tests/test_contradictions.py tests/test_wikilinks.py -v --tb=short
```

**GATE**: Si los tests fallan (y no fallaban en baseline) → REVERTIR y SALTAR.

---

### Fase 4: Re-aplicar Optimización #3 — Catch Blocks Críticos (TS)

**Objetivo**: Mejorar manejo de errores en gateway.ts + provider-usage.ts.

**IMPORTANTE**: Estos archivos están en `.workspace/` (untracked). No hay nada que revertir porque nunca fueron modificados. Las optimizaciones son frescas.

**Archivos a modificar**:
- `.workspace/src/server/gateway.ts`
- `.workspace/src/server/provider-usage.ts` (si existe)
- `.workspace/src/routes/api/provider-usage.ts`

**Comandos**:
```powershell
# Verificar que los archivos existen y están en estado original
cd .workspace

# [EDITAR gateway.ts y provider-usage.ts con catch blocks mejorados]

# Verificar — usar TypeScript compiler check
npx tsc --noEmit --pretty 2>&1 | ForEach-Object { $_ }
```

**GATE**: Si `tsc --noEmit` reporta errores que no existían antes → REVERTIR y SALTAR.

---

### Fase 5: Re-aplicar Optimización #4 — readFile Async (solo si Fase 4 OK)

**Objetivo**: Optimizar lectura de archivos en swarm-memory.ts con async/await.

**Archivos a modificar**:
- `.workspace/src/server/swarm-memory.ts`
- `.workspace/src/routes/api/swarm-memory.ts`

**Comandos**:
```powershell
cd .workspace

# [EDITAR swarm-memory.ts con readFile asíncrono]

# Verificar
npx tsc --noEmit --pretty 2>&1
```

**GATE**: Si `tsc` falla → REVERTIR y SALTAR.

---

### Fase 6: Re-aplicar Optimización #5 — Resto (solo si todo lo anterior OK)

**Objetivo**: Aplicar optimizaciones restantes: crystallize, hebbian, catch blocks adicionales, etc.

**Archivos a modificar**:
- `.memory/_scripts/lib/crystallize.py`
- `.memory/_scripts/lib/hebbian_memory.py`
- `.memory/_scripts/lib/error_daemon.py` (catch blocks adicionales)
- `.memory/_scripts/lib/kratos_hook.py` (catch blocks)
- Más archivos con catch blocks débiles

**Comandos**:
```powershell
cd .memory\_scripts

# [APLICAR optimizaciones crystallize, hebbian, catch blocks]

# Verificar crystallize
$env:PYTHONPATH = "."; python -m pytest tests/test_crystallize.py -v --tb=short

# Verificar hebbian
$env:PYTHONPATH = "."; python -m pytest tests/test_hebbian_memory.py -v --tb=short

# Smoke test final
$env:PYTHONPATH = "."; python -m pytest tests/test_e2e_smoke.py -v --tb=short

# Suite completa (fast)
$env:PYTHONPATH = "."; python tests/run.py --fast
```

**GATE**: Si cualquiera de estos tests falla (y pasaban en baseline) → REVERTIR el archivo específico que introdujo la regresión y CONTINUAR con el resto.

---

### Fase Final: Validación General

```powershell
# ===== VALIDACIÓN FINAL =====
cd .memory\_scripts

Write-Host "=== VALIDACIÓN FINAL COMPLETA ==="

# 1. Suite completa
$env:PYTHONPATH = "."; python tests/run.py --fast 2>&1 | Tee-Object -FilePath "../../.memory/_pipeline/validacion-final.txt"

# 2. Lint (ruff check)
Write-Host "=== RUFF CHECK ==="
python -m ruff check . --quiet 2>&1

# 3. Estado git final
cd ../..
Write-Host "=== ESTADO GIT FINAL ==="
git status --short

# 4. Comparar con baseline
Write-Host "=== COMPARATIVA vs BASELINE ==="
# (comparar manualmente .memory/_pipeline/diagnostico-base-*.txt con validacion-final.txt)

# 5. Commit final si todo está verde
# git add -A
# git commit -m "optimization: re-aplicación controlada — SQLite pool + vectorización + catch blocks"
```

---

## Riesgos y Mitigaciones Detallados

| Riesgo | Probabilidad | Impacto | Mitigación |
|--------|-------------|---------|------------|
| Rollback elimina changes security no-code | Baja | Alto | Stash previo de configs preserva el estado exacto |
| agent_nodes referenciados desde agent_executor.py | Alta | Medio | Fase 1 detectará import errors; documentar como pre-existente |
| Tests no existen para módulo optimizado | Media | Alto | Usar smoke test E2E como gate universal |
| PYTHONPATH incorrecto en pytest | Media | Medio | `cd .memory/_scripts` + `$env:PYTHONPATH="."` como paso estándar previo |
| Windows CRLF warnings interfieren con git operations | Baja | Bajo | Ignorar; git maneja automáticamente |
| Stash pop conflictos por cambios superpuestos | Baja | Medio | Si hay conflicto, resolver manualmente o usar `git checkout stash@{0} -- <file>` |

---

## Próximos Pasos Inmediatos

1. **Ejecutar Fase 0 (Rollback)** — ~2 minutos
2. **Ejecutar Fase 1 (Diagnóstico)** — ~5 minutos
3. **Revisar diagnóstico** — documentar failures pre-existentes
4. **Decidir**: ¿commit del snapshot base?
5. **Ejecutar Fases 2→6 secuencialmente** — ~15 minutos cada una

## Apéndice A: Mapa de Tests por Optimización

| Optimización | Archivo(s) | Test(s) | Cobertura |
|-------------|------------|---------|-----------|
| SQLite pool | `vectorstore.py`, `code_memory.py`, `pipeline.py` | `test_pipeline.py`, `test_memory_persistence.py` | Media |
| Vectorización | `contradictions.py`, `wikilinks.py` | `test_contradictions.py`, `test_wikilinks.py` | Alta |
| Catch blocks (TS) | `gateway.ts`, `provider-usage.ts` | `tsc --noEmit` | Baja (solo compilación) |
| readFile async | `swarm-memory.ts` | `tsc --noEmit` | Baja (solo compilación) |
| Resto | `crystallize.py`, `hebbian_memory.py`, etc. | `test_crystallize.py`, `test_hebbian_memory.py`, `test_e2e_smoke.py` | Media |

## Apéndice B: Script de Rollback Rápido

Si necesitas revertir TODO el working tree (incluyendo configs) en un solo comando de emergencia:
```powershell
git checkout HEAD -- . && git clean -fd
```
> ⚠️ Esto DESCARTARÍA las configs de seguridad. Solo usar si hay emergencia y se pierden configs.

Para revertir SOLO .py sin afectar nada más (un comando):
```powershell
git diff --name-only HEAD -- '*.py' | ForEach-Object { git checkout HEAD -- $_ } 2>$null
```
