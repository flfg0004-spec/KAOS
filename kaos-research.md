# KAOS — Deep Research Tools Research

## 1. Perplexica (now Vane)

- **Language**: TypeScript/Next.js (98.8%), Docker-based
- **Stars**: ⭐ 34,500 | **Last release**: v1.12.2 (Apr 2026) — very active
- **License**: MIT

**How it works**: Privacy-focused AI answering engine. Uses SearXNG as default web search backend, supports Ollama (local LLMs) + OpenAI/Claude/Groq/Gemini. Implements RAG with three search modes: Speed, Balanced, Quality. Supports academic, web, and discussion source types.

**As a service**: Yes — Docker image (`itzcrazykns1337/vane:latest`) runs on port 3000. Comes bundled with SearXNG. Also available as slim variant.

**API**: Yes — full REST API at `/api/search` (POST). Returns JSON with `message` + `sources` (cited). Supports streaming (SSE). Also has `/api/providers` for model discovery. Can be called programmatically.

**MCP**: No native MCP server yet, but has REST API that could be wrapped. Community has requested it.

**LLM support**: OpenAI, Anthropic Claude, Google Gemini, Groq, Ollama (all local models), any OpenAI-compatible endpoint.

**KAOS fit**: Excellent as the **frontend/search interface**. Use its API for multi-query research, swap SearXNG for custom backend.

---

## 2. GPT Researcher

- **Language**: Python (55%) + TypeScript/Next.js frontend
- **Stars**: ⭐ 27,200 | **Last release**: v3.4.4 (Apr 2026) — extremely active
- **License**: Apache 2.0

**How it works**: Planner + execution agents. Generates research questions → parallel crawler agents gather info → publisher aggregates into comprehensive report with citations. Has **Deep Research mode** (tree-based recursive exploration). Multi-agent frameworks via LangGraph and AG2.

**Headless/API-only**: Yes — runs as FastAPI server on port 8000, or as PIP package (`pip install gpt-researcher`). CLI available.

**API**: Yes — REST API via FastAPI. Also has dedicated MCP server (`gptr-mcp`) with tools: `deep_research`, `quick_search`, `write_report`, `get_research_sources`, `get_research_context`. Supports STDIO, SSE, Streamable HTTP transports.

**LLM support**: All major — OpenAI, Anthropic, Google, Groq, Azure, Ollama, any OpenAI-compatible. Uses LiteLLM internally for provider abstraction.

**MCP**: YES — native MCP server (`gptr-mcp`) at github.com/assafelovic/gptr-mcp. Can be plugged into Claude Desktop, n8n, or any MCP client.

**KAOS fit**: Core **deep research engine**. The MCP server makes it trivially integrable. Deep Research mode (~5 min, ~$0.4) is ideal for iterative research.

---

## 3. STORM (Stanford)

- **Language**: Python 100%
- **Stars**: ⭐ 28,200 | **Last release**: v1.1.0 (Jan 2025) — moderate activity
- **License**: MIT

**How it works**: LLM-powered knowledge curation. Two-stage: (1) Pre-writing — Internet research + outline via simulated conversations between Wikipedia writer + topic expert; (2) Writing — full-length article with citations. Uses perspective-guided question asking + multi-perspective simulation. Co-STORM variant adds human-AI collaborative discourse.

**As a service**: Library (`pip install knowledge-storm`). No Docker/server. Runs as Python script. Has Streamlit demo light for local UI.

**API**: No built-in REST API. Pure Python library. Has `STORMWikiRunner` and `CoStormRunner` classes. Could be wrapped in FastAPI.

**LLM support**: All models via **LiteLLM** (OpenAI, Anthropic, Ollama, vLLM, together, etc.). Also supports custom embedding models via LiteLLM.

**Retrieval backends**: YouRM, BingSearch, VectorRM, SerperRM, BraveRM, **SearXNG**, DuckDuckGo, TavilySearch, GoogleSearch, AzureAISearch.

**KAOS fit**: The **article/report generation** layer. Feed it research results from GPT-Researcher/Vane → get Wikipedia-quality output. Modular architecture (4 customizable modules) makes it ideal for surgical integration.

---

## 4. Crawl4AI

- **Language**: Python
- **Stars**: ⭐ 66,000 | **Last release**: v0.8.6 (recent, very active) — 1,468 commits
- **License**: Apache 2.0

**How it works**: Async web crawler optimized for LLM consumption. Generates clean Markdown with citations. Features: anti-bot detection, proxy escalation, Shadow DOM, LLM extraction, CSS/JSON extraction, caching, session management, stealth mode. Runs Chromium via Playwright.

**As a service**: YES — Docker image (`unclecode/crawl4ai:latest`) with FastAPI server + monitoring dashboard at port 11235. JWT auth, browser pooling, real-time monitoring.

**API**: Yes — REST API endpoints: `/crawl`, `/task/{id}`, dashboard at `/dashboard`, playground at `/playground`. Structured JSON responses.

**LLM integration**: Yes — `LLMExtractionStrategy` supports all LiteLLM providers. LLM-driven extraction, chunking, cosine similarity filtering. Also has webhook support for LLM pipelines.

**MCP**: Built-in MCP integration in Docker. Can connect directly to Claude Code and other AI tools.

**KAOS fit**: The **content ingestion layer**. Deep crawling with crash recovery, prefetch mode for 5-10x faster URL discovery, adaptive crawling. Perfect for massive ingestion pipelines.

---

## 5. SearXNG

- **Language**: Python (80.6%)
- **Stars**: ⭐ 30,300 | **Last release**: Very active — 9,401 commits
- **License**: AGPL-3.0

**How it works**: Self-hosted metasearch engine. Aggregates results from Google, Bing, DuckDuckGo, Brave, Yahoo, Qwant, Startpage, and 100+ search engines. No user tracking or profiling. Outputs in JSON, HTML, CSV, RSS.

**As a service**: YES — Docker image, running on port 8888 (default). Lightweight, mature, battle-tested.

**API**: Yes — `/search` endpoint with `format=json`. Returns structured search results. Can be configured for specific engines.

**LLM integration**: Not directly (it's a search engine, not an AI tool). But serves as the **search backend** for Perplexica/Vane, STORM, GPT Researcher, and any AI application.

**MCP**: Not directly, but could be trivially wrapped. Already has a clean JSON API.

**KAOS fit**: Essential **search infrastructure**. Aggregates multiple search engines behind one endpoint. Already used by Perplexica/Vane internally. Provides privacy + engine diversity.

---

## 6. txtai

- **Language**: Python (99.5%)
- **Stars**: ⭐ 12,600 | **Last release**: v9.9.0 (May 2026) — very active, 1,906 commits
- **License**: Apache 2.0

**How it works**: All-in-one AI framework. Core is an embeddings database (vector indexes + graph networks + relational DB). Features: semantic search, RAG, LLM orchestration, agents (via smolagents), knowledge graphs, multimodal indexing, pipelines, workflows. Runs fully local.

**As a service**: YES — built-in FastAPI server with YAML config. Docker available. Bindings for JavaScript, Java, Rust, Go.

**API**: Yes — REST API automatically generated from YAML config. Search, extract, chat, summarize, etc. Full OpenAPI support.

**LLM support**: All — Hugging Face, llama.cpp, OpenAI/Claude/AWS Bedrock via LiteLLM. Supports local micromodels up to full LLMs.

**MCP**: YES — native MCP support via Web and Model Context Protocol APIs. "txtai supports Web and Model Context Protocol (MCP) APIs." (from README).

**KAOS fit**: The **knowledge base/memory layer**. Semantic search + graph + RAG. Can index everything crawled by Crawl4AI and make it searchable. Agents can query it autonomously. Perfect for persistent knowledge.

---

## 7. Haystack (deepset)

- **Language**: Python
- **Stars**: ⭐ 25,300 | **Last release**: v2.29.0 (May 2026) — extremely active, 5,321 commits
- **License**: Apache 2.0

**How it works**: Open-source AI orchestration framework for production RAG. Modular pipeline architecture with components for retrieval, indexing, routing, memory, generation, evaluation. Supports agents with tool calling, conditional routing, loops, branches.

**As a service**: YES — via Hayhooks (REST API wrapper). Docker images available. Deepset also offers Haystack Enterprise Platform (managed cloud or self-hosted).

**API**: Yes — Hayhooks wraps pipelines as REST APIs or MCP servers. OpenAI-compatible chat completion endpoints.

**LLM support**: All — OpenAI, Mistral, Anthropic, Cohere, Hugging Face, Azure, AWS Bedrock, local models. Vendor-agnostic design.

**MCP**: YES — "Hayhooks provides a simple way for you to wrap pipelines and agents with custom logic and expose them through HTTP endpoints or MCP. It also supports OpenAI-compatible chat completion endpoints."

**KAOS fit**: The **orchestration layer**. Build complex pipelines stitching together: Crawl4AI → txtai → GPT-Researcher → STORM. Production-grade, used by Apple, Meta, NVIDIA, Airbus, Netflix.

---

## Integration Architecture for KAOS

```
                  ┌─────────────┐
                  │   Haystack  │  ← Orchestration / pipeline routing
                  │ (Orchestra) │
                  └──────┬──────┘
                         │
         ┌───────────────┼───────────────┐
         │               │               │
  ┌──────▼──────┐ ┌──────▼──────┐ ┌──────▼──────┐
  │  SearXNG    │ │  Crawl4AI   │ │   Vane      │
  │ (Metasearch)│ │ (Ingestion) │ │ (Search UI) │
  └──────┬──────┘ └──────┬──────┘ └──────┬──────┘
         │               │               │
         └───────────────┼───────────────┘
                         │
                  ┌──────▼──────┐
                  │  GPT-Research│  ← Deep research agents
                  │  (MCP)      │
                  └──────┬──────┘
                         │
                  ┌──────▼──────┐
                  │    STORM    │  ← Report generation
                  │  (Stanford) │
                  └──────┬──────┘
                         │
                  ┌──────▼──────┐
                  │   txtai     │  ← Knowledge base / vector store
                  │ (Memory)    │
                  └─────────────┘
```

**Recommended integration points:**
1. **SearXNG** → search backend for everything
2. **Crawl4AI** → massive content ingestion (Docker API)
3. **Vane/Perplexica** → frontend + query routing (REST API)
4. **GPT-Researcher** → deep, iterative research (MCP)
5. **STORM** → Wikipedia-quality article generation (Python lib)
6. **txtai** → persistent semantic knowledge base (API + MCP)
7. **Haystack** → pipeline orchestration (Hayhooks MCP)
