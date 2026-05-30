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
