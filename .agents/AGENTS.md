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

## Skills

| Skill | Model | Cost | Purpose |
|-------|-------|------|---------|
| `/strategy` | Claude Opus | Pago | Strategic analysis, critical decisions |
| `/review` | Gemini Flash | **Free** | Code review, routine analysis |
| `/validate` | Claude Sonnet | Pago | ADR validation, architecture review |
| `/health` | Gemini Flash | **Free** | Vault health check |
| `/quality` | Gemini Flash | **Free** | Quality score |
| `/export-vault` | — | **Free** | Mermaid viz generation |

## MCP Bridge (OpenCode ↔ agy)

OpenCode agents can call agy models via the `agy-bridge` MCP server:

| Agent | Tools available | Use case |
|-------|----------------|----------|
| Aletheia | agy_ask_flash, sonnet, opus | Research validation |
| Kosmos | agy_ask_sonnet, opus | Architecture review |
| Metis | agy_ask_opus | Strategy analysis |
| Kratos | agy_ask_flash, sonnet | Code review |
| Mnemosyne | agy_status, agy_ask_flash | Quality checks |

## Companion vs OpenCode

| Tool | Role |
|------|------|
| OpenCode | 5-agent pipeline: research → architecture → strategy → code → curation |
| agy (this) | Async operations, quality checks, visualization, model-tiered access via bridge |
