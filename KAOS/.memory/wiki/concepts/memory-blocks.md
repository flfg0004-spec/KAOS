---
audience: agent
type: concept
source: Letta (MemGPT) — arXiv:2310.08560
related: [compile-then-query, add-only-extraction]
tags: ["subject/agent", "subject/agentes", "subject/arquitectura", "subject/concept", "subject/extraction", "subject/kaos", "subject/letta", "subject/memgpt"]
---

# Memory Blocks

Segmentos con nombre dentro del Core Memory de la arquitectura [[arxiv-2310-08560-memgpt]]. Cada bloque tiene label, valor (texto), límite de tokens y flag read_only.

## Características
- **Labels**: human, persona, system, task (nombres semánticos)
- **Edición vía tool calls**: `memory`, `memory_apply_patch`, `memory_wipe`
- **Compartidos**: un bloque puede attacharse a múltiples agentes (shared memory en sistemas multi-agente)
- **Last write wins**: sin merge automático entre agentes

## Aplicación en KAOS
Los agentes de KAOS podrían tener bloques de memoria compartidos (ej: "human" con preferencias del usuario, "system" con estado del sistema).
[[kosmos]] es quien diseña esta arquitectura de memoria en KAOS.


## Referencias Cruzadas
- [investigacion-sistemas-memoria](../raw/investigacion-sistemas-memoria.md) — menciones [[memory-blocks]]
- Relacionado: [[sin-páginas-huérfanas]]
- Relacionado: [[estado-memoria-sesion]]
- Relacionado: [[tool-calling]]
- Relacionado: [[add-only-extraction]]
