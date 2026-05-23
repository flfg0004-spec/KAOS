---
name: consolidate
description: Ejecuta ciclo de sueño NREM/REM para consolidar conocimiento
---

# /consolidate

Ejecuta el ciclo de consolidación de memoria (sleep-time compute) sobre el vault.

## Flujo

1. NREM (70%): DBSCAN clustering sobre embeddings → LLM destila patrones
2. REM (30%): Entity linking cross-dominio → síntesis de esquemas L3

## Uso

```
/consolidate
```

## Output

- L1 (Episodic): CodeExperience DB actualizada
- L2 (Semantic): Knowledge Graph MCP + conceptos wiki
- L3 (Schema): Patrones consolidados en schema/

## Monitoreo

```
/tasks
```
