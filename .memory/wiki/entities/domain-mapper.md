---
type: tool
title: Domain Mapper — Herramienta de Metis
aliases:
  - domain-mapper
  - domain-mapper-tool
  - bounded-contexts-mapper
tags:
  - tool
  - metis
  - estrategia
  - clustering
  - arquitectura
  - stakeholders
  - ua-inspiracion
created: '2026-05-27'
modified: '2026-05-27'
confidence: alta
status: design
agent: metis
---

# Domain Mapper

Tool para [[metis|Metis]] que ejecuta clustering semántico sobre el grafo arquitectónico de KAOS para agrupar componentes técnicos en **dominios de negocio** (bounded contexts), produciendo reportes accionables para stakeholders no técnicos.

## Pipeline

```
arch_graph (6 nodos, 7 edges)
       ↓
Feature Extraction (tipo, propiedades, conexiones, peso)
       ↓
txtai Embeddings (fastembed BAAI/bge-small-en-v1.5)
       ↓
K-Means / DBSCAN Clustering (3-5 clusters)
       ↓
Cluster Naming (basado en nodos del cluster)
       ↓
Reporte Markdown con Bounded Contexts
```

### Fallback

Si txtai MCP no responde, el clustering cae a **rule-based** (agrupar por `node_type`).

## Output

Archivo: `.memory/wiki/reports/domain-map-{slug}.md`

**Contenido del Reporte:**
- Diagrama Mermaid `graph TD` coloreado por cluster
- Tabla por bounded context (componentes, tipo, madurez)
- Matriz de dependencias entre contexts (N×N)
- Recomendaciones de evolución (contextos acoplados)
- Glosario técnico → lenguaje de negocio

## Comando

```
/domain-map [topic]
```

## Feature Flag

`use_domain_mapper` (Default: `False` → `True` post-rollout)

## Referencias

- [[ua-inspiracion]] — Inspiración arquitectónica
- [[metis]] — Agente responsable
- [[adr-017-ua-inspiracion-fase1]] — ADR de adopción
- Plan Táctico: UA-EPIC-04 (UA-401, UA-402, UA-403, UA-404)
- Skill: `.memory/guides/domain-mapper-skill.md`
- `.memory/plans/ua-inspiracion-fase1-plan-tactico.md`
