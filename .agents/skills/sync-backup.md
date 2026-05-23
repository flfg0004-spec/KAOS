---
name: sync-backup
description: Backup del vault a almacenamiento externo
---

# /sync-backup

Sincroniza el vault `.memory/` con backup externo.

## Uso

```
/sync-backup
```

## Comportamiento

- Git commit + push de `.memory/` (si hay remote configurado)
- Backup a Google Cloud Storage (si configurado)
- Verifica integridad post-backup con `/health`

## Configuración

Requiere variables de entorno:
- `GIT_REMOTE` — URL del remote git (opcional)
- `GCS_BUCKET` — bucket de Google Cloud Storage (opcional)
- `GCS_PREFIX` — prefijo para los archivos (opcional)
