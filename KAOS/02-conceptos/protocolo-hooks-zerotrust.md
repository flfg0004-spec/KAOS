---
type: concept
title: Protocolo de Hooks Zero Trust — Comunicación Bidireccional KAOS
aliases:
- protocolo-hooks-zerotrust
- zero-trust-hooks
tags:
- concept
- seguridad
- comunicacion
- hooks
created: '2026-05-21'
modified: '2026-05-21'
confidence: media
status: draft
---

# Protocolo de Hooks Zero Trust — Comunicación Bidireccional KAOS

## Contexto

KAOS opera actualmente con dos ecosistemas de agentes aislados:

1. **OpenCode** — `.opencode/opencode.json` — Agentes: Aletheia, Kosmos, Metis, Mnemosyne
2. **Antigravity 2.0 (Olympo)** — `.agents/` — Agentes: DÉDALO, ARGOS, APOLO, HERMES, KENON, METIS, TALOS

El principio de **Zero Cross-Talk** establece aislamiento absoluto para prevenir bucles de ejecución y conflictos de permisos. Sin embargo, el ADR-007 contempla habilitar hooks bidireccionales una vez que se cumplan las condiciones de seguridad.

## Condiciones para Activación

- [ ] Auditoría de seguridad completada por KENON con 100% de cumplimiento
- [ ] Firma de comandos implementada (HMAC-SHA256)
- [ ] Límite de profundidad de 3 niveles
- [ ] Rate limiting: 10 llamadas/minuto máximo
- [ ] Circuit breaker: si hay >5 errores en 1 minuto, desactivar por 5 minutos
- [ ] Log completo de todas las comunicaciones en `.agents/logs/bridge.log`

## Arquitectura Propuesta

```
┌─────────────────────┐          ┌──────────────────────┐
│   Antigravity 2.0   │          │      OpenCode        │
│                     │          │                      │
│  DÉDALO, ARGOS,     │◄────────►│  Aletheia, Kosmos,   │
│  APOLO, HERMES,     │  Hooks   │  Metis, Mnemosyne    │
│  KENON, METIS, TALOS│  Seguros │                      │
└─────────┬───────────┘          └──────────┬───────────┘
          │                                  │
          │     ┌──────────────────────┐     │
          └─────►   .agents/hooks.json  ◄─────┘
                │   (Lifecycle Hooks)   │
                └──────────────────────┘
                          │
                ┌─────────▼──────────┐
                │  Zero Trust Proxy  │
                │  (Validación,      │
                │   Firma, Rate      │
                │   Limit, Log)      │
                └─────────┬──────────┘
                          │
                ┌─────────▼──────────┐
                │  .agents/logs/     │
                │  bridge.log        │
                └────────────────────┘
```

## Formato de Payload

```json
{
  "version": "1.0",
  "from": "metis|DÉDALO",
  "to": "kosmos|ARGOS",
  "type": "task_complete|context_request|signal",
  "payload": {
    "task_id": "uuid",
    "result_summary": "...",
    "artifacts": ["path/to/file.md"]
  },
  "signature": "hmac-sha256(version+from+to+payload+timestamp)",
  "timestamp": "2026-05-21T00:00:00Z",
  "ttl_seconds": 300
}
```

## Políticas de Seguridad

1. **Firma obligatoria**: Cada mensaje debe incluir firma HMAC-SHA256
2. **Expiración**: TTL máximo de 300 segundos por mensaje
3. **Profundidad máxima**: 3 llamadas encadenadas (A→B→C→fin)
4. **Rate limit**: 10 mensajes/minuto por agente
5. **Circuit breaker**: 5 errores → pausa 5 minutos
6. **Log completo**: Todas las comunicaciones se registran en bridge.log
7. **Sin ejecución directa**: Los hooks solo transmiten señales, nunca comandos shell
8. **Validación de origen**: Solo agentes registrados pueden enviar mensajes

## Estados del Bridge

| Estado | Descripción | Acción requerida |
|:-------|:------------|:-----------------|
| 🔴 Disabled | Aislamiento total (estado actual) | Auditoría de seguridad |
| 🟡 Monitor | Solo logs, sin acción | Validación manual |
| 🟢 Active | Comunicación bidireccional permitida | — |

## Referencias

- ADR-003: Zonas de Autonomía del Vault
- ADR-007: Optimización de Arquitectura KAOS
- `.agents/AGENTS.md`: Principio de Aislamiento Absoluto
- `.agents/hooks.json`: Configuración actual de hooks
- `.opencode/opencode.json`: Configuración de agentes OpenCode
