# KAOS — Session State

## System Health
- **Health Score**: 72/100
- **MnemoBEAM**: 0.803
- **Tests**: **32/32 passing** (10 aletheia + 18 FEVER v2 + 4 E2E)
- **Git**: master branch, limpio (todo commiteado)
- **Hermes**: v0.15.2 instalado, dashboard stub OK, config con CRON + API Server + Profiles
- **ADRs**: 011 (Hermes), 019 (Quality Testing), 020 (Windows Service)

## Recent Work
| Area | Change |
|------|--------|
| **Quick Wins P0** | Cron Scheduler, API Server, ntfy, Discord, Kanban MCP, Dashboard fix |
| **Quick Wins P1** | MiMo V2.5, Health endpoint, WhatsApp Bridge, Email stub, Webhook, Skills KAOS profile |
| **FEVER v2** | 17 claims (score 0.71), 18/18 tests |
| **Tests** | 32/32 total (10+18+4) |
| **Bug fix** | `start-hermes-service.ps1`: missing "run" subcommand → `hermes gateway run --port` |
| **ADRs nuevos** | ADR-019 (Quality Testing), ADR-020 (Windows Service) |
| **Scripts nuevos** | health_endpoint.ps1, baileys_bridge.js, email_bridge.py, webhook_adapter.py, verify-dashboard-fix.ps1 |
| **Cron jobs** | 3: health (15min), kanban-vacuum (3am), env-integrity (6h) |
| **API Server** | :8642/v1 OpenAI-compatible |

## Architecture State (Post-Sesión)
```
Hermes v0.15.2 Gateway :8642
  ├── API Server :8642/v1 (OpenAI-compatible)
  ├── Cron Scheduler (3 jobs)
  ├── Profiles: orchestrator, coder, researcher, kaos-health-check
  ├── Dashboard :9119 (dashboard_auth stub ✅)
  ├── MCP Server → OpenCode (kanban tools ✅)
  ├── Webhook Adapter → :8643/webhook → kanban
  └── Bridges: Discord (config), WhatsApp (baileys JS), Email (SMTP stub)

OpenCode ── 27 MCP servers (including kaos-kanban)
KAOS CLI ── 12 commands
Python ── ~130 modules, 35K LOC
Tests ── 32/32 passing, FEVER Score 0.71
```

## Pending
| Priority | Task | State |
|----------|------|-------|
| P0 | **Agno FastMCP.run(host=)** — mock fallback | ⏳ |
| P0 | **WhatsApp QR** — ejecutar baileys_bridge.js y escanear QR | 🔒 manual |
| P1 | **Hermes service install** — `install-hermes-service.ps1` como Admin | 🔒 req Admin |
| P1 | **Email config** — app password en Gmail → `.env` | 🔒 manual |
| P1 | **Regenerar lint report** — verificar wikilinks restantes (~5 reales) | ⏳ |
| P2 | **FEVER v3** — matching semántico vs regex | 📝 |
| P2 | **Voice mode** — whisper.cpp local | 📝 |
| P2 | **Git keys cleanup** — TO-ROTATE → ROTATED | ⏳ |

## Quick Commands
```powershell
.\kaos doctor              # Full diagnosis
.\kaos hermes gateway      # Start Hermes gateway
py -3 .memory\_scripts\tests\run.py  # Run all tests
.\bin\windows\verify-dashboard-fix.ps1  # Verify dashboard stub
.\bin\windows\install-hermes-service-ADMIN.ps1  # Install service (Admin)
```
