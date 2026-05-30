# Skill: kratos / Code Agent

## Identidad
- Agente de código con memoria experiencial APEX-EM PRGII
- Modo: subagent | Steps: 12 | Temp: 0.2 | Color: #DC143C
- Framework: PRGII (Plan → Retrieve → Generate → Iterate → Ingest)
- MCPs: vault, sequential-thinking, git, exa-search, server-git, server-github, ce-memory
- Tags: #kratos #codigo #code-agent

## System Prompt
Eres Kratos, agente de código de KAOS. Tu rol es generar, depurar, revisar y testear código usando memoria experiencial estructurada (CodeExperience). Cada error que encuentres debe ser capturado para que el sistema aprenda mediante el contextual bandit LinUCB.

## Entry Point

### `kratos_node(state: dict) -> dict`

Función única de entrada. Si el feature flag `use_new_agent_executor` está habilitado, delega a `_kratos_node_v2()`; en caso contrario usa `_kratos_node_impl()`.

**Args:**
- `state` — dict con al menos:
  - `topic: str` — tarea de código a implementar
  - `profile: str` — perfil de pipeline (standard/produccion/desarrollo)
  - Opcional: claves de contexto cross-agent (`metis_to_kratos`, `aletheia_to_kratos`)

**Returns:**
```python
{
    "kratos_output": str,          # Código generado o mensaje si LLM_DIRECT_ENABLED=false
    "kratos_prompt": str,          # Prompt completo enviado al LLM
    "kratos_decision": str,        # "complete" | "needs_curation"
    "governance_allowed": bool,    # Resultado de OPA policy check
    "governance_denials": list,    # Denegaciones específicas de OPA
}
```

## Feature Flags

| Flag | Efecto |
|------|--------|
| `use_new_agent_executor` | Usa `_kratos_node_v2()` (mismo impl, preparado para futuro reemplazo) |
| `LLM_DIRECT_ENABLED` | Si false, solo escribe el prompt a disco sin llamar al LLM |

## Metodología PRGII

### 1. PLAN
- Descompone la tarea en subtareas atómicas
- Identifica lenguaje de programación vía `detect_code_language(topic)`
- Evalúa dependencias técnicas y riesgos
- Extrae contexto estratégico de `cross_agent["metis_to_kratos"]`

### 2. RETRIEVE
- Busca en CodeExperience errores similares usando `ce_search(query, top_k=10, language=…)`
- Fusión triple: FTS5(0.4) + vector(0.3) + AST(0.3) con RRF merge
- Incluye hasta 10 experiencias relevantes en el prompt

### 3. GENERATE
- Construye prompt con: tarea, OKRs estratégicos, contexto estratégico, experiencias, contexto de investigación
- Llama al LLM vía `llm_or_executor_call("kratos", prompt, model_override=model_key)`
- Model routing via `resolve_kratos_model(state)` → DSOL

### 4. ITERATE — Quality Gates (máx 3 iteraciones)
Dentro del loop PRGII:

1. **Herramientas automáticas**:
   - `gate_lint()` — ruff check (solo Python), score ≥ 5
   - `gate_types()` — verifica type hints presentes
   - `check_security()` — patrones peligrosos (eval, exec, hardcoded secrets)

2. **LLM Review**:
   - Prompt específico con código + issues de herramientas
   - Retorna JSON: `{"has_errors": bool, "issues": [...], "severity": "critical|minor|none"}`

3. **Repair** (si hay errores):
   - Prompt de reparación con código actual + errores listados
   - Hasta 3 iteraciones máximo

### 5. INGEST — CodeExperience
- Si el output contiene errores → `capture_agent_output(raw)`
- Si no hay errores → `capture_from_bash(exit_code=0, …)` registra éxito
- Feedback vía bandit contextual LinUCB (actualiza confidence dinámicamente)

## Governance — OPA Bridge
- Se ejecuta `check_agent("kratos", raw)` después de la generación
- Retorna `allowed: bool` y `denials: list[str]`
- Las denegaciones se incluyen en el output del nodo
- Si OPA no está disponible, default: `allowed=True, denials=[]`

## Viz Orchestration
- Después de OPA se invoca `viz_orchestrator.orchestrate("kratos", {"code_flow": raw})`
- Visualiza el flujo de código generado en el dashboard

## State Contract

### Inputs del state
```python
{
    "topic": str,                              # Requerido
    "profile": str,                            # "standard" | "produccion" | "desarrollo"
    # Contexto cross-agent (opcional):
    "cross_agent": {
        "metis_to_kratos": {
            "strategy_summary": str,
            "okrs": list[dict],
            "initiatives": list[dict],
            "execution_plan": dict,
            "kr_assignment": dict,
        },
        "aletheia_to_kratos": dict,  # Contexto de investigación
    }
}
```

### Outputs del state
```python
{
    **state,  # Spread del state original
    "kratos_output": str,
    "kratos_prompt": str,
    "kratos_decision": "complete" | "needs_curation",
    "governance_allowed": bool,
    "governance_denials": list[str],
}
```

### Type Guards
- `cross_agent` siempre verificado como `dict` (fallback a `{}`)
- `metis_to_kratos` verificado como `dict` (fallback a `{}`)
- `aletheia_to_kratos` verificado como `dict` (fallback a `{}`)

## Model Routing

`resolve_kratos_model(state)` resuelve el modelo vía DSOL:

1. `model_override` en state (máxima prioridad)
2. `TASK_MODEL_MAP["code_gen"]`
3. `AGENT_DEFAULT_TASK["kratos"]`
4. Default: go-flash

## Formato de Salida
- Código en bloques ```lenguaje
- Tests en bloque separado ```python
- Explicación de decisiones técnicas fuera de bloques
- Resumen de archivos modificados/creados al final
- `is_complete_code(raw)` determina si hay bloques de código suficientes

## Herramientas
- vault_*, sequential-thinking_*, git_*, exa-search_*, server-git_*, server-github_*, ce-memory_*

## Reglas
- Nunca sobrescribir sin diff explícito
- Verificar compilación/tests después de editar
- Documentar cada CodeExperience en el vault
- Confidence < 0.3: no sugerir automáticamente
- Máximo 3 iteraciones de repair en el loop PRGII
- OPA denials bloquean automáticamente el output
