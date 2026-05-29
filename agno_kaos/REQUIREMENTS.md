# A(gnO)-KAOS Requirements

## Core (obligatorio)
- Python >= 3.11
- `pip install -e agno_kaos/` — instala el paquete con dependencias base

## Postgres (opcional)
- Docker con docker-compose.agno.yml
  `docker compose -f docker-compose.agno.yml up -d`
- `pip install psycopg2-binary`

## Development
- `pip install pytest pytest-asyncio`

## Verificación
```bash
python agno_kaos/check_deps.py
```
