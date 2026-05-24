# KAOS — Knowledge Agent Operating System

[![CI](https://github.com/flfg0004-spec/KAOS/actions/workflows/ci.yml/badge.svg)](https://github.com/flfg0004-spec/KAOS/actions/workflows/ci.yml)
[![Quality](https://github.com/flfg0004-spec/KAOS/actions/workflows/quality.yml/badge.svg)](https://github.com/flfg0004-spec/KAOS/actions/workflows/quality.yml)
[![Pipeline](https://github.com/flfg0004-spec/KAOS/actions/workflows/pipeline.yml/badge.svg)](https://github.com/flfg0004-spec/KAOS/actions/workflows/pipeline.yml)

Persistent knowledge vault powered by multi-agent AI. Research → Architecture → Strategy → Code → Curation.

## Quick Start

```bash
# Install dependencies
pip install -r .memory/_scripts/requirements.txt

# Run quality checks
py .memory/_scripts/vault.py lint run
py .memory/_scripts/vault.py health --auto

# Generate visualizations
py .memory/_scripts/vault.py viz

# Run fast test suite
py .memory/_scripts/tests/run.py --fast
```

## Visualization

The vault auto-generates Mermaid diagrams for the knowledge graph, pipeline, quality trends, and timeline.

![Pipeline](.memory/VIZ_PIPELINE.md rendered on GitHub)

## Architecture

| Layer | Path | Description |
|-------|------|-------------|
| Raw | `.memory/raw/` | Immutable research outputs |
| Wiki | `.memory/wiki/` | Curated knowledge with wikilinks |
| Schema | `.memory/schema/` | ADRs, architecture, policies |

## Agents

| Agent | Tool | Role |
|-------|------|------|
| OpenCode | 5 subagents | Research → Architecture → Strategy → Code → Curation |
| agy (Companion) | 6 skills | Async ingest, consolidation, health, quality, viz, backup |
