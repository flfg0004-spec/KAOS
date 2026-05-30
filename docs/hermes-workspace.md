# Hermes Workspace + Swarm Workers — Documentación Operativa

## Estado Actual (2026-05-26)

### Servicios Hermes
| Servicio | Puerto | Estado | Comando |
|----------|--------|--------|---------|
| Gateway (messaging) | 8642 | ✅ Funcional | `hermes gateway run` |
| Dashboard (web) | 9119 | ⚠️ Requiere `--skip-build` | `hermes dashboard --port 9119 --no-open --skip-build` |
| Telegram | — | ❌ Deshabilitado | Token comentado en .env |
| Kanban DB | — | ✅ Operativo | `hermes kanban create/list/comment` |

### Swarm Workers
| Componente | Archivo | Estado |
|------------|---------|--------|
| WorkerManager | `.memory/_scripts/swarm/worker_manager.py` | ✅ |
| NativeWorker | `.memory/_scripts/swarm/backends/native.py` | ✅ Default |
| TmuxWorker | `.memory/_scripts/swarm/backends/tmux.py` | ⚠️ WSL limitation |
| Roles (4) | `.memory/_scripts/swarm/roles/*.py` | ✅ |
| Launcher CLI | `.memory/_scripts/swarm/launcher.py` | ✅ |

### Pipeline
| Componente | Estado |
|------------|--------|
| Pipeline LangGraph | ✅ Intacto, smoke test PASS |
| Notificaciones Telegram | ✅ Vía fallback directo (hermes_router.py) |

## Comandos Útiles

```powershell
# Swarm workers
py -3 .memory\_scripts\swarm\launcher.py start researcher --backend native
py -3 .memory\_scripts\swarm\launcher.py start --all --backend native
py -3 .memory\_scripts\swarm\launcher.py status
py -3 .memory\_scripts\swarm\launcher.py stop --all

# Hermes
hermes gateway run                    # messaging gateway
hermes dashboard --port 9119 --no-open --skip-build  # web UI
hermes kanban list
hermes kanban create "titulo" --body "descripción"

# Pipeline
$env:PYTHONPATH = ".memory\_scripts"
py -3 .memory\_scripts\lib\pipeline.py --smoke
```

## TmuxWorker — Limitación Conocida

El backend TmuxWorker usa WSL2 + tmux 3.6, pero cada invocación `wsl -d Ubuntu` crea un namespace /tmp diferente, lo que impide que tmux encuentre sesiones creadas en invocaciones previas. Soluciones futuras:
1. Usar `tmux -S /ruta/compartida/socket` para socket persistente
2. Mantener un proceso bash persistente en WSL para todos los comandos tmux
3. Ejecutar workers directamente en WSL sin tmux

Para la mayoría de los casos, NativeWorker (subprocess + threading) es suficiente.

## Hermes Workspace UI
- **URL**: http://localhost:3002
- **Estado**: ✅ Activo (Vite dev server)
- **Puerto**: 3002
- **Backend**: Gateway :8642 | Dashboard :9119
- **Modo**: Enhanced (gateway+dashboard detectados)
- **Inicio**: `cd .workspace && $env:NODE_OPTIONS="--max-old-space-size=2048"; $env:PORT=3002; pnpm exec vite dev --port 3002`
