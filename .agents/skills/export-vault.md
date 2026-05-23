---
name: export-vault
description: Genera visualizaciones Mermaid del vault
---

# /export-vault

Genera diagramas Mermaid del vault para visualizar el grafo de conocimiento,
pipeline, calidad y timeline.

## Uso

```
/export-vault
```

## Archivos generados

| Archivo | Contenido |
|---------|-----------|
| `VIZ_GRAPH.md` | Grafo del conocimiento (wikilinks entre conceptos) |
| `VIZ_PIPELINE.md` | Diagrama del pipeline de agentes |
| `VIZ_QUALITY.md` | Timeline de scores de calidad |
| `VIZ_TIMELINE.md` | Timeline de actividad del vault |

## Visualización

Estos archivos .md se renderizan automáticamente en:
- GitHub (subiendo el vault)
- VS Code (con extensión Mermaid)
- Obsidian (nativo)
- Cualquier visor markdown con Mermaid
