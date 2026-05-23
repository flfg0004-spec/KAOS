# ADR-009: Arquitectura del Code Agent Kratos

## Estado
Aceptado

## Contexto
KAOS necesita un agente especializado en código con memoria experiencial estructurada. Investigación (78+ fuentes) confirma que APEX-EM (arXiv 2603.29093) ofrece +48.3pp en benchmarks de generación de código mediante memoria procedural.

## Decisión
Crear Kratos como 5º agente de KAOS con arquitectura APEX-EM PRGII:

- **Pipeline PRGII**: Plan → Retrieve → Generate → Iterate → Ingest
- **Memoria**: CodeExperience (FTS5 + vector search + AST signature)
- **Retrieval**: Triple fusión con RRF merge (FTS5 0.4 + vector 0.3 + AST 0.3)
- **Feedback**: Contextual bandit LinUCB
- **Routing**: Condicional — solo se activa si el tópico contiene keywords de código
- **Steps**: 12 | **Temperatura**: 0.2 | **Color**: #DC143C

### Tools Asignadas
- vault_* — Lectura/escritura en .memory/
- sequential-thinking_* — Descomposición de problemas
- git_* — Commits, branches, PRs
- exa-search_* — Búsqueda de soluciones
- obsidian_* — Lectura vault enriquecido
- mcp-obsidian-cli_* — Lectura alternativa

### Stack de Memoria
- code_experiences.db — SQLite con FTS5 + WAL + triggers de sync
- tree-sitter — AST signature matching (Python, Rust, JavaScript inicial)
- sqlite-vec — Embeddings semánticos (384d, paraphrase-multilingual-MiniLM-L12-v2)

## Consecuencias
### Positivas
+ Memoria procedural estructurada que mejora con el uso
+ Captura automática de errores con hash deduplicado
+ Routing condicional evita overhead en tareas no-code
+ Confidence scoring adaptativo vía contextual bandit

### Negativas
- tree-sitter requiere gramáticas por lenguaje (3 inicial, 15 target)
- DB de experiencias crece sin poda → necesita sleep cycle periódico
- AST matching añade latencia (~50ms por parse)

## Alternativas Consideradas
- **AtomCode** (Rust): No integrable como subagent OpenCode
- **CodeBot**: Audit trail criptográfico, pero sin memoria experiencial
- **LevelCode**: 4-agent architecture, but overkill para 5º agente

## Referencias
- APEX-EM: arXiv 2603.29093
- Hermes Agent v0.14.0: Nous Research (161K⭐)
- LangGraph v1.0: 126K⭐, checkpointing nativo, 9% token overhead
