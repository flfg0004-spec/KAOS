---
name: ingest
description: Lanza ingesta batch de URLs o topics en background
---

# /ingest

Ingiere contenido al vault `.memory/` usando el pipeline de ingesta.

## Uso

```
/ingest url https://ejemplo.com/articulo
/ingest wikipedia "Inteligencia Artificial"
/ingest file ruta/al/archivo.md
```

## Comportamiento

- Corre como tarea async (no bloquea el prompt)
- SHA-256 dedup contra `ingest/queue/manifest.json`
- Escribe en `raw/<slug>.md` — append-only, nunca sobrescribe
- Después de ingestar, ejecuta automáticamente `/health`

## Ver resultados

```
/tasks
```
