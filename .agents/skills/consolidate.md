---
name: consolidate
description: Ejecuta DBSCAN consolidation + quality check
---

# /consolidate

Consolida la memoria episódica (CodeExperience) en patrones semánticos usando DBSCAN.

## Uso

```
/consolidate
```

## Proceso

1. Lee experiencias de CodeExperience DB (confidence > 0.3)
2. DBSCAN clustering (eps=0.3, min_samples=3)
3. Asigna pattern_category a cada cluster
4. Log de compresión en `cache/compression-log.json`
5. Recalcula quality score post-consolidación

## Ver resultados

```
vault.py consolidate
```

## Schedule

Correr semanalmente (domingos 22:00).
