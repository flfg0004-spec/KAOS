# SECURITY.md — Seguridad del Ecosistema KAOS

## ⚠️ Estado Actual: Keys Expuestas en Historial Git

El día **2026-05-25** se detectó que las siguientes API keys fueron comprometidas
porque existían en el archivo `.env` cuando este fue añadido al repositorio git.
Aunque `.env` ya está en `.gitignore`, las claves permanecen en el historial de
commits anteriores.

## Keys Expuestas

| Variable | Servicio | Estado |
|----------|----------|--------|
| `DEEPSEEK_API_KEY` | DeepSeek (LLM Provider) | **TO-ROTATE** |
| `OPENCODE_GO_KEY` | OpenCode AI (LLM Provider) | **TO-ROTATE** |
| `EXA_API_KEY` | Exa Search API | **TO-ROTATE** |
| `OBSIDIAN_API_KEY` | Obsidian Local REST API | **TO-ROTATE** |
| `TELEGRAM_BOT_TOKEN` | Telegram Bot API | **TO-ROTATE** |

## Plan de Rotación

Cada key debe ser regenerada en su servicio correspondiente, luego actualizada
en `.env`, y finalmente el historial git debe ser purgado.

### Paso 1: Regenerar cada key

| Key | Dónde regenerar |
|-----|-----------------|
| `DEEPSEEK_API_KEY` | https://platform.deepseek.com/api_keys |
| `OPENCODE_GO_KEY` | https://opencode.ai/keys |
| `EXA_API_KEY` | https://dashboard.exa.ai/api-keys |
| `OBSIDIAN_API_KEY` | Configuración del plugin Obsidian Local REST API |
| `TELEGRAM_BOT_TOKEN` | Chatear con [@BotFather](https://t.me/botfather) en Telegram |

### Paso 2: Ejecutar script de rotación

```powershell
.\scripts\rotate-keys.ps1
```

Este script guiará la recolección de las nuevas claves, actualizará `.env`,
y opcionalmente purgará el historial git.

### Paso 3: Verificar y reiniciar

Después de rotar las claves:

1. **Open WebUI**: Si cambió `OPENCODE_GO_KEY`, reiniciar el contenedor:
   ```powershell
   wsl.exe -d Ubuntu docker compose -f docker-compose.owui.yml restart open-webui
   ```

2. **Telegram Bot**: Si cambió `TELEGRAM_BOT_TOKEN`, reiniciar el bot.

3. **Obsidian MCP**: Si cambió `OBSIDIAN_API_KEY`, actualizar también en
   `owui/mcpo-config/mcp-servers.json` (campo `OBSIDIAN_API_KEY` en `kaos-obsidian`).

## Buenas Prácticas

1. `.env` NUNCA debe ser añadido al repositorio (ya está en `.gitignore` ✅)
2. Usar `.env.template` con valores placeholder para nuevos desarrolladores
3. Las claves en `mcp-servers.json` también deben ser placeholders (no valores reales)
4. Rotar claves periódicamente (cada 90 días recomendado)
5. No hardcodear claves en ningún script — siempre usar variables de entorno

## Pasos Realizados (2026-05-25)

- [x] Verificar que `.env` esté en `.gitignore`
- [x] Verificar que `.env.template` exista con placeholders
- [x] Marcar keys expuestas como `[TO-ROTATE]` en `.env`
- [x] Crear `scripts/rotate-keys.ps1` para automatizar rotación
- [ ] Regenerar cada key en su servicio
- [ ] Ejecutar `scripts/rotate-keys.ps1`
- [ ] Purgar historial git con `git filter-branch`
- [ ] Forzar push a remoto
