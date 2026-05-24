---
name: explore
description: Exploración rápida con Gemini Flash + consolidación DeepSeek
---

# /explore

Exploración rápida usando Gemini Flash (GRATIS). Para iterar rápido antes de consolidar con DeepSeek.

## Uso

```
/explore "tema a explorar"
```

## Flujo

1. llama `agy_ask_flash()` con el prompt de exploración
2. guarda resultado en `.memory/bridge/reports/`
3. actualiza `_pipeline/context.json` con `cross_agent.flash_exploration`
4. pregunta: ¿iterar con Flash o consolidar con DeepSeek?

## Para consolidar

Ejecutar:
```
vault.py pipeline init --topic "tema" --profile "desarrollo"
```

El pipeline detectará automáticamente la exploración Flash previa.

## Anti-patrones

- ❌ Usar Flash para producir artefactos finales
- ❌ Ignorar los reports de bridge
- ❌ Re-explorar lo que Flash ya exploró
