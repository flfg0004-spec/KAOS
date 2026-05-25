# ADR-009: Arquitectura del Code Agent Kratos

## Estado
Actualizado — v2.0 (Mayo 2026)

## Contexto
KAOS necesita un agente especializado en código con memoria experiencial estructurada. Tras la implementación inicial, investigación adicional (Aletheia, 47+ fuentes) identificó mejoras críticas: RSCB-MC reemplaza LinUCB (5.5pp mejora, 10.7x más rápido), sqlite-vec + RRF híbrido duplica precisión de retrieval, y MCP servers desbloquean 100+ tools.

## Decisión
Kratos v2.0 con arquitectura APEX-EM PRGII mejorada:

- **Pipeline PRGII**: Plan → Retrieve (FTS5+vector+AST RRF) → Generate → Test → Reflect → Ingest
- **Memoria**: CodeExperience (FTS5 + sqlite-vec + AST signature + RRF merge)
- **Retrieval**: Triple fusión con RRF merge (FTS5 0.4 + vector 0.3 + AST 0.3)
- **Feedback**: Risk-Sensitive Contextual Bandit RSCB-MC (arXiv 2604.27283)
- **Bandit**: Monte Carlo estimation, Welford's online variance, persistencia SQLite
- **Routing**: Condicional + Reflexion loop (3 iteraciones máximo)
- **Modelo**: deepseek-flash (evaluar go-pro)
- **Steps**: 12 | **Temperatura**: 0.2 | **Color**: #DC143C

### Tools Asignadas
- vault_* — Lectura/escritura en .memory/
- sequential-thinking_* — Descomposición de problemas
- git_* — Commits, branches, PRs
- exa-search_* — Búsqueda de soluciones
- obsidian_* — Lectura vault enriquecido
- mcp-obsidian-cli_* — Lectura alternativa
- server-git_* — MCP Git nativo
- server-github_* — MCP GitHub (100+ tools)

### Stack de Memoria
- code_experiences.db — SQLite con FTS5 + WAL + triggers de sync + vec0 virtual table
- tree-sitter — AST signature matching (Python, Rust, JavaScript, TypeScript, JSX, TSX, Go)
- sqlite-vec — Embeddings semánticos 384d (bge-small-en-v1.5)
- RSCB-MC — Risk-sensitive bandit con persistencia cross-session

### Quality Gates Pipeline
1. Syntax → 2. Compilation → 3. Lint (ruff 0-10) → 4. Types (mypy) → 5. Tests (%) → 6. Style → 7. Score compuesto

## Consecuencias
### Positivas
+ Memoria procedural estructurada que mejora con el uso (RSCB-MC > LinUCB: +5.5pp)
+ Captura automática de errores con hash deduplicado
+ Routing condicional evita overhead en tareas no-code
+ Retrieval híbrido supera FTS5 solo por +20-30%
+ RSCB-MC es 10.7x más rápido que LinUCB con 0% falsos positivos
+ Bandit persiste entre sesiones

### Negativas
- sqlite-vec requiere extensión (cargar en cada conexión)
- Embeddings a 384d añaden ~50ms por store (modelo lazy-loaded)
- DB de experiencias crece sin poda → necesita sleep cycle
- AST matching añade latencia (~50ms por parse)

## Alternativas Consideradas
- **LinUCB** (reemplazado): 55% éxito, 3,567μs latencia, 0.5% FP → RSCB-MC: 60.5%, 331μs, 0% FP
- **FAISS** (no adoptado): Más rápido pero sin integración FTS5 nativa → sqlite-vec es más simple
- **CTIM** (no adoptado): Episodic memory simple no generaliza (From Knowledge to Noise, ACL 2025)

## Referencias
- APEX-EM: arXiv 2603.29093
- RSCB-MC: arXiv 2604.27283 (Risk-Sensitive Contextual Bandit)
- PYTHALAB-MERA: arXiv 2605.08468 (Validation-grounded memory)
- sqlite-vec: asg017/sqlite-vec (MIT)
- tree-sitter v0.24+: 7+ grammars via WASM
- Hermes Agent v0.14.0: Nous Research (161K⭐)
- LangGraph v1.0: 126K⭐, checkpointing nativo, 9% token overhead
