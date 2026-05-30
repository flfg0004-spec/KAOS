---
audience: agent
type: tool
title: Knowledge Tour Generator — Herramienta de Kosmos
aliases:
  - knowledge-tour
  - knowledge-tour-generator
  - tour-generator
tags:
  - tool
  - kosmos
  - conocimiento
  - onboarding
  - topological-sort
  - ua-inspiracion
created: '2026-05-27'
modified: '2026-05-27'
confidence: alta
status: design
agent: kosmos
---

# Knowledge Tour Generator

Tool para [[kosmos|Kosmos]] que genera guías de aprendizaje topológicas del vault, ordenando conceptos por dependencia para producción óptima de guías "Start Here → Core Concepts → Advanced Topics".

## Algoritmo

1. **Topological Sort** sobre VaultGraph (NetworkX DiGraph) — produce capas ordenadas por dependencia
2. **Detección de Ciclos** — `detect_cycles()` identifica y rompe ciclos artificialmente
3. **Asignación de Niveles** — Nivel 0 (sin dependencias) → Start Here, Nivel medio → Core, Nivel alto → Advanced
4. **Generación Markdown** — Documento completo con frontmatter YAML, Mermaid, TOC y badges

## Output

Archivo: `.memory/wiki/guides/knowledge-tour-{slug}.md`

**Estructura del Tour:**
- 🏁 **Start Here** (Nivel 0: conceptos raíz sin dependencias previas)
- 📘 **Core Concepts** (Nivel medio: conceptos con dependencias moderadas)
- 🚀 **Advanced Topics** (Nivel alto: conceptos hoja con muchas dependencias)
- Diagrama Mermaid de dependencias
- Tabla de contenidos con anclas

## Comando

```
/knowledge-tour [topic]
```

## Feature Flag

`use_knowledge_tour` (Default: `False` → `True` post-rollout)

## Referencias

- [[ua-inspiracion]] — Inspiración arquitectónica (topological sort)
- [[kosmos]] — Agente responsable
- [[adr-017-ua-inspiracion-fase1]] — ADR de adopción
- Plan Táctico: UA-EPIC-03 (UA-301, UA-302, UA-303)
- Skill: `.memory/guides/knowledge-tour-skill.md`
- `.memory/plans/ua-inspiracion-fase1-plan-tactico.md`
