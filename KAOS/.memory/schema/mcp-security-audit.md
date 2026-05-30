# Security Audit: KAOS MCPs
*Updated: 2026-05-20*

## Summary
- **MCPs audited**: 18 (17 enabled, 1 disabled)
- **HIGH risk**: 0 (GitHub removed)
- **MEDIUM risk**: 4 (EXA_API_KEY ×2, remote MCPs ×2)
- **LOW risk**: 14

## Findings

### MEDIUM: EXA_API_KEY in opencode.json
- **MCPs**: `exa-search`, `gptr-deep-research`
- **Issue**: API key stored in plaintext in MCP `env` section (standard MCP practice)
- **Risk**: Read-only search key — can search Exa but not modify. Key also set as system env var.
- **Mitigation**: Ensure `.opencode/.gitignore` prevents committing secrets

### MEDIUM: Remote MCPs — Data exfiltration vector
- **MCPs**: `context7` (https://mcp.context7.com/mcp), `supermemory` (https://mcp.supermemory.ai/mcp)
- **Issue**: Remote HTTP servers receive all tool calls and data
- **Risk**: Agent context or vault content could be sent to external servers
- **Mitigation**: Review privacy policies; use only with trusted providers; consider local alternatives for sensitive data

### LOW: vault/filesystem MCP — Path traversal
- **MCP**: `vault` (server-filesystem)
- **Issue**: Only allows access to whitelisted directories (.memory, .memory/ingest, .memory/cache, .memory/wiki, .memory/raw, .memory/schema, .vault/quality)
- **Risk**: Path traversal via `../` — mitigated by server-filesystem's own path validation
- **Status**: Acceptable

### LOW: Remaining MCPs
All other MCPs (sequential-thinking, depwire, excalidraw, paperjsx, scholar-search, git, rss-reader, searxng, crawl4ai, txtai, structurizr, knowledge-graph, mcp-obsidian-cli) operate locally with no external network access or have minimal risk profile.

## Resolved Issues
- **GitHub MCP** ❌ Removed — GitHub PAT no longer stored in config
- **Lucidity MCP** ❌ Removed — package `lucidity-mcp` does not exist on npm

## Recommendations

| Priority | Action | Risk Reduced |
|:--------:|--------|:------------:|
| 1 | Ensure `.opencode/.gitignore` prevents committing MCP secrets | MEDIUM→LOW |
| 2 | Audit context7 data handling before sensitive use | MEDIUM→LOW |
| 3 | Review supermemory privacy policy for vault data | MEDIUM→LOW |
