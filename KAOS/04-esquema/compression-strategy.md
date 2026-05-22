---
type: adr
title: Compression Strategy — Token Optimization
aliases:
- compression-strategy
tags:
- adr
created: '2026-05-19'
modified: '2026-05-19'
confidence: media
status: draft
---

# Compression Strategy — Token Optimization

## Levels

### Level 1: Normal (<70% pressure)

| Aspect | Detail |
|--------|--------|
| **Load** | index.md + agent entity page + KAOS schema + last 5 log entries |
| **Cache** | LRU 5 entries (TTL: session duration) |
| **Page reads** | Full content |
| **Approx tokens** | ~2-3K |
| **When** | Default for all sessions |

### Level 2: Warning (70-85% pressure)

| Aspect | Detail |
|--------|--------|
| **Load** | index.md only + agent entity page |
| **Cache** | LRU 3 entries, expand only on explicit demand |
| **Page reads** | Summaries only (first 500 chars per page) |
| **Approx tokens** | ~1-2K |
| **When** | Long-running sessions, multiple tool calls |

### Level 3: Critical (>85% pressure)

| Aspect | Detail |
|--------|--------|
| **Load** | index.md summary view (only page names and types, no descriptions) |
| **Cache** | No pre-loading. On-demand only. |
| **Page reads** | Exact sections only (use grep + read offset, never full file) |
| **Approx tokens** | ~500-1K |
| **When** | Sessions near context limit, complex multi-step tasks |

## Priority Order for Loading

1. **entities/** (agent pages first, then related entities)
2. **concepts/** (concepts mentioned in current task)
3. **sources/** (only if referenced by concepts in use)
4. **raw/** (only if deep investigation needed)
5. **schema/** (only for Kosmos and Metis)

## Cache Invalidation Rules

- **Session LRU cache**: Invalidated when a page is modified (checked via git log or last modified timestamp)
- **Cross-session cache**: Not implemented (each session starts fresh; the vault IS the persistent cache)
- **Invalidation trigger**: If a page was written to since last read, re-read it

## Compression Rules for Log.md

- Session log entries older than 30 days: summarize to 1 line each
- Log entries older than 90 days: archive to `raw/archive/log-YYYY-MM.md`
- Keep at least the last 20 entries in full in `log.md`

