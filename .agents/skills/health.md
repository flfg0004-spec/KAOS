---
name: health
description: Health check + lint del vault
---

# /health

Ejecuta verificación de salud del vault `.memory/`.

## Uso

```
/health
```

## Checks

- Lint: wikilinks rotos, orphan pages, frontmatter faltante
- Cobertura: % de archivos raw/ con fuentes y matriz de confianza
- Integridad: estructura raw/wiki/schema completa
- Cache: hydrate cache no corrupto

## Exit codes

- 0: saludable
- 1: issues encontrados (revisar output)
