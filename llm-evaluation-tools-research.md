# LLM Evaluation, Testing & Auditing Tools — Comprehensive Research

> **Research date:** May 20, 2026  
> **Methodology:** Direct GitHub API queries, official documentation review, verified via web fetch from primary sources.

---

## Overview Table

| # | Tool | Open Source (License) | Self-Hosted | Python API | RAG / Agent Testing | GitHub Stars | Unique Value Proposition | Confidence |
|---|------|----------------------|-------------|------------|---------------------|--------------|--------------------------|------------|
| 1 | **DeepEval** | ✅ Apache 2.0 | ✅ Local lib; ☁️ Confident AI cloud | `pip install deepeval` | ✅ RAG metrics (6), Agent metrics (8), Multi-turn, MCP, Multimodal | **15.6k** | Pytest-like test runner for LLMs; G-Eval + DAG custom metrics; synthetic data generation; CI/CD native | High |
| 2 | **RAGAS** | ✅ Apache 2.0 | ✅ Local lib only | `pip install ragas` | ✅ RAG-first; agent evals coming | **14k** | RAG-specific evaluation framework; automated test set generation; aspect critique via DiscreteMetric | High |
| 3 | **LangSmith** | ⚠️ SDK: MIT; **Platform: Proprietary** | ✅ Self-hosted (enterprise paid) | `pip install langsmith` | ✅ Full eval suite, tracing, datasets, agent deployment | **894** (SDK) | Deep LangChain/LangGraph integration; Fleet visual agent builder; built by LangChain team | High |
| 4 | **Arize Phoenix** | ⚠️ Elastic License 2.0 (ELv2) | ✅ Docker, K8s, local, Jupyter | `pip install arize-phoenix` | ✅ Tracing, evals, datasets, experiments for agents & RAG | **9.8k** | OpenTelemetry-native; vendor-agnostic; notebook-first; widest framework integrations (~30+); both Python & TypeScript | High |
| 5 | **MLflow** | ✅ Apache 2.0 | ✅ Fully self-hosted (server, Docker, K8s) | `pip install mlflow` | ✅ 50+ built-in metrics; LLM judges; AI Gateway; prompt mgmt | **26k** | Most mature ML platform (pre-LLM); full MLOps + LLMOps in one; 60M+ monthly downloads; OpenTelemetry + MCP native | High |
| 6 | **Evidently AI** | ✅ Apache 2.0 | ✅ Self-hosted UI; ☁️ Evidently Cloud | `pip install evidently` | ✅ LLM evals (text descriptors, LLM judges); ranking/RAG evals | **7.5k** | Tabular + LLM in one framework; 100+ metrics; data drift detection; originated in ML monitoring | High |
| 7 | **NVIDIA NeMo Guardrails** | ✅ Apache 2.0 | ✅ Docker, local, server | `pip install nemoguardrails` | ⚠️ Primarily guardrails/safety; retrieval rails for RAG | **6.2k** | Colang dialog modeling language; 5 rail types (input/dialog/retrieval/execution/output); by NVIDIA; EMNLP 2023 paper | High |
| 8 | **Guardrails AI** | ✅ Apache 2.0 | ✅ Local lib; server via Flask/Docker | `pip install guardrails-ai` | ⚠️ Focus: I/O validation & guardrails; not eval-first | **6.9k** | Guardrails Hub with pre-built validators; structured data generation; input/output guard framework | High |
| 9 | **OpenAI Evals** | ✅ MIT | ✅ Local lib | `pip install evals` | ⚠️ Model-graded evals; Completion Function Protocol for agents | **18.5k** | Backed by OpenAI; standard benchmark registry; model-graded YAML evals; original eval framework | Medium (less active) |
| 10 | **LangFuse** | ✅ MIT (core); EE folder proprietary | ✅ Docker Compose, K8s, Helm | `pip install langfuse` | ✅ Traces, datasets, LLM-as-a-judge, manual labeling, playground | **27.6k** | Most starred LLM observability project; YC W23; most comprehensive (tracing+prompts+evals+playground); heavy collaboration | High |
| 11 | **Helicone** | ✅ Apache 2.0 | ✅ Docker; Helm (enterprise) | ✅ Python SDK + async logging | ⚠️ Observability-first; agent tracing; integrates with RAGAS | **5.7k** | AI Gateway + Observability combined; 100+ models through 1 API; cost/latency tracking; SOC 2/GDPR | High |
| 12 | **Agenta** | ✅ MIT (core) | ✅ Docker Compose | ✅ Python SDK | ✅ Pre-built + custom evaluators; RAG eval; LLM tracing | **4.1k** | Full platform (prompts+eval+observability); UI for non-technical users (SMEs); OpenTelemetry native | High |
| 13 | **PromptLayer** | ✅ Apache 2.0 | ❌ Cloud-first (unverified self-host) | ✅ Python lib | ❌ Unverified (mentions agent versioning) | **762** | Prompt CMS focus; collaboration between domain experts & engineers | Medium |
| 14 | **W&B Weave (Prompts)** | ✅ Apache 2.0 | ⚠️ W&B core self-hostable; Weave = lib | ✅ Python lib | ✅ Weave tracing/eval; multimodal eval (Hemm) | **1.1k** | Integrated with W&B ecosystem (experiment tracking); multimodal eval; prompt versioning | High |
| 15 | **DSPy** | ✅ MIT | N/A (programming framework) | `pip install dspy` | ✅ Built for RAG pipelines & agent loops; optimizes prompts/weights | **34.5k** | Compiler for LM programs; automatic prompt/weight optimization; Stanford research; Declarative Self-improving Python | High |

---

## Detailed Analysis per Tool

### 1. DeepEval (by Confident AI)

- **GitHub:** [confident-ai/deepeval](https://github.com/confident-ai/deepeval) — 15.6k stars, 1.5k forks
- **License:** Apache 2.0
- **Self-Hosted:** The library runs locally. Confident AI is a complementary cloud platform (optional) for storing/sharing results.
- **Python API:** `pip install deepeval`. Full-featured Python SDK.
- **RAG/Agent Testing (Yes):** Extensive support:
  - **RAG Metrics:** Answer Relevancy, Faithfulness, Contextual Precision/Recall/Relevancy, built-in RAGAS
  - **Agentic Metrics:** Task Completion, Tool Correctness, Goal Accuracy, Step Efficiency, Plan Adherence, Plan Quality, Tool Use, Argument Correctness
  - **Multi-Turn metrics, MCP metrics, Multimodal metrics**
- **Standout Features:**
  - Pytest-like `deepeval test run` — runs evals like unit tests
  - G-Eval (LLM-as-a-judge) and DAG (deterministic graph-based) metrics
  - Synthetic dataset generation (single and multi-turn)
  - 1-line integrations for OpenAI Agents, LangChain, LangGraph, CrewAI, Pydantic AI, LlamaIndex, Anthropic
  - Automatic prompt optimization based on eval results
  - Vibe-coder quickstart for coding agents
- **Recent Activity:** v4.0 released May 13, 2026. Very active (9,459 commits). 54 releases.
- **Best For:** Teams wanting a pytest-style testing workflow for LLM apps with broad framework support.

---

### 2. RAGAS

- **GitHub:** [vibrantlabsai/ragas](https://github.com/vibrantlabsai/ragas) — 14k stars, 1.4k forks
- **License:** Apache 2.0
- **Self-Hosted:** Python library, runs entirely locally.
- **Python API:** `pip install ragas`. Async support.
- **RAG/Agent Testing (Yes):** RAG-first design. Key metrics include:
  - Faithfulness, Answer Relevancy, Context Recall/Precision (RAG-focused)
  - Aspect Critique via `DiscreteMetric`
  - Templates for `rag_eval`, with `agent_evals`, `prompt_evals` coming soon
- **Standout Features:**
  - Test data generation from production data
  - `ragas quickstart` CLI to clone complete example projects
  - DiscreteMetric for custom aspect evaluation
  - Seamless LangChain integration
  - Feedbacks loops from production data
- **Recent Activity:** v0.4.3 (Jan 13, 2026). 89 releases. 1,147 commits. Originally by Exploding Gradients, now under VibrantLabs.
- **Best For:** Teams specifically building and evaluating RAG systems.

---

### 3. LangSmith

- **GitHub:** [langchain-ai/langsmith-sdk](https://github.com/langchain-ai/langsmith-sdk) — 894 stars, 234 forks
- **License:** SDK = MIT; **Platform = Proprietary** (not open source)
- **Self-Hosted:** Yes — listed as "self-hosted environment, or hybrid" in docs. Requires enterprise license.
- **Python API:** `pip install langsmith`. Also JS/TS SDK.
- **RAG/Agent Testing (Yes):**
  - Full observability (tracing), evaluation, dataset management, experiments
  - Prompt engineering with versioning
  - Fleet — visual agent builder and deployment
  - Agent deployment as "Agent Servers"
- **Standout Features:**
  - Deepest LangChain/LangGraph integration (native product)
  - Fleet for visual agent design + deployment
  - CLI for querying traces, datasets, experiments
  - Studio for visual app development
  - HIPAA, SOC 2 Type 2, GDPR compliant
- **Recent Activity:** SDK v0.8.5 (May 15, 2026). Very active (2,675 commits). 442 releases.
- **Best For:** Teams already using LangChain/LangGraph who want an integrated platform with enterprise support.
- **Note:** Not fully open source — the SDK is MIT, the platform itself is proprietary.

---

### 4. Arize AI / Phoenix

- **GitHub:** [Arize-ai/phoenix](https://github.com/Arize-ai/phoenix) — 9.8k stars, 883 forks
- **License:** Elastic License 2.0 (ELv2)
- **Self-Hosted:** Yes — Docker, Docker Compose, Kubernetes (Helm), Jupyter notebook, local machine
- **Python API:** `pip install arize-phoenix`. Plus sub-packages: `arize-phoenix-otel`, `arize-phoenix-client`, `arize-phoenix-evals`. Also TypeScript.
- **RAG/Agent Testing (Yes):**
  - Tracing via OpenTelemetry (30+ instrumentation packages)
  - LLM-based evaluation (response + retrieval evals)
  - Datasets for versioned examples, Experiments for tracking changes
  - Playground + Prompt Management
- **Standout Features:**
  - OpenTelemetry-native — vendor, language, framework agnostic
  - Widest integration coverage (~30+ Python, JS, Java instrumentations)
  - Notebook-first design (Jupyter)
  - MCP server, CLI for coding agents
  - Both Python + TypeScript evals package
  - Containerized deployment via Docker Hub
- **Recent Activity:** v15.11.1 (May 19, 2026). Very active (8,566 commits). 701 releases.
- **Best For:** Teams wanting a vendor-neutral, OpenTelemetry-based observability platform with broad framework support.

---

### 5. MLflow

- **GitHub:** [mlflow/mlflow](https://github.com/mlflow/mlflow) — 26k stars, 5.8k forks
- **License:** Apache 2.0
- **Self-Hosted:** Yes — fully self-hosted via `uvx mlflow server`, Docker, Kubernetes, or cloud.
- **Python API:** `pip install mlflow`. Also JS/TS, Java.
- **RAG/Agent Testing (Yes):**
  - 50+ built-in metrics + LLM judges
  - Tracing (OpenTelemetry-native)
  - Prompt Management + automated prompt optimization
  - AI Gateway (unified LLM API with rate limits, fallbacks, guardrails)
  - Evaluation tracking over time
- **Standout Features:**
  - Most mature offering (started as ML platform, now full LLMOps)
  - 60M+ monthly downloads — most widely adopted
  - 1-line autolog for 60+ frameworks
  - Full MLOps + LLMOps in one platform
  - AI Gateway with A/B testing traffic splitting
  - MCP native integration
- **Recent Activity:** v3.12.0 (May 5, 2026). Very active (12,255 commits). 168 releases.
- **Best For:** Organizations that need a unified platform for both traditional ML and LLM workflows, especially Databricks ecosystem users.

---

### 6. Evidently AI

- **GitHub:** [evidentlyai/evidently](https://github.com/evidentlyai/evidently) — 7.5k stars, 849 forks
- **License:** Apache 2.0
- **Self-Hosted:** Yes — monitoring UI can be self-hosted via `evidently ui`. Evidently Cloud also available (free tier).
- **Python API:** `pip install evidently`. Conda also available.
- **RAG/Agent Testing (Yes):**
  - Text descriptors (sentiment, length, toxicity, regex)
  - LLM-based evals (semantic similarity, retrieval relevance, summarization)
  - Ranking metrics (NDCG, MAP, MRR, Hit Rate) for RAG
  - 100+ built-in metrics
- **Standout Features:**
  - Tabular + text data in one framework
  - Data drift detection (20+ statistical tests)
  - Originated in ML monitoring before LLM boom
  - Easy pass/fail test conditions
  - Interactive HTML reports
  - Open architecture — export to any tool
- **Recent Activity:** v0.7.21 (Mar 10, 2026). 124 releases. 2,795 commits.
- **Best For:** Teams needing both traditional ML monitoring and LLM evaluation in one tool.

---

### 7. NVIDIA NeMo Guardrails

- **GitHub:** [NVIDIA-NeMo/Guardrails](https://github.com/NVIDIA-NeMo/Guardrails) — 6.2k stars, 682 forks
- **License:** Apache 2.0
- **Self-Hosted:** Yes — Docker, local Python, server via CLI (`nemoguardrails server`)
- **Python API:** `pip install nemoguardrails`. Async-first API.
- **RAG/Agent Testing (Partial):**
  - Primarily a guardrail/safety toolkit, not eval-first
  - 5 types of rails: input, dialog, retrieval, execution, output
  - Retrieval rails for RAG (reject/alter chunks)
  - Built-in evaluation tool (`nemoguardrails evaluate`)
  - Jailbreak and injection detection
- **Standout Features:**
  - Colang dialog modeling language (Python-like syntax)
  - 5 programmable rail types with fine-grained control
  - By NVIDIA — backed by research (EMNLP 2023 paper)
  - Built-in guardrails library (fact-checking, hallucination, moderation)
  - VSCode extension
  - LangChain integration (opt-in)
- **Recent Activity:** v0.21.0 (Mar 12, 2026). 30 releases. 3,612 commits.
- **Best For:** Teams needing safety guardrails and content moderation for conversational AI, especially enterprise NVIDIA users.

---

### 8. Guardrails AI

- **GitHub:** [guardrails-ai/guardrails](https://github.com/guardrails-ai/guardrails) — 6.9k stars, 611 forks
- **License:** Apache 2.0
- **Self-Hosted:** Yes — local Python library; Flask server via `guardrails start`; Docker with Gunicorn for production.
- **Python API:** `pip install guardrails-ai`. Also JS support.
- **RAG/Agent Testing (Partial):**
  - I/O guardrails framework, not eval-first
  - Pre-built validators for common risks (toxic language, competitors, regex, etc.)
  - Structured data generation from LLMs via Pydantic schemas
- **Standout Features:**
  - Guardrails Hub — marketplace of pre-built validators
  - Guardrails Index — benchmark of 24 guardrails across 6 categories
  - Input/Output Guard architecture
  - Structured data generation via function calling or prompt optimization
  - Pydantic-native output validation
- **Recent Activity:** v0.10.0 (Apr 3, 2026). 67 releases. 3,220 commits.
- **Best For:** Teams needing reliable input/output validation and guardrails for LLM outputs, especially structured data extraction.

---

### 9. OpenAI Evals

- **GitHub:** [openai/evals](https://github.com/openai/evals) — 18.5k stars, 3k forks
- **License:** MIT
- **Self-Hosted:** Yes — local Python library.
- **Python API:** `pip install evals`
- **RAG/Agent Testing (Partial):**
  - Model-graded evals (YAML-defined)
  - Completion Function Protocol for prompt chains / tool-using agents
  - Not specifically RAG-focused
- **Standout Features:**
  - Backed by OpenAI — original LLM eval framework
  - Registry of standard benchmarks (MMLU, etc.)
  - Model-graded eval templates (no code needed)
  - Integration with W&B for logging
- **Recent Activity:** Lower activity compared to others (691 commits). Appears less actively maintained.
- **Best For:** Reference implementation and understanding OpenAI's eval methodology. Less suited for active development.
- **Note:** OpenAI now recommends using the OpenAI Dashboard for evals instead.

---

### 10. LangFuse

- **GitHub:** [langfuse/langfuse](https://github.com/langfuse/langfuse) — 27.6k stars, 2.8k forks
- **License:** MIT (core); **EE folder proprietary**
- **Self-Hosted:** Yes — Docker Compose (5 min), Kubernetes (Helm), Terraform (AWS/Azure/GCP)
- **Python API:** `pip install langfuse`. Also JS/TS SDK.
- **RAG/Agent Testing (Yes):**
  - Full tracing (OpenTelemetry, decorators)
  - LLM-as-a-judge evaluation
  - User feedback collection, manual labeling
  - Datasets for test sets and benchmarks
  - Prompt Management + Playground
  - Integrates with LangChain, LlamaIndex, Haystack, DSPy, CrewAI, AutoGen
- **Standout Features:**
  - #1 most starred LLM observability project on GitHub (27.6k)
  - YC W23 company
  - Most feature-complete: tracing + prompts + evals + playground + datasets
  - Heavy collaboration focus (team workflows)
  - Comprehensive API (OpenAPI, Postman, typed SDKs)
  - Battle-tested production deployments
- **Recent Activity:** Very active (7,057 commits). Continuous releases.
- **Best For:** Teams wanting a full-featured, self-hostable LLM engineering platform with strong community backing.

---

### 11. Helicone

- **GitHub:** [Helicone/helicone](https://github.com/Helicone/helicone) — 5.7k stars, 584 forks
- **License:** Apache 2.0
- **Self-Hosted:** Yes — Docker Compose; Helm for enterprise (contact required).
- **Python API:** Yes — Python SDK + async logging (OpenLLMetry).
- **RAG/Agent Testing (Partial):**
  - Observability-first: agent tracing, session inspection
  - Integrates with RAGAS for evaluation
  - Cost & latency tracking for RAG/agent pipelines
- **Standout Features:**
  - AI Gateway + Observability in one platform
  - 100+ models accessible through 1 OpenAI-compatible API key
  - Intelligent routing + automatic fallbacks
  - Largest open-source LLM pricing database (300+ models)
  - SOC 2 and GDPR compliant
  - Fine-tuning integrations (OpenPipe, Autonomi)
- **Recent Activity:** Last release Aug 2025. 5,477 commits. 4 releases.
- **Best For:** Teams needing both an AI Gateway (multi-provider routing) and observability in a single solution.

---

### 12. Agenta

- **GitHub:** [Agenta-AI/agenta](https://github.com/Agenta-AI/agenta) — 4.1k stars, 521 forks
- **License:** MIT (core)
- **Self-Hosted:** Yes — Docker Compose.
- **Python API:** Yes — Python SDK + REST API.
- **RAG/Agent Testing (Yes):**
  - 20+ pre-built evaluators (LLM-as-judge)
  - Custom evaluator support
  - RAG evaluation
  - LLM tracing (OpenTelemetry, OpenLLMetry, OpenInference)
  - Testsets from production data or playground experiments
- **Standout Features:**
  - Full platform: prompt management + evaluation + observability in one
  - UI-first design for non-technical users (SMEs, product teams)
  - Interactive LLM playground (side-by-side prompt comparison)
  - Multi-model support (50+ models or bring-your-own)
  - Version control with branching and environments
- **Recent Activity:** v0.100.0 (May 20, 2026). Very active (19,758 commits). 391 releases.
- **Best For:** Teams where both engineers and non-technical stakeholders (SMEs) need to collaborate on prompt engineering and evaluation.

---

### 13. PromptLayer

- **GitHub:** [MagnivOrg/prompt-layer-library](https://github.com/MagnivOrg/prompt-layer-library) — 762 stars
- **License:** Apache 2.0
- **Self-Hosted:** Appears cloud-first; no clear self-hosting documentation found. **Unverified.**
- **Python API:** Yes — Python library available.
- **RAG/Agent Testing:** Mentions "version and test your agents" on website. Specific RAG support unverified.
- **Standout Features:**
  - Prompt CMS — focus on managing prompts as a content management system
  - Collaboration layer between domain experts and engineering teams
  - Log, track, debug, and replay old completions
- **Recent Activity:** Lower activity than peers. 762 stars.
- **Best For:** Teams needing prompt version management with a CMS-like approach. Smaller community.

---

### 14. Weights & Biases — Weave (formerly W&B Prompts)

- **GitHub:** [wandb/weave](https://github.com/wandb/weave) — 1.1k stars
- **License:** Apache 2.0
- **Self-Hosted:** W&B core can be self-hosted (enterprise); Weave is a Python library.
- **Python API:** Yes — Python SDK.
- **RAG/Agent Testing (Yes):**
  - Weave: LLM tracing, evaluation, dataset management
  - W&B Prompts: prompt engineering and versioning
  - Hemm: holistic evaluation for multimodal generative models
  - Integrates with OpenAI Evals
- **Standout Features:**
  - Part of the W&B ecosystem (experiment tracking, model registry)
  - Multimodal evaluation support (Hemm)
  - Integrated with the broader W&B MLOps platform
  - W&B MCP server for coding agent integration
- **Recent Activity:** Updated May 20, 2026. 1.1k stars.
- **Best For:** Teams already using W&B for ML experiment tracking who want LLM evaluation in the same ecosystem.

---

### 15. DSPy

- **GitHub:** [stanfordnlp/dspy](https://github.com/stanfordnlp/dspy) — 34.5k stars, 2.9k forks
- **License:** MIT
- **Self-Hosted:** N/A — it is a programming framework/library, not a hosted platform.
- **Python API:** `pip install dspy`
- **RAG/Agent Testing (Yes):**
  - Built for composing RAG pipelines and agent loops
  - Optimizers automatically improve prompts and weights
  - Supports classifiers, sophisticated RAG, and complex agent systems
- **Standout Features:**
  - **Programming, not prompting** — you write Python code, DSPy optimizes the LM interactions
  - Compiler for LM programs — automates prompt engineering
  - Stanford research-backed (ICLR 2024)
  - Automatic prompt optimization and fine-tuning together
  - DSPy Assertions for self-refining pipelines
  - GEPA (reflective prompt evolution, Jul 2025)
- **Recent Activity:** v3.2.1 (May 5, 2026). Very active (4,517 commits). 108 releases.
- **Best For:** Researchers and engineers who want to programmatically optimize LM pipelines rather than manually prompt engineer.

---

## Comparative Summary by Use Case

| Use Case | Best Tools |
|----------|-----------|
| **Pytest-style LLM testing** | DeepEval |
| **RAG evaluation** | RAGAS, DeepEval, Evidently AI |
| **Multi-agent evaluation** | DeepEval, Phoenix, LangFuse |
| **Full LLM observability platform** | LangFuse, Phoenix, MLflow, Agenta |
| **Enterprise ML + LLM platform** | MLflow |
| **Safety & guardrails** | NVIDIA NeMo Guardrails, Guardrails AI |
| **LLM-as-a-judge metrics** | DeepEval, MLflow, LangFuse |
| **Self-hosted (on-premise)** | MLflow, LangFuse, Phoenix, Evidently AI, Agenta, Helicone |
| **Non-technical team collaboration** | Agenta, PromptLayer, LangFuse |
| **AI Gateway + Observability** | Helicone, MLflow |
| **Programmatic prompt optimization** | DSPy, DeepEval |
| **Traditional ML monitoring + LLM** | Evidently AI, MLflow |
| **OpenTelemetry-native** | Phoenix, MLflow, Agenta, LangFuse |
| **Research/academic use** | DSPy, OpenAI Evals |

## Key Recommendations

1. **For most teams starting LLM evaluation:** **DeepEval** or **LangFuse** — broadest feature sets with active communities.
2. **For RAG-specific evaluation:** **RAGAS** is purpose-built and most mature.
3. **For full enterprise MLOps + LLMOps:** **MLflow** — the most mature and widely adopted platform.
4. **For vendor-neutral self-hosted observability:** **Phoenix** — OpenTelemetry-native with the widest framework support.
5. **For safety/guardrails:** **NVIDIA NeMo Guardrails** — most comprehensive rail system with research backing.
6. **For prompt optimization without manual engineering:** **DSPy** — unique compiler approach.
