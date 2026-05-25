---
type: guide
title: Sistema DUAL — Gemini Flash + DeepSeek
aliases:
- dual-system
- dual
tags:
- guide
- dual
- gemini
- deepseek
created: '2026-05-19'
modified: '2026-05-25'
confidence: alta
status: published
---

[[index]] [[checkpoint]] [[vault]] [[adr]] [[gestion-conocimiento]]

# Sistema DUAL: Gemini Flash + DeepSeek

Guía rápida para el desarrollo iterativo usando el sistema dual de KAOS.

## Qué es

Sistema DUAL = dos modelos trabajando juntos:

| Modelo | Plataforma | Costo | Velocidad | Propósito |
|--------|-----------|-------|-----------|-----------|
| **Gemini 3.5 Flash** | agy (Antigravity CLI) | **GRATIS** | <2 min | Exploración, prototipado, review |
| **DeepSeek v4** | OpenCode | Variable | 5-15 min | Consolidación, pipeline formal, producción |

## Cuándo usar cada uno

### Usar Gemini Flash (rápido y gratis)
- Explorar una idea nueva
- Debug rápido de un error
- Code review antes de commit
- Prototipar un script
- Escribir tests unitarios
- Refinar un prompt
- Health check / lint / quality

### Usar DeepSeek (pipeline formal)
- Consolidar una exploración exitosa
- Pipeline completo multi-agente
- ADRs y arquitectura
- Producción final

## Cómo explorar con Gemini Flash

```
/explore "describe qué quieres explorar"
```

Esto:
1. Ejecuta `agy_ask_flash()` con tu prompt
2. Guarda el resultado en `.memory/bridge/reports/`
3. Deja el contexto listo para DeepSeek

## Cómo consolidar con DeepSeek

```
vault.py pipeline init --topic "tema" --profile "desarrollo"
```

El pipeline detecta automáticamente si hay exploración Flash reciente y la usa como contexto.

## El vault como estado único

Ambos modelos leen y escriben al mismo vault:

```
.memory/
├── bridge/reports/    ← Output de Gemini Flash
├── _pipeline/         ← Estado del pipeline DeepSeek
├── bridge/signals/    ← Requests entre sistemas
├── raw/               ← Investigaciones
└── wiki/              ← Conocimiento curado
```

## Medir la velocidad

```
vault.py speed
```

Muestra:
- Llamadas Flash en últimas 24h/1h
- Ratio Flash→Production
- Time-to-commit promedio
- Reportes recientes

## Anti-patrones a evitar

- ❌ **No usar Flash para producir artefactos finales** — Flash explora, DeepSeek produce
- ❌ **No ignorar los reports de bridge** — son el insumo del pipeline
- ❌ **No re-explorar lo que Flash ya exploró** — el pipeline lo detecta automáticamente
- ❌ **No mezclar modelos en el mismo pipeline** — o Flash rápido o DeepSeek profundo
