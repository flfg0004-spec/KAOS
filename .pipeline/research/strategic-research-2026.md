# 🧠 Strategic Research Report 2026 — KAOS Ecosystem

> **Compiled**: 2026-05-25  
> **Scope**: 10 strategic technology domains evaluated for KAOS integration  
> **Methodology**: Desk research, cross-domain synthesis, KAOS-specific fit analysis  
> **Status**: Final  

---

## Table of Contents

1. [A2A Protocol (Google)](#1-a2a-protocol-google)
2. [LangGraph Platform (Cloud)](#2-langgraph-platform-cloud)
3. [Mem0 / Memobase / Memary](#3-mem0--memobase--memary)
4. [Open WebUI + MCPO Bridge](#4-open-webui--mcpo-bridge)
5. [Fine-Tuning for Agents](#5-fine-tuning-for-agents)
6. [Evaluation of Agents](#6-evaluation-of-agents)
7. [Federated Knowledge Graphs](#7-federated-knowledge-graphs)
8. [Local Models (Ollama, vLLM, llama.cpp)](#8-local-models-ollama-vllm-llamacpp)
9. [Semantic Cache](#9-semantic-cache)
10. [Multimodal Agents](#10-multimodal-agents)
11. [Synthesis & Recommendations](#11-synthesis--recommendations)

---

## 1. A2A Protocol (Google)

### Overview

| Attribute | Detail |
|-----------|--------|
| **Type** | Horizontal agent-to-agent communication protocol |
| **Creator** | Google (announced April 2025) |
| **License** | Apache 2.0 → Linux Foundation (June 2025) |
| **Current Version** | v1.0.0 |
| **Transport** | JSON-RPC 2.0 over HTTP(S), SSE, gRPC |
| **Discovery** | Agent Card at `/.well-known/agent-card.json` |
| **State Machine** | `submitted → working → input-required / auth-required → completed / failed / canceled / rejected` |
| **SDK** | Python, `a2a-langchain-adapters`, `langgraph-a2a` (v0.1.6), `a2a-langgraph` adapter |

### State Machine

```
                        ┌─→ input-required ──┐
submitted → working ────┤                    ├──→ completed
                        └─→ auth-required ───┘
                            → failed / canceled / rejected
```

### Ecosystem Adoption

| Platform | Status | Notes |
|----------|--------|-------|
| Google ADK | ✅ Native | First-class A2A support |
| LangGraph | ✅ `langgraph-a2a` | v0.1.6, FastAPI mounting |
| CrewAI | ✅ In development | Building A2A support |
| Semantic Kernel | ✅ In development | Microsoft integration |
| LangChain | ✅ `a2a-langchain-adapters` | Bridge package available |
| 150+ orgs | ✅ Adopted | Stellagent, 2026 count |

### Comparison: A2A vs MCP

| Dimension | A2A | MCP |
|-----------|-----|-----|
| **Primary axis** | Horizontal (agent↔agent) | Vertical (agent↔tools) |
| **Creator** | Google (Apr 2025) | Anthropic (Nov 2024) |
| **Governance** | Linux Foundation | Linux Foundation / AAIF |
| **Interaction** | Peer-to-peer, opaque agents | Client-server, model invokes tools |
| **Discovery** | Agent Card at well-known URL | Capability handshake at connect |
| **State model** | Stateful task lifecycle | Mostly stateless |
| **Long-running ops** | ✅ First-class | ❌ Limited |
| **Auth** | OpenAPI-style (OAuth2, mTLS, API Key) | Implementation-specific |
| **Human-in-loop** | ✅ `input-required` state | ❌ Not built-in |

### ⚡ KAOS Relevance

| Factor | Assessment |
|--------|------------|
| **Current state** | ⚡ KAOS is MCP-only with 19 MCP servers |
| **Opportunity** | ✅ External agent discovery & cross-framework collaboration |
| **ADR coverage** | ✅ ADR-002 (mcp-gateway) evaluated as **"ADOPT"** with **"STRONG"** fit |
| **KRONOS alignment** | ✅ A2A Agent Cards could enable dynamic agent routing |
| **Risk** | ❗ Maintaining both protocols doubles surface area |

### Recommendation

> **CONSIDER for Phase 3** — Not urgent. Re-evaluate once MCP ecosystem stabilizes and LangGraph A2A support matures. KRONOS should define Agent Card schema as a design exercise.

---

## 2. LangGraph Platform (Cloud)

### Overview

| Attribute | Detail |
|-----------|--------|
| **Type** | Managed deployment platform for LangGraph agents |
| **Provider** | LangChain Inc. |
| **License** | LangGraph OSS: MIT (free) |
| **Deployment Models** | Self-Hosted Lite, Cloud SaaS, BYOC (AWS), Self-Hosted Enterprise |

### Pricing Breakdown

| Plan | Price | Limits | Best For |
|------|-------|--------|----------|
| **Developer (Free)** | $0 | Up to 100K nodes/month | Prototyping, personal use |
| **Self-Hosted Lite** | Free | Up to 1M nodes | Single-user production |
| **Plus** | $39/user/mo + $0.001/node | Standby charges apply | Small teams |
| **Enterprise** | Custom | Unlimited | Large orgs |

#### Standby Charges (Plus Plan)

| Environment | Cost |
|-------------|------|
| Development | $0.0007/min |
| Production | $0.0036/min |

#### Estimated Monthly Cost: Team of 5, 500K nodes/month

| Component | Cost |
|-----------|------|
| Users (5 × $39) | $195.00 |
| Nodes executed (500K × $0.001) | $500.00 |
| Standby (~730 hrs dev) | ~$30.66 |
| **Total** | **~$350/month** |

### Feature Comparison

| Feature | Cloud/SaaS | Self-Hosted |
|---------|-----------|-------------|
| Checkpointing | ✅ Managed (Postgres) | ⚡ Manual (SQLite dev / Postgres prod) |
| Auto-scaling | ✅ Built-in | ❌ Manual |
| Cron jobs | ✅ Built-in | ❌ External |
| Webhooks | ✅ Built-in | ❌ External |
| Store API (long-term memory) | ✅ Managed | ⚡ Manual |
| LangSmith tracing | ✅ Deeper eval | ✅ Basic |
| Cost (single user) | $39+/month | **$0** |

### ⚡ KAOS Relevance

| Factor | Assessment |
|--------|------------|
| **Current state** | ⚡ Self-hosted LangGraph ≥1.0.0 with SQLite checkpointing |
| **Node volume** | ✅ <100K nodes/month → fits Self-Hosted Lite perfectly |
| **Cost benefit** | ✅ Self-hosted = $0. Cloud = $39+/month for minimal gain |
| **Durability** | ❗ Postgres checkpointing has value but not critical for single-user |
| **LangSmith** | ⚡ Already integrated. Cloud adds deeper eval at cost |

### Recommendation

> ✅ **STAY SELF-HOSTED.** The Cloud premium does not justify for a single-user system. If checkpoint durability becomes critical, migrate SQLite → Postgres before considering Cloud.

---

## 3. Mem0 / Memobase / Memary

### Ecosystem Overview

| Framework | Stars | Approach | LongMemEval | Self-Host | Funding | Best For |
|-----------|-------|----------|-------------|-----------|---------|----------|
| **Mem0** | ⭐ 48K+ | Hybrid V+G+KV | **93.4%** | ✅ Yes | $24M, YC S24 | General purpose, rapid prototyping |
| **Zep/Graphiti** | ⭐ 12K | Temporal KG | 63.8% | ✅ Yes | — | Temporal reasoning |
| **Letta** | ⭐ 18K | OS-tiered | **83.2%** | ✅ Yes | — | Long-running autonomous agents |
| **Memobase** | ⭐ ~1K | User profiles | 75.8% | ✅ Yes | — | User personalization |
| **txtai** | ⭐ 10K | Embeddings pipeline | N/A | ✅ Yes | — | Document-centric RAG |
| **MemPalace** | ⭐ 52K+ | Local-first | N/A | ✅ Yes | $0 | Local, zero cloud cost |

### Detailed Comparison

| Criterion | Mem0 | Letta | Zep/Graphiti | Memobase | txtai |
|-----------|------|-------|-------------|----------|-------|
| **LOCOMO Score** | 92.5% | 83.2% | 63.8% | 75.8% | N/A |
| **Temporal Score** | — | — | +17.3pp | 85.05% | — |
| **Auto fact extraction** | ✅ | ⚡ Partial | ❌ | ❌ | ❌ |
| **Graph memory** | ✅ | ✅ | ✅ | ✅ | ⚡ Vector only |
| **Vector memory** | ✅ | ✅ | ⚡ | ✅ | ✅ |
| **KV memory** | ✅ | ✅ | ❌ | ❌ | ❌ |
| **Embedded DB** | ✅ | ✅ | ❌ (needs GraphDB) | ⚡ | ✅ |
| **Setup complexity** | Low | Medium | High | Low | Low |
| **Maturity** | ~1.5 years | ~2 years | ~2 years | ~1 year | **8+ years** |

### ⚡ KAOS Relevance

| Factor | Assessment |
|--------|------------|
| **Current state** | ⚡ Significant investment in txtai: **3,682 chunks**, `mcp_txtai.py`, custom pipeline |
| **Architecture fit** | ✅ L0-L3 hierarchy maps best to **Letta's tiered** or **txtai's layered** model |
| **Mnemosyne synergy** | ✅ Mem0's automatic fact extraction could automate curation phases |
| **Risk** | ❗ Replacing txtai = rewriting **~60% of Mnemosyne pipeline** |
| **Cost** | ✅ Mem0 free tier = 10K memories. Managed from $19-249/month |

### Recommendation

> ✅ **AUGMENT txtai, DON'T REPLACE.** Add Mem0 as a complementary agent-memory layer (for agent state, not document storage). Letta is the backup option if tiered memory becomes critical.

---

## 4. Open WebUI + MCPO Bridge

### Overview

| Component | Version | Stars | License | Purpose |
|-----------|---------|-------|---------|---------|
| **Open WebUI** | v0.8.11+ (Mar 2026) | — | MIT | Self-hosted AI chat interface |
| **MCPO bridge** | v0.0.20 (Feb 2026) | ⭐ 4.1K | MIT | MCP-to-OpenAPI proxy |

### Open WebUI Capabilities

| Feature | Status | Notes |
|---------|--------|-------|
| Native MCP Streamable HTTP | ✅ | Supported natively |
| MCP tools | ✅ | Tool-calling via MCP |
| OAuth 2.1 | ✅ | Authentication support |
| RAG | ✅ | Built-in retrieval |
| Web search | ✅ | Integrated |
| Multi-model | ✅ | LiteLLM proxy backend |
| Channels | ✅ | Multi-user rooms |
| Open Responses protocol | ⚡ Experimental | Reasoning tokens |
| MCP Apps extension | 🔜 In development | Interactive iframe components |
| Self-expose as MCP server | 🔜 Issue #24117 | Feature request |

### Alternatives

| Platform | Pros | Cons |
|----------|------|------|
| **Open WebUI** | Self-hosted, MCP native, active dev | Overlaps with Obsidian |
| **LobeChat** | Plugin ecosystem | No MCP support |
| **Chatbot UI** | Simple, clean | Limited features |
| **Gradio** | Fast prototyping | Not agent-oriented |
| **Streamlit** | Data apps focus | Not chat-first |
| **Obsidian Smart Connections** | Local-first | Limited to Obsidian |

### ⚡ KAOS Relevance

| Factor | Assessment |
|--------|------------|
| **Current state** | ⚡ `owui/` directory exists, ports 3000/9090 configured but **not validated end-to-end** |
| **MCPO bridge value** | ✅ Protocol translation pattern could validate future A2A bridge design |
| **User interface** | ✅ Provides non-technical UI vs current OpenCode-only interface |
| **Risk** | ❗ **OWUI + Obsidian overlap** — both provide chat interfaces |
| **Separation strategy** | ⚡ Use OWUI for casual interaction, Obsidian for knowledge work |

### Recommendation

> ✅ **COMPLETE THE INTEGRATION, VALIDATE END-TO-END.** Use OWUI for casual/interactive agent sessions. Reserve Obsidian for deep knowledge work, curation, and persistent vault operations.

---

## 5. Fine-Tuning for Agents

### State of the Art (2026)

| Technique | Parameter Efficiency | GPU Savings | Quality vs Full FT | Hardware Needed (7B) |
|-----------|---------------------|-------------|-------------------|---------------------|
| **LoRA** | 0.1–1% parameters | ~70% less | 90–95% | 16GB VRAM |
| **QLoRA** | 0.1–1% + 4-bit NF4 | ~85% less | 80–90% | **6–8GB VRAM** |
| **DoRA** | Like LoRA + magnitude/direction | ~70% less | Better convergence | 16GB VRAM |
| **Full FT** | 100% | Baseline | 100% | **112GB VRAM** |

### VRAM Requirements

| Model Size | Full FP16 | LoRA | QLoRA (4-bit) |
|-----------|-----------|------|---------------|
| **7B** | 112 GB | 16 GB | **6–8 GB** ✅ |
| **13B** | 208 GB | 30 GB | **10 GB** |
| **70B** | 1,120 GB | 160 GB | **48 GB** |

### Hardware Cost Analysis

| Setup | Cost | Training Time (7B QLoRA) |
|-------|------|------------------------|
| RTX 4090 (24GB) | <$1,500 | 2–4 hours |
| RTX 3090 (24GB) | ~$800 | 3–5 hours |
| RTX 4060 Ti (16GB) | ~$500 | 4–6 hours |

### Toolkit Landscape

| Tool | Focus | Notes |
|------|-------|-------|
| **DSPy** | Programmatic prompt optimization | ⚡ Experimental fine-tuning via `BootstrapFinetune` |
| **Unsloth** | Fastest QLoRA | Consumer GPU optimized |
| **Torcha** | LoRA-based RL (GRPO, DPO) | Built on torchtune |
| **Axolotl** | Full fine-tuning pipeline | More complex |
| **LLaMA-Factory** | All-in-one FT | Most feature-complete |

### Best Practice 2026

```
RAG for facts + Fine-tuning for behavior
```

### ⚡ KAOS Relevance

| Factor | Assessment |
|--------|------------|
| **Best candidate** | ✅ **Kratos** (code generation) = highest volume agent |
| **Quality-sensitive** | ✅ **Aletheia** (research) = benefits from specialized synthesis training |
| **Data source** | ⚡ KAOS pipeline logs provide months of production interaction data |
| **Lower-risk path** | ✅ **DSPy** — evaluate programmatic optimization before full fine-tuning |
| **Cost analysis** | 🟢 1M tokens/day @ DeepSeek Flash ≈ **$4.20/month** |
| **ROI assessment** | ❗ Fine-tuning ROI at current scale is **marginal** |

### Recommendation

> ⏸️ **MONITOR ONLY. Evaluate DSPy first.** Fine-tune only if local models are adopted (see [Topic 8](#8-local-models-ollama-vllm-llamacpp)). The current API cost ($4.20/month) does not justify fine-tuning infrastructure investment.

---

## 6. Evaluation of Agents

### Benchmark Landscape

| Benchmark | Domain | Tasks | Primary Use |
|-----------|--------|-------|-------------|
| **GAIA** | Multi-step reasoning | 466 tasks | General agent capability |
| **SWE-bench Verified** | Software engineering | 500 curated GitHub issues | Code agent evaluation |
| **AgentBench** | Multi-domain | 8 environments | Broad capability scan |
| **WebArena** | Web automation | — | Web task completion |
| **AgencyBench** | Multi-agent | 138 tasks, 6 capabilities | Framework comparison |

### Evaluation Frameworks

| Framework | Stars | Key Features | Best For |
|-----------|-------|-------------|----------|
| **DeepEval** | ⭐ 28K+ | pytest-like, local LLM-as-judge, hallucination detection | KAOS-aligned, already integrated |
| **LangFuse** | ⭐ 8K+ | Tracing + evaluation, cost tracking | Production monitoring |
| **Inspect AI** | ⭐ 4K+ | 200+ pre-built evals, UK AISI | Safety & compliance |
| **MASEval** | — | Multi-agent benchmark harness | Multi-agent systems |
| **NVIDIA NeMo** | ⭐ 8K+ | Agent toolkit, RLHF pipeline | Enterprise |

### KAOS Evaluation Architecture (Current)

```
                    ┌──────────────────────────────┐
                    │    LLM-as-Judge (DeepEval)    │
                    │  Veracidad | Coherencia |     │
                    │  Completitud | Repro. | Util. │
                    └──────────┬───────────────────┘
                               │
            ┌──────────────────┼──────────────────┐
            ▼                  ▼                  ▼
    ┌──────────────┐  ┌──────────────┐  ┌──────────────┐
    │  L1 — DeepEval│  │ L2 — Cross-  │  │ L3 — Blind   │
    │  auto-check   │  │ agent verify │  │ review       │
    └──────────────┘  └──────────────┘  └──────────────┘
```

### Three Evaluation Types

| Type | Box | What It Measures | When |
|------|-----|------------------|------|
| **End-to-end** | Black box | Task Success Rate | Final validation |
| **Trajectory** | Glass box | Tool Call Accuracy, Path Efficiency | Debugging |
| **Component-level** | White box | Individual model/framework metrics | Development |

### Key Finding 2026

> **Model benchmarks (MMLU) ≠ Agent benchmarks.** Framework-model interaction matter more than model capability alone.

### ⚡ KAOS Relevance

| Factor | Assessment |
|--------|------------|
| **Current quality** | ⚡ **76.8/100** — 5-dimensional system (Veracidad, Coherencia, Completitud, Reproducibilidad, Utilidad) with DeepEval |
| **Target** | ✅ **85+** |
| **Anti-hallucination** | ✅ L1 (DeepEval) → L2 (Cross-agent) → L3 (Blind review) |
| **Expansion needed** | ⚡ **Tool Call Accuracy** for Kratos, **Citation Quality** for Aletheia |

### Recommendation

> ✅ **EXPAND, DON'T REPLACE.** Add agent-specific sub-dimensions: Tool Call Accuracy (Kratos), Citation Quality (Aletheia). Integrate pipeline-level evaluation as a gating step before artifact delivery.

---

## 7. Federated Knowledge Graphs

### GraphRAG vs LightRAG

| Dimension | Microsoft GraphRAG | LightRAG |
|-----------|-------------------|----------|
| **Stars** | ⭐ 32.8K | ⭐ 30.5K |
| **Latest Version** | v3.0.9 (Apr 2026) | v1.4.14 (Apr 2026) |
| **Conference** | — | EMNLP 2025 |
| **Entity Extraction** | Full + community detection | Simpler, flat graph |
| **Hierarchical summaries** | ✅ Multi-level | ❌ Flat only |
| **Dual-level retrieval** | ❌ | ✅ Local + Global |
| **Incremental updates** | ❌ Difficult | ✅ Easy |

#### Cost & Performance

| Metric | GraphRAG | LightRAG |
|--------|----------|----------|
| **Indexing cost (500 pages)** | **$50–200** ❌ | **~$0.50** ✅ |
| **Indexing time (500 pages)** | **~45 min** ❌ | **~3 min** ✅ |
| **Global queries** | ✅ Excellent | ❌ Poor |
| **Domain-specific QA** | Good | ✅ Very good |
| **RAGAS integration** | ❌ | ✅ |
| **Langfuse integration** | ❌ | ✅ |

### ⚡ KAOS Relevance

| Factor | Assessment |
|--------|------------|
| **Current state** | ⚡ Knowledge-graph MCP with **53 wiki concepts** (L2 Semantic layer, ADR-011) |
| **Scale match** | ✅ LightRAG more appropriate for KAOS scale (~200 pages, 53 concepts) |
| **Cost alignment** | ✅ LightRAG's embedding-based approach = no GPT-4 dependency |
| **Mnemosyne automation** | ✅ LightRAG could automate Phases 10–12 (Graph → Gaps → Cross-Ref) |
| **txtai relationship** | ⚡ **Augment, don't replace** — LightRAG as L2 Semantic layer complement |

### Recommendation

> ✅ **ADOPT LIGHTGAG** as a complementary layer for L2 Semantic memory. Do **not** replace txtai — LightRAG handles graph relationships while txtai handles dense retrieval.

---

## 8. Local Models (Ollama, vLLM, llama.cpp)

### Engine Comparison (2026)

| Engine | Language | Quantization | Single-User t/s (8B, RTX 4090) | Multi-User | Strengths |
|--------|----------|-------------|--------------------------------|------------|-----------|
| **Ollama** | Go | GGUF | ~45 t/s | ❌ Fails >5 concurrent | Easiest setup, wraps llama.cpp |
| **vLLM** | Python | AWQ, GPTQ, FP8 | ~50 t/s | ✅ 10x at 64 concurrent | PagedAttention, production serving |
| **llama.cpp** | C/C++ | GGUF (Q4_K_M) | ~45 t/s | ⚡ Moderate | Max portability (CPU, AMD, Apple, ARM) |

### Quantization Formats

| Format | Bits | Size (8B model) | Quality |
|--------|------|-----------------|---------|
| **Q4_K_M** | 4-bit | **5.8 GB** | ⚡ Good |
| **AWQ** | 4-bit | **6.1 GB** | ✅ Better |
| **GPTQ** | 4-bit | ~6 GB | ✅ Better |
| **FP8** | 8-bit | ~8 GB | ✅ Near-lossless |

### Top Open Models (2026)

| Model | Size | Best For |
|-------|------|----------|
| **Qwen2.5-32B** | 32B | General purpose |
| **Llama-4-17B** | 17B | Balanced quality/speed |
| **DeepSeek-Coder-V2-Lite** | 16B | Code generation |
| **Mixtral 8x22B (4-bit)** | 22B active | Complex reasoning |

### Performance Note

> Single-user: All 3 engines within **10–15%** of each other.  
> Multi-user: **vLLM dominates** — 10x+ at 64 concurrent users.

### ⚡ KAOS Relevance

| Factor | Assessment |
|--------|------------|
| **Current model** | ⚡ 100% API-based (DeepSeek, Gemini, Claude) |
| **Monthly cost** | 🟢 ~1M tokens/day @ DeepSeek Flash ≈ **$4.20/month** |
| **Hardware need** | ❗ Local models add hardware cost (~$800–1,500) but **eliminate API dependency** |
| **Best option** | ✅ **Ollama** for simplicity, **llama.cpp** for performance |
| **Model specialization** | ⚡ Small (7B) → Mnemosyne curation | Medium (8–14B) → Kratos codegen | Large → API for Metis |
| **Latency impact** | 🟡 Local adds ~1–5s vs API 0.5–2s — acceptable for pipeline ops |

### Recommendation

> 🟡 **PILOT WITH OLLAMA** on a 7B–8B model. Evaluate quality vs DeepSeek Flash. If quality gap <10%, migrate gradually. Start with Mnemosyne (least quality-sensitive agent).

---

## 9. Semantic Cache

### State of the Art

| Tool | Type | Hit Quality | Setup Effort | Best For |
|------|------|-------------|-------------|----------|
| **GPTCache** | Library | ✅ High | 🟢 Medium | Python apps, quick setup |
| **Redis Stack** | Database | ✅ High | 🟡 Medium–High | Production, already on Redis |
| **vLLM Prefix Cache** | Built-in | 🟡 Medium | 🟢 None (free) | vLLM users |
| **Provider Cache** | Platform | N/A | 🟢 Auto | API discount (OpenAI, Anthropic) |

### Expected Hit Rates

| Query Type | Expected Hit Rate |
|------------|------------------|
| Code/docs queries | **40–60%** ✅ |
| FAQ / static knowledge | **30–50%** ✅ |
| Conversational | **5–15%** ❌ |
| **Break-even threshold** | **15–20%** |

### Advanced Research

| System | Improvement | Notes |
|--------|-------------|-------|
| **vCache** (arXiv 2502.03771) | **12.5x** better hit rates | 26x lower error vs GPTCache |
| **SemCache** (Rust) | In-memory + Prometheus | Metrics-native |

### ⚡ KAOS Relevance

| Factor | Assessment |
|--------|------------|
| **Current state** | ❌ No semantic cache — only DSOL cache exists |
| **Biggest impact** | ⚡ Repeated MCP tool responses (embedding calls) + agent outputs (daily QA, weekly audit) |
| **Integration** | ✅ Add as layer between MCP proxy and model routing |
| **Existing infrastructure** | ✅ **Use txtai embeddings** for cache key generation = zero new infra |
| **Storage** | ✅ Local SQLite cache (simple, zero ops) |
| **Format** | ⚡ Semantic similarity for QA queries, exact match for deterministic calls |
| **Estimated impact** | ✅ **25–40% API cost reduction** |

### Recommendation

> ✅ **IMPLEMENT NOW.** Low effort (<2 days), high impact. Use txtai embeddings + local SQLite cache. Target: cache daily QA, weekly audit, repeated MCP tool responses.

---

## 10. Multimodal Agents

### Vision Models (2026)

| Model | Provider | Strengths |
|-------|----------|-----------|
| **GPT-4o Vision** | OpenAI | Best general vision |
| **Claude 3.5 Sonnet Vision** | Anthropic | Document analysis |
| **Gemini 2.0 Flash** | Google | Speed + cost |
| **Llama-4** | Meta | Open source |
| **Qwen2.5-VL** | Alibaba | Open source, strong |
| **DeepSeek-VL2** | DeepSeek | Cost-effective |

### MCP Servers for Multimodal

| Server | Capabilities |
|--------|-------------|
| **OpenRouter MCP Multimodal** | Vision, audio, image gen, 300+ models |
| **Multimodal MCP (rsmdt)** | OpenAI, xAI, Gemini, ElevenLabs, BFL |
| **imagine-mcp** | Understand, generate, edit (Gemini + OpenAI + Grok) |
| **Pixelle-MCP** | TISV stack (Text/Image/Sound/Video), ComfyUI-based |
| **Google-managed MCP servers** | Maps, BigQuery, GKE, Cloud Run |
| **Human MCP** | 29 tools, human-like senses |

### Media Capabilities

| Modality | Provider Options |
|----------|-----------------|
| **Speech-to-Text** | Whisper (OpenAI), Gemini |
| **Text-to-Speech** | ElevenLabs, Gemini TTS |
| **Image Generation** | GPT-4o Image, Imagen 4, FLUX Pro, Grok Imagine, Stable Diffusion 3 |
| **Music Generation** | Lyria (Google) |
| **Video Generation** | Sora 2, Veo 3.1, Grok Imagine Video |

### ⚡ KAOS Relevance

| Factor | Assessment |
|--------|------------|
| **Current state** | ⚡ Text-only. Excalidraw MCP exists for diagrams |
| **Highest value** | ✅ **Vision for Aletheia** — analyzing figures/charts in research papers |
| **Medium value** | 🟡 Audio for voice note inbox (Whisper STT) |
| **Lower value** | ❌ Image generation (Excalidraw already works for diagrams) |
| **Cost impact** | ❗ Vision API calls **3–10x more expensive** than text |

### Recommendation

> 🟡 **IMPLEMENT VISION ONLY.** Add image analysis to Aletheia's research pipeline. Skip audio/image generation for now. Re-evaluate when costs decrease.

---

## 11. Synthesis & Recommendations

### Executive Summary Matrix

| # | Topic | Impact | Effort | Risk | Priority | Action |
|---|-------|--------|--------|------|----------|--------|
| 1 | A2A Protocol | 🟡 Medium | 🔴 High | ⚠️ Protocol fragmentation | ⏸️ Phase 3 | Monitor, design Agent Card schema |
| 2 | LangGraph Cloud | 🟢 Low | 🟢 Low | ✅ None | ❌ Skip | Stay self-hosted |
| 3 | Mem0/Memobase | 🟢 High | 🔴 High | ⚠️ txtai rewrite risk | 🟡 Phase 2 | Augment txtai, don't replace |
| 4 | Open WebUI | 🟢 Medium | 🟡 Medium | ⚠️ Obsidian overlap | ✅ **Now** | Complete E2E validation |
| 5 | Fine-Tuning | 🟡 Medium | 🔴 High | ⚠️ ROI marginal | ⏸️ Hold | Evaluate DSPy first |
| 6 | Agent Evaluation | 🟢 High | 🟢 Low | ✅ Low risk | ✅ **Now** | Add sub-dimensions |
| 7 | LightRAG | 🟢 High | 🟡 Medium | ✅ Low risk | ✅ **Phase 1** | Adopt as L2 augment |
| 8 | Local Models | 🟡 Medium | 🟡 Medium | ⚠️ Quality gap risk | 🟡 Pilot | Ollama 7B-8B trial |
| 9 | Semantic Cache | 🟢 **High** | 🟢 **Low** | ✅ Very low | ✅ **🔝 NOW** | Implement immediately |
| 10 | Multimodal | 🟡 Low | 🟡 Medium | ⚠️ Cost 3-10x | 🟡 Phase 3 | Vision only for Aletheia |

### Confidence Indicators

| Icon | Meaning |
|------|---------|
| ✅ Ready to act — clear path available |
| 🟡 Proceed with caution — needs validation first |
| ⏸️ Hold — not yet justified |
| ❌ Skip — not relevant at this time |

### 🔝 Top 3 Priorities

| Rank | Topic | Why Now |
|------|-------|---------|
| **#1** | **Semantic Cache** (Topic 9) | Lowest effort (<2 days), highest impact (25–40% cost reduction). Uses existing txtai infra. Zero new dependencies. |
| **#2** | **Agent Evaluation** (Topic 6) | Already at 76.8/100, targeting 85+. Adding sub-dimensions is low effort and directly improves all agent outputs. |
| **#3** | **Open WebUI + MCPO** (Topic 4) | Already configured but not validated. Completing this unlocks non-technical UI access and validates protocol translation patterns. |

### ⚠️ Top 3 Risks

| Risk | Topic | Impact | Mitigation |
|------|-------|--------|------------|
| **Protocol fragmentation** | #1 A2A | MCP-only → dual protocol maintenance | Hold A2A until Phase 3. Define Agent Card schema as design doc only. |
| **txtai replacement spiral** | #3 Mem0 | Rewriting 60% of Mnemosyne pipeline | Strictly augment, never replace. Mem0 for agent state only. |
| **Quality regression with local models** | #8 Local | Degraded agent outputs vs API models | Pilot on Mnemosyne (lowest quality sensitivity). Measure gap before wider rollout. |

### Impact / Effort Matrix

```
                    HIGH IMPACT
                        │
            ┌───────────┼───────────┐
            │           │           │
            │  ✅       │  ✅       │
            │  Semantic │  Agent    │
            │  Cache    │  Eval     │
            │  (Now)    │  (Now)    │
    LOW ────┼───────────┼───────────┼──── HIGH
  EFFORT    │           │           │  EFFORT
            │           │  ✅       │
            │  ❌       │  LightRAG │
            │  LangGraph│  OWUI     │
            │  Cloud    │  Mem0     │
            │           │           │
            └───────────┼───────────┘
                        │
                    LOW IMPACT
```

### Phased Roadmap

#### Phase 0 — Immediate (<1 week)
- ✅ **Semantic Cache** — implement with txtai + SQLite
- ✅ **Agent Evaluation** — add Tool Call Accuracy, Citation Quality sub-dimensions

#### Phase 1 — Short-term (1–4 weeks)
- ✅ **Open WebUI** — complete E2E validation, establish use-case boundary with Obsidian
- ✅ **LightRAG** — integrate as L2 Semantic memory layer, automate Mnemosyne Phases 10–12

#### Phase 2 — Medium-term (1–3 months)
- 🟡 **Mem0** — add as agent-memory layer for agent state (not document storage)
- 🟡 **Local Models** — pilot Ollama 7B-8B for Mnemosyne, evaluate quality gap

#### Phase 3 — Long-term (3–6 months)
- ⏸️ **A2A Protocol** — re-evaluate ecosystem maturity, potentially implement Agent Card discovery
- 🟡 **Multimodal Vision** — add image analysis to Aletheia research pipeline
- ⏸️ **Fine-Tuning** — evaluate DSPy results, decide on full fine-tuning if local models adopted

### Cost Impact Summary

| Action | Current Cost | Post-Implementation | Savings |
|--------|-------------|-------------------|---------|
| API calls (DeepSeek Flash) | ~$4.20/month | ~$2.50–3.15/month | **$1–2/month** |
| Semantic Cache | $0 | $0 (SQLite + txtai) | **25–40% token reduction** |
| Open WebUI hosting | $0 | $0 (self-hosted) | — |
| LightRAG indexing | $0 | ~$0.50/run | — |
| Ollama pilot | $0 | $0 (existing GPU) | Potential $4.20/month full offset |

> **Note**: Current absolute costs are low (~$4.20/month). The strategic value of these recommendations lies in **architecture, autonomy, and quality** — not cost savings alone.

---

*End of Report — Generated 2026-05-25*
