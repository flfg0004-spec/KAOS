---
type: adr
title: 'ADR-010: Integracion DSOL ↔ LangGraph Orchestrator'
aliases:
- adr-010-integracion-dsol-langgraph
tags:
- adr
created: '2026-05-21'
modified: '2026-05-21'
confidence: media
status: draft
---

# ADR-010: Integracion DSOL ↔ LangGraph Orchestrator

## Estado
Aceptado

## Contexto
ADR-004 define DSOL (DeepSeek Optimization Layer) como capa de routing que decide que modelo usar (Flash vs Pro) segun complejidad. LangGraph (implementado en ADR-009) define routing condicional entre agentes (Metis → Kratos si hay codigo, → Mnemosyne si no). Ambas capas deciden "routing" pero en niveles distintos. Sin integracion explicita, pueden contradecirse.

## Decision
**LangGraph decide QUE agente ejecuta. DSOL decide COMO ejecuta.**

### Arquitectura de Integracion
```
LangGraph routing (QUE)
  ├── determina: Aletheia → Kosmos → Metis → {Kratos|Mnemosyne}
  ├── condicional: basado en topic keywords
  └── stateful: checkpointing SQLite

DSOL routing (COMO)
  ├── recibe: (agent, task, complexity_estimate)
  ├── determina: (model, thinking_mode, token_budget, temperature)
  └── configura: hydrate.py → build_optimized_context()
```

### Pipeline de Decision
1. LangGraph selecciona el nodo (agente) a ejecutar
2. Antes de ejecutar el nodo, llama a DSOL con el contexto actual
3. DSOL retorna la configuracion optima (flash para tareas simples, pro para complejas)
4. El nodo se ejecuta con la configuracion de DSOL
5. Al completar, LangGraph persiste el estado via checkpoint

### Beneficios
- Responsabilidades separadas y claras
- Sin conflicto: LangGraph no decide modelos, DSOL no decide agentes
- Token budget controlado por DSOL segun agente (Kratos usa mas tokens que Metis)

## Consecuencias
### Positivas
+ Resuelve el conflicto C3 identificado por Kosmos en la auditoria
+ Permite que cada agente tenga su perfil DSOL optimo
+ LangGraph se mantiene como orquestador puro, sin logica de modelos

### Negativas
- Se necesita modificar `lib/dsol.py` para exponer `select_config(agent, task)`
- LangGraph nodes deben invocar DSOL antes de ejecutar (token overhead adicional ~2%)

## Referencias
- ADR-004: DeepSeek Optimization Layer
- ADR-009: Arquitectura Kratos
- Kosmos Audit: auditoria-estrategia-orquesta-kosmos.md (Issue C3)

