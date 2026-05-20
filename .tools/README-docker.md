# KAOS Docker Infrastructure

## Servicios

| Servicio | Puerto | URL | Propósito |
|----------|--------|-----|-----------|
| SearXNG | 8888 | http://127.0.0.1:8888 | Metasearch privado (100+ motores) |
| Crawl4AI | 11235 | http://127.0.0.1:11235 | Web crawler masivo asíncrono |
| txtai | 8000 | http://127.0.0.1:8000 | Knowledge base con Graph RAG |

## Uso

```bash
# Iniciar todos los servicios
docker compose -f .tools/docker-compose.yml up -d

# Ver estado
docker compose -f .tools/docker-compose.yml ps

# Ver logs
docker compose -f .tools/docker-compose.yml logs -f

# Detener
docker compose -f .tools/docker-compose.yml down

# Actualizar imágenes
docker compose -f .tools/docker-compose.yml pull
```

## Integración con KAOS

### SearXNG
- Buscar: `curl "http://127.0.0.1:8888/search?format=json&q=consulta"`
- Formato JSON para agentes, HTML para debugging humano

### Crawl4AI
- Crawlear: `curl -X POST "http://127.0.0.1:11235/crawl" -H "Content-Type: application/json" -d '{"url":"https://ejemplo.com"}'`
- Auto-extracción LLM vía `LLMExtractionStrategy`

### txtai
- Indexar: `curl -X POST "http://127.0.0.1:8000/index" -H "Content-Type: application/json" -d '{"text":"contenido","tags":["concepto"]}'`
- Buscar: `curl "http://127.0.0.1:8000/search?query=consulta"`
- RAG: `curl "http://127.0.0.1:8000/rag" -H "Content-Type: application/json" -d '{"query":"consulta","context":"texto de fondo"}'`

## Plugins de OpenCode

Agregar al `opencode.json`:

```json
{
  "mcp": {
    "searxng": {
      "type": "local",
      "command": ["npx", "-y", "@anthropic/searxng-mcp", "--url", "http://127.0.0.1:8888"],
      "enabled": true
    },
    "crawl4ai": {
      "type": "local",
      "command": ["npx", "-y", "@anthropic/crawl4ai-mcp", "--url", "http://127.0.0.1:11235"],
      "enabled": true
    },
    "txtai": {
      "type": "local",
      "command": ["npx", "-y", "@anthropic/txtai-mcp", "--url", "http://127.0.0.1:8000"],
      "enabled": true
    }
  }
}
```
