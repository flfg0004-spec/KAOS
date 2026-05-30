# ADR-010: Integracion Ether (DSOL) ↔ LangGraph Orchestrator

## Estado
Aceptado — Implementado. DSOL fue renombrado a Ether en v2 (ver ADR-004 sección "Evolución: DSOL → Ether").

## Contexto
ADR-004 define Ether (originalmente DSOL — DeepSeek Optimization Layer) como capa de routing que decide que modelo usar (Flash vs Pro vs Kimi) segun complejidad. LangGraph (implementado en ADR-009) define routing condicional entre agentes (Metis → Kratos si hay codigo, → Mnemosyne si no). Ambas capas deciden "routing" pero en niveles distintos. Sin integracion explicita, pueden contradecirse.

## Decision
**LangGraph decide QUE agente ejecuta. Ether decide COMO ejecuta.**

### Arquitectura de Integracion
```
LangGraph routing (QUE)
  ├── determina: Aletheia → Kosmos → Metis → {Kratos|Mnemosyne}
  ├── condicional: basado en topic keywords
  └── stateful: checkpointing SQLite

Ether routing (COMO)  ← antes DSOL
  ├── recibe: (agent, task, complexity_estimate)
  ├── determina: (model, thinking_mode, token_budget, temperature)
  └── configura: hydrate.py → build_optimized_context()
```

### Pipeline de Decision
1. LangGraph selecciona el nodo (agente) a ejecutar
2. Antes de ejecutar el nodo, llama a Ether con el contexto actual
3. Ether retorna la configuracion optima (flash para tareas simples, pro para complejas, kimi para estrategia)
4. El nodo se ejecuta con la configuracion de Ether
5. Al completar, LangGraph persiste el estado via checkpoint

### Beneficios
- Responsabilidades separadas y claras
- Sin conflicto: LangGraph no decide modelos, Ether no decide agentes
- Token budget controlado por Ether segun agente (Kratos usa mas tokens que Metis)

## Consecuencias
### Positivas
+ Resuelve el conflicto C3 identificado por Kosmos en la auditoria
+ Permite que cada agente tenga su perfil Ether optimo
+ LangGraph se mantiene como orquestador puro, sin logica de modelos

### Negativas
- Se necesita modificar `lib/ether/router.py` para exponer `select_config(agent, task)`
- LangGraph nodes deben invocar Ether antes de ejecutar (token overhead adicional ~2%)

## Referencias
- ADR-004: DeepSeek Optimization Layer → Ether (renombrado v2)
- ADR-009: Arquitectura Kratos
- Kosmos Audit: auditoria-estrategia-orquesta-kosmos.md (Issue C3)
- `lib/ether/` — Paquete Ether (antes `lib/dsol.py`)
