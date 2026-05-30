# ADR-011: Hermes Integration Strategy

## Estado
Aceptado

## Contexto
KAOS opera como un ecosistema de agentes (Aletheia, Kosmos, Metis, Mnemosyne, Kratos, Kronos) que requieren:

1. **Routing de modelos LLM** — acceso a proveedores (MiMo, OpenRouter, DeepSeek) con failover automático
2. **Mensajería** — notificaciones Telegram, reports de pipeline, alerts de degradación
3. **Kanban** — tickets cross-agent con dispatch automático y cola local de fallback
4. **Dashboard** — UI de administración y monitoreo
5. **MCP Gateway** — exposición de herramientas KAOS como MCP servers

Hermes Agent v0.15.2 se introdujo como gateway central. Sin embargo, existen dependencias directas a Telegram API y cola JSON local que operan como fallback. Es necesario formalizar la estrategia de integración.

## Decisión
Usar **Hermes como gateway central con fallback local** siguiendo el principio de "Hermes-first, fallback-always":

### Arquitectura

```
                            ┌─────────────────────┐
                            │   OpenCode (KAOS)    │
                            │   Agentes vía MCP    │
                            └──────┬──────────────┘
                                   │ hermes-gateway MCP (:8642)
                                   ▼
                    ┌──────────────────────────────┐
                    │     Hermes Gateway (:8642)    │
                    │  ┌────────────────────────┐   │
                    │  │ Provider Chain          │   │
                    │  │ 1. MiMo (primary)       │   │
                    │  │ 2. OpenRouter (fallback)│   │
                    │  │ 3. DeepSeek (cold)      │   │
                    │  └────────────────────────┘   │
                    │  ┌────────────────────────┐   │
                    │  │ Kanban Engine           │   │
                    │  │ Dispatch cada 60s       │   │
                    │  │ Auto-decompose          │   │
                    │  │ Max 5 concurrent        │   │
                    │  └────────────────────────┘   │
                    │  ┌────────────────────────┐   │
                    │  │ Notificaciones          │   │
                    │  │ Telegram / Discord      │   │
                    │  └────────────────────────┘   │
                    └──────┬───────────────────────┘
                           │
              ┌────────────┼────────────────┐
              ▼            ▼                ▼
     ┌────────────┐ ┌───────────┐ ┌────────────────┐
     │ KAOS MCPs  │ │ Telegram  │ │ Cola Local     │
     │ (23 MCPs)  │ │ API Direct│ │ JSON (fallback) │
     │ vía proxy   │ │ (fallback)│ │ kanban_queue    │
     └────────────┘ └───────────┘ └────────────────┘
```

### Flujo de Mensajería

```
1. hermes_router.send() → ¿Hermes disponible?
   ├── Sí:  hermes send --to telegram "<mensaje>"
   └── No:  Telegram Bot API directa (fallback)

2. notify_pipeline() → send_boxed() → send()
   └── Reporta progreso de pipelines cross-agent
```

### Flujo de Kanban

```
1. kanban_dispatcher.list_ready() → ¿Hermes disponible?
   ├── Sí:  hermes kanban list --json → filtrar "ready"
   └── No:  leer cola local JSON (fallback)

2. claim() → dispatch_ticket() → build_graph() → invoke()
3. notify_pipeline() al completar
```

### Conexión MCP con OpenCode

```json
{
  "hermes-gateway": {
    "command": ["hermes", "mcp", "serve", "--accept-hooks"],
    "enabled": true,
    "timeout": 600
  }
}
```

## Consecuencias

### Positivas
+ **Resiliencia**: cada módulo tiene fallback local, no hay single point of failure
+ **Latencia**: gateway local a :8642, sin round-trips externos para routing
+ **Provider chain**: failover automático MiMo → OpenRouter → DeepSeek
+ **Kanban persistente**: cola JSON local sobrevive reinicios de Hermes
+ **Dashboard**: UI en :9119 para administración visual (con stub dashboard_auth)

### Negativas
- **Dashboard incompleto**: módulo `dashboard_auth` faltante en v0.15.2 requiere stub
- **Dependencia de CLI**: `hermes` binario debe estar en PATH (manejado vía venv)
- **MCP timeout**: 600s necesario para operaciones largas de kanban
- **Workspace UI**: puerto 3002 requiere Vite dev server (no incluido en instalación base)

### Riesgos y Mitigaciones

| Riesgo | Probabilidad | Impacto | Mitigación |
|--------|-------------|---------|------------|
| Hermes crash | Baja | Alto | Script restart en tarea programada |
| Provider caído (MiMo) | Media | Medio | Fallback OpenRouter automático |
| Cola JSON corrupta | Baja | Bajo | Backup automático en `_pipeline/` |
| Dashboard auth rotura | Media | Bajo | Stub funcional, fix upstream pending |

## Alternativas Consideradas

### Alternativa A: Telegram API directa siempre
- ❌ Sin kanban, sin dashboard, sin gateway central
- ❌ Sin provider chain automático
- ✅ Simple, sin dependencia externa

### Alternativa B: Solo cola local (sin Hermes)
- ❌ Sin UI, sin provider chain, sin MCP gateway
- ❌ Sin notificaciones Telegram
- ✅ 0 dependencias externas

### Alternativa C: Hermes como dependency obligatoria (sin fallback)
- ❌ Si Hermes falla, todo el sistema deja de funcionar
- ❌ Sin cola local, pérdida de tickets
- ✅ Más simple (sin lógica de fallback)

## Diagrama de Flujo

```
                    ┌──────────────┐
                    │ Llamada a    │
                    │ hermes_router │
                    └──────┬───────┘
                           ▼
                    ┌──────────────┐
                    │ Hermes       │
                    │ disponible?  │
                    └──┬───────┬───┘
                   Sí  │       │  No
                       ▼       ▼
              ┌────────────┐ ┌──────────────┐
              │ hermes send│ │ Telegram API  │
              │ vía CLI    │ │ directa       │
              └─────┬──────┘ └──────┬────────┘
                    ▼               ▼
              ┌────────────┐ ┌──────────────┐
              │ Éxito?     │ │ Éxito?       │
              └──┬─────┬───┘ └──┬───────┬────┘
              Sí │     │ No    Sí │      │ No
                 ▼     ▼         ▼      ▼
              return  log     return  log
              True    warn    True    error
```

## ADRs Relacionados
- **ADR-007**: Optimización de Arquitectura KAOS (MCPs, Config, Pipeline)
- **ADR-009**: Migración de Stack de Scraping y Pipeline de Investigación
- **ADR-010**: Integración Ether (DSOL) ↔ LangGraph Orchestrator

## Referencias
- Hermes Agent v0.15.2: `entities/hermes-agent.md`
- Kanban Dispatcher: `_scripts/lib/kanban_dispatcher.py`
- Hermes Router: `_scripts/lib/hermes_router.py`
- Config: `~/.hermes/config.yaml` (182 líneas)
- MCP Config: `opencode.json` (sección hermes-gateway)
