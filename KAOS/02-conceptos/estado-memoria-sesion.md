---
type: concept
title: Estado de la Memoria entre Sesiones
aliases:
- estado-memoria-sesion
- memory-blocks
- compile-then-query
- add-only-extraction
tags:
- concept
created: '2026-05-19'
modified: '2026-05-20'
confidence: media
status: draft
source: Metis — ciclo operativo
---

# Estado de la Memoria entre Sesiones

Reporte generado durante el primer ciclo operativo completo del sistema de memoria de KAOS.

## Hallazgos
- El sistema de memoria entre sesiones (Fase 0-4) fue implementado y está operativo.
- 7 scripts PowerShell gestionan el ciclo de vida: hydrate, extract, lint, health, pressure, index, commit.
- 3 ADRs documentan la arquitectura (híbrida), aislamiento (OpenCode-only) y autonomía (zonas).
- vault-policy.md define ownership, conflictos, protocolo humano ausente y graceful degradation.

## Próximos Pasos
- Completar entrelazado de [[compile-then-query]] entre entities, concepts y sources.
- Implementar lint automatizado vía scheduler.
- Establecer hábito de memoria: cada sesión debe terminar con extract-session.


## Referencias Cruzadas
- Relacionado: [[memory-blocks]]
- Relacionado: [[add-only-extraction]]
- Relacionado: [[hallazgos-clave]]
- Relacionado: [[arquitectura-integracion-herramientas]]
