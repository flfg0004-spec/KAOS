---
type: concept
title: Cadena de Verificación
aliases:
- cadena-verificacion
tags:
- concept
created: '2026-05-20'
modified: '2026-05-21'
confidence: media
status: draft
---

# Cadena de Verificación

**Tipo**: concepto técnico
**Tags**: #verificacion #calidad #cross-agent #triangulacion

Protocolo triangular de verificación cruzada entre agentes: Kosmos verifica a Aletheia (V, C), Metis verifica a Kosmos (CP, U), Aletheia verifica a Metis (V, R). Cada verificación produce JSON con scores, discrepancias y evidence hash. Implementado en `.tools/verification_chain.py`. 3 niveles anti-alucinación: L1 (DeepEval), L2 (cross-agent), L3 (blind peer).

**Relacionado con**: [[evaluacion]], [[score-engine]], [[aletheia]], [[kosmos]], [[metis]]


## Referencias Cruzadas
- Relacionado: [[component-nivel-3]]

