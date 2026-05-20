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

## Tendencias (7 días)
| Fecha | Score Compuesto | Cambio | Perfil |
|-------|----------------|--------|--------|
| 2026-05-20 | 76.8 | — | desarrollo |

## Alertas
- Ninguna activa. Todos los scores sobre umbral del perfil desarrollo.
- Umbrales actuales: V≥65, C≥60, CP≥55, R≥50, U≥55, Compuesto≥70

## Pipeline de Conocimiento
| Métrica | Valor |
|---------|-------|
| Time-to-Knowledge (promedio) | 1.8 horas |
| Tasa de conversión raw→wiki | 86% |
| Cross-links entre conceptos | 23 añadidos |
| Investigaciones totales en raw/ | 7 |
| Conceptos destilados | 12 activos |

## Programación Automática
| Sesión | Frecuencia | Última ejecución | Próxima |
|--------|-----------|-----------------|---------|
| Distill | Diaria | 2026-05-20 ✅ | 2026-05-21 |
| Functional | Diaria | 2026-05-20 ✅ | 2026-05-21 |
| Verification | Semanal (lunes) | — | 2026-05-25 |
| Audit | Semanal (lunes) | — | 2026-05-25 |
| Monthly Audit | Mensual (1ro) | — | 2026-06-01 |

## Comandos Rápidos
| Comando | Acción |
|---------|--------|
| `py -3 .tools\session_runner.py smoke` | Smoke check (2 min) |
| `py -3 .tools\session_runner.py functional` | Sesión funcional (15 min) |
| `py -3 .tools\session_runner.py audit` | Auditoría completa (60 min) |
| `py -3 .tools\verification_chain.py` | Cadena de verificación (A→K→M→A) |
| `py -3 .tools\schedule.py` | Ejecutar sesiones programadas |

---
*Auto-generado por Metis — 2026-05-20*
