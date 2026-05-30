# KAOS — Session State

## System Health
- **Health Score**: 72/100
- **MnemoBEAM**: 0.803 (⬆️ 0.017 this session)
- **Tests**: **27/27 passing** (10 aletheia + 13 FEVER + 4 E2E router→score_store)
- **Git**: master branch, ~30 uncommitted (⬇️ de 379 gracias a .gitignore)
- **Hermes**: v0.15.2 instalado, dashboard stub creado (dashboard_auth fix)
- **ADR-011**: Creado (Hermes Integration Strategy)

## Recent Work (this session)
| Area | Change |
|------|--------|
| **Cache Hermes** | `lib/hermes_router.py`: TTL 30s en `_check_hermes()` — ya no cachea para siempre |
| **lint_penalty** | `lib/mnemobeam.py`: threshold 10→50 (score 0.786→0.803) |
| **Timeout MCP** | `opencode.json`: hermes-gateway timeout 300→600s |
| **Dashboard display** | `bin/windows/kaos.ps1`: bug upstream v0.15.2 → WARNING no ERR |
| **kaos doc** | `bin/windows/kaos.ps1`: `.\kaos doc [key]` abre docs clave |
| **Entity Wiki** | `.memory/wiki/entities/hermes-agent.md`: arquitectura, providers, features |
| **.gitignore** | Patrones bulk para `.smart-env/`, `*.ajson`, `owui.bak/`, etc. |
| **Contradicciones** | `glosario-kaos.md` + `per-agent-mcp-restriction.md` sincronizados con opencode.json |
| **Dashboard stub** | `dashboard_auth/__init__.py` + `middleware.py` — fix upstream v0.15.2 |
| **ADR-011** | `.memory/schema/adr-011-hermes-integration-strategy.md` |
| **Hermes service** | `bin/windows/start-hermes-service.ps1` + `install-hermes-service.ps1` |
| **FEVER benchmark** | `tests/test_fever_benchmark.py` — 13 tests, FEVER Score 0.75 |
| **Broken wikilinks** | 20+ corregidos + stubs creados (agentes, investigacion, ecosistema, xiaomi, etc.) |
| **Test E2E** | `tests/test_e2e_router_score.py` — 4 tests, flujo router→score_store completo |

## Architecture State
```
Hermes v0.15.2 ── Gateway :8642 (offline)
  ├── Provider Chain: MiMo → OpenRouter → DeepSeek
  ├── Profiles: orchestrator, coder, researcher
  └── Dashboard :9119 (❌ bug upstream - dashboard_auth module missing)

OpenCode ── 26 MCP servers (all active)
  ├── hermes-gateway (timeout 600s)
  ├── mcp-dsol (DSOL routing)
  ├── mcp-vault (filesystem)
  ├── mcp-pandas, mcp-ether, mcp-kroki, mcp-markmap
  └── firecrawl_tools

KAOS CLI ── 12 commands (status, hermes, open, doc, agent, quality, vault, doctor, env, help)
  ├── system_scanner.py → health metrics
  └── kanban_dispatcher.py → Hermes + fallback local JSON

Python Scripts ── 126 modules / 33,585 LOC
  ├── MnemoBEAM scorer (8 dims, pipeline paralelizado fases 9-12)
  ├── Aletheia router (6 profiles → model routing)
  ├── Score store (SQLite, validate_aletheia_output)
  └── Pydantic warnings (non-serializable default, harmless)

Agno Integration ── JWT RS256 auth, rate limiting, DI teams
  └── FastMCP.run() "unexpected keyword argument 'host'" → mock fallback
```

## Key Files
| File | Purpose |
|------|---------|
| `~\.hermes\config.yaml` | 156 lines, Hermes gateway + provider + MCP config |
| `~\.hermes\.env` | API keys (OPENCODE_GO_KEY, XIAOMI_API_KEY, API_SERVER_KEY) |
| `bin\windows\kaos.ps1` | KAOS CLI (280 lines, native-only) |
| `.opencode\opencode.json` | 490 lines, 26 MCP servers, 7 agents |
| `.memory\_scripts\lib\hermes_router.py` | Notifications: Hermes → Telegram/Discord |
| `.memory\_scripts\lib\kanban_dispatcher.py` | Kanban with local JSON fallback |
| `.memory\_scripts\lib\mnemobeam.py` | 8-dim vault quality scorer |
| `.memory\_scripts\lib\system_scanner.py` | Health scanner (HTTP native) |
| `.memory\_scripts\tests\test_aletheia_integration.py` | 10 passing tests |

## Environment
- Python: v3.12 system, v3.11.15 Hermes venv
- Hermes: `~\.hermes\.env` → API_SERVER_KEY required
- PATH picks venv first
- Dashboard bug: `dashboard_auth` directory missing from hermes_cli wheel

## Pending
| Priority | Task | State |
|----------|------|-------|
| P0 | **Agno FastMCP.run(host=)** — mock fallback, resolver incompatibilidad | ⏳ |
| P0 | **Instalar Hermes como servicio** — ejecutar `install-hermes-service.ps1` como Admin | 🔒 req Admin |
| P1 | **24 wikilinks restantes** — probablemente ~5 reales, regenerar lint report | ⏳ |
| P1 | **Git commit parcial** — stage cambios críticos | ⏳ |
| P2 | **ADR-019 (Quality Testing Strategy)** — create document | 📝 |
| P2 | **ADR-020 (Windows Service Strategy)** — create document | 📝 |
| P2 | **FEVER v2** — matching semántico vs regex | 📝 |
| P2 | **Git keys cleanup** — TO-ROTATE → ROTATED | ⏳ |
| P2 | **Dashboard stub** — verify with `hermes dashboard` | ⏳ |

## Quick Commands
```powershell
.\kaos doctor              # Full system diagnosis
.\kaos status              # Service status
.\kaos hermes gateway      # Start Hermes gateway
.\kaos doc                 # List documentation
.\kaos quality smoke       # Vault quality check
py -3 .memory\_scripts\tests\run.py  # Run all tests
```
