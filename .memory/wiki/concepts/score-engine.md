---
type: concept
source: KAOS
related: [veracidad, coherencia, completitud, reproducibilidad, utilidad, evaluacion, cadena-verificacion, metricas-calidad]
tags: [agentes, calidad, coherencia, completitud, evaluacion, metricas, reproducibilidad, score, score-engine, utilidad, veracidad, verificacion]
---

# Score Engine

**Tipo**: concepto técnico
**Tags**: #score #calidad #evaluacion #metricas

Motor de 5 dimensiones para evaluar calidad de outputs de agentes: [[veracidad]], [[coherencia]], [[completitud]], [[reproducibilidad]], [[utilidad]]. Perfiles: desarrollo (default), produccion, exploracion, auditoria — cada uno con pesos y thresholds diferentes. Implementado en `.tools/score_engine.py`.

**Relacionado con**: [[evaluacion]], [[cadena-verificacion]], [[metricas-calidad]]
