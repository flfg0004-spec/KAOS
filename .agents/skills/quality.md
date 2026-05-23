---
name: quality
description: Quality score + reporte del vault
---

# /quality

Calcula score de calidad multidimensional del vault.

## Uso

```
/quality
```

## Dimensiones

- Veracidad (V) — truthfulness de fuentes
- Coherencia (C) — consistencia interna
- Completitud (CP) — coverage de conceptos
- Reproducibilidad (R) — trazabilidad de fuentes
- Utilidad (U) — relevancia práctica

## Output

- Score compuesto (0-100)
- Score por dimensión
- Recomendaciones de mejora
