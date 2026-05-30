# Langfuse Setup — Configuración Inicial

## Estado Actual

Langfuse está corriendo en **http://localhost:3001** con todos sus servicios adjuntos:
- **Postgres 16** (`langfuse-pg-data` volume) — base de datos principal
- **OTEL Collector** (puerto `4318`) — receptor de telemetría OpenTelemetry
- **Clickhouse** — no presente en esta configuración (modo Postgres-only)

Es un **fresh install**: no hay cuenta admin, proyectos ni API keys configuradas aún.

---

## Paso 1: Crear Cuenta Admin

1. Abre http://localhost:3001 en el navegador
2. Haz clic en **"Sign up"** (registro)
3. Completa los datos:
   - **Name**: `Admin KAOS`
   - **Email**: `admin@kaos.local`
   - **Password**: Define una contraseña segura (ej. `kaos-admin-2026`)
4. Haz clic en **"Create account"**

> ⚠️ La primera cuenta creada es automáticamente **admin** de la instancia.

---

## Paso 2: Verificar Instancia

1. Una vez dentro, ve a **Settings → Organization**
2. Verifica que el nombre de la organización sea el correcto (puedes renombrarla a "KAOS")
3. Opcional: invita a otros miembros si los hay

---

## Paso 3: Crear Proyecto de Tracing

1. En la barra lateral, haz clic en **"Projects"**
2. Haz clic en **"New Project"**
3. Nombre: `KAOS Ecosystem`
4. Descripción (opcional): `Tracing de agentes y pipelines del ecosistema KAOS`
5. Haz clic en **"Create"**

Proyectos adicionales recomendados:

| Proyecto | Propósito |
|----------|-----------|
| `KAOS Agents` | Trazas de agentes (Aletheia, Kratos, Mnemosyne, etc.) |
| `KAOS Pipelines` | Trazas de pipelines de Open WebUI |
| `KAOS Tests` | Trazas de tests y evaluaciones |

---

## Paso 4: Generar API Keys

Para cada proyecto que quieras monitorear:

1. Dentro del proyecto, ve a **Settings → API Keys**
2. Haz clic en **"New API Key"**
3. Copia **inmediatamente** los valores de:
   - **Secret Key** (`sk-...`)
   - **Public Key** (`pk-...`)
4. Guárdalos en `.env` del proyecto KAOS:

```ini
# .env — Langfuse Credentials
LANGFUSE_SECRET_KEY=sk-... (el que generaste)
LANGFUSE_PUBLIC_KEY=pk-... (el que generaste)
LANGFUSE_HOST=http://localhost:3001
```

5. También actualiza `docker-compose.langfuse.yml` si deseas usar estas keys:

```yaml
# En el servicio langfuse, agrega:
LANGFUSE_SECRET_KEY: ${LANGFUSE_SECRET_KEY}
LANGFUSE_PUBLIC_KEY: ${LANGFUSE_PUBLIC_KEY}
```

---

## Paso 5: Verificar Pipeline OTEL → Langfuse

Langfuse recibe trazas de OpenTelemetry a través del `otel-collector` en el puerto `4318`.

### 5.1 Verificar el OTEL Collector

```powershell
# Verificar que el collector está corriendo
wsl.exe -d Ubuntu docker ps --filter name=otel-collector --format "{{.Names}} | {{.Status}}"

# Ver logs del collector
wsl.exe -d Ubuntu docker logs kaos-otel-collector-1 --tail 20
```

### 5.2 Enviar un trace de prueba

El OTEL collector expone el endpoint HTTP en `http://localhost:4318/v1/traces`.

Prueba rápida con curl desde WSL:

```bash
curl -X POST "http://127.0.0.1:4318/v1/traces" \
  -H "Content-Type: application/json" \
  -d '{
    "resourceSpans": [{
      "resource": { "attributes": [{ "key": "service.name", "value": { "stringValue": "test-service" } }] },
      "scopeSpans": [{
        "scope": { "name": "test" },
        "spans": [{
          "traceId": "0af7651916cd43dd8448eb211c80319c",
          "spanId": "b7ad6b7169203331",
          "name": "test-span",
          "startTimeUnixNano": "1680000000000000000",
          "endTimeUnixNano": "1680000000100000000"
        }]
      }]
    }]
  }'
```

### 5.3 Verificar en Langfuse UI

1. Ve al proyecto que creaste en Langfuse
2. Busca la pestaña **"Traces"**
3. Deberías ver el trace de prueba (puede tardar unos segundos)

### 5.4 Configurar integración desde Open WebUI

Para que Open WebUI envíe trazas a Langfuse, añade estas variables a `docker-compose.owui.yml`:

```yaml
# En el servicio open-webui:
environment:
  - OTEL_EXPORTER_OTLP_ENDPOINT=http://host.docker.internal:4318
  - OTEL_SERVICE_NAME=open-webui
  - ENABLE_OTEL=true
```

Luego reinicia Open WebUI:

```powershell
wsl.exe -d Ubuntu docker compose -f docker-compose.owui.yml restart open-webui
```

---

## Paso 6: Verificar End-to-End

```powershell
# 1. Langfuse responde
curl -s -o /dev/null -w "%{http_code}" http://127.0.0.1:3001

# 2. OTEL collector responde
curl -s -o /dev/null -w "%{http_code}" http://127.0.0.1:4318

# 3. Ver logs de Langfuse (sin errores)
wsl.exe -d Ubuntu docker logs kaos-langfuse-1 --tail 10
```

---

## Referencia: Variables de Entorno

| Variable | Descripción | Default |
|----------|-------------|---------|
| `DATABASE_URL` | Conexión a Postgres | `postgresql://postgres:postgres@db:5432/langfuse` |
| `NEXTAUTH_SECRET` | Secreto de autenticación | `change-me-langfuse-secret` (cambiar en producción) |
| `NEXTAUTH_URL` | URL pública de Langfuse | `http://localhost:3001` |
| `SALT` | Salt para hashing de passwords | `change-me-langfuse-salt` (cambiar en producción) |
| `TELEMETRY_ENABLED` | Enviar telemetría a Langfuse | `false` |
| `OTEL_EXPORTER_OTLP_ENDPOINT` | Endpoint OTEL | `http://otel-collector:4318` |

---

## Troubleshooting

| Problema | Causa | Solución |
|----------|-------|----------|
| `ECONNREFUSED` al acceder | Postgres no listo | Esperar 10-15s, el healthcheck tarda |
| Error 500 en signup | `NEXTAUTH_SECRET` o `SALT` incorrectos | Verificar `.env` |
| No aparecen trazas | OTEL collector no configurado | Verificar paso 5 |
| Login no funciona | Base de datos corrupta | `wsl -d Ubuntu docker compose -f docker-compose.langfuse.yml down -v && up -d` |

---

## Seguridad

- **Cambiar `NEXTAUTH_SECRET` y `SALT`** de sus valores por defecto (`change-me-...`)
- No exponer el puerto 3001 a internet sin HTTPS y autenticación
- Las API keys de Langfuse tienen permisos de proyecto: generar keys separadas por proyecto
- Rotar keys periódicamente (ver `SECURITY.md` y `scripts/rotate-keys.ps1`)
