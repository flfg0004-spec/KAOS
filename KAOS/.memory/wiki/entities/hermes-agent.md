---
type: agent
role: messaging-gateway
description: "Hermes Agent v0.15.2 — gateway LLM, sistema de mensajería, kanban, y orquestación de tickets del ecosistema KAOS"
mode: native
version: 0.15.2
status: active
color: "#FFD700"
mcp-servers: [hermes-gateway]
endpoints:
  gateway: "http://localhost:8642"
  dashboard: "http://localhost:9119"
  workspace: "http://localhost:3002"
providers:
  primary: "Xiaomi MiMo (mimo-v2.5-pro)"
  fallback: "OpenRouter (Gemini Flash, GPT-4o-mini)"
integrations:
  - kanban (tickets, dispatch, orchestrator)
  - telegram (notificaciones)
  - pipeline notify (progreso de agentes)
  - system_scanner (health check)
profiles:
  - orchestrator
  - coder
  - researcher
features_active:
  - context_compression (threshold: 0.50)
  - session_auto_prune (retention: 30d)
  - delegation (5 concurrent children)
  - kanban_dispatch (auto_decompose)
  - auxiliary_models (Gemini Flash)
features_pending:
  - dashboard (bug upstream v0.15.2, missing dashboard_auth)
  - cron_jobs
  - memory_provider (holographic/honcho)
related_entities: [aletheia, mnemosyne, metis, kosmos, kratos, kronos]
---
# Hermes Agent

## Descripción

Hermes Agent es el **gateway LLM y sistema de mensajería** del ecosistema KAOS. 
Corre nativamente en Windows (sin Docker, sin WSL) y provee:

- **Gateway API** (:8642) — routing de modelos LLM, sesiones, tools, MCP, kanban
- **Dashboard** (:9119) — UI de administración (pendiente de fix en v0.15.2)
- **Workspace UI** (:3002) — interfaz de usuario completa (Vite dev server)

## Arquitectura

```
OpenCode (agentes KAOS) ──MCP──▶ Hermes Gateway (:8642)
                                     ├── Provider Chain (MiMo → OpenRouter → DeepSeek)
                                     ├── Kanban (tickets → dispatch → orchestrator)
                                     ├── Notificaciones (Telegram)
                                     └── Pipeline notify (progreso agentes)
```

## Configuración

- **Home**: `~/.hermes/`
- **Config**: `~/.hermes/config.yaml` (156 líneas, expandida desde 29)
- **Envs**: `~/.hermes/.env` (API keys)
- **Profiles**: `~/.hermes/profiles/{orchestrator,coder,researcher}/`

## Provider Chain

| Prioridad | Provider | Modelo | API Key |
|-----------|----------|--------|---------|
| 1 | Xiaomi MiMo | mimo-v2.5-pro | XIAOMI_API_KEY |
| 2 | OpenRouter | google/gemini-3-flash-preview | OPENROUTER_API_KEY |
| 3 | OpenRouter (fallback) | openai/gpt-4o-mini | OPENROUTER_API_KEY |

## Features Activas

- **Compresión de contexto**: threshold=0.50, target_ratio=0.20
- **Auto-prune de sesiones**: retention=30 días, vacuum automático
- **Delegación**: 5 hijos concurrentes, orchestrator habilitado
- **Kanban**: auto_decompose, dispatch cada 60s, orchestrator profile
- **Modelos auxiliares**: Gemini Flash para compresión, búsqueda, curator

## Dependencias en KAOS

| Módulo | Tipo | Fallback |
|--------|------|----------|
| lib/hermes_router.py | Notificaciones | Telegram API directa ✅ |
| lib/hermes_bridge.py | Pipeline notify | Router fallback ✅ |
| lib/kanban_dispatcher.py | Tickets | Cola local JSON ✅ |
| lib/system_scanner.py | Health | HTTP directo ✅ |
| agent_executor.py | Notificaciones progreso | HERMES_ENABLED flag ✅ |

## Historial de Versiones en KAOS

- **2026-05-29**: Update v0.14.0 → v0.15.2 (370 commits, 15 P0 fixes)
- **2026-05-29**: Config expandida 29→156 líneas, BOM corregido
- **2026-05-29**: Profiles creados (orchestrator, coder, researcher)
- **2026-05-28**: Migración a nativo (sin Docker, sin WSL)
- **2026-05-28**: Provider MiMo configurado
