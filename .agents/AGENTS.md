# KAOS Companion

## Project
Knowledge Agent Operating System — vault of persistent knowledge powered by agents.

## Agent

- **KAOS-Companion**: Operates the `.memory/` vault. Does not duplicate OpenCode agents.
  - Skills: `/ingest` `/consolidate` `/health` `/quality` `/export-vault` `/sync`
  - Tools: vault filesystem, txtai, knowledge-graph, mcp-obsidian-cli
  - Directives:
    - Read `.memory/wiki/index.md` first to understand vault structure
    - All knowledge persists in `.memory/` — read before writing
    - Never overwrite existing knowledge; use ADD-only pattern
    - Run `/health` after any write to the vault

## Companion vs OpenCode

| Tool | Role |
|------|------|
| OpenCode | 5-agent pipeline: research → architecture → strategy → code → curation |
| agy (this) | Async operations, quality checks, visualization, remote/SSH, Desktop export |
