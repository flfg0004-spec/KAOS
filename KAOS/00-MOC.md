---
type: moc
title: "Mapa de Contenido — Vault Enriquecido KAOS"
aliases: [moc, index, mapa]
tags: [moc, kaos, index]
created: 2026-05-21
modified: 2026-05-21
---

# Mapa de Contenido — Vault Enriquecido KAOS

## Agentes (1-agentes/)
```dataview
TABLE role AS Rol, file.outlinks AS Conexiones
FROM "01-agentes"
SORT file.name ASC
```

## Conceptos (2-conceptos/)
```dataview
TABLE confidence AS Confianza, status AS Estado, agent AS Agente
FROM "02-conceptos"
SORT file.name ASC
```

## Referencias (3-referencias/)
```dataview
TABLE category AS Categoria, confidence AS Confianza
FROM "03-referencias"
SORT file.name ASC
```

## Esquema (4-esquema/)
```dataview
TABLE file.name AS ADR
FROM "04-esquema"
SORT file.name ASC
```
