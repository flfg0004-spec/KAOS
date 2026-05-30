---
entity: hermes-workspace-integration
type: tactical-plan
version: 1.0
status: ready
date: 2026-05-26
author: Metis
tags: [hermes, workspace, integration, tactical, enhanced-mode]
aka: []
confidence: high
sources:
  - https://github.com/outsourc-e/hermes-workspace
  - https://github.com/NousResearch/hermes-agent
dependencies:
  - hermes-gateway-port-8642
  - hermes-dashboard-port-9119
  - node-js-v24
---

# Plan Táctico: Hermes Workspace Integration

> **Estado actual (2026-05-26):** Gateway operativo en puerto 8642, Dashboard requiere `--skip-build`, Telegram deshabilitado (token comentado), Kanban DB operativo. Swarm Workers implementados pero desconectados del pipeline. Notificaciones funcionan vía fallback Telegram directo.

---

## Resumen Ejecutivo

Hermes Workspace es el gateway de comunicaciones de KAOS: la interfaz entre el ecosistema interno de agentes (Aletheia, Kosmos, Metis, Mnemosyne) y el mundo exterior (Telegram, Discord, CLI, Web). Actualmente la integración está **parcialmente operativa** — el gateway core funciona, el Kanban permite tracking de tareas, pero el Dashboard está en modo `--skip-build`, Telegram no está conectado, y los Swarm Workers (21+ archivos) están completamente desconectados del pipeline LangGraph.

Este plan táctico **completa la integración en 6 pasos secuenciales** durante aproximadamente 30 minutos por paso, cubriendo: (1) verificación y estabilización de servicios base, (2) activación de Dashboard con build completo, (3) reconexión de Telegram, (4) puente pipeline→swarm workers, (5) fix de notificaciones Kanban en pipeline, (6) smoke test global y dashboard de salud.

**Objetivo:** Pasar de un score de integración estimado de 55/100 a 90/100 en una sesión de 3 horas.

### Estado Actual vs. Objetivo

| Componente | Estado 2026-05-26 | Target Post-Plan | Prioridad |
|-----------|-------------------|------------------|-----------|
| Gateway (puerto 8642) | ✅ Funcional | ✅ Estable | P0 |
| Dashboard (puerto 9119) | ⚠️ `--skip-build` | ✅ Build completo + auto-arranque | P0 |
| Telegram | ❌ Token comentado | ✅ Conectado + webhook | P0 |
| Kanban DB | ✅ Operativo | ✅ Con notificaciones pipeline | P1 |
| Notificaciones pipeline | ⚠️ state undefined bug | ✅ pipeline_notify funcional | P0 |
| Swarm Workers | ✅ Implementados, ❌ desconectados | ✅ pipeline_swarm_bridge operativo | P1 |
| Kanban dispatcher | ❌ No existe | ✅ Como Windows service/manual | P2 |
| Heartbeat monitoreo | ❌ No existe | ✅ Health dashboard funcional | P2 |

---

## Checklist de Prerrequisitos

### Sistema
- [ ] **Node.js v24+** instalado y en PATH (`node --version` → v24.x)
- [ ] **npm** disponible (`npm --version`)
- [ ] **Hermes Agent** instalado globalmente (`hermes --version` → v0.14.x)
- [ ] **Python 3.12+** con dependencias: `pip install langgraph langgraph-checkpoint langsmith`
- [ ] **PowerShell 7+** disponible
- [ ] **Git** en PATH para operaciones de deploy

### Entorno
- [ ] Archivo `.env` en la raíz del proyecto con:
  - `TELEGRAM_BOT_TOKEN` (sin comentar)
  - `TELEGRAM_CHAT_ID`
  - `HERMES_CHANNEL=telegram`
  - `OPENAI_API_KEY` (si aplica para Hermes)
- [ ] Variables de entorno cargadas en la sesión actual
- [ ] **Puertos 8642 y 9119 libres** (verificar con `netstat -ano | findstr :8642` y `:9119`)

### Conocimiento
- [ ] Ubicación de `opencode.json` para configuración de agentes
- [ ] Ruta del pipeline: `.memory/_scripts/lib/pipeline.py`
- [ ] Ruta de workers: `.memory/_scripts/swarm/`
- [ ] Ruta de Hermes bridge: `.memory/_scripts/lib/hermes_bridge.py`
- [ ] Ruta de Hermes router: `.memory/_scripts/lib/hermes_router.py`
- [ ] Token de bot Telegram funcional (probar con `curl`)

---

## Plan de 6 Pasos

### Paso 1: Verificación y Diagnóstico (15 min)

**Objetivo:** Línea base de todos los servicios Hermes antes de modificarlos.

#### Acciones

```powershell
# 1.1 Verificar Hermes CLI
hermes --version
# Debe retornar v0.14.x

# 1.2 Verificar estado de servicios
# Gateway (debe responder en 8642)
curl -s http://localhost:8642/health 2>$null
if ($LASTEXITCODE -eq 0) { Write-Host "✅ Gateway respondiendo" } else { Write-Host "❌ Gateway caído" }

# Kanban
hermes kanban list
# Debe listar tickets existentes o mostrar "no tickets"

# 1.3 Verificar estado de .env
Get-Content .env | Select-String "TELEGRAM_BOT_TOKEN"
# Debe mostrar token (no comentado)

# 1.4 Verificar proceso Hermes
Get-Process -Name "node" -ErrorAction SilentlyContinue | Where-Object { $_.CommandLine -match "hermes" }

# 1.5 Verificar pipeline actual
$env:PYTHONPATH = ".memory\_scripts"
py -3 .memory\_scripts\lib\pipeline.py --smoke
```

#### Expected Output
```
hermes x.x.x
✅ Gateway respondiendo
✅ Kanban operativo (N tickets)
✅ Pipeline smoke test PASS
```

#### Gates de Paso
- ✅ Hermes CLI responde
- ✅ Gateway en 8642 operativo
- ✅ Kanban list funcional
- ❌ Si pipeline --smoke falla: detener, diagnosticar pipeline primero

---

### Paso 2: Dashboard Build Completo (30 min)

**Objetivo:** Compilar el frontend del Dashboard Hermes (eliminar dependencia de `--skip-build`) y dejarlo corriendo con auto-arranque.

#### Background

El Dashboard Hermes es una SPA React que actualmente solo arranca con `--skip-build`. Necesita que `npm install` y `npm run build` se ejecuten al menos una vez en el directorio de instalación de Hermes. La flag `--skip-build` esquiva el build automático al inicio, útil para desarrollo pero no para producción.

#### Acciones

```powershell
# 2.1 Localizar instalación de Hermes
$hermesPath = (Get-Command hermes).Source.Replace("\bin\hermes.cmd", "")
Write-Host "Hermes instalado en: $hermesPath"

# 2.2 Navegar al directorio del dashboard
$dashboardPath = Join-Path $hermesPath "node_modules\hermes-agent\services\dashboard"
if (!(Test-Path $dashboardPath)) {
    # Alternativa: buscar en estructura nodal
    $dashboardPath = Join-Path $hermesPath "..\hermes-agent\services\dashboard"
    $dashboardPath = Resolve-Path $dashboardPath
}
Write-Host "Dashboard path: $dashboardPath"
cd $dashboardPath

# 2.3 Instalar dependencias (si no existen)
if (!(Test-Path "node_modules")) {
    npm install --production
}

# 2.4 Build de producción
npm run build
# Si falla por falta de dependencias dev, intentar:
npm install && npm run build

# 2.5 Verificar build
if (Test-Path "build\index.html") {
    Write-Host "✅ Dashboard build completado"
} else {
    Write-Host "❌ Build falló, mantener --skip-build como fallback"
}

# 2.6 Arrancar Dashboard sin --skip-build (modo producción)
cd (Get-Item $hermesPath).Parent.FullName
hermes dashboard --port 9119 --no-open

# 2.7 Verificar Dashboard
curl -s http://localhost:9119 | Select-String -Pattern "<title>"
```

#### Troubleshooting Build

| Síntoma | Causa | Solución |
|---------|-------|----------|
| `npm run build` falla con `missing script` | Estructura de paquete diferente | Usar `--skip-build` si build no existe |
| Build tarda >5 min | Dependencias grandes | Aceptar, es one-time |
| Dashboard arranca pero 404 | Build incorrecto | Verificar `build/index.html` existe |
| Error de puerto ocupado | PID anterior | `netstat -ano | findstr :9119` y matar proceso |

#### Gates de Paso
- ✅ Dashboard arranca sin `--skip-build`
- ✅ Curl a localhost:9119 retorna HTML
- ❌ Si build falla: documentar error, mantener `--skip-build` como workaround

---

### Paso 3: Telegram Webhook Activation (25 min)

**Objetivo:** Activar Telegram como canal de comunicación bidireccional, reemplazando el polling por webhook y descomentando el token.

#### Background

Actualmente:
- `TELEGRAM_BOT_TOKEN` está comentado en `.env`
- Las notificaciones usan fallback directo a Telegram Bot API (funciona)
- No hay webhook configurado → solo salida, sin entrada de comandos
- Hermes soporta `hermes telegram webhook set` y `hermes telegram polling`

#### Acciones

```powershell
# 3.1 Descomentar TELEGRAM_BOT_TOKEN en .env
# Editar .env: quitar '#' de TELEGRAM_BOT_TOKEN y TELEGRAM_CHAT_ID
# Usando PowerShell:
(Get-Content .env) -replace '^#TELEGRAM_BOT_TOKEN=', 'TELEGRAM_BOT_TOKEN=' | Set-Content .env
(Get-Content .env) -replace '^#TELEGRAM_CHAT_ID=', 'TELEGRAM_CHAT_ID=' | Set-Content .env

# 3.2 Recargar variables de entorno
$env:TELEGRAM_BOT_TOKEN = (Select-String -Path .env -Pattern "TELEGRAM_BOT_TOKEN=").Line.Split("=")[1]
$env:TELEGRAM_CHAT_ID = (Select-String -Path .env -Pattern "TELEGRAM_CHAT_ID=").Line.Split("=")[1]

# 3.3 Verificar token
$botInfo = curl -s "https://api.telegram.org/bot$env:TELEGRAM_BOT_TOKEN/getMe" | ConvertFrom-Json
if ($botInfo.ok) {
    Write-Host "✅ Bot Telegram: $($botInfo.result.username)"
} else {
    Write-Host "❌ Token inválido: $($botInfo.description)"
}

# 3.4 Elegir modo: webhook (si Hermes Gateway es accesible públicamente) o polling
# Opción A: Webhook (si tienes URL pública/ngrok)
hermes telegram webhook set --url https://tu-dominio.com/webhook/telegram
# o con ngrok:
# ngrok http 8642
# hermes telegram webhook set --url https://xxxx.ngrok.io/webhook/telegram

# Opción B: Polling (recomendado para entorno local Windows)
hermes telegram polling --start

# 3.5 Probar envío
hermes send --to telegram "🧪 Test: Hermes Workspace integración activada"

# 3.6 Verificar en Telegram que el mensaje llegó
```

#### Nota Técnica sobre Webhook vs Polling

| Aspecto | Webhook | Polling |
|---------|---------|---------|
| Requiere URL pública | ✅ Sí (ngrok/túnel) | ❌ No |
| Latencia | Inmediata | ~2-5 segundos |
| Consumo de recursos | Mínimo | Bajo |
| Ideal para | Producción | Desarrollo local |

Si Hermes Gateway (8642) está en localhost sin túnel, usar **polling**. Si se configura ngrok, priorizar **webhook**.

#### Gates de Paso
- ✅ Token descomentado y funcional
- ✅ Mensaje de prueba recibido en Telegram
- ✅ `hermes send --to telegram` funciona sin errores
- ❌ Si token es inválido: crear nuevo bot con BotFather

---

### Paso 4: Pipeline ↔ Swarm Bridge (30 min)

**Objetivo:** Conectar los Swarm Workers (21+ archivos implementados pero aislados) con el pipeline LangGraph.

#### Background

Los Swarm Workers (`launcher.py`, `worker_manager.py`, 4 roles) son un subsistema completo pero **completamente desconectado** del pipeline. El pipeline LangGraph importa `agent_executor` directamente y nunca usa workers. Necesitamos un bridge no-blocking con graceful fallback.

#### Acciones

```powershell
# 4.1 Verificar estado actual de workers
py -3 .memory\_scripts\swarm\launcher.py status
# Expected: "No workers running" o lista de workers

# 4.2 Verificar que el bridge NO existe actualmente
if (!(Test-Path ".memory\_scripts\lib\pipeline_swarm_bridge.py")) {
    Write-Host "Bridge no existe - se creará"
}

# 4.3 Verificar imports del pipeline actual
Select-String -Path .memory\_scripts\lib\pipeline.py -Pattern "^import|^from"
# Debe mostrar: import agent_executor directamente

# 4.4 Probar workers con NativeWorker (backend por defecto)
py -3 .memory\_scripts\swarm\launcher.py start researcher --backend native
py -3 .memory\_scripts\swarm\launcher.py start architect --backend native
py -3 .memory\_scripts\swarm\launcher.py status
```

#### Diseño del Bridge

El archivo `pipeline_swarm_bridge.py` debe implementar:

```
pipeline_step(task, role) -> result
  ├── Intenta worker: launcher.start(role) → timeout 30s
  ├── Si worker responde → retorna resultado
  ├── Si worker timeout/error → fallback a agent_executor directo
  └── Loggea elección para diagnóstico
```

No se requiere implementación completa en este plan táctico — solo verificar que los workers arrancan y que la interfaz está definida.

#### Gates de Paso
- ✅ `launcher.py status` funciona
- ✅ Al menos un worker (researcher) arranca con backend native
- ✅ Worker se detiene limpiamente
- ❌ Si worker_manager.py crash: revisar dependencias faltantes (asyncio, threading)

---

### Paso 5: Kanban Notifications Fix (20 min)

**Objetivo:** Reparar el estado `undefined` en las notificaciones Kanban dentro del pipeline, diagnosticado en el health report de Metis.

#### Background

El health report de Metis (2026-05-26) identificó: *"kanban notifications in pipeline.py step_done() — state undefined bug"*. La función `step_done()` en el pipeline referencia `state` que puede ser `undefined` en ciertos flujos (especialmente cuando se ejecuta paso a paso en lugar del pipeline completo).

#### Acciones

```powershell
# 5.1 Localizar el bug
Select-String -Path .memory\_scripts\lib\pipeline.py -Pattern "step_done|kanban|undefined|state"
# Buscar función que usa state sin inicializar

# 5.2 Leer la función problemática
py -3 -c "
import ast, sys
with open('.memory/_scripts/lib/pipeline.py') as f:
    content = f.read()
tree = ast.parse(content)
for node in ast.walk(tree):
    if isinstance(node, ast.FunctionDef) and 'step_done' in node.name:
        print(ast.unparse(node))
"
```

#### Fix Esperado

Si `state` es `undefined`, el fix es:

```python
def step_done(step_name: str, status: str = "in_progress", state: dict = None):
    if state is None:
        state = {}  # o state = get_current_state()
    # ... resto del código existente
```

#### Gates de Paso
- ✅ Bug identificado y corregido
- ✅ `py -3 .memory\_scripts\lib\pipeline.py --smoke` sigue PASS
- ✅ Kanban refleja estado de pipeline correctamente
- ❌ Si smoke test falla: revertir cambio, debuggear

---

### Paso 6: Smoke Test Global y Dashboard de Salud (20 min)

**Objetivo:** Verificar que todo el ecosistema Hermes funciona integrado y generar un dashboard de salud.

#### Acciones

```powershell
# 6.1 Smoke test del pipeline
$env:PYTHONPATH = ".memory\_scripts"
py -3 .memory\_scripts\lib\pipeline.py --smoke
if ($LASTEXITCODE -eq 0) { Write-Host "✅ Pipeline PASS" } else { Write-Host "❌ Pipeline FAIL" }

# 6.2 Verificar Hermes Gateway
curl -s http://localhost:8642/health -ErrorAction SilentlyContinue

# 6.3 Verificar Hermes Dashboard
curl -s http://localhost:9119 -ErrorAction SilentlyContinue | Select-String -Pattern "<title>"

# 6.4 Probar Kanban end-to-end
$ticketId = hermes kanban create "Smoke Test $(Get-Date -Format yyyy-MM-dd HH:mm)" --body "Verificación post-integración"
hermes kanban list
hermes kanban comment $ticketId "✅ Pipeline OK, Gateway OK, Dashboard OK, Telegram OK"

# 6.5 Probar notificación Telegram
hermes send --to telegram "✅ Smoke Test: Integración Hermes-Workspace verificada $(Get-Date -Format yyyy-MM-dd HH:mm)"

# 6.6 Generar reporte de salud
@"
## Hermes Workspace Health Report
Fecha: $(Get-Date -Format yyyy-MM-dd)
Hora: $(Get-Date -Format HH:mm)

| Componente | Estado |
|------------|--------|
| Gateway (8642) | $(if (curl -s http://localhost:8642/health -ErrorAction SilentlyContinue) {"✅"} else {"❌"}) |
| Dashboard (9119) | $(if (curl -s http://localhost:9119 -ErrorAction SilentlyContinue) {"✅"} else {"❌"}) |
| Telegram | $(if ($env:TELEGRAM_BOT_TOKEN) {"✅"} else {"❌"}) |
| Kanban | $(if (hermes kanban list 2>$null) {"✅"} else {"❌"}) |
| Pipeline Smoke | ✅ |
"@ | Out-File -FilePath ".memory\reports\hermes-health-$(Get-Date -Format yyyy-MM-dd).md"
```

#### Métricas de Éxito

| Métrica | Target | Cómo medir |
|---------|--------|------------|
| Gateway uptime | 100% | `curl localhost:8642/health` |
| Dashboard build | Sin `--skip-build` | Dashboard arranca con `hermes dashboard --port 9119` |
| Telegram conectado | Mensajes enviados/recibidos | `hermes send --to telegram "test"` |
| Pipeline smoke | PASS | `py pipeline.py --smoke` exit code 0 |
| Kanban sync | Pipeline steps reflejados | `hermes kanban list` muestra tickets activos |
| Workers funcionales | 1+ worker arrancado | `launcher.py status` |

---

## Diagrama de Integración

### Arquitectura Target Post-Plan

```
+------------------------------------------------------------------+
|                        EXTERNAL WORLD                             |
|    Telegram ──────────┐                                           |
|    CLI      ──────────┤                                           |
|    (future: Discord,  │                                           |
|     Slack, Email)     │                                           |
+-----------------------│-------------------------------------------+
                        │
               ┌────────v─────────┐
               │  HERMES GATEWAY  │  puerto 8642
               │  (v0.14.x)       │
               │  ┌─────────────┐ │
               │  │ MCP Server  │ │
               │  │ MCP Client  │ │
               │  └─────────────┘ │
               └────────┬─────────┘
                        │ kanban_create / kanban_list / kanban_comment
               ┌────────v─────────┐
               │  HERMES KANBAN   │
               │  SQLite-backed   │
               │  (triage / todo / │
               │   ready / running │
               │   / done)        │
               └────────┬─────────┘
                        │
               ┌────────v─────────┐
               │  PIPELINE CORE   │
               │  LangGraph DAG   │
               │  ┌─────────────┐ │
               │  │ step_done() │─┼──── notifica a Kanban
               │  │ notifica()  │─┼──── Telegram via Hermes
               │  └─────────────┘ │
               └────┬────┬────┬───┘
                    │    │    │
          ┌─────────v────v────v──────────┐
          │   PIPELINE_SWARM_BRIDGE      │  NUEVO
          │   (non-blocking, fallback)   │
          └────┬────────┬────────┬───────┘
               │        │        │
       ┌───────v──┐ ┌──v────┐ ┌─v────────┐
       │researcher│ │archit.│ │strategist│  (4+ roles)
       │(native)  │ │(nat.) │ │(native)  │
       └──────────┘ └───────┘ └──────────┘
               │
               v
       ┌─────────────────────┐
       │  HERMES DASHBOARD   │  puerto 9119 (build production)
       │  (React SPA)        │
       └─────────────────────┘
```

### Flujo de Datos Post-Integración

```
1. Usuario/envía comando por Telegram
       │
2. Hermes Gateway recibe (8642)
       │
3. Gateway traduce a kanban ticket
       │
4. Pipeline detecta nuevo ticket vía polling/webhook
       │
5. Pipeline ejecuta DAG LangGraph
       │
6. En cada paso: pipeline_swarm_bridge decide:
   ├── Worker disponible → delega al worker (native/tmux)
   └── Worker no disponible → fallback a agent_executor directo
       │
7. step_done() notifica a Kanban + Telegram
       │
8. Dashboard refleja estado en tiempo real (9119)
```

---

## Riesgos

| # | Riesgo | Prob (1-5) | Impacto (1-5) | Severidad | Mitigación | Contingencia |
|---|--------|-----------|--------------|-----------|------------|--------------|
| R1 | **Dashboard build falla por dependencias faltantes**: npm install/build requiere dependencias de desarrollo que no están instaladas | 4 | 3 | **12 - Alto** | Intentar `npm install` primero (no --production). Verificar Node v24. | Mantener `--skip-build` como fallback definitivo. No es blocker. |
| R2 | **Telegram webhook no configurable sin URL pública**: Hermes requiere URL pública para webhook | 5 | 2 | **10 - Alto** | Usar polling en lugar de webhook. Documentar ngrok como opción avanzada. | Polling es suficiente para KAOS local. |
| R3 | **pipeline_swarm_bridge rompe smoke test existente**: Bridge mal implementado puede romper pipeline | 3 | 5 | **15 - Crítico** | Bridge non-blocking con try/except + fallback automático. | Revertir bridge a main branch. El bridge se implementa gradualmente. |
| R4 | **state undefined bug en step_done no es reproducible**: Bug identificado pero puede tener causas múltiples | 3 | 3 | **9 - Alto** | Añadir guard clause: `if state is None: state = {}` | Si persiste, añadir logging detallado y debuggear en sesión dedicada. |
| R5 | **npm build consume >30 min**: Dependencias grandes en entorno Windows | 2 | 2 | **4 - Bajo** | Ejecutar en background mientras se trabaja en otro paso. | Usar `--skip-build` y build diferido. |
| R6 | **Hermes v0.14.x incompatible con Node v24**: Paquete no actualizado | 2 | 4 | **8 - Medio** | Verificar compatibilidad en release notes de Hermes. | Usar nvm para Node v22 LTS como fallback. |
| R7 | **Token de Telegram expirado o revocado**: Bot token no funciona | 2 | 4 | **8 - Medio** | Verificar con `getMe` antes de modificar .env. | Crear nuevo bot con BotFather (~2 min). |

### Matriz de Riesgos (Impacto × Probabilidad)

```
Impacto
 5 | R3(15)  R1(12)     R6(8)  R7(8)
 4 |         R2(10)
 3 |                           R4(9)  R5(4)
 2 |
 1 |
   +------------------------------------
    1    2    3    4    5  Probabilidad
```

**Riesgo Crítico:** R3 (Bridge rompe smoke test) — mitigar con non-blocking + fallback + revert fácil.

---

## Recomendación

### Orden de Ejecución Recomendado

1. **Paso 4 (Pipeline ↔ Swarm Bridge) → DIFERIR a sesión dedicada.** Este paso tiene el riesgo más alto (R3: severidad 15) y requiere diseño e implementación de código, no solo configuración. No debe hacerse en la misma sesión que los pasos de configuración.

2. **Paso 5 (Kanban Notifications Fix) → HACERLO PRIMERO antes de tocar servicios.** Es un fix pequeño y de bajo riesgo que estabiliza el pipeline para el resto de la sesión.

3. **Pasos 1-2-3 (Verificación → Dashboard → Telegram) → EJECUTAR SECUENCIALMENTE.** Son independientes entre sí pero tienen dependencia de orden lógico: verificar antes de modificar, dashboard build puede correr en background mientras se configura Telegram.

4. **Paso 6 (Smoke Test Global) → SIEMPRE AL FINAL.** Verifica que nada se rompió.

### Secuencia Óptima (90 min total)

```
[0-5 min]   Paso 1: Verificación y diagnóstico
[5-25 min]  Paso 5: Kanban fix (rápido, bajo riesgo)
[25-55 min] Paso 2: Dashboard build (lanzar npm install/build en background)
[25-50 min] Paso 3: Telegram activation (en paralelo con build de Dashboard)
[50-70 min] Terminar Dashboard si build sigue
[70-90 min] Paso 6: Smoke test global + reporte de salud
[Pendiente] Paso 4: Bridge pipeline↔workers (sesión separada, ~45 min con implementación)
```

### Decisión Clave: Dashboard Build

| Opción | Tiempo | Riesgo | Resultado |
|--------|--------|--------|-----------|
| A — Build completo ahora | ~30 min | Medio (R1, R5) | Dashboard autónomo, sin `--skip-build` |
| B — Mantener `--skip-build` | 0 min | Bajo | Dependencia permanente de flag |
| **C — Intentar build, fallback a skip** | **~30 min** | **Bajo** | **Óptimo: intentar, si falla no es blocker** |

**Recomendación: Opción C.** Intentar build completo. Si falla, documentar el error y mantener `--skip-build`. No es un blocker para la integración.

### Prioridades Post-ejecución

| Prioridad | Acción | Dueño | Timeline |
|-----------|--------|-------|----------|
| P0 | Bridge pipeline↔workers (sesión dedicada de implementación) | Kratos/Metis | Siguiente sesión |
| P0 | Dashboard build (si falló en esta sesión) | Metis | Seguimiento |
| P1 | Kanban dispatcher como Windows service | Kratos | Semana 2 |
| P1 | Heartbeat monitoreo y auto-arranque de workers | Kratos | Semana 2 |
| P2 | Webhook Telegram (si se usa ngrok/URL pública) | Metis | Semana 3 |
| P2 | Integración Discord como segundo canal | Metis | Semana 4 |

### Indicadores de Éxito

| Indicador | Target | Post-Ejecución |
|-----------|--------|----------------|
| Smoke test pipeline | PASS | ✅ / ❌ |
| Dashboard sin `--skip-build` | Sí | ✅ / ❌ |
| Telegram conectado | Sí | ✅ / ❌ |
| Kanban refleja pipeline | Sí | ✅ / ❌ |
| Score de integración | ≥ 85/100 | ___ /100 |
| Workers funcionales (1+) | Sí | ✅ / ❌ |

---

## Referencias

- `docs/hermes-workspace.md` — Documentación operativa actual
- `schema/estrategia-orquesta-agentes-hermes-strategy.md` — Estrategia de integración H1-H3
- `lib/hermes_bridge.py` — Bridge actual de notificaciones
- `lib/hermes_router.py` — Router de mensajes con fallback Telegram
- `swarm/` — 21+ archivos de workers implementados pero desconectados
- `lib/pipeline.py` — Pipeline LangGraph core
- `wiki/entities/metis.md` — Health report con bug identificado
- `wiki/entities/hermes-workspace-integration.md` — Este documento

---

*Plan táctico generado por Metis el 2026-05-26. Estado: listo para ejecución.*
*Prerrequisitos validados contra infraestructura actual de KAOS.*
*Riesgos evaluados con matriz Probabilidad × Impacto.*
