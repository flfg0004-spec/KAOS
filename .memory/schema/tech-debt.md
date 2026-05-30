# Tech Debt Log

> Registro formal de deuda técnica sistémica en KAOS.
> Revisión mensual por Metis para priorización.
> Trigger: cada vez que Kosmos detecta un antipatrón o Metis identifica un riesgo estructural.

| ID | Issue | Category | Impact | Agent | Date | Status |
|----|-------|----------|--------|-------|------|--------|
| TD-001 | opencode.json tiene entradas duplicadas `mcp-verification-chain` y `mcp-session-runner` a nivel raíz y dentro de `mcp` | code | high | metis | 2026-05-30 | open |
| TD-002 | bridge module (`mcp_hermes_bridge.py`) usa `json.dumps` sin límite de tamaño en `handle_call` — puede causar OOM con schemas grandes | code | high | kratos | 2026-05-30 | open |
| TD-003 | BM25 index en `lib/bridge/tool_search.py` se construye una vez en `__init__` y no se auto-reconstruye cuando se agregan nuevas MCP tools en runtime | code | med | kratos | 2026-05-30 | open |
| TD-004 | No existe CI/CD pipeline para ejecutar tests de bridge automáticamente (`test_bridge.py` no está en ningún workflow) | test | med | metis | 2026-05-30 | open |
| TD-005 | Progressive disclosure token estimation no maneja correctamente objetos anidados profundos — subestima tokens para schemas complejos | code | med | kratos | 2026-05-30 | open |
| TD-006 | Health dashboard especificado en ADR-024 no tiene implementación — scripts de dashboard inexistentes, `.vault/quality/dashboard.md` no se genera automáticamente | docs | med | kosmos | 2026-05-30 | open |
| TD-007 | Quality gates existentes (flake8, mypy, pytest) se ejecutan pero no son vinculantes — no bloquean merges aunque fallen (ADR-024, Práctica 1) | code | med | metis | 2026-05-30 | open |

## Métricas

- **Total deuda abierta**: 7
- **Por categoría**: code (4), test (1), docs (2)
- **Por agente**: kratos (3), metis (3), kosmos (1)
- **Deuda crítica (high)**: 2
- **Deuda media (med)**: 5
- **Última revisión**: 2026-05-30

## Formato de Entrada

Cada entrada debe tener:

| Campo | Descripción |
|-------|-------------|
| ID | `TD-NNN` secuencial |
| Issue | Descripción clara del problema |
| Category | code / docs / arch / test |
| Impact | high / med / low |
| Agent | Agente responsable de resolver |
| Date | Fecha de detección (ISO) |
| Status | open / fixed / wontfix |

> **Trigger de registro**: Cuando Kosmos detecta un antipatrón arquitectónico, o Metis identifica un riesgo estructural durante el análisis estratégico, o cualquier agente encuentra una práctica que viola ADR-024 (Harness Engineering).
