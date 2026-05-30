# KAOS OKRs — Q2 2026

## O1: Pipeline + Workers integrados
- KR1: pipeline_swarm_bridge.py funcional con timeout configurable (300s default)
- KR2: step_done() notifica kanban al completar cada paso
- KR3: 4 workers persistentes (researcher, architect, strategist, curator)

## O2: Gateway + Dashboard operativos
- KR1: Gateway :8642 responde health OK 24/7
- KR2: Dashboard :9119 con web UI build completo
- KR3: Workers visibles en dashboard

## O3: Sistema seguro y documentado
- KR1: API keys rotadas (DeepSeek, OpenCode, Telegram)
- KR2: Documentación operativa actualizada
- KR3: Smoke test del stack completo pasa en <30s

## O4: Base para Hermes Workspace
- KR1: Gateway + Dashboard estables por 7 días consecutivos
- KR2: Workers procesan tareas reales sin errores
- KR3: Bridge pipeline→workers probado con 3 roles diferentes
