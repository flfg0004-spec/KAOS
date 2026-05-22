# Dashboard de Calidad — KAOS

## Score Compuesto Actual: 76.8 🟡
- Perfil: desarrollo
- Delta vs anterior: — (primera medición)

## Scores por Dimensión
| Dimensión | Score | Tendencia (7d) |
|-----------|-------|----------------|
| Veracidad | 83.3  | —              |
| Coherencia | 80.3 | —              |
| Completitud | 73.0 | —              |
| Reproducibilidad | 68.7 | —            |
| Utilidad | 78.3    | —              |

## Scores por Agente
| Agente | V | C | CP | R | U | Compuesto |
|--------|---|---|----|---|----|-----------|
| Aletheia | 85 | 78 | 72 | 68 | 80 | 76.6 |
| Kosmos | 80 | 85 | 75 | 70 | 75 | 77.0 |
| Kratos | — | — | — | — | — | MVP |
| **Sistema** | **83.3** | **80.3** | **73.0** | **68.7** | **78.3** | **76.8** |

## Última Sesión
- Tipo: functional
- Fecha: 2026-05-20
- Resultados: 2/2 tests passed — health: ok
- Score promedio: 76.8

## Cadena de Verificación
| Verificador → Verificado | Dimensiones | Score | Resultado |
|--------------------------|-------------|-------|-----------|
| Kosmos → Aletheia | V, C | 82, 76 | ✅ pass |
| Metis → Kosmos | CP, U | 80, 78 | ✅ pass |
| Aletheia → Metis | V, R | 85, 72 | ✅ pass |
| Kratos | — | — | En evaluación |

## Tendencias (7 días)
| Fecha | Score Compuesto | Cambio | Perfil |
|-------|----------------|--------|--------|
| 2026-05-20 | 76.8 | — | desarrollo |
| 2026-05-20 | 76.6 | -0.2 | desarrollo |

## Alertas
- Ninguna activa. Todos los scores sobre umbral del perfil desarrollo.
- Umbrales actuales: V≥65, C≥60, CP≥55, R≥50, U≥55, Compuesto≥70
- GitHub: ❌ Eliminado del sistema. HIGH risk resuelto.
- supermemory: ❌ Deshabilitado (requiere API key no configurada).
- structurizr: ✅ Implementado como MCP local (Python wrapper).
- txtai: ✅ Implementado (semsearch + dedup con sentence-transformers).
- opencode.db: ✅ Reducido de 733 MB a 22.1 MB (VACUUM aplicado).
- Lint: ✅ 1 issue (glosario orphan — referencia externa aceptable).
- Mnemosyne: ✅ Ciclo de 8 fases automatizado vía run_curation.py.
- Pipeline: ✅ Trigger automático de curación al completarse.
- Kratos: ✅ 5º agente implementado. CodeExperience FTS5 + AST matching. Routing condicional.
- LangGraph: ✅ Orchestrator DAG con checkpointing SQLite + LangSmith tracing.
- Contexto: ✅ Compaction duplicado (10 turns / 16K tokens). Context sharing implementado.
- DSOL: ✅ build_optimized_context() conectado a hydrate. build_prompt() marcado como deprecated.

## Score de Curación (Mnemosyne)
| Métrica | Valor | Objetivo |
|---------|-------|----------|
| Tasa conversión raw→wiki | 86% | ≥95% |
| Cobertura wikilinks | ~73% | ≥90% |
| Días desde última curación | 0 | <7 |

## Pipeline de Conocimiento
| Métrica | Valor |
|---------|-------|
| Time-to-Knowledge (promedio) | 1.8 horas |
| Tasa de conversión raw→wiki | 86% |
| Cross-links entre conceptos | ~296 (synapse) |
| Investigaciones totales en raw/ | 21 |
| Conceptos destilados | 60 activos (wiki/concepts) |
| Memoria de código (CodeExperience) | 0 (lista para capturar) |
| Agentes totales | 5 (Aletheia, Kosmos, Metis, Mnemosyne, **Kratos**) |
| Routing | Condicional: Metis → Kratos (código) / → Mnemosyne (no código) |

## Programación Automática
| Sesión | Frecuencia | Última ejecución | Próxima | Tarea Windows |
|--------|-----------|-----------------|---------|--------------|
| Distill | Diaria | 2026-05-20 ✅ | 2026-05-21 | — |
| Functional | Diaria | 2026-05-20 ✅ | 2026-05-21 | ✅ KAOS-Daily-Quality (08:00) |
| Verification | Semanal (lunes) | — | 2026-05-25 | ✅ KAOS-Weekly-Audit (06:00) |
| Audit | Semanal (lunes) | — | 2026-05-25 | ✅ KAOS-Weekly-Audit (06:00) |
| Vault Health | Semanal (domingo) | — | 2026-05-25 | ✅ KAOS-Vault-Health (22:00) |
| Monthly Audit | Mensual (1ro) | — | 2026-06-01 | — |

## Comandos Rápidos
| Comando | Acción |
|---------|--------|
| `py -3 .tools\session_runner.py smoke desarrollo` | Smoke check (2 min) |
| `py -3 .tools\session_runner.py functional desarrollo` | Sesión funcional (15 min) |
| `py -3 .tools\session_runner.py audit desarrollo` | Auditoría completa (60 min) |
| `py -3 .tools\verification_chain.py desarrollo` | Cadena de verificación (A→K→M→A) |
| `py -3 .tools\score_engine.py test` | Score engine test |
| `py -3 .tools\schedule.py` | Ejecutar sesiones programadas |
| `py -3 .memory\_scripts\clean_opencode_db.py --analyze` | Diagnosticar DB de OpenCode |
| `obsidian-cli search glosario-kaos` | Ver glosario global del sistema |
| `py -3 .memory\_scripts\vault.py pipeline check` | Estado del pipeline actual |
| `py -3 .memory\_scripts\lib\code_memory.py` | Estado de CodeExperience DB |

---
*Auto-generado por Metis — 2026-05-21*
