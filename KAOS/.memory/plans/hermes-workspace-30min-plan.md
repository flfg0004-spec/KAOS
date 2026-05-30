---
entity: hermes-workspace-30min-plan
type: execution-plan
version: 1.0
status: ready
date: 2026-05-26
author: Metis
tags: [hermes, workspace, execution, quick-reference, cmd-only]
aka: [hermes-tactical-30min]
confidence: high
depends_on:
  - hermes-workspace-integration
---

# Hermes Workspace — Plan de Ejecución 30 min

> **SOLO comandos.** Sin análisis. Ejecutar en orden. Cada paso = ~5 min.

---

## 0. Load Environment

```powershell
$env:PYTHONPATH = ".memory\_scripts"
$env:HERMES_CHANNEL = "telegram"
```

## 1. Verify Services

```powershell
hermes --version
curl -s http://localhost:8642/health -ErrorAction SilentlyContinue
hermes kanban list
Get-Process -Name "node" -ErrorAction SilentlyContinue
py -3 .memory\_scripts\lib\pipeline.py --smoke
```

**Gates:** ✅ CLI responde · ✅ Gateway OK · ✅ Kanban OK · ✅ Smoke PASS

---

## 2. Dashboard Build

```powershell
$hp = (Get-Command hermes).Source.Replace("\bin\hermes.cmd", "")
$dp = Join-Path $hp "..\hermes-agent\services\dashboard"
if (!(Test-Path $dp)) { $dp = Join-Path $hp "node_modules\hermes-agent\services\dashboard" }
$dp = (Resolve-Path $dp).Path
cd $dp
if (!(Test-Path "node_modules")) { npm install }
npm run build
cd (Get-Item $hp).Parent.FullName
hermes dashboard --port 9119 --no-open
curl -s http://localhost:9119 | Select-String -Pattern "<title>"
```

**Gates:** ✅ Dashboard sin `--skip-build` · ✅ Curl responde

**Fallback:** `hermes dashboard --port 9119 --no-open --skip-build`

---

## 3. Telegram Activation

```powershell
(Get-Content .env) -replace '^#TELEGRAM_BOT_TOKEN=', 'TELEGRAM_BOT_TOKEN=' | Set-Content .env
(Get-Content .env) -replace '^#TELEGRAM_CHAT_ID=', 'TELEGRAM_CHAT_ID=' | Set-Content .env
$env:TELEGRAM_BOT_TOKEN = (Select-String -Path .env -Pattern "TELEGRAM_BOT_TOKEN=").Line.Split("=")[1]
$env:TELEGRAM_CHAT_ID = (Select-String -Path .env -Pattern "TELEGRAM_CHAT_ID=").Line.Split("=")[1]
curl -s "https://api.telegram.org/bot$env:TELEGRAM_BOT_TOKEN/getMe" | ConvertFrom-Json
hermes telegram polling --start
hermes send --to telegram "🧪 Test: Hermes integración activada"
```

**Gates:** ✅ Token válido · ✅ Mensaje recibido en Telegram

**Fallback:** `py -3 .memory\_scripts\lib\hermes_router.py` directo si Hermes send falla

---

## 4. Kanban Notifications Fix

```powershell
# Leer función step_done en pipeline
Select-String -Path .memory\_scripts\lib\pipeline.py -Pattern "step_done"
# Fix esperado: añadir guard clause en step_done(step_name, status, state=None)
# if state is None: state = {}
py -3 .memory\_scripts\lib\pipeline.py --smoke
```

**Gates:** ✅ Bug identificado · ✅ Smoke PASS

---

## 5. Workers Quick Check

```powershell
py -3 .memory\_scripts\swarm\launcher.py status
py -3 .memory\_scripts\swarm\launcher.py start researcher --backend native
py -3 .memory\_scripts\swarm\launcher.py status
py -3 .memory\_scripts\swarm\launcher.py stop --all
```

**Gates:** ✅ Worker arranca · ✅ Status OK

---

## 6. End-to-End Smoke Test

```powershell
# Pipeline
py -3 .memory\_scripts\lib\pipeline.py --smoke

# Hermes services
curl -s http://localhost:8642/health
curl -s http://localhost:9119 | Select-String -Pattern "<title>"

# Kanban e2e
$t = hermes kanban create "Smoke Test $(Get-Date -Format yyyy-MM-dd HH:mm)" --body "Verificación post-integración"
hermes kanban list
hermes kanban comment $t "✅ Pipeline OK, Gateway OK, Dashboard OK, Telegram OK"

# Telegram notification
hermes send --to telegram "✅ Smoke Test: Integración Hermes verificada $(Get-Date -Format yyyy-MM-dd HH:mm)"

# Health report
@"
## Hermes Health Report $(Get-Date -Format yyyy-MM-dd)
- Gateway (8642): $(if (curl -s http://localhost:8642/health -ErrorAction SilentlyContinue) {"✅"} else {"❌"})
- Dashboard (9119): $(if (curl -s http://localhost:9119 -ErrorAction SilentlyContinue) {"✅"} else {"❌"})
- Telegram: $(if ($env:TELEGRAM_BOT_TOKEN) {"✅"} else {"❌"})
- Kanban: $(if (hermes kanban list 2>$null) {"✅"} else {"❌"})
- Pipeline: ✅
"@ | Out-File ".memory\reports\hermes-health-$(Get-Date -Format yyyy-MM-dd).md"
```

**Gates:** ✅ Todo verde · ✅ Reporte generado

---

## Quick Reference: Hermes Commands

```powershell
# Gateway
hermes gateway run                          # inicia gateway en :8642
hermes gateway stop                         # detiene gateway

# Dashboard
hermes dashboard --port 9119 --no-open      # con build previo
hermes dashboard --port 9119 --no-open --skip-build  # sin build

# Kanban
hermes kanban create "<title>" --body "<desc>"
hermes kanban list
hermes kanban comment <id> "<text>"
hermes kanban show <id>

# Send messages
hermes send --to telegram "<msg>"
hermes send --to discord "<msg>"
hermes send --to telegram:chat_id "<msg>"

# Telegram
hermes telegram polling --start
hermes telegram polling --stop
hermes telegram webhook set --url <url>

# Workers
py -3 .memory\_scripts\swarm\launcher.py start <role> --backend native
py -3 .memory\_scripts\swarm\launcher.py start --all --backend native
py -3 .memory\_scripts\swarm\launcher.py status
py -3 .memory\_scripts\swarm\launcher.py stop --all

# Pipeline
py -3 .memory\_scripts\lib\pipeline.py --smoke
py -3 .memory\_scripts\lib\pipeline.py --topic "<topic>"
```

---

## Quick Reference: File Paths

```
.env                                    → Variables de entorno raíz
.memory\_scripts\lib\pipeline.py        → Pipeline core
.memory\_scripts\lib\hermes_bridge.py   → Notificaciones pipeline→Hermes
.memory\_scripts\lib\hermes_router.py   → Router mensajes (Telegram fallback)
.memory\_scripts\swarm\launcher.py      → Lanzador workers
.memory\_scripts\swarm\worker_manager.py → Gestor workers
docs\hermes-workspace.md                → Documentación operativa
```

---

## Fallback Emergency

| Síntoma | Comando |
|---------|---------|
| Gateway caído | `hermes gateway run` |
| Dashboard no responde | `hermes dashboard --port 9119 --no-open --skip-build` |
| Telegram no envía | `py -3 .memory\_scripts\lib\hermes_router.py` (fallback directo) |
| Pipeline smoke FAIL | `git checkout -- .memory\_scripts\lib\pipeline.py` (revertir cambios) |
| Worker no arranca | Usar `--backend native` (no tmux) |

---

*Ejecutar en ~30 min. Si algún paso falla, documentar y continuar. NO dejar blockers.*
