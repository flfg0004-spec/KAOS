# KAOS — Knowledge Agent Operating System

[![CI](https://github.com/flfg0004-spec/KAOS/actions/workflows/ci.yml/badge.svg)](https://github.com/flfg0004-spec/KAOS/actions/workflows/ci.yml)
[![Quality](https://github.com/flfg0004-spec/KAOS/actions/workflows/quality.yml/badge.svg)](https://github.com/flfg0004-spec/KAOS/actions/workflows/quality.yml)
[![Pipeline](https://github.com/flfg0004-spec/KAOS/actions/workflows/pipeline.yml/badge.svg)](https://github.com/flfg0004-spec/KAOS/actions/workflows/pipeline.yml)

Persistent knowledge vault powered by multi-agent AI — **Quality Score: 94.6/100**

## Quick Start (5 min)

```bash
pip install -r .memory/_scripts/requirements.txt
py .memory/_scripts/vault.py health --auto
py .memory/_scripts/vault.py lint run
py .memory/_scripts/tests/run.py --fast
py .memory/_scripts/vault.py viz
```

See [QUICKSTART.md](docs/QUICKSTART.md) for detailed usage.

## Architecture

```
OpenCode (5 subagents)          agy Companion (7 skills)
       │                              │
       └──────────┬───────────────────┘
                  │
          .memory/ vault (shared state)
          ├── raw/       → Research outputs
          ├── wiki/      → Curated knowledge
          ├── schema/    → ADRs & policies
          └── bridge/    → Inter-agent signaling
```

## System DUAL

| Mode | Model | Cost | Speed | Use |
|------|-------|------|-------|-----|
| **Explore** | Gemini Flash (agy) | Free | <2 min | Prototyping, review, debug |
| **Produce** | DeepSeek (OpenCode) | ~$0.003 | 5-15 min | Pipeline, ADRs, production |

## Agents

| Agent | Tool | Role |
|-------|------|------|
| OpenCode | 5 subagents | Research → Architecture → Strategy → Code → Curation |
| agy (Companion) | 7 skills | Ingest, consolidate, health, quality, viz, sync, explore |

## Quality Dashboard

```bash
py .memory/_scripts/vault.py quality     # Score compuesto
py .memory/_scripts/vault.py speed       # Métricas DUAL
py .memory/_scripts/vault.py lint run    # Broken wikilinks, orphans
py .memory/_scripts/vault.py lint coverage  # Coverage raw/
```

## Troubleshooting

See [TROUBLESHOOTING.md](docs/TROUBLESHOOTING.md) for common issues.
