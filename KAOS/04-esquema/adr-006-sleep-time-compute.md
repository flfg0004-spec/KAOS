---
type: adr
title: 'ADR-006: Sleep-Time Compute para Consolidación de Memoria'
aliases:
- adr-006-sleep-time-compute
tags:
- adr
created: '2026-05-20'
modified: '2026-05-21'
confidence: media
status: draft
---

# ADR-006: Sleep-Time Compute para Consolidación de Memoria

**ESTADO: DEPRECADO** — Reemplazado por ADR-011 (Memory Matrix L0-L3) y `.tools/sleep.py` (Sleep Cycle v1.0).
Ver `.memory/schema/adr-011-memory-matrix.md` para la arquitectura actual de consolidación de memoria.

## Opciones Consideradas

### Opción 1: Sleep-time Compute completo (Letta)
Dos agentes: primario (rápido, conversación) + sleep-time (potente, consolidación).

**Pros:** Reducción 5x de tokens, consolidación automática, mejora de precisión 18%.
**Cons:** Complejidad alta, requiere runtime persistente, dos modelos activos.

### Opción 2: Consolidación post-sesión (Simplificado)
Script que ejecuta consolidación al finalizar cada sesión de agente.

**Pros:** Simple, sin runtime persistente, ejecución under 30s.
**Cons:** No es asíncrono, el agente espera, limitado a una sesión.

### Opción 3: Consolidación programada (Seleccionada)
Script que ejecuta consolidación en background según calendario.

**Pros:** Sin bloqueo del agente primario, programable, desacoplado.
**Cons:** No es en tiempo real, la consolidación puede quedar desactualizada.

## Decisión

**Consolidación programada**, ejecutada por `schedule.py` como parte de la sesión funcional diaria.

## Justificación

1. **Simplicidad**: No requiere runtime persistente ni dos modelos activos.
2. **Alineación con schedule.py**: Se integra con el orquestador existente.
3. **Sin bloqueo**: La consolidación ocurre en background, el agente sigue operando.
4. **Suficiente para el volumen actual**: ~30 páginas, consolidación diaria es adecuada.

## Consecuencias

### Positivas
- Consolidación automática sin overhead operativo.
- Integración con el sistema de calidad existente.
- Sin cambios en la arquitectura de agentes.

### Negativas
- Consolidación no en tiempo real (diaria vs inmediata).
- Sin sleep-time compute avanzado (memory blocks rewrite).

### Neutrales
- Frecuencia configurable en `eval-profile.yaml`.
- Escalable a sleep-time completo cuando el volumen lo requiera.

## Estado

Aceptada

## Detalle Técnico

### Proceso de Consolidación
```
1. schedule.py ejecuta consolidación diaria
2. Lee raw/ de las últimas 24h
3. Actualiza wiki/entities/ con nuevos hallazgos
4. Actualiza wiki/concepts/ con nuevas conexiones
5. Marca contradicciones con ⚠️
6. Actualiza index.md y log.md
```

### Trigger
- Diario: como parte de la sesión functional (schedule.py)
- Semanal: como parte de la auditoría (lint + consolidate)
- Manual: `py -3 .tools\session_runner.py functional`

### Herramientas
- Script: integrado en `session_runner.py` (modo functional)
- Métrica: diferencia de score compuesto pre/post consolidación

## Referencias
- Sleep-time Compute Paper: arXiv:2504.13171
- Letta Blog: letta.com/blog/sleep-time-compute
- ADR-002: Sistema de Scores y Pesos Dinámicos
- ADR-003: Protocolo de Verificación Cruzada

