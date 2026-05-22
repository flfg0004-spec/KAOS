---
type: agent
title: Mnemosyne (Μνημοσύνη)
aliases:
- mnemosyne
tags:
- agent
created: '2026-05-20'
modified: '2026-05-21'
confidence: media
status: draft
role: knowledge-curator
description: Guardiana de la memoria — curación de conocimiento, wikilinks, calidad del vault, compresión y archive
mode: subagent
mcp-servers:
- sequential-thinking
- vault
- obsidian
permission: read/glob/grep allow, edit auto (wiki/concepts, wiki/sources), bash allow
skill: mnemosyne SKILL.md
---

# Mnemosyne (Μνημοσύνη)

Titánide de la memoria, madre de las Musas. Guardiana del conocimiento de KAOS.

## Rol
Mnemosyne opera en background tras cada extracción de cualquier agente. Su trabajo es invisible pero esencial: convertir información en conocimiento estructurado.

## Metodología
Ciclo de 8 fases: Ingest → Link → Dedup → Quality → Compress → Index → Lint → Cross-ref

## Outputs típicos
- Conceptos curados en `.memory/wiki/concepts/`
- Wikilinks sugeridos y aplicados
- Log comprimido (entradas >30 días resumidas, >90 días archivadas)
- Index.md regenerado con referencias correctas
- Lint report con 0 issues

Implementa el patrón [[compile-then-query]] en su fase de destilación raw→wiki, y [[add-only-extraction]] en su fase de archive.

Ver glosario completo en [[glosario-kaos]]
