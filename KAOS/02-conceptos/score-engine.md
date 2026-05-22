---
type: concept
title: Score Engine
aliases:
- score-engine
tags:
- concept
created: '2026-05-20'
modified: '2026-05-20'
confidence: media
status: draft
---

# Score Engine

**Tipo**: concepto técnico
**Tags**: #score #calidad #evaluacion #metricas

Motor de 5 dimensiones para evaluar calidad de outputs de agentes: [[veracidad]], [[coherencia]], [[completitud]], [[reproducibilidad]], [[utilidad]]. Perfiles: desarrollo (default), produccion, exploracion, auditoria — cada uno con pesos y thresholds diferentes. Implementado en `.tools/score_engine.py`.

**Relacionado con**: [[evaluacion]], [[cadena-verificacion]], [[metricas-calidad]]

