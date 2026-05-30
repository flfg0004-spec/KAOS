---
type: entity
title: "Obsidian Workflow — Dual Track Knowledge System"
tags: [obsidian, workflow, knowledge-management, documentation]
audience: public
created: 2026-05-30
modified: 2026-05-30
---

# Obsidian Workflow — Dual Track Knowledge System

## Estructura del Vault

```
KAOS/                          ← Vault Obsidian (raíz)
├── .memory/                   ← Memoria de agentes (junction)
│   ├── wiki/concepts/         → audience: agent (por defecto)
│   ├── wiki/entities/         → audience: agent (por defecto)
│   ├── _scripts/              ← Pipeline de curación
│   └── cache/                 ← Índices y reports
├── library/                   ← Biblioteca pública curada
│   ├── concepts/              → audience: public
│   ├── guides/
│   ├── maps/
│   ├── processes/
│   ├── reference/
│   └── queries/               ← Dataview reports
└── Templates/                 ← Templater templates
```

## Flujo de Trabajo

### Captura Rápida (QuickAdd)
1. `CMD/CTRL + P` → "QuickAdd: Run QuickAdd"
2. Seleccionar "New Concept" → template `standard-concept.md`
3. Escribir contenido
4. Opcional: ejecutar macro "Mark for Library" para promoción

### Pipeline Automático (Mnemosyne)
```powershell
py -3 .memory/_scripts/scripts/pipeline_e2e.py
# gap → tag → score → promote → sync → index
```

### Verificación de Salud
```powershell
py -3 .memory/_scripts/scripts/quality_gates.py
```

### Divergence Detection
```powershell
py -3 .memory/_scripts/scripts/memory_diff.py --check
```

## Criterio de Audiencia

| audience | Dónde | Quién escribe | Quién lee |
|----------|-------|---------------|-----------|
| `agent` | wiki/ | Agentes KAOS | Agentes KAOS |
| `public` | library/ | Mnemosyne (promoción) | Usuario humano |
| `both` | wiki/ + library/ | Ambos | Todos |

## Comandos Útiles

```powershell
# Pipeline completo (dry-run)
py -3 .memory\_scripts\scripts\pipeline_e2e.py --dry-run --skip-tag

# Tagger incremental
py -3 .memory\_scripts\scripts\schedule_tagger.py --incremental

# Gap detection
py -3 .memory\_scripts\scripts\schedule_gaps.py --now

# Scoring
py -3 .memory\_scripts\scripts\pipeline_e2e.py --until-score

# Promoción
py -3 .memory\_scripts\scripts\promote_to_library.py --apply

# Tests de integración
py -3 -m pytest .memory/_scripts/tests/test_integration.py -v --no-header
```
