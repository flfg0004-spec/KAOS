# KAOS — Agent Configuration

## Workflow

- **Build mode**: Ejecuto cambios directamente en archivos
- **Plan mode**: Solo leo, investigo y planeo — no ejecuto cambios

## Comandos de verificación

- Tests: `py -3 -m pytest .memory/_scripts/tests/test_kosmos_quality.py .memory/_scripts/tests/test_aletheia_router.py .memory/_scripts/tests/test_verification.py -v --no-header`
- Golden dataset: `py -3 .memory/_scripts/tests/aletheia_golden_dataset.py`
- Sintaxis: `py -3 -c "compile(open('path', encoding='utf-8').read(), 'path', 'exec')"`
- Lint: `py -3 -m flake8 .memory/_scripts/lib/`
- Typecheck: `py -3 -m mypy .memory/_scripts/lib/`

## Estructura

- `lib/quality/` — Quality engines unificados (agent.py, vault.py, store.py)
- `lib/file_lock.py` — File locking con portalocker
- `lib/feature_flags.py` — Feature flags con dual load (JSON + env vars)
- `lib/docker_lazy.py` — Docker lazy start con DOCKERLESS_MODE
- `scripts/rotate-keys.ps1` — Rotación de API keys + purga git
- `.tools/sandbox/Dockerfile` — Sandbox multi-stage alpine

### Kratos — Code Agent
**Version**: 2.0 Alpha (H3 Sprint 4)
**Tests**: 73+ passing
**Feature flags**: 20+ flags (all disabled by default)
**Capabilities**:
- PRGII pipeline (Plan → Retrieve → Generate → Iterate → Document)
- 8 quality gates (syntax, compilation, lint, types, structure, security, coverage, style)
- Multi-lang support (Rust, TypeScript, Go) via feature flags
- Parallel gate execution via ThreadPoolExecutor
- Real mypy --strict type checking (feature-flagged)
- Real pytest --cov coverage measurement (feature-flagged)
- Circuit Breaker for LLM critic calls (per-invocation)
- Self-healing triggers based on telemetry
- Telemetry dashboard (CLI) with health score
- OPA governance (configurable fail-open/fail-close)
- KratosDecision enum (5 values, str-compatible)
- Type guards for cross-agent data (never crashes)
**Key Files**:
- `lib/agent_nodes/kratos.py`
- `lib/quality_gate/` (package, 11 files)
- `lib/kratos_decision.py`
- `lib/kratos_telemetry.py`
- `lib/kratos_dashboard.py`
- `lib/kratos_self_heal.py`
- `lib/kratos_contract.py`

## Skills

| Agent | Skill | Description |
|-------|-------|-------------|
| Aletheia | [aletheia](.opencode/skills/aletheia/SKILL.md) | Truth verification and quality assurance |
| Kosmos | [kosmos](.opencode/skills/kosmos/SKILL.md) | Architecture analysis and system design |
| Kratos | [kratos](.opencode/skills/kratos/SKILL.md) | Code generation and PRGII pipeline execution |
| Metis | [metis](.opencode/skills/metis/SKILL.md) | Strategic planning, OKRs, and competitive analysis |
| Mnemosyne | [mnemosyne](.opencode/skills/mnemosyne/SKILL.md) | Memory curation and knowledge management |
