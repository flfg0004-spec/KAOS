---
title: "Arquitectura de Sistema: Anthropic/Claude como Opción Principal en Ecosistema KAOS"
date: 2026-05-29
agent: kosmos
status: published
type: architecture
tags: [anthropic, claude, architecture, integration, aether, routing, mcp, caching, subagents, implementation]
confidence: alta
---

# Arquitectura de Sistema: Anthropic/Claude en Ecosistema KAOS

## Resumen Arquitectónico

Esta arquitectura define cómo integrar **Anthropic/Claude como tier premium** dentro del ecosistema KAOS, aprovechando el routing Aether v3 existente, la infraestructura MCP de 25+ servidores, y el bridge agy que ya expone Claude Sonnet/Opus como herramientas. La estrategia es **quirúrgica**: Claude maneja ~5% del tráfico (tareas de alto valor como ADRs críticos, estrategia, validación dual) mientras DeepSeek V4 Flash mantiene ~70% como backbone. La arquitectura añade **Prompt Caching nativo** (90% descuento en reads), **Haiku 4.5** para clasificación del pipeline, **Batch API nocturna** (50% descuento), y **Constitutional AI via Rego** ($0 runtime). El costo incremental estimado es ~$35/mes (+$0.10/semana quick wins → +$1.00/semana integración → +$0.20/semana transformación) por un +15-25% de calidad en tareas críticas.

---

## 1. Diagrama de Arquitectura — Capa por Capa

```
╔═══════════════════════════════════════════════════════════════════════════════╗
║                   ARQUITECTURA ANTHROPIC × KAOS                              ║
║                                                                               ║
║  ┌─────────────────────────────────────────────────────────────────────────┐  ║
║  │  CAPA DE ACCESO (Interfaces)                                            │  ║
║  │                                                                          │  ║
║  │  ┌───────────┐ ┌───────────┐ ┌──────────┐ ┌──────────┐ ┌──────────┐    │  ║
║  │  │  OpenCode  │ │ Claude    │ │  Cline   │ │  Agno    │ │  Custom  │    │  ║
║  │  │  TUI/CLI  │ │ Code      │ │  VS+CLI  │ │  Agents  │ │  Scripts │    │  ║
║  │  │  (165K⭐) │ │  ($2.5B)  │ │  (62K⭐) │ │ (KAOS)   │ │          │    │  ║
║  │  └─────┬─────┘ └─────┬─────┘ └─────┬────┘ └────┬─────┘ └─────┬────┘    │  ║
║  └────────┼──────────────┼─────────────┼───────────┼─────────────┼────────┘  ║
║           │              │             │           │             │           ║
║           └──────────────┼─────────────┼───────────┼─────────────┘           ║
║                          │             │           │                         ║
║  ┌───────────────────────┼─────────────┼───────────┼───────────────────────┐ ║
║  │  CAPA DE ROUTING      ▼             ▼           ▼                       │ ║
║  │                                                                          │ ║
║  │  ┌────────────────────────────────────────────────────────────────────┐  │ ║
║  │  │  AETHER ROUTER v3 (16 archivos, lib/aether/)                       │  │ ║
║  │  │  resolve_model() — 10 etapas                                       │  │ ║
║  │  │  ┌──────────┐ ┌──────────┐ ┌──────────┐ ┌──────────┐              │  │ ║
║  │  │  │ Circuit  │ │ Quality  │ │ Ether    │ │ Rate     │              │  │ ║
║  │  │  │ Breaker  │ │ Store    │ │ Tracker  │ │ Limiter  │              │  │ ║
║  │  │  └──────────┘ └──────────┘ └──────────┘ └──────────┘              │  │ ║
║  │  └────────────────────────────────────────────────────────────────────┘  │ ║
║  │                                                                          │ ║
║  │  ┌────────────────────────────────────────────────────────────────────┐  │ ║
║  │  │  CLAUDE-ROUTER (Intercept Layer)                                   │  │ ║
║  │  │  ┌─────────────┐ ┌──────────────┐ ┌──────────────┐               │  │ ║
║  │  │  │ Haiku Router│ │ Sonnet Router│ │ Opus Router  │               │  │ ║
║  │  │  │ (clasif)    │ │ (ADRs/review)│ │ (estrategia) │               │  │ ║
║  │  │  └──────┬──────┘ └──────┬───────┘ └──────┬───────┘               │  │ ║
║  │  └─────────┼───────────────┼────────────────┼───────────────────────┘  │ ║
║  └────────────┼───────────────┼────────────────┼─────────────────────────┘ ║
║               │               │                │                           ║
║  ┌────────────┼───────────────┼────────────────┼─────────────────────────┐ ║
║  │  CAPA DE   ▼               ▼                ▼                         │ ║
║  │  PROVEEDORES                                                                │ ║
║  │                                                                          │ ║
║  │  ┌──────────────────┐ ┌──────────────────┐ ┌──────────────────┐        │ ║
║  │  │ ANTHROPIC DIRECT  │ │ AWS BEDROCK      │ │ PROVEEDORES      │        │ ║
║  │  │ • Sonnet 4.6     │ │ • Sonnet 4.6     │ │ CON MARGEN       │        │ ║
║  │  │ • Opus 4.8       │ │ • Opus 4.8       │ │                  │        │ ║
║  │  │ • Haiku 4.5      │ │ • Haiku 4.5      │ │ ┌──────────────┐│        │ ║
║  │  │ • Batch API      │ │ • Batch API      │ │ │ OpenRouter   ││        │ ║
║  │  │ • Prompt Caching │ │ • Prompt Caching │ │ │ (~5.5% mark.)││        │ ║
║  │  └────────┬─────────┘ └────────┬─────────┘ │ │              ││        │ ║
║  │           │                    │           │ │ Izzi API     ││        │ ║
║  │           │                    │           │ │ (sin TC)     ││        │ ║
║  │           │                    │           │ │              ││        │ ║
║  │           │                    │           │ │ AIcheap.io   ││        │ ║
║  │           │                    │           │ │ ($4.99/mes)  ││        │ ║
║  │           │                    │           │ │              ││        │ ║
║  │           │                    │           │ │ claude-router ││        │ ║
║  │           │                    │           │ │ (auto-tier)  ││        │ ║
║  │           │                    │           │ └──────────────┘│        │ ║
║  │           │                    │           │                  │        │ ║
║  │           │                    │           │  ┌────────────┐  │        │ ║
║  │           │                    │           │  │ Fallback:  │  │        │ ║
║  │           │                    │           │  │ go-kimi    │  │        │ ║
║  │           │                    │           │  │ go-pro     │  │        │ ║
║  │           │                    │           │  │ go-flash   │  │        │ ║
║  │           │                    │           │  └────────────┘  │        │ ║
║  │  └────────┼────────────────────┼───────────┼──────────────────┘        │ ║
║  │           │                    │           │                            │ ║
║  │           └────────┬───────────┘           │                            │ ║
║  │                    ▼                       │                            │ ║
║  │  ┌─────────────────────────────────────────┴──────────────┐            │ ║
║  │  │  agy-bridge (mcp_agy_bridge.py)                        │            │ ║
║  │  │  • agy_ask_sonnet — Claude Sonnet 4.6                  │            │ ║
║  │  │  • agy_ask_opus — Claude Opus 4.6/4.8                 │            │ ║
║  │  │  • agy_ask_haiku — Claude Haiku 4.5 (NUEVO)           │            │ ║
║  │  │  • agy_ask_flash — Gemini 3.5 Flash (FREE)            │            │ ║
║  │  │  • agy_ask_gpt55 — GPT-5.5 (ChatGPT Plus)             │            │ ║
║  │  │  • agy_ask_opus_thinking — Opus + Extended Thinking   │            │ ║
║  │  └────────────────────────────────────────────────────────┘            │ ║
║  └──────────────────────────────────────────────────────────────────────────┘ ║
║                                                                               ║
║  ┌─────────────────────────────────────────────────────────────────────────┐  ║
║  │  CAPA DE HERRAMIENTAS (MCP)                                            │  ║
║  │                                                                          │  ║
║  │  ┌──────────┐ ┌──────────┐ ┌──────────┐ ┌──────────┐ ┌──────────┐      │  ║
║  │  │ GitHub   │ │ Redis    │ │PostgreSQL│ │Puppeteer │ │Memory    │      │  ║
║  │  │ MCP      │ │ MCP      │ │ MCP      │ │ MCP      │ │ MCP      │      │  ║
║  │  └──────────┘ └──────────┘ └──────────┘ └──────────┘ └──────────┘      │  ║
║  │                                                                          │  ║
║  │  ┌──────────┐ ┌──────────┐ ┌──────────┐ ┌──────────────────┐          │  ║
║  │  │ Struct-  │ │ agy-     │ │ mcp-     │ │ mcp-ether (NUEVO)│          │  ║
║  │  │ urizr    │ │ bridge   │ │ dsol     │ │ + Claude routing │          │  ║
║  │  └──────────┘ └──────────┘ └──────────┘ └──────────────────┘          │  ║
║  │                                                                          │  ║
║  │  ┌──────────────────────────────────────────────────────────────────┐   │  ║
║  │  │  MCP HUB (TypeScript, .workspace/src/server/)                    │   │  ║
║  │  │  • mcp-hub-sources-store → multi-source aggregation              │   │  ║
║  │  │  • mcp-presets-store → server presets & templates                │   │  ║
║  │  │  • mcp-tools-cache → caching layer for MCP tools                │   │  ║
║  │  │  • mcp-normalize → standardize MCP server configs               │   │  ║
║  │  │  • mcp-input-validate → schema validation for MCP inputs        │   │  ║
║  │  └──────────────────────────────────────────────────────────────────┘   │  ║
║  └─────────────────────────────────────────────────────────────────────────┘  ║
║                                                                               ║
║  ┌─────────────────────────────────────────────────────────────────────────┐  ║
║  │  CAPA DE OBSERVABILIDAD                                                │  ║
║  │                                                                          │  ║
║  │  ┌──────────────┐ ┌──────────────┐ ┌──────────────┐ ┌────────────────┐  │  ║
║  │  │ EtherTracker  │ │ QualityStore │ │ EtherJudge   │ │ Prometheus     │  │  ║
║  │  │ (tokens/      │ │ (scores por  │ │ (6 dims:     │ │ (métricas      │  │  ║
║  │  │ costos/sesión)│ │ modelo+tarea)│ │ V/C/CP/R/U)  │ │ de sistema)    │  │  ║
║  │  └──────────────┘ └──────────────┘ └──────────────┘ └────────────────┘  │  ║
║  │                                                                          │  ║
║  │  ┌──────────────┐ ┌──────────────┐ ┌──────────────┐ ┌────────────────┐  │  ║
║  │  │ Ether        │ │ DeepEval     │ │ AB Testing   │ │ Dashboard      │  │  ║
║  │  │ Dashboard    │ │ (halluc./    │ │ (chi-cuad.)  │ │ (HTML + CLI)   │  │  ║
║  │  │ (HTML + CLI) │ │ relevancy)   │ │              │ │                │  │  ║
║  │  └──────────────┘ └──────────────┘ └──────────────┘ └────────────────┘  │  ║
║  └─────────────────────────────────────────────────────────────────────────┘  ║
╚═══════════════════════════════════════════════════════════════════════════════╝
```

---

## 2. Flujos de Decisión

### 2.1 ¿Cuándo usar Claude Code nativo vs OpenCode vs Cline?

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                 MATRIZ DE SELECCIÓN DE HERRAMIENTAS                          │
│                                                                              │
│ ┌─────────────────────┬─────────────────────┬──────────────────────────────┐ │
│ │ CRITERIO            │ RECOMENDACIÓN       │ JUSTIFICACIÓN                │ │
│ ├─────────────────────┼─────────────────────┼──────────────────────────────┤ │
│ │ Tarea default       │ OpenCode            │ Multi-provider, ACP protocol │ │
│ │ (code gen, lint)    │                     │ 165K⭐, ya integrado en KAOS │ │
│ ├─────────────────────┼─────────────────────┼──────────────────────────────┤ │
│ │ Refactor complejo   │ Claude Code         │ SWE-bench 80.8%, agent loop  │ │
│ │ multi-archivo       │ (externo)           │ más sofisticado              │ │
│ ├─────────────────────┼─────────────────────┼──────────────────────────────┤ │
│ │ Debugging profundo  │ Claude Code         │ Extended Thinking, circuit   │ │
│ │ con razonamiento    │                     │ tracing-like capabilities    │ │
│ ├─────────────────────┼─────────────────────┼──────────────────────────────┤ │
│ │ MCP-heavy workflow  │ Cline               │ MCP nativo, 30+ LLM prov.   │ │
│ │ (muchas tools)      │                     │ 62K⭐, VS Code + CLI + JB    │ │
│ ├─────────────────────┼─────────────────────┼──────────────────────────────┤ │
│ │ Tareas rutinarias   │ OpenCode (go-flash) │ Costo 357x menor que Opus   │ │
│ │ de bajo riesgo      │                     │                             │ │
│ ├─────────────────────┼─────────────────────┼──────────────────────────────┤ │
│ │ Multi-agent         │ OpenCode (KAOS)     │ Agentes nativos, routing     │ │
│ │ orchestrations      │                     │ Aether v3                    │ │
│ └─────────────────────┴─────────────────────┴──────────────────────────────┘ │
└─────────────────────────────────────────────────────────────────────────────┘
```

**Regla de oro**: KAOS usa OpenCode como cliente default. Claude Code se invoca **solo bajo demanda** para tareas que requieren su SWE-bench 80.8%, mediante un wrapper que sincroniza el workspace y ejecuta `claude` con `CLAUDE.md` específico del proyecto.

### 2.2 ¿Cuándo enrutar a Anthropic Direct vs OpenRouter vs proveedor con margen?

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                ÁRBOL DE DECISIÓN DE PROVEEDOR CLAUDE                         │
│                                                                              │
│  ¿Es una tarea crítica (ADR, estrategia, validación)?                        │
│  ├── SÍ → ¿Necesita baja latencia (<10s)?                                   │
│  │      ├── SÍ → Anthropic Direct (sin intermediarios)                      │
│  │      └── NO → ¿Tiene presupuesto para Batch?                              │
│  │             ├── SÍ → Anthropic Batch API (50% descuento)                 │
│  │             └── NO → Anthropic Direct (estándar)                         │
│  │                                                                           │
│  └── NO → ¿Es una tarea experimental/exploratoria?                          │
│         ├── SÍ → OpenRouter (~5.5% markup, multi-modelo)                    │
│         │       o Izzi API (créditos gratis, sin TC)                        │
│         └── NO → ¿Requiere alta disponibilidad?                             │
│                ├── SÍ → AWS Bedrock (failover geográfico)                   │
│                └── NO → Proveedor con margen:                               │
│                         AIcheap.io ($4.99/mes) o ClaudeAPI.cheap ($19 life) │
│                                                                              │
│  ¿El proveedor primario falló?                                               │
│  └── SÍ → Fallback chain:                                                    │
│           claude-sonnet → claude-opus → go-kimi-latest →                    │
│           go-pro → go-flash                                                  │
└─────────────────────────────────────────────────────────────────────────────┘
```

### 2.3 ¿Cuándo usar Haiku vs Sonnet vs Opus?

```yaml
# aether.yaml — Nuevas entradas para Claude tiers
task_model_map:
  # ... existing entries ...
  
  # NUEVOS: Claude tiers premium
  classification:    {model: claude-haiku,   thinking: null, tier: claude_haiku}
  quick_review:      {model: claude-haiku,   thinking: null, tier: claude_haiku}
  adr_validation:    {model: claude-sonnet,  thinking: light, tier: claude_sonnet}
  design_review:     {model: claude-sonnet,  thinking: medium, tier: claude_sonnet}
  quality_audit:     {model: claude-sonnet,  thinking: medium, tier: claude_sonnet}
  strategy_critical: {model: claude-opus,    thinking: high,  tier: claude_opus}
  ethics_review:     {model: claude-opus,    thinking: high,  tier: claude_opus}
  dual_validation:   {model: claude-opus,    thinking: xmax,  tier: claude_opus}

# NUEVOS: Claude cost rates (Prompt Caching: 90% descuento en reads)
cost_rates:
  claude-haiku:  {input: 0.00100, output: 0.00500, cache_read: 0.00010}
  claude-sonnet: {input: 0.00300, output: 0.01500, cache_read: 0.00030}
  claude-opus:   {input: 0.00500, output: 0.02500, cache_read: 0.00050}

# NUEVOS: Claude cost caps (semanales, estrictos)
cost_caps:
  claude_haiku:  {weekly_usd: 0.20, daily_calls: 20}
  claude_sonnet: {weekly_usd: 0.50, daily_calls: 10}
  claude_opus:   {weekly_usd: 0.30, daily_calls: 3}

# NUEVOS: Claude model tiers
model_tiers:
  claude_haiku: {description: "Claude rápido para clasificación", target_pct: 3}
  claude_sonnet: {description: "Claude balance para ADRs/review", target_pct: 5}
  claude_opus:   {description: "Claude premium para estrategia",  target_pct: 2}

# NUEVOS: Claude fallback chains
fallback_chains:
  claude-haiku:  [claude-haiku, claude-sonnet, go-flash, go-mimo]
  claude-sonnet: [claude-sonnet, claude-opus, go-kimi-latest, go-pro, go-flash]
  claude-opus:   [claude-opus, go-kimi-latest, go-pro, go-flash, go-mimo]
```

### 2.4 Estrategia de Fallback Completa

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                    ESTRATEGIA DE FALLBACK MULTI-CAPA                          │
│                                                                              │
│  NIVEL 1 — Circuit Breaker (por modelo):                                     │
│  ┌──────────┬─────────┬──────────┬────────────────────────────────────────┐ │
│  │ Modelo   │ Umbral  │ Timeout  │ Acción                                 │ │
│  ├──────────┼─────────┼──────────┼────────────────────────────────────────┤ │
│  │ Haiku    │ 5 fail  │ 60s      │ → claude-sonnet → go-flash             │ │
│  │ Sonnet   │ 3 fail  │ 120s     │ → claude-opus → go-kimi-latest         │ │
│  │ Opus     │ 2 fail  │ 300s     │ → go-kimi-latest → go-pro → go-flash   │ │
│  └──────────┴─────────┴──────────┴────────────────────────────────────────┘ │
│                                                                              │
│  NIVEL 2 — Proveedor Failover:                                               │
│  Anthropic Direct → AWS Bedrock → OpenRouter → Proveedor margen             │
│                                                                              │
│  NIVEL 3 — Model Degradation:                                                │
│  claude-opus → claude-sonnet → haiku → go-kimi-latest → go-pro → go-flash   │
│                                                                              │
│  NIVEL 4 — Cost Cap Enforcement:                                             │
│  Si cost_caps.exceeded → downgrade automático a go-flash (siempre disponible)│
└─────────────────────────────────────────────────────────────────────────────┘
```

---

## 3. Estrategia de Caching y Costos

### 3.1 Prompt Caching — Arquitectura

```
┌─────────────────────────────────────────────────────────────────────────────┐
│          ESTRATEGIA DE PROMPT CACHING (90% descuento en reads)               │
│                                                                              │
│  ┌──────────────────────────────────────────────────────────────────────┐   │
│  │  ESTRUCTURA DE PROMPT (orden crítico para caching)                   │   │
│  │                                                                       │   │
│  │  ┌────────────────────────────────────────────────────────────┐      │   │
│  │  │ BLOQUE ESTÁTICO (CACHEABLE — 90% descuento)                │      │   │
│  │  │ ├── System prompt del agente (SOUL.md)    ~2K tokens      │      │   │
│  │  │ ├── Skill del agente (SKILL.md)           ~3K tokens      │      │   │
│  │  │ ├── Vault constitution (KAOS.yaml)        ~1K tokens      │      │   │
│  │  │ ├── ADRs relevantes (fixos)               ~2K tokens      │      │   │
│  │  │ └── Rego policies                         ~1K tokens      │      │   │
│  │  │                                           Total: ~9K       │      │   │
│  │  └────────────────────────────────────────────────────────────┘      │   │
│  │                                                                       │   │
│  │  ┌────────────────────────────────────────────────────────────┐      │   │
│  │  │ BLOQUE SEMI-ESTÁTICO (PARCIALMENTE CACHEABLE)              │      │   │
│  │  │ ├── Contexto del vault     ~5K tokens  (cambia ~10%)      │      │   │
│  │  │ ├── Historial de sesión    ~3K tokens  (cambia ~30%)      │      │   │
│  │  │ └── Documentos referencia  ~4K tokens  (cambia ~20%)      │      │   │
│  │  │                                     Total: ~12K            │      │   │
│  │  └────────────────────────────────────────────────────────────┘      │   │
│  │                                                                       │   │
│  │  ┌────────────────────────────────────────────────────────────┐      │   │
│  │  │ BLOQUE DINÁMICO (SIN CACHE — PRECIO COMPLETO)              │      │   │
│  │  │ ├── Consulta específica        ~1K tokens                  │      │   │
│  │  │ ├── Instrucción de tarea       ~0.5K tokens                │      │   │
│  │  │ └── Contexto inmediato         ~1K tokens                  │      │   │
│  │  │                                     Total: ~2.5K           │      │   │
│  │  └────────────────────────────────────────────────────────────┘      │   │
│  └──────────────────────────────────────────────────────────────────────┘   │
│                                                                              │
│  AHORRO ESTIMADO:                                                            │
│  Sin caching: 23.5K tokens × $0.003/1K = $0.0705 por llamada Sonnet         │
│  Con caching: (9K × $0.0003 + 12K × $0.001 + 2.5K × $0.003) = $0.0222      │
│  Ahorro: 68.5% por llamada                                                  │
│                                                                              │
│  Cache invalidation: 5 min de inactividad (mecanismo nativo Anthropic)       │
└─────────────────────────────────────────────────────────────────────────────┘
```

### 3.2 Batch API — Pipeline Nocturno

```
┌─────────────────────────────────────────────────────────────────────────────┐
│              PIPELINE BATCH API NOCTURNA (50% descuento)                     │
│                                                                              │
│  HORARIO: 3:00 AM (cuando KAOS está inactivo)                               │
│                                                                              │
│  ┌────────┐    ┌──────────────┐    ┌──────────────┐    ┌──────────────┐     │
│  │ 3:00AM │───▶│ Mnemosyne    │───▶│ Clasificador  │───▶│ Enviar lote  │     │
│  │ Trigger│    │ recopila docs │    │ por complej. │    │ a Batch API  │     │
│  └────────┘    └──────────────┘    └──────────────┘    └──────┬───────┘     │
│                                                               │              │
│                    ┌──────────────────────────────────────────┘              │
│                    ▼                                                         │
│  ┌─────────────────────────────────────────────────────────────────────┐    │
│  │  CLASIFICACIÓN MULTI-TIER                                            │    │
│  │                                                                       │    │
│  │  ┌───────────┬─────────────┬──────────┬───────────┬──────────────┐   │    │
│  │  │ Categoría │ Porcentaje  │ Modelo   │ Costo/doc │ Costo total  │   │    │
│  │  ├───────────┼─────────────┼──────────┼───────────┼──────────────┤   │    │
│  │  │ SIMPLE    │ 80% (800)   │ go-mimo  │ $0.000014 │ $0.011       │   │    │
│  │  │ STANDARD  │ 15% (150)   │ Sonnet   │ $0.006    │ $0.90        │   │    │
│  │  │           │             │ (batch)  │           │              │   │    │
│  │  │ COMPLEX   │ 5% (50)     │ Opus     │ $0.02     │ $1.00        │   │    │
│  │  │           │             │ (batch)  │           │              │   │    │
│  │  └───────────┴─────────────┴──────────┴───────────┴──────────────┘   │    │
│  │                                       TOTAL NOCHE: ~$1.91            │    │
│  └─────────────────────────────────────────────────────────────────────┘    │
│                                                                              │
│  SINCRONIZACIÓN (4:00 AM):                                                   │
│  ┌──────────────┐    ┌──────────────┐    ┌──────────────┐                   │
│  │ Recibir      │───▶│ Actualizar   │───▶│ Regenerar    │                   │
│  │ resultados   │    │ vault        │    │ índices txtai │                   │
│  └──────────────┘    └──────────────┘    └──────────────┘                   │
└─────────────────────────────────────────────────────────────────────────────┘
```

### 3.3 Context Window Management

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                ESTRATEGIA DE CONTEXT WINDOW MANAGEMENT                       │
│                                                                              │
│  Principio: Claude tiene 200K contexto — gestionar para evitar             │
│  degradación de calidad y costos innecesarios.                              │
│                                                                              │
│  TÉCNICAS:                                                                   │
│                                                                              │
│  1. SLIDING WINDOW                                                          │
│     • Ventana activa: últimos 50K tokens de conversación                    │
│     • Resúmenes periódicos cada 40K tokens                                  │
│     • Cache de historial comprimido para referencia                         │
│                                                                              │
│  2. PROMPT COMPRESSION                                                      │
│     • Comprimir tools MCP: solo descripciones, no schemas completos         │
│     • Skills cargados como referencia, no inline                            │
│     • Contexto del vault: solo secciones relevantes (RAG)                   │
│                                                                              │
│  3. TIER-BASED CONTEXT ALLOCATION                                           │
│     │ Agent          │ Base  │ With Thinking │ Max                          │
│     │────────────────│───────│───────────────│─────                         │
│     │ Haiku          │ 25K   │ N/A           │ 50K                          │
│     │ Sonnet (light) │ 50K   │ 75K           │ 100K                         │
│     │ Sonnet (medium)│ 50K   │ 100K          │ 150K                         │
│     │ Opus (high)    │ 75K   │ 150K          │ 200K                         │
│     │ Opus (xmax)    │ 50K   │ 180K          │ 200K                         │
│                                                                              │
│  4. LONG-CONTEXT ROUTING                                                    │
│     • Prompts >100K tokens → claude-opus (routing automático)               │
│     • Prompts >150K tokens → advertencia + compresión forzada               │
│     • Alternativa: go-kimi-latest para contexto largo no crítico            │
└─────────────────────────────────────────────────────────────────────────────┘
```

### 3.4 Cálculo de Ahorros — Proyección Completa

```
┌─────────────────────────────────────────────────────────────────────────────┐
│          PROYECCIÓN DE COSTOS — CON vs SIN OPTIMIZACIONES                    │
│                                                                              │
│  Escenario base (sin Claude, solo DeepSeek/Kimi): $27/mes                    │
│                                                                              │
│  ┌──────────────────────────────────────┬──────────┬──────────┬───────────┐ │
│  │ Componente                           │ Sin opt. │ Con opt. │ Ahorro    │ │
│  ├──────────────────────────────────────┼──────────┼──────────┼───────────┤ │
│  │ Llamadas Sonnet (sin cache)          │ $21.00   │ $6.60    │ 68.5%     │ │
│  │ Llamadas Opus (sin cache)            │ $12.00   │ $3.80    │ 68.3%     │ │
│  │ Llamadas Haiku (clasificación)       │ $5.00    │ $1.50    │ 70.0%     │ │
│  │ Batch API (nocturna)                 │ $0.00    │ $7.64    │ (nuevo)   │ │
│  ├──────────────────────────────────────┼──────────┼──────────┼───────────┤ │
│  │ Subtotal Claude                      │ $38.00   │ $19.54   │ 48.6%     │ │
│  │ Backbone DeepSeek+Kimi (sin cambio)  │ $27.00   │ $27.00   │ 0%        │ │
│  ├──────────────────────────────────────┼──────────┼──────────┼───────────┤ │
│  │ TOTAL                                │ $65.00   │ $46.54   │ 28.4%     │ │
│  └──────────────────────────────────────┴──────────┴──────────┴───────────┘ │
│                                                                              │
│  Diferencia contra línea base ($27): +$19.54/mes (+72% vs +140% sin opt.)   │
│  Retorno: +15-25% calidad por +72% costo (ratio 1:3.5 favorable)            │
└─────────────────────────────────────────────────────────────────────────────┘
```

---

## 4. Integración MCP

### 4.1 MCP Servers Core Recomendados para Ecosistema Claude

```yaml
# mcp_config.json — Servidores MCP recomendados para Claude
{
  "mcpServers": {
    "kaos-anthropic-bridge": {
      "command": "python",
      "args": [".memory/_scripts/mcp_agy_bridge.py"],
      "description": "Bridge to Claude Sonnet/Opus/Haiku + Gemini Flash + GPT-5.5",
      "alwaysAllow": ["agy_ask_haiku", "agy_ask_sonnet", "agy_ask_opus"]
    },
    "kaos-aether-router": {
      "command": "python",
      "args": [".memory/_scripts/mcp_ether.py"],
      "description": "Model routing decisions via Aether v3"
    },
    "kaos-quality-store": {
      "command": "python",
      "args": [".memory/_scripts/mcp_ether_judge.py"],
      "description": "Quality evaluation and scoring"
    },
    "github": {
      "command": "npx",
      "args": ["-y", "@modelcontextprotocol/server-github"],
      "env": {
        "GITHUB_TOKEN": "${GITHUB_TOKEN}"
      }
    },
    "memory": {
      "command": "npx",
      "args": ["-y", "@modelcontextprotocol/server-memory"],
      "env": {
        "MEMORY_FILE_PATH": ".memory/cache/mcp-memory.json"
      }
    },
    "postgresql": {
      "command": "npx",
      "args": ["-y", "@modelcontextprotocol/server-postgres", "--connection-string", "${DATABASE_URL}"]
    },
    "puppeteer": {
      "command": "npx",
      "args": ["-y", "@modelcontextprotocol/server-puppeteer"]
    },
    "redis": {
      "command": "npx",
      "args": ["-y", "@modelcontextprotocol/server-redis", "${REDIS_URL}"]
    },
    "composio": {
      "command": "npx",
      "args": ["-y", "composio-mcp"],
      "env": {
        "COMPOSIO_API_KEY": "${COMPOSIO_API_KEY}"
      }
    }
  }
}
```

### 4.2 Exposición de Tools Internas como MCP Servers

```
┌─────────────────────────────────────────────────────────────────────────────┐
│               EXPOSICIÓN DE TOOLS INTERNAS COMO MCP SERVERS                  │
│                                                                              │
│  Herramientas actuales a exponer:                                            │
│                                                                              │
│  ┌──────────────────────┬────────────────────┬────────────────────────────┐ │
│  │ Tool MCP             │ Función Interna     │ Uso para Claude            │ │
│  ├──────────────────────┼────────────────────┼────────────────────────────┤ │
│  │ claude_route(task,   │ Aether resolve()   │ Seleccionar modelo óptimo │ │
│  │   context)           │                     │ Claude vs DeepSeek vs Kimi│ │
│  ├──────────────────────┼────────────────────┼────────────────────────────┤ │
│  │ claude_cache(prompt) │ Prompt Caching     │ Cachear prompts            │ │
│  │                      │ Manager             │ reutilizables              │ │
│  ├──────────────────────┼────────────────────┼────────────────────────────┤ │
│  │ claude_judge(        │ EtherJudge         │ Evaluar calidad de         │ │
│  │   prompt, response)  │                     │ respuestas Claude          │ │
│  ├──────────────────────┼────────────────────┼────────────────────────────┤ │
│  │ claude_track(model,  │ EtherTracker       │ Tracking de costos y       │ │
│  │   tokens, cost)      │                     │ tokens de Claude           │ │
│  ├──────────────────────┼────────────────────┼────────────────────────────┤ │
│  │ claude_batch(        │ Anthropic Batch    │ Enviar lote nocturno       │ │
│  │   requests)          │ Pipeline            │ a procesamiento asíncrono  │ │
│  ├──────────────────────┼────────────────────┼────────────────────────────┤ │
│  │ claude_kb(topic)     │ txtai Qdrant       │ Recuperar knowledge base   │ │
│  │                      │ RAG                │ para contexto              │ │
│  └──────────────────────┴────────────────────┴────────────────────────────┘ │
└─────────────────────────────────────────────────────────────────────────────┘
```

### 4.3 Estrategia de Seguridad y Permisos MCP

```
┌─────────────────────────────────────────────────────────────────────────────┐
│              ESTRATEGIA DE SEGURIDAD MCP (Basado en ADR-003)                │
│                                                                              │
│  PRINCIPIOS:                                                                 │
│  1. Least Privilege: cada MCP solo expone las tools mínimas necesarias      │
│  2. Read-Only by Default: servidores externos solo lectura                  │
│  3. Rate Limiting: por agente, por servidor MCP                              │
│  4. Audit Logging: todas las llamadas MCP registradas                       │
│  5. Prompt Injection Defense: validación de entrada en MCP bridge           │
│                                                                              │
│  PERMISOS POR AGENTE (Per-Agent MCP Restriction):                           │
│                                                                              │
│  ┌──────────┬──────────────────────────┬──────────────────────────────────┐ │
│  │ Agente   │ MCPs Permitidos          │ MCPs Restringidos               │ │
│  ├──────────┼──────────────────────────┼──────────────────────────────────┤ │
│  │ Aletheia │ agy-bridge, firecrawl,   │ Todos los de escritura          │ │
│  │          │ search, puppeteer        │ (postgres, filesystem, github)  │ │
│  ├──────────┼──────────────────────────┼──────────────────────────────────┤ │
│  │ Kratos   │ github, filesystem,      │ agy-bridge (solo Sonnet, no     │ │
│  │          │ postgres, agy-bridge     │ Opus sin aprobación)            │ │
│  ├──────────┼──────────────────────────┼──────────────────────────────────┤ │
│  │ Kosmos   │ agy-bridge, structurizr, │ firecrawl, puppeteer            │ │
│  │          │ aether, quality-store    │                                  │ │
│  ├──────────┼──────────────────────────┼──────────────────────────────────┤ │
│  │ Metis    │ agy-bridge (Opus+thinking)│ firecrawl, puppeteer, github    │ │
│  │          │ stratey-memory           │                                  │ │
│  ├──────────┼──────────────────────────┼──────────────────────────────────┤ │
│  │ Mnemosyne│ agy-bridge, txtai, embed,│ puppeteer, github               │ │
│  │          │ filesystem (read-only)   │                                  │ │
│  └──────────┴──────────────────────────┴──────────────────────────────────┘ │
│                                                                              │
│  SEGURIDAD DE TOOLS MCP INDIVIDUALES:                                        │
│  • agy_ask_opus: requiere confirmación explícita (costoso)                  │
│  • agy_ask_opus_thinking: requiere doble confirmación + justificación       │
│  • agy_ask_haiku: sin restricciones (económico)                             │
│  • agy_ask_sonnet: disponible en perfiles producción                        │
│  • firecrawl_write: solo para Mnemosyne                                     │
└─────────────────────────────────────────────────────────────────────────────┘
```

---

## 5. Arquitectura de Subagentes

### 5.1 Patrones Recomendados

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                       PATRONES DE SUBAGENTES                                 │
│                                                                              │
│  ┌─────────────────────────────────────────────────────────────────────────┐│
│  │ PATRÓN 1: SUPERVISOR (para metis)                                       ││
│  │                                                                          ││
│  │  ┌──────────┐                                                           ││
│  │  │  Metis   │ ← Supervisor: asigna subtareas, sintetiza resultados      ││
│  │  │ (Opus)   │                                                           ││
│  │  └────┬─────┘                                                           ││
│  │       │                                                                 ││
│  │  ┌────┴─────────────────────────────────────────────────────────┐      ││
│  │  │ ┌──────────┐ ┌──────────┐ ┌──────────┐ ┌──────────┐        │      ││
│  │  │ │ Aletheia │ │ Kosmos   │ │ Kratos   │ │ Mnemosyne│        │      ││
│  │  │ │ (Flash)  │ │ (Sonnet) │ │ (Flash)  │ │ (Flash)  │        │      ││
│  │  │ └──────────┘ └──────────┘ └──────────┘ └──────────┘        │      ││
│  │  │ Cada subagente ejecuta subtarea en paralelo                 │      ││
│  │  │ Metis sintetiza resultados → produce output final           │      ││
│  │  └─────────────────────────────────────────────────────────────┘      ││
│  └─────────────────────────────────────────────────────────────────────────┘│
│                                                                              │
│  ┌─────────────────────────────────────────────────────────────────────────┐│
│  │ PATRÓN 2: PIPELINE (para Kosmos)                                        ││
│  │                                                                          ││
│  │  Discover ──▶ Model ──▶ Analyze ──▶ Quality ──▶ Visualize ──▶ Document  ││
│  │  (Flash)     (Flash)    (Sonnet)   (Sonnet)   (Flash)     (Opus)       ││
│  │  Cada etapa del pipeline usa el modelo óptimo para esa tarea             ││
│  └─────────────────────────────────────────────────────────────────────────┘│
│                                                                              │
│  ┌─────────────────────────────────────────────────────────────────────────┐│
│  │ PATRÓN 3: ENSEMBLE (para validación dual)                              ││
│  │                                                                          ││
│  │  ┌──────────────┐  ┌──────────────┐                                    ││
│  │  │  Claude Opus │  │  GPT-5.1     │  ← Dos modelos independientes      ││
│  │  │  evalúa ADR  │  │  evalúa ADR  │                                    ││
│  │  └──────┬───────┘  └──────┬───────┘                                    ││
│  │         │                 │                                              ││
│  │         └────────┬────────┘                                              ││
│  │                  ▼                                                       ││
│  │         ┌────────────────┐                                              ││
│  │         │ EtherJudge     │ ← Compara scores, detecta discrepancias      ││
│  │         │ reconcilia     │                                               ││
│  │         └────────────────┘                                              ││
│  └─────────────────────────────────────────────────────────────────────────┘│
│                                                                              │
│  ┌─────────────────────────────────────────────────────────────────────────┐│
│  │ PATRÓN 4: PARALLEL (para clasificación masiva)                          ││
│  │                                                                          ││
│  │  ┌────────────────────────────────────────────────────────────────────┐ ││
│  │  │ Batch de 100 documentos → Haiku 4.5 clasifica en paralelo         │ ││
│  │  │ Cada documento es independiente → throughput máximo                │ ││
│  │  │ Costo: 100 × ~500 tokens × $0.001/1K = $0.05                       │ ││
│  │  └────────────────────────────────────────────────────────────────────┘ ││
│  └─────────────────────────────────────────────────────────────────────────┘│
└─────────────────────────────────────────────────────────────────────────────┘
```

### 5.2 ¿Cuándo Spawnear Subagentes vs Ejecución Secuencial?

```
┌─────────────────────────────────────────────────────────────────────────────┐
│              ÁRBOL DE DECISIÓN: SUBAGENTE vs SECUENCIAL                      │
│                                                                              │
│  ¿La tarea se puede dividir en subtareas independientes?                     │
│  ├── SÍ → ¿Las subtareas requieren el mismo contexto?                       │
│  │      ├── SÍ → ¿Hay >3 subtareas?                                         │
│  │      │      ├── SÍ → Supervisor Pattern (1 subagente llama subagentes)   │
│  │      │      └── NO → Ejecución secuencial (menos overhead)               │
│  │      └── NO → Parallel Pattern (subagentes con contexto aislado)         │
│  └── NO → Ejecución secuencial simple                                       │
│                                                                              │
│  ¿La tarea requiere validación cruzada?                                      │
│  ├── SÍ → Ensemble Pattern (2 modelos, mismo input, comparar outputs)       │
│  └── NO → Pipeline Pattern (etapas secuenciales con modelo óptimo cada una) │
│                                                                              │
│  COSTO DE SUBAGENTE:                                                        │
│  • Overhead de contexto: ~500 tokens por subagente (instrucciones)          │
│  • Overhead de comunicación: ~200 tokens por resultado                      │
│  • Break-even: subagente vale la pena si la tarea es >700 tokens            │
└─────────────────────────────────────────────────────────────────────────────┘
```

### 5.3 Compartición de Cache entre Subagentes

```
┌─────────────────────────────────────────────────────────────────────────────┐
│              COMPARTICIÓN DE CACHE ENTRE SUBAGENTES                          │
│                                                                              │
│  ESTRATEGIA: System Prompts Compartidos                                      │
│  • Todos los subagentes KAOS comparten el mismo system prompt base           │
│  • Cache hit rate: cada subagente nuevo hereda el cache del anterior         │
│  • Esto funciona porque Anthropic cachea por prefix de prompt                │
│  • Ejemplo práctico:                                                         │
│                                                                              │
│  Subagente 1: [System Prompt ~9K] + [Task 1 ~2K] → 11K, cachea primeros 9K  │
│  Subagente 2: [System Prompt ~9K] + [Task 2 ~2K] → 11K, cache hit primeros  │
│                9K → ahorro 90% en 9K tokens                                  │
│                                                                              │
│  AHORRO POR SUBAGENTE ADICIONAL:                                             │
│  Sin compartir: 11K × $0.003 = $0.033                                       │
│  Con compartir: (9K × $0.0003) + (2K × $0.003) = $0.0087                    │
│  Ahorro: 73.6% por subagente adicional                                       │
│                                                                              │
│  LÍMITES:                                                                    │
│  • El cache expira después de 5 minutos de inactividad                       │
│  • Máximo beneficio si los subagentes se ejecutan en serie rápida            │
│  • Para subagentes en paralelo: cada uno tiene su propio cache (no comparten)│
└─────────────────────────────────────────────────────────────────────────────┘
```

---

## 6. Plan de Implementación Técnica

### 6.1 Fase 1 — Quick Wins (Semana 1-2)

```yaml
# sprint-1-quick-wins.yaml
fase: 1
duracion: "Semana 1-2"
costo_incremental: "+$0.10/semana"

tareas:
  - id: QW-1
    nombre: "Agregar Haiku 4.5 a agy-bridge"
    archivos:
      - .memory/_scripts/mcp_agy_bridge.py
    cambios:
      - "Nuevo tool: agy_ask_haiku(PROMPT, timeout=60)"
      - "Mapear tier='haiku' en call_agy()"
    comando: |
      # Test:
      python -c "from lib.agy_client import call_agy; print(call_agy('Hello', tier='haiku'))"

  - id: QW-2
    nombre: "Prompt Caching en agy-bridge"
    archivos:
      - .memory/_scripts/mcp_agy_bridge.py
      - .memory/_scripts/lib/agy_client.py
    cambios:
      - "Reestructurar prompts: bloque estático (cacheable) + bloque dinámico"
      - "Agregar cache headers en llamadas Anthropic"
      - "Configurar cache_control en system prompt"
    detalle: |
      # En agy_client.py, modificar build_prompt():
      system_prompt = {
          "type": "text",
          "text": SOUL_MD + SKILL_MD,
          "cache_control": {"type": "ephemeral"}  # ← cache header
      }
    test: |
      # Verificar cache hit:
      python .memory/_scripts/tests/test_prompt_cache.py

  - id: QW-3
    nombre: "Configurar Claude tiers en Aether"
    archivos:
      - .memory/_scripts/aether.yaml
    cambios:
      - "Agregar claude-haiku, claude-sonnet, claude-opus en task_model_map"
      - "Agregar cost_rates para Claude (con cache_read)"
      - "Agregar cost_caps para Claude (estrictos)"
      - "Agregar fallback_chains para Claude"
    contenido: |
      # Ver aether.yaml sección 2.3 para configuración completa

  - id: QW-4
    nombre: "Routing Claude via Aether"
    archivos:
      - .memory/_scripts/lib/aether/router.py
      - .memory/_scripts/lib/aether/client.py
    cambios:
      - "router.py: nueva etapa 2.5 _resolve_via_agy() para modelos claude-*"
      - "client.py: chat() detecta modelo claude-*, llama a call_agy()"
    test: |
      python .memory/_scripts/tests/test_aether_router.py --include-claude
```

### 6.2 Fase 2 — Integración (Semana 3-6)

```yaml
# sprint-2-integration.yaml
fase: 2
duracion: "Semana 3-6"
costo_incremental: "+$1.00/semana"

tareas:
  - id: INT-1
    nombre: "Constitutional AI via Rego"
    archivos:
      - policy/agents.rego
      - policy/synthesis.rego
      - .memory/_scripts/lib/aether/judge/__init__.py
    cambios:
      - "agents.rego: +10 reglas CAI (CAI-HARM-001, CAI-TRUTH-001, etc.)"
      - "judge/__init__.py: nuevo método constitutional_review()"
    detalle: |
      Ver analisis-arquitectonico-anthropic-kaos.md sección 2B para reglas completas

  - id: INT-2
    nombre: "Batch API Nocturna"
    archivos:
      - .memory/_scripts/anthropic_batch.py (NUEVO)
      - .memory/_scripts/run_curation.py
    cambios:
      - "anthropic_batch.py: pipeline completo batch"
      - "Programar con Windows Task Scheduler a las 3:00 AM"
    comando: |
      # Instalar scheduler:
      schtasks /create /tn "KAOS-Anthropic-Batch" /tr "python .memory\_scripts\anthropic_batch.py" /sc daily /st 03:00

  - id: INT-3
    nombre: "Extended Thinking para Opus"
    archivos:
      - .memory/_scripts/mcp_agy_bridge.py
    cambios:
      - "Nuevo tool: agy_ask_opus_thinking(PROMPT, budget_tokens=16000, timeout=300)"
      - "Solo para Metis (estrategia) y Kosmos (ADRs críticos)"

  - id: INT-4
    nombre: "Claude en QualityStore + EtherJudge"
    archivos:
      - .memory/_scripts/lib/aether/quality_store.py
      - .memory/_scripts/lib/aether/judge/__init__.py
    cambios:
      - "QualityStore: thresholds y sampling para modelos Claude"
      - "EtherJudge: nueva dimensión 'reasoning_depth' (weight 0.15)"
      - "Sampling: Sonnet 15%, Opus 20%, Haiku 5%"

  - id: INT-5
    nombre: "Haiku 4.5 en pipeline Mnemosyne"
    archivos:
      - .memory/_scripts/mcp_txtai.py
    cambios:
      - "Clasificación de documentos con Haiku 4.5"
      - "Routing: SIMPLE→go-mimo, STANDARD→Sonnet, COMPLEX→Opus"
```

### 6.3 Fase 3 — Transformación (Semana 7-12)

```yaml
# sprint-3-transformation.yaml
fase: 3
duracion: "Semana 7-12"
costo_incremental: "+$0.20/semana"

tareas:
  - id: TRF-1
    nombre: "Unificar Tool Use bajo MCP"
    archivos:
      - .memory/_scripts/lib/aether/client.py
      - .memory/_scripts/lib/llm.py
    cambios:
      - "chat_with_tools(): MCP como capa universal de tool calling"
      - "Claude usa tool use nativo (JSON schema)"
      - "DeepSeek/Kimi usan function calling"
      - "MCP unifica ambos"

  - id: TRF-2
    nombre: "Dashboard de Interpretabilidad"
    archivos:
      - .vault/reports/interpretability-dashboard.html (NUEVO)
    cambios:
      - "Inspirado en SAEs de Anthropic (34M features)"
      - "Monitoreo de características internas de agentes"
      - "Calidad predictiva vs reactiva"

  - id: TRF-3
    nombre: "Hermes: Agente de Gobernanza CAI"
    archivos:
      - .memory/_scripts/mcp_hermes.py (NUEVO)
    cambios:
      - "Nuevo agente que audita decisiones contra principios CAI"
      - "Inspirado en CAI pipeline de Anthropic (RLAIF 88% vs RLHF 76%)"
      - "Reglas Rego + EtherJudge + auto-crítica"

  - id: TRF-4
    nombre: "Integración Claude Code externo"
    archivos:
      - .agents/scripts/claude-code-wrapper.ps1 (NUEVO)
    cambios:
      - "Wrapper que sincroniza workspace y ejecuta claude"
      - "CLAUDE.md generado desde opencode.json"
      - "Solo para refactors complejos (bajo demanda)"
```

### 6.4 Configuraciones Recomendadas

#### Variables de Entorno

```bash
# .env — Anthropic/Claude
ANTHROPIC_API_KEY=sk-ant-...
ANTHROPIC_DIRECT_URL=https://api.anthropic.com/v1
ANTHROPIC_BEDROCK_URL=  # Opcional: AWS Bedrock endpoint

# Cost caps
CLAUDE_HAIKU_WEEKLY_BUDGET=0.20
CLAUDE_SONNET_WEEKLY_BUDGET=0.50
CLAUDE_OPUS_WEEKLY_BUDGET=0.30

# Proveedores alternativos (opcional)
OPENROUTER_API_KEY=sk-or-...
IZZI_API_KEY=...
AICHEAP_API_KEY=...

# Feature flags
ETHER_CLAUDE_ENABLED=true
ETHER_CLAUDE_PROMPT_CACHE=true
ETHER_CLAUDE_BATCH_ENABLED=true
ETHER_CLAUDE_EXTENDED_THINKING=true
ETHER_CLAUDE_HAIKU_CLASSIFICATION=true
```

#### CLAUDE.md para Claude Code (cuando se use)

```markdown
# CLAUDE.md — Proyecto KAOS
## Stack
- Python 3.12+ (backend/scripts)
- TypeScript 5.7+ (workspace UI)
- PowerShell 5.1 (tooling)
- OpenCode (agentes)
- MCP (conectividad)

## Comandos
- `py -3 .tools\session_runner.py smoke` → Smoke tests
- `py -3 .tools\score_engine.py test` → Score engine
- `py -3 .memory\_scripts\aether_serve.py` → Start Aether

## Reglas
1. NO modificar .memory/raw/ (investigaciones inmutables)
2. NO modificar .memory/schema/ ADRs sin aprobación
3. Usar `--dry-run` antes de cambios destructivos
4. Respetar cost_caps: Opus $0.30/semana, Sonnet $0.50/semana

## MCP Config
- Puerto: 3100
- Servidores: kaos-anthropic-bridge, kaos-aether-router, github, memory
```

### 6.5 Repos Clave a Clonar/Referenciar

| Repo | Propósito | Prioridad |
|------|-----------|-----------|
| [open-code/open-code](https://github.com/open-code/open-code) | Cliente default (ya integrado) | Alta |
| [cline/cline](https://github.com/cline/cline) | Alternativa MCP-native (62K⭐) | Baja |
| [nodnarbnitram/claude-code-extensions](https://github.com/nodnarbnitram/claude-code-extensions) | 60+ agents, 15 skills | Media |
| [claude-router](https://github.com/topics/claude-router) | Routing Haiku→Sonnet→Opus | Media |
| [modelcontextprotocol/servers](https://github.com/modelcontextprotocol/servers) | MCP servers oficiales | Alta |
| [composio/composio](https://github.com/composio/composio) | 250+ plataformas MCP | Media |

### 6.6 Integración CI/CD

```yaml
# .github/workflows/anthropic-quality-check.yml
name: Anthropic Quality Check
on:
  schedule:
    - cron: '0 6 * * 1'  # Every Monday 6 AM
  workflow_dispatch:

jobs:
  evaluate:
    runs-on: windows-latest
    steps:
      - uses: actions/checkout@v4
      - name: Run A/B test comparison
        run: |
          python .memory/_scripts/tests/test_ab_comparison.py --models claude-sonnet,go-pro --task-types adr,analyze --samples 10
      - name: Check quality scores
        run: |
          python .memory/_scripts/lib/aether/cli.py status --json > quality-report.json
      - name: Alert if degradation
        run: |
          python .tools/check_quality_degradation.py --baseline .vault/quality/last-run.json --current quality-report.json
      - name: Archive results
        uses: actions/upload-artifact@v4
        with:
          name: anthropic-quality-report
          path: quality-report.json
```

---

## 7. Decisiones Arquitectónicas Clave

- **ADR-ANTH-001**: Claude es **tier premium**, no backbone — DeepSeek V4 Flash mantiene ~70% del tráfico por su relación costo-beneficio 357x superior.
- **ADR-ANTH-002**: La integración usa **Aether v3 existente** (no se crea nuevo router) — el router actual tiene 10 etapas de resolución, Circuit Breaker, QualityStore, y AB testing.
- **ADR-ANTH-003**: **Prompt Caching** es la prioridad #1 — 90% descuento en reads, 68.5% ahorro estimado en llamadas Claude, implementación en 3-5 días.
- **ADR-ANTH-004**: **Constitutional AI via Rego** tiene $0 costo runtime y alto impacto — traducir los 72 principios CAI de Anthropic a reglas Rego no requiere nuevas APIs.
- **ADR-ANTH-005**: **Haiku 4.5** se usa exclusivamente para clasificación del pipeline — su precisión 92%+ justifica el costo incremental ($0.20/semana).
- **ADR-ANTH-006**: **Batch API nocturna** procesa ~1,000 documentos por $1.91/noche — solo el 20% va a Claude (80% a MiMo $0.000014/1K).
- **ADR-ANTH-007**: **No crear nuevos MCPs Anthropic** — agy-bridge ya expone Sonnet/Opus. Solo agregar Haiku y Extended Thinking como tools nuevas.
- **ADR-ANTH-008**: **Claude Code es externo y bajo demanda** — no reemplaza a OpenCode. Se invoca mediante wrapper que sincroniza workspace.

---

## 8. Métricas de Salud

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                      MÉTRICAS DE SALUD DEL SISTEMA                           │
│                                                                              │
│  ┌──────────────────────────────────────┬──────────┬──────────────────────┐ │
│  │ Métrica                              │ Target   │ Tracking              │ │
│  ├──────────────────────────────────────┼──────────┼──────────────────────┤ │
│  │ Cache hit rate (Prompt Caching)       │ ≥60%    │ EtherTracker         │ │
│  │ Costo semanal Claude                  │ ≤$1.00  │ EtherTracker         │ │
│  │ % tráfico en Claude                   │ 3-5%    │ Aether routing stats │ │
│  │ Calidad Sonnet vs DeepSeek (score)    │ +1.5 pt │ QualityStore         │ │
│  │ Haiku precisión clasificación         │ ≥92%    │ Pipeline logs        │ │
│  │ Latencia promedio Claude              │ <15s    │ EtherTracker         │ │
│  │ Circuit Breaker opens/semana          │ <3      │ Circuit Breaker      │ │
│  │ AB tests significativos               │ ≥2/sem  │ ABTest framework     │ │
│  │ Costo mensual total                   │ ≤$62    │ EtherTracker         │ │
│  │ Routing óptimo (modelo correcto)      │ ≥85%    │ QualityStore review  │ │
│  └──────────────────────────────────────┴──────────┴──────────────────────┘ │
│                                                                              │
│  HEALTH SCORE ESTIMADO: 72/100                                               │
│  (Baseline sin Claude: 65/100. Mejora esperada: +7 puntos por integración)  │
└─────────────────────────────────────────────────────────────────────────────┘
```

---

## 9. Recomendaciones

### Acciones Inmediatas (Día 1)
1. **Implementar Prompt Caching** en `mcp_agy_bridge.py` y `lib/agy_client.py` — 68.5% ahorro, 3-5 días de esfuerzo. Costo: $0. Beneficio: $0.50/semana ahorrados.
2. **Agregar Haiku 4.5** como tool `agy_ask_haiku` — 30 minutos, $0. Costo: $0.20/semana. Beneficio: clasificación pipeline 2-3x más rápida.
3. **Configurar Aether** con Claude tiers en `aether.yaml` — 2 horas. Costo: $0. Beneficio: routing óptimo inmediato.

### Acciones a Corto Plazo (Semana 2-3)
4. **Implementar Constitutional AI en Rego** — 10 reglas CAI en `policy/agents.rego`. Costo: $0 runtime. Beneficio: alineamiento sin costo adicional.
5. **Activar AB Testing** para Sonnet vs DeepSeek en tareas de ADR. 50 muestras. Costo: $0.25. Beneficio: datos para decisiones de routing.

### Acciones a Medio Plazo (Semana 4-8)
6. **Implementar Batch API nocturna** — `anthropic_batch.py`, scheduler. Costo: $0. Beneficio: $1.91/noche procesa 1,000 documentos.
7. **Extended Thinking para Metis** — solo tareas estratégicas, budget 16K tokens. Costo: $0.30/semana. Beneficio: +10-15% veracidad.

### Acciones a Largo Plazo (Semana 8+)
8. **Unificar Tool Use bajo MCP** — chat_with_tools() universal. Costo: $0.20/semana. Beneficio: tool calling homogéneo.
9. **Hermes: Agente de Gobernanza CAI** — auditoría automática de decisiones. Costo: $0.50/semana. Beneficio: governance multi-agente.

---

## 10. Anti-recomendaciones

1. ❌ **No hacer de Claude el backbone** — costaría 50x más por solo +15-25% de calidad general.
2. ❌ **No migrar a CLAUDE.md** — KAOS tiene SOUL.md, SKILL.md, opencode.json como estándares consolidados.
3. ❌ **No crear nuevos MCPs Anthropic** — agy-bridge ya expone Claude; 25+ MCPs ya existen; duplicar aumentaría complejidad.
4. ❌ **No reemplazar QualityStore/EtherJudge** — el sistema de calidad de KAOS (6 dimensiones, rúbricas por tarea) es más completo que alternativas externas.
5. ❌ **No usar Claude para tareas rutinarias** — código boilerplate, búsquedas web, wikilinks, consultas rápidas son 357x más baratas con MiMo o DeepSeek Flash.
6. ❌ **No subscribirse a Claude Pro/Enterprise** — el modelo API-by-usage con cost_caps estrictos da mejor relación costo-beneficio que suscripciones fijas.

---

## Apéndice A: Matriz de Costos Detallada

| Proveedor | Haiku Input | Sonnet Input | Opus Input | Notas |
|-----------|-------------|--------------|------------|-------|
| Anthropic Direct | $1.00/M | $3.00/M | $5.00/M | Línea base |
| Anthropic + Cache | $0.10/M | $0.30/M | $0.50/M | 90% descuento |
| Anthropic Batch | $0.50/M | $1.50/M | $2.50/M | 50% descuento |
| AWS Bedrock | $1.10/M | $3.30/M | $5.50/M | +10% regional |
| GCP Vertex AI | $1.10/M | $3.30/M | $5.50/M | +10% premium |
| OpenRouter | $1.06/M | $3.17/M | $5.28/M | ~5.5% markup |
| Izzi API | $0.90/M | $2.70/M | $4.50/M | Créditos gratis sin TC |
| AIcheap.io | $0.80/M | $2.40/M | $4.00/M | $4.99/mes subscripción |
| ClaudeAPI.cheap | — | — | — | $19 lifetime (limitado) |

## Apéndice B: Mapeo de Modelos Actualizados

| Clave Aether | Provider | Modelo Real | Input/1K | Output/1K | Cache/1K |
|-------------|----------|-------------|----------|-----------|----------|
| claude-haiku | agy-bridge | claude-4-5-haiku | $0.0010 | $0.0050 | $0.00010 |
| claude-sonnet | agy-bridge | claude-4-6-sonnet | $0.0030 | $0.0150 | $0.00030 |
| claude-opus | agy-bridge | claude-4-8-opus | $0.0050 | $0.0250 | $0.00050 |
| go-flash | OpenCode Go | deepseek-v4-flash | $0.00014 | $0.00028 | $0.000028 |
| go-pro | OpenCode Go | deepseek-v4-pro | $0.00174 | $0.00348 | $0.000145 |
| go-kimi-latest | OpenCode Go | kimi-k2.6 | $0.00095 | $0.00400 | $0.00016 |
| go-mimo | OpenCode Go | mimo-v2-pro | $0.000014 | $0.000028 | $0.0000028 |

## Apéndice C: Fuentes

1. Dossier Anthropic: `.memory/raw/dossier-anthropic-kaos.md` (507 líneas)
2. Análisis Arquitectónico: `.memory/raw/analisis-arquitectonico-anthropic-kaos.md` (218 líneas)
3. Estrategia Anthropic: `.memory/raw/estrategia-anthropic-kaos.md` (160 líneas)
4. Investigación Gaps: `.memory/raw/investigacion-anthropic-gaps.md` (458 líneas)
5. Catálogo Modelos AI: `ai-models-catalog.md` (1350 líneas, sección Anthropic líneas 167-298)
6. Aether Routing v3: `.memory/wiki/concepts/aether-routing-v3.md` (219 líneas)
7. Multi-Model Router: `docs/architecture/multi-model-router.md` (141 líneas)
8. KosmosV2 Integración: `.vault/reports/kosmos-v2-integracion-global.md` (372 líneas)
9. Código agy-bridge: `.memory/_scripts/mcp_agy_bridge.py` (179 líneas)
10. Config Aether: `.memory/_scripts/aether.yaml` (106 líneas)
