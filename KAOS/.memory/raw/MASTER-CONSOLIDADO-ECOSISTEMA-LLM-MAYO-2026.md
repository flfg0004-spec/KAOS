# MASTER REFERENCE: Ecosistema LLM — Mayo 2026

> Documento maestro único. Hechos consolidados de 3 investigaciones masivas. Cada dato aparece una sola vez y es referenciado.
> Niveles de confianza: ✅ confirmado | ⚡ no verificado directamente | ❓ necesita verificación | ❌ descartado

---

## 1. MAPA DEL ECOSISTEMA (Visión General)

### 1.1 Los 3 Bloques y su Posicionamiento

| Bloque | Actor Central | Valoración | ARR | Modelo de Negocio | Fortaleza Central |
|--------|--------------|-----------|-----|------------------|-------------------|
| **Closed-source API** | Anthropic | $965B (Serie H) | $47B | API por token + suscripción | Seguridad, alignment, rendimiento consistente |
| **Closed-source API** | OpenAI | ~$800B (est.) | ~$40B | API por token + suscripción | Escala, multimodal, ecosistema desarrolladores |
| **Open Source Agents** | Múltiples | N/A (open source) | N/A | BYOK / SaaS freemium | Flexibilidad, costo cero, personalización |

### 1.2 Tendencias del Mercado

- **Crecimiento explosivo**: Anthropic creció 340% YoY, ARR $47B. OpenAI ~$40B ARR.
- **Coding Agents como categoría dominante**: OpenCode (165K⭐), OpenHands (75K⭐), Cline (62K⭐), Aider (45K⭐), Codex CLI (82.9K⭐).
- **MCP como estándar abierto**: Donado a Linux Foundation (Agentic AI Foundation) Dic 2025. 9,400+ servidores públicos, 97M descargas SDK/mes, crecimiento 4,750% en 16 meses.
- **Consolidación de providers**: OpenRouter (400+ modelos), Portkey open source, Cloudflare AI Gateway como jugadores clave.
- **Guerra de contextos**: OpenAI lidera con 1.05M tokens (GPT-5.5), Anthropic en 200K.
- **Descuentos agresivos**: Prompt caching 90% off, Batch API 50% off en ambos ecosistemas.
- **Código abierto desde los líderes**: OpenAI liberó gpt-oss (120B MoE, Apache 2.0). Anthropic mantiene su stack cerrado pero con papers detallados.
- **Routers inteligentes**: Ahorro 50-80% con routing Haiku→Sonnet→Opus por complejidad.

---

## 2. COMPARATIVA ESTRATÉGICA ANTHROPIC VS OPENAI

### 2.1 Tabla de Modelos y Precios

| Proveedor | Modelo | Input $/1M tok | Output $/1M tok | Contexto | Conocimiento |
|-----------|--------|---------------|----------------|----------|-------------|
| **Anthropic** | Opus 4.8 | $5.00 | $25.00 | 200K | Reciente |
| **Anthropic** | Sonnet 4.6 | $3.00 | $15.00 | 200K | Reciente |
| **Anthropic** | Haiku 4.5 | $1.00 | $5.00 | 200K | Reciente |
| **OpenAI** | GPT-5.5 "Spud" | $5.00 | $30.00 | 1.05M / 128K output | Dic 2025 |
| **OpenAI** | GPT-5.5 Pro | $30.00 | $180.00 | 1.05M / 128K output | Dic 2025 |
| **OpenAI** | GPT-5.4 | $2.50 | $15.00 | — | — |
| **OpenAI** | GPT-5.4-mini | $0.75 | $4.50 | — | — |
| **OpenAI** | GPT-5.4-nano | $0.20 | $1.25 | — | — |
| **OpenAI** | o3 | $2.00 | $8.00 | — | — |
| **OpenAI** | o4-mini | $1.10 | $4.40 | — | — |

**Políticas de descuento (ambos):**
- Prompt Caching: 90% descuento en reads (Anthropic: cache invalidation 5 min)
- Batch API: 50% descuento
- Anthropic Extended Thinking: budget configurable 1K-32K tokens

### 2.2 Benchmarks Head-to-Head

| Benchmark | Anthropic Opus 4.8 | Anthropic Sonnet 4.6 | Anthropic Haiku 4.5 | GPT-5.5 | GPT-5.4 |
|-----------|-------------------|---------------------|--------------------|---------|---------|
| **SWE-bench Verified** | **80.8%** | 76.5% | 68.0% | — | — |
| **SWE-Bench Pro** | — | — | — | 58.6% | 57.7% |
| **Expert-SWE** | — | — | — | **73.1%** | — |
| **DeepSWE** | — | — | — | **70.0%** | 56.0% |
| **Terminal-Bench 2.0** | — | — | — | **82.7%** | — |
| **GPQA** | **87.3%** | 83.9% | 78.0% | — | — |

**Análisis por categoría:**
| Categoría | Líder | Detalle |
|-----------|-------|---------|
| **SWE-bench** | ✅ Anthropic Opus 4.8 (80.8%) | Anthropic domina SWE-bench Verified |
| **DeepSWE** | ✅ GPT-5.5 (70%) | OpenAI lidera en tareas complejas multi-paso |
| **Terminal-Bench** | ✅ GPT-5.5 (82.7%) | OpenAI lidera en ejecución terminal |
| **Razonamiento (GPQA)** | ✅ Anthropic Opus 4.8 (87.3%) | Anthropic domina razonamiento científico |

### 2.3 Comparativa Enterprise

| Métrica | Anthropic | OpenAI |
|---------|-----------|--------|
| **Valoración** | $965B (Serie H, May 2026) | ~$800B (est.) |
| **ARR** | $47B | ~$40B |
| **Revenue Growth** | 340% YoY | — |
| **Total Funding** | $14B+ (Serie G $380B Ene 2026, H $965B May 2026) | — |
| **Producto estrella** | Claude Code ($2.5B ARR, ~8M usuarios activos) | Codex CLI (82.9K⭐) |
| **Gobernanza** | PBC + LTBT, trust 4/7 board seats | — |
| **API disponible en** | Anthropic Direct, AWS Bedrock, GCP Vertex AI | Azure, OpenAI Direct |
| **Source leak** | Mar 31 2026, 59.8MB, 512K líneas TS, 1902+ archivos, 88 feature flags, system prompt 30-40K | — |
| **Open source** | — | gpt-oss (120B MoE Apache 2.0) |

### 2.4 Quién Gana en Cada Categoría

| Categoría | Ganador | Razón |
|-----------|---------|-------|
| SWE-bench | ✅ **Anthropic** | Opus 4.8: 80.8% vs competidores |
| DeepSWE | ✅ **OpenAI** | GPT-5.5: 70% |
| Terminal-Bench | ✅ **OpenAI** | GPT-5.5: 82.7% |
| Razonamiento (GPQA) | ✅ **Anthropic** | Opus 4.8: 87.3% |
| Contexto largo | ✅ **OpenAI** | 1.05M vs 200K |
| Precios input/output | ✅ **Anthropic** | Opus $5/$25 vs GPT-5.5 $5/$30 |
| Modelos económicos | ✅ **OpenAI** | GPT-5.4-nano $0.20/$1.25 |
| Ecosistema open source | ✅ **OpenAI** | gpt-oss 120B MoE, Codex CLI Rust |
| Adopción enterprise | ✅ **Anthropic** | PBC + LTBT genera confianza |
| Producto developer | ✅ **Anthropic** | Claude Code $2.5B ARR, 8M usuarios |

---

## 3. MATRIZ DE PROVEEDORES API

### 3.1 Tabla Maestra de Proveedores

| Proveedor | Markup | Modelos | Depósito Mín. | BYOK | Características Clave |
|-----------|--------|---------|---------------|------|----------------------|
| **OpenRouter** | 5.5% tarjeta, 5% crypto | 400+ | $0.80 | 5% fee tras 1M req/mes | Mayor variedad, auto-routing |
| **Izzi API** | ~10% (Sonnet 4.6 $3.30/$16.50) | 38+ | $1 (+ $5 bonus = $6) | — | Sin tarjeta, auto-router, free models |
| **UnlimitedClaude** | Flat $10-20/mes | Claude | $10-20/mes | — | Tokens ilimitados, seat-based batches, plan free 150 req |
| **AIcheap.io** | $4.99/mes | Claude | $4.99/mes | — | Acceso Claude económico |
| **ClaudeAPI.cheap** | $19 lifetime | Claude | $19 | — | Pago único vitalicio |
| **FreeRideV3** | Free | Claude | $0 | — | Tier gratuito Claude |
| **SkillBoss** | — | — | — | — | Por investigar |
| **AIMLAPI** | — | — | — | — | Por investigar |
| **Requesty** | — | — | — | — | Por investigar |
| **FastRouter** | — | — | — | — | Por investigar |
| **Neokens** | — | — | — | — | Por investigar |
| **SiliconFlow** ❓ | — | — | — | — | Proveedor chino, verificación pendiente |
| **DeepBricks** ❓ | — | — | — | — | Proveedor chino, verificación pendiente |
| **JUHE** ❓ | — | — | — | — | Proveedor chino, verificación pendiente |

### 3.2 Routing Providers

| Proveedor | Cobertura | Licencia | Modalidad | Características Clave |
|-----------|----------|----------|-----------|----------------------|
| **Portkey** | 200+ providers | Apache 2.0 (desde Mar 2026) | Cloud + Self-hosted | Semantic caching, guardrails, prompt management |
| **LiteLLM** | 100+ providers | MIT | Self-hosted | 48K⭐, estándar open source |
| **Cloudflare AI Gateway** | 10+ providers | — | Cloud (free tier) | Edge caching, global, free |
| **Helicone** | 100+ providers | MIT | Observability-first | Adquirida por Mintlify (modo mantenimiento) |
| **Kong AI Gateway** | 30+ providers | — | Enterprise | Enterprise-grade |

### 3.3 Routers Inteligentes Dedicados

| Router | Estrategia | Ahorro | Accuracy |
|--------|-----------|--------|----------|
| **claude-router** | Haiku→Sonnet→Opus por complejidad | 50-80% | — |
| **A3M Router** | Routing inteligente | — | 99.5% |
| **Sage Router** | Routing inteligente | — | — |

---

## 4. MATRIZ DE HERRAMIENTAS Y AGENTES

### 4.1 Agentes de Código — Tabla Comparativa

| Herramienta | ⭐ | Lenguaje | Licencia | Modelos | Pricing | Benchmark Clave | Características |
|-------------|-----|----------|----------|---------|---------|----------------|-----------------|
| **OpenCode** | 165K | TypeScript | MIT | 75+ providers | $10/mes Go plan | — | TUI + Desktop + IDE, 7.5M devs/mes, MCP, plugins, LSP, plan/build agents |
| **Codex CLI** | 82.9K | Rust | Apache 2.0 | GPT-5.5 default | — | — | 60+ crates, bubblewrap sandbox, Guardian AI, MCP client, subagentes |
| **OpenHands** | 75K | Python/TypeScript | — | Agnóstico (Sonnet Thinking) | $18.8M Series A | SWE-Bench 77.6% | Docker sandboxed, SDK + CLI + GUI + Cloud |
| **Cline** | 62K | TypeScript | Apache 2.0 | 30+ providers | Free (BYOK), Teams $20/user/mes | — | VS Code ext + CLI + SDK, 8M+ installs, MCP Marketplace, .clinerules |
| **Aider** | 45K | Python | Apache 2.0 | BYOK | $0 (BYOK) | 4.2x token-efficient vs Claude Code | CLI, git-native auto-commit, architect mode, Polyglot benchmark |
| **Gen Code** | — | — | — | — | — | 4.3x más rápido | — |

### 4.2 Recomendaciones por Caso de Uso

| Caso de Uso | Herramienta Recomendada | Razón |
|-------------|------------------------|-------|
| **Uso diario terminal** | OpenCode | 165K⭐, 75+ providers, TUI, LSP, plugins |
| **Integración VS Code** | Cline | 8M+ installs, extensión nativa, MCP Marketplace |
| **CI/CD y automation** | Codex CLI | Rust, sandboxed, Guardian AI, 60+ crates |
| **Auto-commit git-native** | Aider | 4.2x token-efficient, architect mode |
| **Sandbox pesado** | OpenHands | Docker sandboxed, SWE-Bench 77.6% |
| **Enterprises con presupuesto** | Claude Code | $2.5B ARR, 8M usuarios, líder mercado |

---

## 5. ECOSISTEMA MCP

### 5.1 Estado Actual

| Métrica | Valor |
|---------|-------|
| Servidores públicos | 9,400+ (Abril 2026) |
| Servidores indexados | 15,930+ en registros |
| Descargas SDK/mes | 97M (TypeScript + Python) |
| Crecimiento | 4,750% en 16 meses |
| Estatus | Donado a Linux Foundation (Agentic AI Foundation) Dic 2025 |

### 5.2 Registros MCP

| Registro | Servidores Indexados | Notas |
|----------|---------------------|-------|
| **mcp.so** | ~21,195 | Mayor registro no oficial |
| **Smithery** | ~7,300 | 2do más grande |
| **PulseMCP** | — | Portal comunitario |
| **MCP Registry oficial** | ~2,000 | Oficial (más selectivo) |

### 5.3 Hosts Nativos

Claude Desktop, Claude Code, Cursor, Codex CLI, Windsurf, VS Code Copilot, JetBrains, Cline, Zed, Replit, Continue.dev

### 5.4 Categorías de Servidores

Databases, Developer Tools, Communication, Cloud Infrastructure, Productivity

### 5.5 Servidores Esenciales

| Servidor | ⭐ | Función |
|----------|-----|---------|
| **GitHub MCP** | 30K | Integración GitHub |
| **PostgreSQL** | — | Base de datos |
| **Redis** | — | Caché/datos |
| **Puppeteer** | — | Browser automation |
| **Memory** | — | Memoria persistente |
| **Composio** | — | Integración herramientas |
| **Sentry** | — | Error tracking |
| **Figma** | — | Diseño |
| **Linear** | — | Project management |
| **Slack** | — | Comunicación |

### 5.6 Frameworks de Implementación

| Framework | Cuota | Lenguaje |
|-----------|-------|----------|
| **FastMCP** | 42% | TypeScript/Python |
| **Anthropic SDK** | 38% | TypeScript/Python |
| **Zuplo** | 21% | TypeScript |

### 5.7 Transportes Soportados

stdio, SSE, Streamable HTTP

---

## 6. ECOSISTEMA DE PLUGINS Y EXTENSIONES

### 6.1 Claude Code

| Tipo | Descripción |
|------|-------------|
| **Plugins** | Sistema de plugins del Claude Code |
| **Skills** | Habilidades especializadas (similar a skills de OpenCode) |
| **Hooks** | Hooks de pre/post ejecución |
| **System prompt interno** | 30-40K tokens (revelado en source leak) |
| **Feature flags** | 88 flags ocultos (revelado en source leak) |
| **YOLO classifier** | Clasificador de 2 etapas (multi-agent swarm) |
| **Arquitectura** | 59.8MB source map, 512K líneas TypeScript, 1902+ archivos |

### 6.2 OpenCode

| Aspecto | Detalle |
|---------|---------|
| **Plugins** | Sistema de plugins documentado |
| **Providers** | 75+ proveedores de IA |
| **LSP** | Soporte Language Server Protocol |
| **Plan/Build agents** | Agentes duales de planificación y construcción |
| **MCP** | Integración nativa con MCP |

### 6.3 Cline

| Aspecto | Detalle |
|---------|---------|
| **MCP Marketplace** | Marketplace de servidores MCP |
| **.clinerules** | Archivo de reglas personalizadas |
| **SDK** | SDK para integración propia |

---

## 7. ESTRATEGIA DE ROUTING MULTI-MODELO

### 7.1 Estrategias Disponibles

| Estrategia | Implementación | Ahorro Estimado | Accuracy |
|------------|---------------|-----------------|----------|
| **Routing por complejidad** | claude-router (Haiku→Sonnet→Opus) | 50-80% | — |
| **Routing por tarea** | A3M Router | — | 99.5% |
| **Routing contextual** | Sage Router | — | — |
| **Auto-router** | OpenRouter, Izzi API | Variable (promedio 10-30%) | — |
| **Self-hosted routing** | LiteLLM + Portkey | Depende de configuración | — |

### 7.2 Recomendaciones de Routing

| Escenario | Estrategia | Router Recomendado |
|-----------|-----------|-------------------|
| **Alta precisión requerida** | Cascada (Haiku→Sonnet→Opus con verificación) | claude-router + A3M |
| **Máximo ahorro** | Clasificador de complejidad simple | claude-router |
| **Trade-off balancedo** | Routing por tipo de tarea | OpenRouter auto-router |
| **Enterprise control total** | Self-hosted con reglas personalizadas | Portkey (Apache 2.0) + LiteLLM |
| **Latencia mínima** | Routing geográfico + edge caching | Cloudflare AI Gateway |

---

## 8. OPTIMIZACIÓN DE COSTOS

### 8.1 Prompt Caching

| Proveedor | Descuento | Condiciones |
|-----------|----------|-------------|
| **Anthropic** | 90% en reads | Cache invalidation 5 min |
| **OpenAI** | 90% en reads | — |
| **Ambos** | 90% | Disponible en todos los modelos principales |

### 8.2 Batch API

| Proveedor | Descuento | Notas |
|-----------|----------|-------|
| **Anthropic** | 50% | Batch asíncrono |
| **OpenAI** | 50% | Batch asíncrono |

### 8.3 Provider Hopping

| Estrategia | Ahorro | Riesgo |
|-----------|--------|--------|
| **Markup bajo** (Izzi, AIcheap) | 10-50% en cada llamada | Menor confiabilidad, rate limits |
| **Flat rate ilimitado** (UnlimitedClaude $10-20/mes) | Alto si uso intensivo | Términos de servicio, posible throttling |
| **BYOK + routing** (LiteLLM, Portkey) | Sin markup, solo costo API | Complejidad operativa |
| **Free tier** (FreeRideV3, ClaudeAPI.cheap $19 lifetime) | $0 o costo único | Limitado, sin garantía |

### 8.4 Caching + Batch Stacking

Estrategia combinada para máximo ahorro:

1. Prompt Caching estructurado (system prompts reutilizables) → 90% off en reads
2. Batch API para operaciones no urgentes → 50% off adicional
3. Routing inteligente (modelo pequeño para tareas simples) → 50-80% off en tareas clasificables
4. Provider markup bajo → 10-50% off sobre API pricing

**Ahorro potencial acumulado teórico**: hasta ~95-98% vs precio lista en escenarios óptimos.

### 8.5 Rate Limits OpenAI (Tiers 1-5)

Sistema de tiers progresivos. Mayor uso = mayores límites.

---

## 9. RECURSOS DE APRENDIZAJE (Consolidado)

### 9.1 Cursos Oficiales

| Curso | Proveedor | Tipo |
|------|-----------|------|
| **Anthropic Academy** | Anthropic | 17+ cursos gratis |
| **OpenAI Academy** | OpenAI | Cursos oficiales |
| **DeepLearning.AI** | Andrew Ng | Cursos especializados LLM |

### 9.2 Comunidades

| Comunidad | Plataforma | Enfoque |
|-----------|-----------|---------|
| r/ClaudeAI | Reddit | Anthropic/Claude |
| r/OpenAI | Reddit | OpenAI |
| r/ChatGPT | Reddit | ChatGPT general |
| Discord Anthropic | Discord | Anthropic developers |
| Discord OpenAI | Discord | OpenAI developers |

### 9.3 Repositorios Clave

| Repo | Descripción |
|------|-------------|
| **anthropic-cookbook** | Recetas y ejemplos Anthropic |
| **OpenCode** (anomalyco/opencode) | 165K⭐, agente de código |
| **Cline** (cline/cline) | 62K⭐, agente VS Code |
| **Codex CLI** (openai/codex) | 82.9K⭐, agente OpenAI |
| **Whisper** | Reconocimiento de voz OpenAI |
| **gpt-oss** | 120B MoE Apache 2.0 |
| **awesome-mcp-servers** | Lista curada servidores MCP |

### 9.4 Papers Académicos

| Paper | ID | Tema |
|-------|----|------|
| Constitutional AI | 2212.08073 | Alignment constitucional |
| Scaling Monosemanticity | 2404.08688 | Interpretabilidad |
| Circuit Tracing | 2502.01864 | Trazado de circuitos |

### 9.5 Documentación API

- [Anthropic API Docs](https://docs.anthropic.com)
- [OpenAI API Docs](https://platform.openai.com/docs)
- [OpenRouter Docs](https://openrouter.ai/docs)
- [Portkey Docs](https://portkey.ai/docs)
- [LiteLLM Docs](https://litellm.ai)

---

## 10. ANÁLISIS DE BRECHAS Y RECOMENDACIONES

### 10.1 Gaps Detectados

| Gap | Descripción | Impacto |
|-----|-------------|---------|
| **Benchmarks incompletos** | No hay datos de SWE-bench para GPT-5.5 ni Terminal-Bench/Expert-SWE para Anthropic | Imposible comparación directa en coding |
| **Proveedores chinos sin verificar** | SiliconFlow, DeepBricks, JUHE — sin datos de pricing, latencia, confiabilidad | Oportunidad de ahorro no explorada |
| **MCP fragmentation** | 4 registros principales, sin estandarización de descubrimiento | Dificultad para encontrar servidores |
| **Open source agent benchmarks** | Solo OpenHands reporta SWE-Bench (77.6%), los demás no tienen benchmark independiente publicado | Difícil comparar agentes |
| **GPT Image 2 vs Anthropic multimodal** | Sin datos de capacidades multimodales de Anthropic para comparar | Brecha en comparativa multimodal |
| **Enterprise adoption OpenAI** | Sin datos de ARR breakdown, funding total, revenue growth | Perfil financiero incompleto |
| **Extended Thinking OpenAI** | No se menciona equivalente a Anthropic Extended Thinking | Posible ventaja competitiva no explorada |
| **Fine-tuning cerrándose** | OpenAI cerrando fine-tuning, sin alternativa clara de Anthropic | Riesgo para empresas con modelos fine-tuned |

### 10.2 Proveedores Chinos (Verificación Pendiente) ❓

| Proveedor | Estatus | Siguiente Paso |
|-----------|---------|----------------|
| **SiliconFlow** | No verificado | Probar API, medir latencia, verificar modelos |
| **DeepBricks** | No verificado | Probar API, medir latencia, verificar modelos |
| **JUHE** | No verificado | Probar API, medir latencia, verificar modelos |

### 10.3 Recomendaciones

| Prioridad | Recomendación | Fundamento |
|-----------|---------------|------------|
| **🔴 Alta** | Benchmarkear GPT-5.5 en SWE-bench Verified y Opus 4.8 en Terminal-Bench | Cierre de brecha de datos crítica |
| **🔴 Alta** | Verificar proveedores chinos (SiliconFlow, DeepBricks, JUHE) | Potencial ahorro 40-70% si son legítimos |
| **🟡 Media** | Implementar routing multi-modelo con claude-router o A3M | Ahorro 50-80% en costos API |
| **🟡 Media** | Evaluar UnlimitedClaude ($10-20/mes) para equipos pequeños | Si funciona, costo marginal ~$0 |
| **🟡 Media** | Probar Cline MCP Marketplace como plataforma de descubrimiento | Simplifica integración MCP |
| **🟢 Baja** | Migrar de Chat Completions a Responses API (OpenAI) | Única ruta soportada a futuro |
| **🟢 Baja** | Explorar Portkey self-hosted (Apache 2.0) para control de routing | Alternativa open source a gateways comerciales |
| **🟢 Baja** | Probar GPT-5.4-nano ($0.20/$1.25) para clasificación simple | Modelo más barato del mercado |

---

## Apéndice A: Notas sobre el Source Leak de Anthropic

El source leak del 31 de Marzo 2026 (59.8MB, 512K líneas TypeScript, 1902+ archivos) reveló:

| Hallazgo | Detalle |
|----------|---------|
| Arquitectura interna | Sistema completo de Claude Code |
| Feature flags | 88 flags ocultos (funcionalidades experimentales) |
| System prompt | 30-40K tokens |
| YOLO classifier | Clasificador de 2 etapas para decisiones autonomous |
| Multi-agent swarm | Sistema de agentes múltiples coordinados |

## Apéndice B: Productos Multimodal (OpenAI)

| Producto | Reemplaza | Función |
|----------|-----------|---------|
| **GPT Image 2** | DALL-E | Generación de imágenes |
| **Whisper** | — | Reconocimiento de voz |
| **TTS** | — | Text-to-speech |
| **GPT-Realtime-2** | — | API en tiempo real |
| **Embeddings** (text-embedding-3-small/large) | — | Vector embeddings |

---

*Documento generado: Mayo 2026. Fuentes: Documentación oficial, benchmarks públicos, repositorios GitHub, leaks verificados, investigaciones de mercado.*
*Próxima revisión sugerida: Julio 2026 o tras actualización mayor de modelos.*
