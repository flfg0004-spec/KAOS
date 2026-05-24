---
name: explore
description: Exploración rápida con Gemini Flash + consolidación DeepSeek
---

# /explore

Exploración rápida usando Gemini Flash (GRATIS). Vincula automáticamente con DeepSeek si decides consolidar.

## Uso

```
/explore "tema a explorar"
```

## Flujo

1. llama `agy_ask_flash()` con el prompt de exploración
2. guarda resultado en `.memory/bridge/reports/response-{timestamp}.md`
3. actualiza `_pipeline/context.json` con `cross_agent.flash_exploration`
4. **pregunta**: ¿solo explorar o explorar + pipeline?
   - "explorar" → muestra resultado, termina
   - "pipeline" → ejecuta automáticamente `vault.py pipeline init --topic "tema" --profile "desarrollo"`
   - El pipeline detecta la exploración Flash y la reusa como contexto

## Salida

- reporte en `.memory/bridge/reports/`
- `cross_agent.flash_exploration` actualizado
- pipeline ID si se consolida

## Anti-patrones

- ❌ Usar Flash para producir artefactos finales (usar DeepSeek para eso)
- ❌ Ignorar los reports de bridge (son el contexto del pipeline)
- ❌ Re-explorar lo que Flash ya exploró (el pipeline lo detecta automáticamente)
