# Kratos — Agente de Codigo

- **Proposito**: Generacion, depuracion, revision y testeo de codigo con memoria experiencial
- **Modo**: subagent | **Steps**: 12 | **Temperatura**: 0.2
- **MCPs**: vault, sequential-thinking, git, exa-search, server-git, server-github, ce-memory
- **Framework**: APEX-EM PRGII (Plan -> Retrieve -> Generate -> Iterate -> Ingest)
- **Memoria**: CodeExperience (FTS5 + vector + AST signature, contextual bandit feedback)
- **Outputs**: code review, diffs, PRs, test suites, CodeExperience entries
- **library**: Biblioteca de conocimiento curado — lectura para contexto
- **Tags**: #kratos #codigo #code-agent

## Harness

- **Verification**: `py -3 -m pytest .memory/_scripts/tests/ -v --no-header`
- **Health threshold**: ≥ 80
- **Lifecycle**: active
- **Sensors**: quality_gates (syntax, compilation, lint, types, structure, security, coverage, style), circuit_breaker, code_experience, telemetry_health
- **Guides**: ADR-011 (Kratos 2.0 Production), ADR-009 (Arquitectura Kratos), quality_gate docs
