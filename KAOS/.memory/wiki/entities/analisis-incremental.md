---
type: concept
title: Análisis Incremental — Mnemosyne Pipeline
aliases:
  - incremental-analysis
  - hash-fingerprinting
  - git-diff-detection
tags:
  - concept
  - mnemosyne
  - incremental
  - pipeline
  - optimizacion
created: '2026-05-27'
modified: '2026-05-27'
confidence: alta
status: active
---

# Análisis Incremental

Patrón de procesamiento selectivo que evita re-analizar archivos no modificados en el vault de KAOS, inspirado en el proyecto [[ua-inspiracion|Understand Anything]].

## Mecanismo de Detección

### Dual Validation (Doble Validación)

```
Hash Cache (SHA-256) ←──→ git diff HEAD
       ↓                         ↓
  Archivos sin cambio       Archivos modificados
       ↓                         ↓
    SKIP (Phase C-J)        Solo estos → Phase B Workers
```

1. **Hash Fingerprinting**: SHA-256 de cada `.md` persistido en `.memory/cache/file-hashes.json`
2. **git diff HEAD**: `git diff --name-only HEAD` como fuente de verdad
3. **Unificación**: Unión de ambos métodos para máxima cobertura

### Pipeline Condicional

| Condición | Acción |
|-----------|--------|
| 0 archivos cambiados | Solo Phase A-B (lint + tagger + wikilinks + crystallize), skip C-J |
| 1+ archivos cambiados | Pipeline completo, pero solo archivos modificados + vecinos en VaultGraph |
| Cache corrupto / sin git | Fallback a full scan (backward compatible) |

## Feature Flag

`use_incremental_analysis` (Default: `False` → `True` post-rollout)

## Módulos

| Archivo | Propósito |
|---------|-----------|
| `lib/incremental.py` | Hash fingerprinting, git diff, detección de cambios |
| `lib/feature_flags.py` | Flag `use_incremental_analysis` |
| `lib/agent_nodes/mnemosyne.py` | Pipeline condicional con flag |

## Referencias

- [[ua-inspiracion]] — Inspiración arquitectónica
- [[mnemosyne]] — Pipeline de curación mejorado
- [[adr-017-ua-inspiracion-fase1]] — ADR de adopción
- Plan Táctico: UA-EPIC-01 (UA-101, UA-102, UA-103)
- `.memory/plans/ua-inspiracion-fase1-plan-tactico.md`
