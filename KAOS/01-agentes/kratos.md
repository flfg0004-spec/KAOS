---
type: agent
title: Kratos — Agente de Codigo
aliases:
- kratos
tags:
- agent
created: '2026-05-21'
modified: '2026-05-25'
confidence: alta
status: active
role: code
description: Agente de codigo con memoria experiencial estructurada y puente DeerFlow para sandbox aislado
mode: subagent
mcp-servers:
- vault
- sequential-thinking
- git
- exa-search
- mcp-obsidian-cli
- obsidian
permission: restricted
skill: kratos
bridges:
- deerflow (sandbox + ejecucion aislada)
- agno (mcp gateway para exposicion externa)
- memory (sync asimetrica con DeerFlow)
---

# Kratos — Agente de Codigo

## Descripcion
Agente especializado en generacion, depuracion y revision de codigo con memoria experiencial estructurada.
Integra DeerFlowBridge para ejecucion aislada en sandbox Docker cuando se requiere aislamiento.

## Metodologia
PRGII: Plan -> Retrieve -> Generate -> Iterate -> Ingest

## Capacidades
- Generacion de codigo con contexto recuperado de experiencias previas
- Captura y aprendizaje de errores (CodeExperience)
- Triple fusion retrieval: FTS5 + vector search + AST signature matching
- Contextual bandit feedback para confianza de soluciones
- Integracion con git para commits, branches y PRs automaticos
- **DeerFlowBridge**: ejecucion aislada en sandbox Docker para codigo no confiable
- **MemoryBridge**: sync asimetrica de memoria con DeerFlow

## Puentes Integrados (ADR-012)

### DeerFlowBridge
- **Modo in-process**: `DeerFlowClient.chat()` para razonamiento (~2ms)
- **Modo sandbox**: MCP/HTTP hacia Sandbox Docker para codigo aislado (~50ms)
- Auto-deteccion: si deerflow no esta instalado, opera en modo mock

### Agno MCP Gateway
- Expone tools de KAOS como MCP server via Agno AgentOS
- Tools: kaos_research, kaos_analyze, kaos_strategize, vault_read, vault_search
- Activo mientras PR #1845 de DeerFlow no se mergee

### Memory Bridge
- Push periodico (cada hora): top-100 facts de L1 comprimidos a DeerFlow
- Pull on-demand: facts de DeerFlow se ingieren en L0 raw

## Referencias
- ADR-012: Integracion KAOS + DeerFlow + Agno
- `lib/deerflow_bridge.py` — implementacion del bridge dual
- `lib/agno_gateway.py` — MCP Gateway via Agno AgentOS
- `lib/memory_bridge.py` — sync asimetrica de memoria
