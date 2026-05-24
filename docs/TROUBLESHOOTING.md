# Troubleshooting — Problemas Comunes

## 1. `agy --print` no produce output

**Síntoma**: `agy --print "hola"` no muestra nada en stdout.

**Causa**: agy usa TUI text dripping que no se captura en pipes/subprocess.

**Solución**: Usar el MCP bridge (`agy_ask_flash/sonnet/opus`) que lee `brain/{conv-id}/transcript.jsonl` post-ejecución. No intentar capturar stdout directamente.

**Verificación**: `py -3 .memory/_scripts/lib/agy_client.py` y testear `call_azy("hola", tier="flash")`.

## 2. `vault.py health --auto` devuelve exit code 1

**Síntoma**: Health check falla sin errores claros.

**Causa común**: Cambios sin commit en el vault (git dirty).

**Solución**: `git status` para ver archivos modificados. Hacer commit o agregar a .gitignore.

**Verificación**: `py -3 .memory/_scripts/vault.py health` (sin --auto) para ver el reporte completo.

## 3. Tests fallan con timeout

**Síntoma**: `tests/run.py` muestra `⏰ TIMEOUT` en algunos tests.

**Causa común**: Tests que cargan el modelo de embeddings (sentence-transformers/fastembed) pueden tardar >60s si el modelo no está cachead.

**Solución**: 
- Usar `--fast` para saltar tests lentos (embeddings)
- El modelo se cachea en `~/.cache/huggingface/` después de la primera carga
- Aumentar `TEST_TIMEOUT` en `tests/run.py` si es necesario

**Verificación**: `py -3 .memory/_scripts/tests/run.py --fast`

## 4. Modelo de agy no cambia

**Síntoma**: `agy_ask_opus()` sigue usando Gemini Flash.

**Causa**: Race condition en `settings.json`. Dos procesos intentan cambiar el modelo simultáneamente.

**Solución**: El bridge tiene file locking (`_acquire_lock timeout=15`). Si ves este error, espera y reintenta. Verificar que no haya procesos agy colgados.

**Verificación**: `Get-Process agy` — matar procesos zombies con `Stop-Process`.

## 5. MCP server no se conecta

**Síntoma**: OpenCode muestra "MCP server not found" o timeout.

**Causa común**: El server no está en `PATH` o el comando falla.

**Solución**: Verificar que el comando del MCP server funciona standalone:
```bash
py -3 .memory/_scripts/mcp_agy_bridge.py
# Debe iniciar y esperar en stdio
```

**Verificación**: `py -3 -c "import json; d=json.load(open('.opencode/opencode.json')); print('MCPs:', len(d['mcp']))"`
