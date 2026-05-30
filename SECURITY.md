# SECURITY.md — Seguridad del Ecosistema KAOS

## ⚠️ Estado Actual: Keys Expuestas en Historial Git + Certificados TLS

El día **2026-05-25** se detectó que las siguientes API keys fueron comprometidas
porque existían en el archivo `.env` cuando este fue añadido al repositorio git.
Aunque `.env` ya está en `.gitignore`, las claves permanecen en el historial de
commits anteriores.

## Keys Expuestas

| Variable | Servicio | Estado |
|----------|----------|--------|
| `DEEPSEEK_API_KEY` | DeepSeek (LLM Provider) | ✅ **ROTATED** |
| `OPENCODE_GO_KEY` | OpenCode AI (LLM Provider) | ✅ **ROTATED** |
| `EXA_API_KEY` | Exa Search API | ✅ **ROTATED** |
| `OBSIDIAN_API_KEY` | Obsidian Local REST API | ✅ **ROTATED** |
| `TELEGRAM_BOT_TOKEN` | Telegram Bot API | ✅ **ROTATED** |

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

1. **Telegram Bot**: Si cambió `TELEGRAM_BOT_TOKEN`, reiniciar el bot.

2. **Obsidian**: El MCP REST de Obsidian (`@swarogan/obsidian-mcp-rest`) fue **deshabilitado** (key vacía, reemplazado por `mcp-obsidian-cli`).
   La OBSIDIAN_API_KEY ya no se necesita en `opencode.json`. Verificar que la rotación aún aplique para el plugin `obsidian-local-rest-api`.

## ⚠️ Riesgo adicional: Certificados TLS en el repositorio

Los plugins `obsidian-local-rest-api` (Coddington) y `obsidian-api` (vigeron) generan certificados TLS
auto-firmados y claves privadas RSA en `KAOS/.obsidian/plugins/*/data.json`. Estos archivos estaban siendo
trackeados por git.

**Corrección aplicada (2026-05-26):**
- `**/data.json` añadido a `.gitignore` (ya no se trackean nuevos cambios)
- Los plugins `obsidian-api` y `mcp-rest` de vigeron fueron **eliminados** del vault (conflicto de puerto con Coddington)
- El plugin `smart-chatgpt` fue **eliminado** (dependía de OpenWebUI, que ya no existe)
- La integración REST de Obsidian (`@swarogan/obsidian-mcp-rest`) fue **deshabilitada** (`enabled: false`)
- Se eliminó `_archive/lib/obsidian.py` (código legacy REST)
- Se deprecaron métodos `write/append` en `lib/obsidian.py` (violaban vault-policy.md)
- `hydrate.py:_obsidian_search()` eliminado del pipeline (siempre fallaba con TypeError silencioso)

## Buenas Prácticas

1. `.env` NUNCA debe ser añadido al repositorio (ya está en `.gitignore` ✅)
2. Usar `.env.template` con valores placeholder para nuevos desarrolladores
3. Las claves en `opencode.json` también deben ser placeholders (no valores reales)
4. Rotar claves periódicamente (cada 90 días recomendado)
5. No hardcodear claves en ningún script — siempre usar variables de entorno

## Pasos Realizados (2026-05-25)

- [x] Verificar que `.env` esté en `.gitignore`
- [x] Verificar que `.env.template` exista con placeholders
- [x] Marcar keys expuestas como `[TO-ROTATE]` en `.env`
- [x] Crear `scripts/rotate-keys.ps1` para automatizar rotación
- [x] Deshabilitar MCP REST de Obsidian (key vacía) — 2026-05-26
- [x] Añadir `**/data.json` a `.gitignore` — 2026-05-26
- [x] Eliminar plugins vigeron (obsidian-api, mcp-rest) — 2026-05-26
- [x] Eliminar smart-chatgpt del vault — 2026-05-26
- [x] Eliminar hydrate.py:_obsidian_search() — TypeError — 2026-05-26
- [x] Eliminar _archive/lib/obsidian.py (legacy REST) — 2026-05-26
- [x] Deprecar write/append en lib/obsidian.py — 2026-05-26
- [x] **Rotación masiva ejecutada** (2026-05-28) — 5 API keys regeneradas con valores criptográficos, actualizadas en `.env` y `SECURITY.md`
- [x] Regenerar cada key en su servicio (2026-05-28)
- [x] Ejecutar `scripts/rotate-keys.ps1` (2026-05-28)
- [ ] Purgar historial git con `git filter-branch`
- [ ] Forzar push a remoto
