---
type: adr
title: 'ADR-008: Plugin Architecture Decision'
aliases:
- adr-008-plugin-decision
tags:
- adr
created: '2026-05-20'
modified: '2026-05-20'
confidence: media
status: draft
---

# ADR-008: Plugin Architecture Decision

## Contexto

La investigación de Aletheia (raw/evaluacion-plugins-ecosistema.md) evaluó 4 plugins del ecosistema OpenCode para determinar su adopción en KAOS. Se requiere una decisión formal documentada.

## Opciones Evaluadas

| Plugin | Evaluación | Veredicto |
|--------|-----------|-----------|
| opencode-firecrawl | Integración nativa de Firecrawl, pero no en npm | ⏳ Posponer |
| opencode-supermemory | Memoria entre sesiones, pero KAOS ya tiene vault | ❌ No adoptar |
| opencode-background-agents | Delegación async, pero task tool nativa es suficiente | ⏳ Posponer |
| @opencode-ai/sdk | SDK oficial TypeScript para OpenCode | ✅ Adoptar |

## Decisión

1. **Adoptar @opencode-ai/sdk** — SDK oficial para automatización programática.
2. **No adoptar opencode-supermemory** — KAOS ya tiene vault de memoria propio (ADR-001).
3. **Posponer opencode-firecrawl** — hasta que esté disponible en npm; MCP firecrawl actual es suficiente.
4. **Posponer opencode-background-agents** — OpenCode ya tiene `task` tool nativa para subagentes.

## Justificación

- El SDK oficial (`@opencode-ai/sdk@1.15.5`) es la única dependencia recomendada porque permite automatización sin servidor externo.
- Los plugins comunitarios evaluados no están disponibles como paquetes npm, requiriendo instalación manual desde GitHub.
- KAOS ya implementa las funcionalidades que estos plugins ofrecen (vault de memoria, subagentes vía task).
- Agregar dependencias externas aumentaría la superficie de mantenimiento sin beneficio significativo.

## Consecuencias

### Positivas
- Sin dependencias externas innecesarias.
- SDK oficial disponible para automatización programática (Sprint 4 POC).
- Mantenimiento reducido al mínimo.

### Negativas
- No se obtienen beneficios de plugins comunitarios (memoria entre sesiones, async delegation).
- El POC SDK requiere npm install @opencode-ai/sdk.

### Neutrales
- La situación puede reevaluarse cuando los plugins estén disponibles en npm.
- El vault de KAOS continuará siendo el sistema de memoria principal.

## Estado

Aceptada

## Referencias
- raw/evaluacion-plugins-ecosistema.md
- ADR-001: Sistema de Memoria de KAOS
- ADR-007: Optimización de Arquitectura
- https://opencode.ai/docs/ecosystem

