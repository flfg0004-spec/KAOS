# Catálogo Completo de Modelos de IA — Benchmarks, Innovaciones y Detalles Técnicos

> **Fecha:** 24 de mayo de 2026
> **Propósito:** Base de conocimiento para el ruteo inteligente de tareas en KAOS (Knowledge Agent Operating System)
> **Fuentes:** LMSYS Chatbot Arena, Artificial Analysis, HuggingFace Open LLM Leaderboard, SWE-bench, documentación oficial de API, papers técnicos

---

## Resumen Ejecutivo

El panorama de modelos de inteligencia artificial en mayo de 2026 representa un punto de inflexión sin precedentes. La competencia entre laboratorios estadounidenses y chinos ha escalado a niveles nunca vistos, con más de una docena de modelos alcanzando puntuaciones en la LMSYS Arena superiores a 1460 ELO — un umbral que hace apenas 18 meses era territorio exclusivo de los líderes indiscutibles.

**Tendencias clave observadas:**

1. **Razonamiento híbrido como estándar:** Prácticamente todos los modelos frontier lanzados desde finales de 2025 incorporan mecanismos de "thinking" o razonamiento encadenado, ya sea como modo opcional (Claude, Qwen, Gemini) o como arquitectura base (DeepSeek-R1, o3). La diferenciación ya no está en *si* un modelo razona, sino en *cómo* gestiona el costo computacional de ese razonamiento.

2. **Contextos de 1M+ tokens:** El límite de contexto se ha convertido en un campo de batalla principal. Gemini estableció el estándar con 1M desde 2024; para 2026, Claude Opus 4.7, GPT-5.4/5.5, DeepSeek-V4, Qwen3.7-Max, Xiaomi MiMo y MiniMax-01 (este último con 4M) manejan contextos de longitud extrema. Llama 4 Scout ostenta el récord con 10M de contexto.

3. **Revolución en eficiencia (MoE + atención lineal):** La arquitectura Mixture-of-Experts se ha vuelto ubicua, pero la innovación más significativa es la adopción de mecanismos de atención lineal (Lightning Attention, Mamba-2, Delta-Attention) que rompen la barrera cuadrática del transformer clásico. Modelos como Step-3.5-Flash (196B total, 11B activos) demuestran que es posible obtener rendimiento frontier con una fracción de los parámetros activos.

4. **Guerra de precios feroz:** DeepSeek-V4 Flash a $0.0028/M input (promocional) y modelos chinos entre $0.30-$2.50/M han forzado a Anthropic a reducir precios 67% (Opus 4.5) y a OpenAI a mantener GPT-5.5 en $5/$30. El costo por token sigue una pendiente descendente pronunciada.

5. **Ascenso chino imparable:** Por primera vez, modelos chinos (ERNIE 5.1, GLM-5.1, Qwen3.7-Max) aparecen consistentemente en el top 20 de la Arena. GLM-5 de Zhipu, entrenado íntegramente en hardware doméstico Huawei Ascend 910B (100K GPUs, cero NVIDIA), marca un hito geopolítico. Kimi K2.6 logra el #1 en HLE (54.0%), superando a todos los modelos occidentales.

6. **Modelos abiertos de clase mundial:** Meta, Alibaba, DeepSeek, Zhipu, Mistral y NVIDIA publican modelos abiertos (Apache 2.0 o MIT) que compiten directamente con propietarios. DeepSeek-V4 y Qwen3.6 demuestran que el open-source ya no es sinónimo de "inferior".

7. **Especialización aguda:** El mercado se fragmenta en modelos diseñados para código (GPT-5.3 Codex, Codestral, DeepSeek-Coder-V2), matemáticas (Mathstral, DeepSeek-Math, rStar-Math), agentes (GLM-5, Kimi K2.6, Claude), y razonamiento puro (o3, DeepSeek-R1, QwQ-32B).

---

### Tabla Comparativa — Top 20 Modelos (Mayo 2026)

| # | Modelo | Laboratorio | Params | Arquitectura | Contexto | Price $ Input | Price $ Output | Arena ELO | SWE-bench | GPQA | MMLU-Pro | HLE | Licencia |
|---|--------|------------|--------|-------------|----------|--------------|---------------|-----------|-----------|------|----------|-----|----------|
| 1 | Claude Opus 4.6 Thinking | Anthropic | ~2T (est.) | Transformer + Thinking Adaptativo | 1M | $5 | $25 | 1502 | 80.8% | 91.3% | — | — | Proprietaria |
| 2 | Claude Opus 4.7 Thinking | Anthropic | ~2T (est.) | Transformer + Tokenizer nuevo | 1M | $5 | $25 | 1501 | 87.6% | 94.2% | — | — | Proprietaria |
| 3 | Claude Opus 4.6 | Anthropic | ~2T (est.) | Transformer | 1M | $5 | $25 | 1498 | 80.8% | — | — | — | Proprietaria |
| 4 | Claude Opus 4.7 | Anthropic | ~2T (est.) | Transformer + Tokenizer nuevo | 1M | $5 | $25 | 1492 | 87.6% | 94.2% | — | — | Proprietaria |
| 5 | Muse Spark | Meta | — | MoE (rumoreado) | — | $0.95 | $3.80 | 1491 | — | — | — | — | Abierta |
| 6 | Gemini 3.1 Pro Preview | Google | MoE | MoE + MCP Atlas | 1-2M | $2 | $12 | 1490 | 80.6% | 94.3% | — | 51.4% | Proprietaria |
| 7 | Gemini 3 Pro | Google | MoE | MoE + Deep Think | 1M | $2 | $12 | 1486 | 76.2% | 91.9% | — | 37.5% | Proprietaria |
| 8 | GPT-5.5 High | OpenAI | — | Omnimodal Router | 1M | $5 | $30 | 1484 | 88.7% | — | — | — | Proprietaria |
| 9 | Grok 4.20 Beta1 | xAI | — | Transformer | 256K | $5 | $15 | 1479 | — | 88% | — | 24.5% | Proprietaria |
| 10 | GPT-5.4 High | OpenAI | — | Transformer + Computer Use | 1M | $2.50 | $15 | 1479 | ~80% | — | — | — | Proprietaria |
| 11 | GPT-5.2 Chat | OpenAI | — | Transformer + 5 Reasoning Levels | 400K | $1.75 | $14 | 1477 | 80% | 92.4% | — | — | Proprietaria |
| 12 | Grok 4.20 Beta Reasoning | xAI | — | Transformer + Reasoning | 256K | $5 | $15 | 1477 | — | — | — | — | Proprietaria |
| 13 | GPT-5.5 | OpenAI | — | Omnimodal | 1M | $5 | $30 | 1476 | 88.7% | — | — | — | Proprietaria |
| 14 | Grok 4.20 Multi-Agent | xAI | — | Multi-Agent Ensemble | 256K | $5 | $15 | 1474 | — | — | — | — | Proprietaria |
| 15 | Gemini 3 Flash | Google | MoE | MoE Flash | 1M | $0.50 | $3 | 1474 | 78% | 90.4% | 81.2% | — | Proprietaria |
| 16 | ERNIE 5.1 | Baidu | ~800B | MoE Once-for-All | 128K | $0.59 | $2.65 | 1473 | — | — | — | — | Proprietaria |
| 17 | Claude Opus 4.5 Thinking 32K | Anthropic | — | Transformer | 200K | $5 | $25 | 1473 | ~77-80% | — | — | — | Proprietaria |
| 18 | GPT-5.5 Instant | OpenAI | — | Omnimodal (rápido) | 1M | — | — | 1472 | — | — | — | — | Proprietaria |
| 19 | GLM-5.1 | Zhipu AI | 744B (40B act.) | MoE+DSA+MLA | 203K | — | — | 1471 | 77.8% | 86.2% | — | — | MIT |
| 20 | Claude Opus 4.5 | Anthropic | — | Transformer | 200K | $5 | $25 | 1468 | ~77-80% | — | — | — | Proprietaria |
| — | Grok 4.1 Thinking | xAI | — | Transformer | — | — | — | 1467 | — | — | — | — | Proprietaria |
| — | Claude Sonnet 4.6 | Anthropic | — | Transformer + Thinking | 1M | $3 | $15 | 1467 | 79.6% | 89.9% | — | — | Proprietaria |
| — | GPT-5.4 | OpenAI | — | Transformer | 1M | $2.50 | $15 | 1467 | ~80% | — | — | — | Proprietaria |
| — | MiMo V2.5 Pro | Xiaomi | 1.02T (42B act.) | MoE Multimodal | 1M | — | — | 1465 | — | — | — | — | Apache 2.0 |
| — | Qwen3.5 Max Preview | Alibaba | 397B (17B act.) | MoE+Gated DeltaNet | 256K | — | — | 1465 | 76.4% | 81.0% | — | — | Apache 2.0 |

---

## Por Laboratorio / Región

---

### 1. OpenAI (EE.UU.)

OpenAI mantiene su posición como uno de los laboratorios líderes, aunque la competencia se ha intensificado dramáticamente. Con GPT-5.5, la compañía ha consolidado su arquitectura de "ruteo unificado" donde un solo modelo base maneja todas las modalidades (texto, imagen, audio, video) mediante un sistema de enrutamiento interno. La estrategia de OpenAI se centra en tres líneas: modelos generales (GPT-5.x), modelos de razonamiento (o-series), y modelos especializados (Codex, DALL-E, Sora, gpt-image-1).

#### GPT-4.5
- **Fecha de publicación:** 27 de febrero de 2025
- **Arquitectura:** MoE de ~1.8 billones de parámetros
- **Contexto:** 128K tokens
- **Precio:** $75/$150 por millón de tokens (input/output) — **deprecado**
- **Benchmarks:** SimpleQA 62.5%, AIME 2024 36.7%, GPQA 71.4%, MMLU ~89.6%
- **Notas:** Considerado un modelo de transición. Fue el último modelo puramente textual de OpenAI antes de la unificación de modalidades. Su alto precio y rendimiento mediocre en razonamiento matemático llevaron a su rápido reemplazo por GPT-5.

#### GPT-5
- **Fecha de publicación:** 7 de agosto de 2025
- **Arquitectura:** Sistema unificado con router interno de modalidades
- **Contexto:** 400K tokens
- **Precio:** $1.25/$10 por millón de tokens
- **Benchmarks:** AIME 2024 94.6%, SWE-bench 74.9%
- **Modalidades:** Texto + imagen + audio (nativo)
- **Notas:** Primer modelo verdaderamente unificado de OpenAI. El router decide internamente qué "experto" modal activar. Representó un salto cualitativo en razonamiento matemático y capacidades de código.

#### GPT-5.1
- **Fecha de publicación:** 12 de noviembre de 2025
- **Contexto:** 410K tokens
- **Precio:** $1.25/$10 (sin cambios respecto a GPT-5)
- **Benchmarks:** AIME 2024 94%, GPQA 88.1%, SWE-bench 76.3%, MMMU 89.5%
- **Notas:** Mejora incremental sobre GPT-5, con enfoque en precisión factual (GPQA subió de ~85% a 88.1%) y mejores capacidades multimodales (MMMU 89.5%).

#### GPT-5.2 "Garlic"
- **Fecha de publicación:** 11 de diciembre de 2025
- **Contexto:** 400K tokens
- **Precio:** $1.75/$14 por millón de tokens
- **Benchmarks:** GPQA 92.4%, AIME 2024 100% (¡perfecto!), SWE-bench 80%, ARC-AGI-2 52.9%
- **Característica distintiva:** 5 niveles de razonamiento seleccionables (bajo, medio, alto, muy alto, automático). El usuario puede controlar la profundidad computacional del razonamiento, similar a lo que Anthropic implementaría después con "adaptive thinking".
- **Notas:** GPT-5.2 logró un hito histórico: puntuación perfecta en AIME 2024. ARC-AGI-2 52.9% indica capacidades emergentes de adaptación a novel tasks. El nombre en clave "Garlic" fue filtrado por personal de OpenAI.

#### GPT-5.3 Codex
- **Fecha de publicación:** 5 de febrero de 2026
- **Contexto:** 400K tokens
- **Especialización:** Modelo optimizado para tareas de programación y agencia
- **Benchmarks:** SWE-bench Pro 56.8%, Terminal-Bench 77.3%, OSWorld 64.7%, Cybersecurity CTF 77.6%
- **Notas:** Versión especializada de GPT-5.2 con fine-tuning intensivo en datos de programación, terminales UNIX, entornos de escritorio (OSWorld) y competiciones de ciberseguridad. No es un reemplazo de GPT-5.2 sino un modelo complementario para ingeniería de software.

#### GPT-5.4
- **Fecha de publicación:** 5 de marzo de 2026
- **Contexto:** 1M tokens (salto significativo desde 400K)
- **Precio:** $2.50/$15 por millón de tokens
- **Capacidad distintiva:** Computer use nativo — el modelo puede controlar directamente interfaces gráficas
- **Benchmarks:** OSWorld 75% (supera a humanos que promedian 72.4%), SWE-bench ~80%, MMMU Pro 81.2%
- **Notas:** GPT-5.4 marcó la primera vez que un modelo de IA supera a humanos en una tarea de interacción con entorno de escritorio (OSWorld). Con 1M de contexto, puede procesar repositorios completos en una sola ventana.

#### GPT-5.5 "Spud"
- **Fecha de publicación:** 23 de abril de 2026
- **Arquitectura:** Omnimodal — texto + imagen + audio + video de forma nativa
- **Contexto:** 1M tokens
- **Precio:** $5/$30 por millón de tokens; $30/$180 para modo Pro (razonamiento profundo habilitado)
- **Benchmarks:**
  - Terminal-Bench: 82.7%
  - SWE-bench: 88.7%
  - OSWorld: 78.7%
  - MRCR v2: 74%
  - MMLU: 92.4%
  - ARC-AGI-1: 95%
- **Innovaciones:** 60% menos alucinaciones que GPT-5.4 gracias a un nuevo mecanismo de verificación interna. Enrutamiento de modalidades mejorado con asignación dinámica de recursos computacionales según la complejidad de la tarea.
- **Modelos derivados:**
  - **GPT-5.5 High:** $5/$30, 1484 Arena ELO
  - **GPT-5.5 Instant:** 1472 Arena ELO, presumiblemente versión optimizada para latencia

#### o1
- **Fecha de publicación:** 12 de septiembre de 2024
- **Contexto:** 200K tokens
- **Precio:** $15/$60 por millón de tokens
- **Benchmarks:** AIME 2024 74.3%, GPQA 78%, Codeforces 1891, MMLU 92.3%
- **Notas:** El primer modelo de razonamiento ("thinking") de OpenAI. Introduce la cadena de pensamiento interna (hidden chain-of-thought). Codeforces 1891 lo sitúa en el percentil 89 de programadores competitivos humanos. Su precio elevado ($15/$60) reflejaba el costo computacional del razonamiento interno.

#### o3
- **Anuncio:** 20 de diciembre de 2024
- **Release público:** 16 de abril de 2025
- **Contexto:** 200K tokens
- **Precio:** $2/$8 (reducido significativamente desde precios de preview)
- **Benchmarks:**
  - AIME 2024: 96.7% (preview) / 91.6% (release)
  - GPQA: 87.7% (preview) / 83.3% (release)
  - Codeforces: 2727 (rating de Gran Maestro, supera al 99.8% de competidores humanos)
  - ARC-AGI: 87.5%
- **Notas:** o3 representó la maduración de la tecnología de razonamiento de OpenAI. La versión de release tuvo puntuaciones ligeramente inferiores a la preview (trade-off típico entre rendimiento máximo y generalización). ARC-AGI 87.5% — aunque impresionante — quedó lejos del 100% requerido para el premio ARC.

#### o4-mini
- **Fecha de publicación:** 16 de abril de 2025 (simultáneo con o3 release)
- **Contexto:** 200K tokens
- **Precio:** $1.10/$4.40 por millón de tokens
- **Benchmarks:** AIME 2024 93.4%, Codeforces 2719, HumanEval 97.5%
- **Notas:** Versión eficiente de la serie o. Codeforces 2719 (también Gran Maestro) demuestra que la reducción de tamaño no sacrificó significativamente el rendimiento en código. HumanEval 97.5% — near-perfect en generación de código funcional.

#### gpt-image-1
- **ELO Arena:** 1264 (modelo de generación de imágenes líder en LMSYS)
- **Notas:** El modelo de generación de imágenes de OpenAI, integrado en el ecosistema GPT. Compite directamente con FLUX.2 Pro (1265 ELO), Midjourney v7 (~1240), DALL-E 3 (1200) e Imagen 4 Ultra.

---

### 2. Anthropic (EE.UU.)

Anthropic ha emergido como el laboratorio con la puntuación más alta en LMSYS Arena (Claude Opus 4.6 Thinking: 1502 ELO, el más alto registrado). La compañía ha seguido una trayectoria de mejoras incrementales pero consistentes, con Claude Opus 4.7 estableciendo nuevos estándares en SWE-bench (87.6%), GPQA (94.2%) y OSWorld (78%). La filosofía de Anthropic se centra en la seguridad (ASL-3 alcanzado), el razonamiento "adaptive thinking" y la reducción agresiva de costos (67% de reducción en Opus 4.5).

#### Claude 3 Opus
- **Fecha de publicación:** 4 de marzo de 2024
- **Contexto:** 200K tokens
- **Precio:** $15/$75 por millón de tokens
- **Benchmarks:** MMLU 86.8%, GPQA 50.4%, HumanEval 84.9%, GSM8K 95%, MATH 60.1%
- **Notas:** Modelo fundacional de la era Claude 3. Estableció a Anthropic como competidor serio frente a GPT-4. GPQA 50.4% — apenas por encima del azar (50%) — revelaba limitaciones en razonamiento científico profundo.

#### Claude 3.5 Sonnet v1
- **Fecha de publicación:** 20 de junio de 2024
- **Precio:** $3/$15 (significativamente más barato que Opus)
- **Benchmarks:** MMLU 88.7%, GPQA 59.4%, SWE-bench 33.4%
- **Notas:** Por primera vez, un modelo "Sonnet" (gama media) superaba al "Opus" anterior en múltiples métricas. SWE-bench 33.4% — modesta capacidad de reparación de software.

#### Claude 3.5 Sonnet v2
- **Fecha de publicación:** 22 de octubre de 2024
- **Precio:** $3/$15
- **Benchmarks:** SWE-bench 49% (mejora significativa), computer use beta (primera incursión de Anthropic en control de interfaces)
- **Notas:** Introdujo la capacidad de "computer use" en fase beta — el modelo podía mover el cursor, hacer clic, y navegar interfaces gráficas, aunque con limitaciones.

#### Claude 3.7 Sonnet
- **Fecha de publicación:** 24 de febrero de 2025
- **Arquitectura:** Primer modelo híbrido con razonamiento (thinking mode opcional)
- **Contexto:** 200K tokens
- **Precio:** $3/$15 (normal), $15 (thinking habilitado, output únicamente)
- **Benchmarks:**
  - GPQA: 62.1% (normal) / 84.8% (thinking)
  - SWE-bench: 62.3% (normal) / 70.3% (thinking)
  - AIME: 73.6% (normal) / 80% (thinking)
- **Notas:** Claude 3.7 Sonnet introdujo el concepto de "hybrid reasoning" que se convertiría en estándar de la industria. La diferencia entre modo normal y thinking (22.7 puntos en GPQA) demostró el valor del razonamiento encadenado.

#### Claude Opus 4
- **Fecha de publicación:** 22 de mayo de 2025
- **Precio:** $15/$75
- **Benchmarks:** SWE-bench 72.5%, GPQA 74.9%
- **Hito:** Alcanzó ASL-3 (AI Safety Level 3), el nivel más alto de seguridad voluntariamente implementado por un laboratorio de IA.
- **Notas:** Retorno del modelo Opus después de más de un año. SWE-bench 72.5% — mejora sustancial sobre Claude 3.7 Sonnet thinking (70.3%).

#### Claude Sonnet 4
- **Fecha de publicación:** 22 de mayo de 2025 (junto con Opus 4)
- **Precio:** $3/$15
- **Contexto:** 200K tokens (estándar) / 1M tokens (máximo)
- **Benchmarks:** SWE-bench 72.7% (ligeramente superior a Opus 4 en código)
- **Notas:** Caso inusual donde el modelo "Sonnet" (medio) iguala o supera al "Opus" (premium) en una métrica clave.

#### Claude Opus 4.5
- **Fecha de publicación:** 24 de noviembre de 2025
- **Precio:** $5/$25 — **reducción del 67% respecto a Opus 4** ($15/$75)
- **Benchmarks:** SWE-bench ~77-80% (estimado)
- **Eficiencia:** 76% menos tokens de output que Sonnet 4.5 para tareas equivalentes
- **Notas:** La reducción de precio más agresiva en la historia de Anthropic. La mejora en eficiencia (76% menos tokens) sugiere optimizaciones arquitectónicas significativas, probablemente un mejor modelo de razonamiento que requiere menos pasos.

#### Claude Haiku 4.5
- **Fecha de publicación:** 15 de octubre de 2025
- **Precio:** $1/$5
- **Benchmarks:** SWE-bench ~73.3%
- **Notas:** Modelo ligero con rendimiento sorprendentemente alto en código. Competitivo con GPT-5.2 en SWE-bench a una fracción del costo.

#### Claude Opus 4.6
- **Fecha de publicación:** 5 de febrero de 2026
- **Contexto:** 1M tokens
- **Precio:** $5/$25
- **Arquitectura:** Adaptive thinking — el modelo ajusta dinámicamente la profundidad de razonamiento según la complejidad de la tarea
- **Benchmarks:**
  - SWE-bench: 80.8%
  - GPQA: 91.3%
  - Terminal-Bench: 65.4%
  - MMMLU: 91.1%
  - ARC-AGI-2: 68.8%
- **Versión Thinking:** 1502 Arena ELO (#1 global en ese momento)
- **Notas:** Claude Opus 4.6 se convirtió en el primer modelo en superar 1500 ELO en la LMSYS Arena. ARC-AGI-2 68.8% — segundo mejor en esa métrica (solo superado por Gemini 3.1 Pro Preview con 77.1%).

#### Claude Sonnet 4.6
- **Fecha de publicación:** 17 de febrero de 2026
- **Contexto:** 1M tokens
- **Precio:** $3/$15
- **Benchmarks:** SWE-bench 79.6%, GPQA 89.9% (thinking habilitado)
- **Notas:** Se convirtió en el modelo por defecto (default) de Anthropic, reemplazando a Opus 4.5 como recomendación general. La relación calidad/precio ($3/$15 vs $5/$25 de Opus) con solo ~1-2 puntos de diferencia en benchmarks lo convierte en el mejor balance calidad/precio de Anthropic.

#### Claude Opus 4.7
- **Fecha de publicación:** 16 de abril de 2026
- **Contexto:** 1M tokens
- **Precio:** $5/$25
- **Arquitectura:** Adaptive thinking **exclusivamente** — no existe modo "normal" sin razonamiento
- **Nuevo tokenizador:** Tokenización más eficiente que reduce la cantidad de tokens necesarios para texto codificado
- **Resolución de visión:** Hasta 2576px (significativamente superior a modelos anteriores)
- **Benchmarks:**
  - SWE-bench Verified: 87.6% (récord en su momento)
  - SWE-bench Pro: 64.3%
  - GPQA: 94.2%
  - OSWorld: 78%
  - MMMLU: 91.5%
  - CharXiv: 82.1%
- **Regresiones identificadas:**
  - MRCR v2: 59.2% a 256K contexto, **32.2% a 1M contexto** (caída dramática con contexto largo)
  - BrowseComp: 79.3%
- **Notas:** Opus 4.7 muestra el primer caso documentado de regresión severa con contexto largo (MRCR v2 cae 27 puntos al extender de 256K a 1M). Esto sugiere que el nuevo tokenizador o la arquitectura de razonamiento adaptativo tienen dificultades con recuperación de información en ventanas muy largas.

#### Claude Mythos Preview
- **Fecha de publicación:** 7 de abril de 2026
- **Estado:** Modelo de investigación con acceso restringido (gated)
- **Precio publicado:** $25/$125 por millón de tokens
- **Benchmarks:**
  - SWE-bench Verified: **93.9%** (récord absoluto)
  - SWE-bench Pro: **77.8%**
  - GPQA: **94.6%**
  - USAMO 2026: **97.6%** (Olimpiada de Matemáticas de EE.UU.)
  - Cybench: **100%** (ciberseguridad — perfecto)
- **Documentación:** 244 páginas de system card técnica
- **Clasificación de seguridad:** ASL-3 (el más alto)
- **Notas:** Mythos Preview es el modelo más capaz jamás creado por Anthropic, pero no está disponible para el público general. Sus puntuaciones en SWE-bench Verified (93.9%) y Cybench (100%) sugieren capacidades muy por encima de cualquier modelo comercial. El precio publicado ($25/$125) es prohibitivo, consistente con un modelo de investigación de acceso limitado.

#### Resumen de la Línea Claude

| Modelo | Fecha | SWE-bench | GPQA | Precio I/O | Contexto |
|--------|-------|-----------|------|-----------|----------|
| 3 Opus | Mar 2024 | — | 50.4% | $15/$75 | 200K |
| 3.5 Sonnet v1 | Jun 2024 | 33.4% | 59.4% | $3/$15 | 200K |
| 3.5 Sonnet v2 | Oct 2024 | 49% | — | $3/$15 | 200K |
| 3.7 Sonnet | Feb 2025 | 62.3/70.3% | 62.1/84.8% | $3/$15 | 200K |
| Opus 4 | May 2025 | 72.5% | 74.9% | $15/$75 | 200K |
| Sonnet 4 | May 2025 | 72.7% | — | $3/$15 | 200K-1M |
| Opus 4.5 | Nov 2025 | ~77-80% | — | $5/$25 | 200K |
| Haiku 4.5 | Oct 2025 | ~73.3% | — | $1/$5 | — |
| Opus 4.6 | Feb 2026 | 80.8% | 91.3% | $5/$25 | 1M |
| Sonnet 4.6 | Feb 2026 | 79.6% | 89.9% | $3/$15 | 1M |
| Opus 4.7 | Abr 2026 | 87.6% | 94.2% | $5/$25 | 1M |
| Mythos Preview | Abr 2026 | 93.9% | 94.6% | $25/$125 | — |

---

### 3. Google DeepMind (EE.UU.)

Google DeepMind ha apostado fuertemente por la arquitectura MoE (Mixture-of-Experts) y ventanas de contexto masivas (1M+ tokens como estándar desde Gemini 2.0). Con Gemini 3.1 Pro Preview, Google ha logrado puntuaciones de élite en ARC-AGI-2 (77.1%, la más alta registrada) y lidera en benchmarks de navegación web (BrowseComp 85.9%). La familia Gemma 4 representa la apuesta open-source más importante de Google, con modelos que compiten directamente con Llama 4 y DeepSeek.

#### Gemini 2.0 Flash
- **Fecha de publicación:** 11 de diciembre de 2024
- **Arquitectura:** MoE (Mixture-of-Experts)
- **Contexto:** 1M tokens (estándar en Gemini)
- **Precio:** $0.10/$0.40 por millón de tokens (extremadamente barato)
- **Benchmarks:** MMLU-Pro 78.2%, GPQA 63.6%, HumanEval 89.7%, Arena 1268
- **Notas:** Gemini 2.0 Flash estableció un nuevo estándar de relación calidad/precio. Por $0.10 por millón de tokens de entrada, ofrecía rendimiento competitivo con modelos mucho más caros. Contexto de 1M tokens — Google fue el primer laboratorio en ofrecer esto como estándar.

#### Gemini 2.5 Pro
- **Fecha de publicación:** 25 de marzo de 2025
- **Arquitectura:** MoE
- **Contexto:** 1M tokens
- **Precio:** $1.25/$10 (≤200K tokens/día, luego tarifas diferentes)
- **Benchmarks:**
  - GPQA: 84.4%
  - AIME 2024: 88%
  - SWE-bench: 59.6% (Verified) / 67.2% (con herramientas)
  - Arena: 1470
- **Notas:** Gemini 2.5 Pro fue el primer modelo de Google en incorporar "thinking" de forma nativa. GPQA 84.4% — salto significativo sobre 2.0 Flash (63.6%). SWE-bench 67.2% competitivo con Claude 3.7 Sonnet thinking (70.3%).

#### Gemini 3.0 Pro
- **Fecha de publicación:** 18 de noviembre de 2025
- **Arquitectura:** MoE de última generación
- **Contexto:** 1M tokens
- **Precio:** $2/$12 por millón de tokens
- **Benchmarks:**
  - GPQA: 91.9% — **supera a humanos (89.8%)**
  - MMLU: 91.8%
  - AIME 2024: 95% — 100% con uso de código Python
  - HLE: 37.5%
  - ARC-AGI-2: 31.1% (45.1% con Deep Think)
  - LiveCodeBench: 91.7%
  - SWE-bench: 76.2%
  - Arena: **1501** (primer modelo en superar 1500 ELO, aunque luego superado por Claude Opus 4.6 Thinking con 1502)
- **Modo Deep Think:** Modo de razonamiento extremo que mejora significativamente en benchmarks difíciles (ARC-AGI-2: 31.1% → 45.1%, HLE: probable mejora similar)
- **Notas:** Gemini 3 Pro fue el primer modelo en superar 1500 ELO en la Arena y el primero en superar a humanos en GPQA (91.9% vs 89.8%). AIME 95% (100% con código) muestra dominio absoluto de matemáticas de competencia.

#### Gemini 3.1 Pro Preview
- **Fecha de publicación:** 19 de febrero de 2026
- **Arquitectura:** MoE con mejoras en razonamiento contextual
- **Contexto:** 1-2M tokens
- **Precio:** $2/$12 (mismo que Gemini 3 Pro)
- **Benchmarks:**
  - ARC-AGI-2: **77.1%** (la puntuación más alta registrada — más del doble que Gemini 3 Pro)
  - GPQA: 94.3%
  - MMMLU: 92.6%
  - HLE: 44.4% (51.4% con Deep Think)
  - SWE-bench: 80.6%
  - MCP Atlas: 69.2%
  - BrowseComp: **85.9%** (líder en navegación web)
  - Arena: 1490
- **Notas:** Gemini 3.1 Pro Preview es posiblemente el modelo más equilibrado del mercado. ARC-AGI-2 77.1% sugiere capacidades de adaptación a novel tasks muy superiores a cualquier competidor. BrowseComp 85.9% — dominio absoluto en tareas de navegación web autónoma. MCP Atlas 69.2% indica excelente integración con el protocolo MCP.

#### Gemini 3.0 Flash
- **Fecha de publicación:** 17 de diciembre de 2025
- **Arquitectura:** MoE optimizado para velocidad
- **Contexto:** 1M tokens
- **Precio:** $0.50/$3 por millón de tokens
- **Benchmarks:**
  - GPQA: 90.4% (increíble para un modelo "Flash")
  - MMMU-Pro: 81.2%
  - SWE-bench: 78%
  - AIME: 99.7% (casi perfecto)
  - Aider Polyglot: 95.2%
  - Arena: 1474
- **Notas:** Gemini 3.0 Flash es quizás el modelo con mejor relación calidad/precio del mercado. GPQA 90.4% a $0.50/$3 es extraordinario. AIME 99.7% — prácticamente perfecto en matemáticas de competencia. SWE-bench 78% supera a Claude Opus 4.5.

#### Gemini 3.5 Flash
- **Fecha de publicación:** 19 de mayo de 2026 (I/O 2026)
- **Arquitectura:** MoE con 4x mejora de velocidad respecto a 3.0 Flash
- **Contexto:** 1M tokens
- **Precio:** $1.50/$9 por millón de tokens
- **Benchmarks:**
  - Terminal-Bench 2.1: 76.2%
  - MCP Atlas: **83.6%** (récord)
  - Toolathlon: 56.5%
  - OSWorld: 78.4%
  - Finance Agent v2: 57.9%
  - MMMU-Pro: 83.6%
  - ARC-AGI-2: 72.1%
  - HLE: 40.2%
- **Notas:** Gemini 3.5 Flash, presentado en Google I/O 2026, es un modelo orientado a agencia y herramientas. MCP Atlas 83.6% — el puntaje más alto en este benchmark de integración MCP. ARC-AGI-2 72.1% — notable para un modelo flash, solo superado por Gemini 3.1 Pro (77.1%).

#### Gemma 4
- **Fecha de publicación:** 2 de abril de 2026
- **Licencia:** Apache 2.0 (totalmente abierta)
- **Familia de modelos:**

| Variante | Params | Arquitectura | Contexto | GPQA | AIME | MMLU-Pro | LiveCodeBench |
|----------|--------|-------------|----------|------|------|----------|---------------|
| Gemma 4 31B | 31B Dense | Transformer Denso | 256K | 84.3% | 89.2% | 85.2% | 80% |
| Gemma 4 26B MoE | 26B A4B | MoE (4 activos) | 256K | 82.3% | — | — | — |
| Gemma 4 E4B | — | Audio nativo | — | — | — | — | — |
| Gemma 4 E2B | — | Edge optimizado | — | — | — | — | — |

- **Notas:** Gemma 4 31B Dense es particularmente notable — GPQA 84.3% compite directamente con Claude 3.7 Sonnet thinking y Gemini 2.5 Pro, pero con solo 31B parámetros y licencia Apache 2.0. Ideal para despliegue local, fine-tuning y aplicaciones on-premise.

---

### 4. Meta (EE.UU.)

Meta ha adoptado una estrategia dual: modelos abiertos (Llama 4 Scout, Llama 4 Maverick) y un modelo cerrado de élite (Muse Spark, #5 en Arena). Muse Spark, con 1491 ELO, es el modelo propietario de Meta que compite directamente con Claude, Gemini y GPT en el frente cerrado. Llama 4 Scout ostenta el récord de contexto más largo del mercado (10M tokens).

#### Muse Spark
- **ELO Arena:** 1491 (#5 global, el modelo más alto de Meta)
- **Precio:** $0.95/$3.80 por millón de tokens (competitivo)
- **Licencia:** Abierta (free / open)
- **Notas:** Se sabe poco sobre la arquitectura de Muse Spark. Su posición (#5 global) sugiere capacidades de élite. El precio agresivo ($0.95/$3.80) lo posiciona como una alternativa económica a Claude Opus y GPT-5.5.

#### Llama 4 Maverick
- **Arquitectura:** MoE con 17B parámetros activos / 128 expertos totales
- **Capacidad:** Multimodal nativa (texto + imagen)
- **Contexto:** 200K tokens
- **Benchmarks:** MMLU-Pro: 18 en BenchLM (significativamente por debajo de líderes)
- **Notas:** Aunque multimodal y de arquitectura moderna, Maverick no logra puntuaciones competitivas en benchmarks estándar. Su fortaleza probablemente reside en tareas específicas o fine-tuning.

#### Llama 4 Scout
- **Arquitectura:** MoE con 17B parámetros activos / 16 expertos
- **Contexto:** **10M tokens** — el contexto más largo del mercado
- **Precio:** $0.11/$0.34 por millón de tokens (extremadamente barato)
- **Licencia:** Open-weight
- **Benchmarks:** MMLU-Pro: 24 en BenchLM (modesto)
- **Notas:** El contexto de 10M tokens es la característica distintiva. Ningún otro modelo comercial se acerca. Sin embargo, los benchmarks sugieren que el rendimiento en tareas estándar es limitado. Ideal para aplicaciones que requieren procesamiento de documentos extremadamente largos donde la precisión no es crítica.

#### Llama 4 Behemoth
- **Estado:** Solo entrenamiento — nunca lanzado al público
- **Benchmarks reportados:** MMMLU 85.8%, GPQA 73.7%
- **Notas:** Meta entrenó un modelo masivo que no liberó. Los benchmarks sugieren que habría sido competitivo con Claude Opus 4 y GPT-5.2 de haberse lanzado.

---

### 5. xAI (EE.UU.)

xAI, fundada por Elon Musk, ha escalado rápidamente con Grok 4.20 Beta alcanzando 1479 ELO. La compañía experimenta con arquitecturas multi-agente (Grok 4.20 Multi-Agent: 1474 ELO) y modos de razonamiento (Grok 4.20 Reasoning: 1477 ELO, Grok 4.1 Thinking: 1467 ELO).

#### Grok 4.20 Beta1
- **ELO Arena:** 1479 (#9 global)
- **Precio:** $5/$15 por millón de tokens
- **Contexto:** 256K tokens
- **Benchmarks:** GPQA 88%, HLE 24.5%, MMLU 86.6%
- **Notas:** Grok 4.20 Beta1 es el modelo principal de xAI. GPQA 88% — competitivo con GPT-5.1 y Claude Opus 4.6. HLE 24.5% — bajo en comparación con líderes (Kimi K2.6 tiene 54%), sugiriendo limitaciones en tareas extremadamente difíciles.

#### Grok 4.20 Beta Reasoning
- **ELO Arena:** 1477 (empate técnico con GPT-5.2 Chat)
- **Notas:** Versión con razonamiento mejorado de Grok 4.20.

#### Grok 4.20 Multi-Agent
- **ELO Arena:** 1474
- **Arquitectura:** Ensemble multi-agente — múltiples instancias del modelo colaboran en la respuesta
- **Notas:** xAI experimenta con sistemas multi-agente para mejorar la calidad de las respuestas. El enfoque es similar a "mixture of agents" pero aplicado a inferencia en lugar de entrenamiento.

#### Grok 4.1 Thinking
- **ELO Arena:** 1467
- **Notas:** Versión anterior del modelo de razonamiento de xAI.

#### Grok 4.3
- **Artificial Analysis Index:** 53.2
- **Precio:** $1.56/M blended
- **Notas:** Información limitada. El AA Index de 53.2 sugiere rendimiento competitivo con modelos de gama media.

---

### 6. Microsoft (EE.UU.)

Microsoft ha reducido su presencia directa en el desarrollo de modelos frontier, optando por integrar OpenAI (GPT-5.x) y ofrecer modelos propios más pequeños (Phi-4). Sin embargo, su infraestructura Azure es la plataforma de despliegue principal para OpenAI, Meta (Llama) y Mistral.

#### Phi-4-multimodal
- **Notas:** Modelo multimodal de Microsoft, parte de la familia Phi de modelos pequeños pero capaces. Diseñado para integración en productos Microsoft (Copilot, Azure AI).

---

### 7. DeepSeek (China)

DeepSeek se ha convertido en el laboratorio chino más influyente a nivel global, conocido por sus modelos abiertos (licencia MIT) de rendimiento frontier a precios radicalmente bajos. DeepSeek-V4 Flash, con precios promocionales de $0.0028/M input, es el modelo frontier más barato del mundo. La compañía ha popularizado arquitecturas MoE con atención híbrida (CSA/HCA) que rompen la barrera cuadrática del transformer.

#### DeepSeek-V3
- **Fecha de publicación:** Diciembre 2024 - Enero 2025
- **Arquitectura:** MoE de 671B parámetros totales (37B activos)
- **Contexto:** 128K tokens
- **Licencia:** MIT
- **Benchmarks:** MMLU 88.5%, HumanEval 82.6%
- **Precio:** $0.14/$0.28 por millón de tokens
- **Notas:** DeepSeek-V3 sacudió la industria por su relación calidad/precio. Por $0.14/$0.28, ofrecía rendimiento cercano a GPT-4 a una fracción del costo. Arquitectura MoE con 37B parámetros activos — eficiencia energética y computacional excepcional.

#### DeepSeek-R1
- **Fecha de publicación:** Enero 2025
- **Arquitectura:** MoE de 671B (37B activos), mismo esqueleto que V3 pero con RL intensiva
- **Contexto:** 128K tokens
- **Licencia:** MIT
- **Benchmarks:**
  - MMLU: 90.8%
  - GPQA: 71.5%
  - AIME 2024: 79.8%
  - MATH-500: 97.3%
  - SWE-bench: 49.2%
- **Precio:** $0.55/$2.19 por millón de tokens
- **Notas:** DeepSeek-R1 demostró que el razonamiento podía lograrse con reinforcement learning a gran escala sin supervisión humana (SFT). MATH-500 97.3% — rendimiento casi perfecto en matemáticas. AIME 79.8% — competitivo con o1 (74.3%) a un costo mucho menor. DeepSeek-R1 inspiró una ola de réplicas y adaptaciones open-source.

#### DeepSeek-V4 Pro
- **Fecha de publicación:** 24 de abril de 2026
- **Arquitectura:** MoE de 1.6T parámetros totales (49B activos) + CSA (Cross-Step Attention) / HCA (Hybrid Cross Attention)
- **Contexto:** 1M tokens
- **Licencia:** MIT (totalmente abierto)
- **Precio:** $0.435/$0.87 (promoción de lanzamiento); precio lista $1.74/$3.48
- **Benchmarks:**
  - GPQA: 90.1%
  - SWE-bench: 80.6%
  - LiveCodeBench: 93.5%
  - AIME: 95.2%
  - HLE: 37.7%
  - MMLU-Pro: 87.5%
- **Notas:** DeepSeek-V4 Pro es posiblemente el modelo abierto más poderoso jamás creado. GPQA 90.1%, SWE-bench 80.6% — rendimiento frontier con licencia MIT. La arquitectura CSA/HCA representa una innovación significativa en eficiencia atencional. El precio promocional de $0.435/$0.87 (60% del precio de lista) fue una ofensiva comercial directa contra OpenAI y Anthropic.

#### DeepSeek-V4 Flash
- **Fecha de publicación:** 24 de abril de 2026 (junto con V4 Pro)
- **Arquitectura:** MoE de 284B parámetros totales (13B activos)
- **Contexto:** 1M tokens
- **Licencia:** MIT
- **Benchmarks:** GPQA 88.1%, SWE-bench 79.0%, LiveCodeBench 91.6%
- **Precio:** $0.0028/$0.14/$0.28 (promocional) — **el modelo frontier más barato del mundo**
- **Notas:** DeepSeek-V4 Flash con solo 13B parámetros activos logra GPQA 88.1% — superior a GPT-5.1 (88.1%) y casi igual a Claude Opus 4.6 (91.3%). El precio promocional de $0.0028/M input es 3 órdenes de magnitud menor que Claude Opus ($5/M). Esto representa una democratización radical del acceso a IA frontier.

#### DeepSeek-Coder-V2
- **Arquitectura:** MoE de 236B (21B activos)
- **Benchmarks:** HumanEval 90.2%
- **Notas:** Modelo especializado en código con rendimiento de élite. Competitivo con GPT-5.3 Codex en tareas de generación de código.

#### Janus-Pro-7B
- **Licencia:** MIT
- **Capacidad:** Multimodal — generación + comprensión de imágenes
- **Notas:** Modelo unificado que combina generación y comprensión visual en una sola arquitectura. 7B parámetros — ligero y desplegable localmente.

---

### 8. Alibaba / Qwen (China)

Alibaba, a través de su división Qwen, ha emergido como uno de los contribuyentes open-source más importantes del mundo (licencia Apache 2.0). La familia Qwen abarca desde modelos pequeños (Qwen3.6: 35B-A3B) hasta modelos frontier propietarios (Qwen3.7-Max). La innovación clave de Qwen es la integración de mecanismos de atención subcuadrática (DeltaNet, Mamba híbrido) que permiten eficiencia extrema.

#### Qwen3
- **Arquitectura:** MoE de 235B-A22B (22B activos)
- **Licencia:** Apache 2.0
- **Contexto:** 128K tokens
- **Idiomas:** 119 lenguajes
- **Característica distintiva:** Modo dual thinking/no-thinking configurable
- **Notas:** Qwen3 estableció un nuevo estándar para modelos abiertos multilingües. 119 idiomas supera a cualquier competidor abierto. El modo dual permite elegir entre respuestas rápidas (no-thinking) y razonamiento profundo (thinking).

#### Qwen3.5
- **Arquitectura:** MoE de 397B-A17B (17B activos) + **Gated DeltaNet** (mecanismo de atención lineal)
- **Contexto:** 256K tokens
- **Licencia:** Apache 2.0
- **Idiomas:** 201 lenguajes
- **Benchmarks:** AIME 2024 91.3%, GPQA 81.0%, SWE-bench 76.4%
- **Notas:** Gated DeltaNet es una innovación arquitectónica que reemplaza la atención softmax tradicional con un mecanismo de compuertas lineales, reduciendo la complejidad de O(n²) a O(n). 201 idiomas — cobertura lingüística sin precedentes.

#### Qwen3.6
- **Arquitectura:** MoE de 35B-A3B (3B activos) — **extremadamente eficiente**
- **Mecanismo:** Mamba híbrido + Delta-Attention — **75% de las capas sin KV cache**
- **Contexto:** 262K tokens
- **Benchmarks:** GPQA 87.8%, AIME 2024 94.1%, SWE-bench 77.2%
- **Notas:** Qwen3.6 es quizás la demostración más impresionante de eficiencia arquitectónica. Con solo 3B parámetros activos, logra GPQA 87.8% — mejor que GPT-5.1 (88.1%) con una fracción del costo computacional. El 75% de las capas sin KV cache significa que la inferencia es dramáticamente más rápida y barata que cualquier transformer equivalente.

#### Qwen3.7-Max
- **Fecha de publicación:** 21 de mayo de 2026
- **Arquitectura:** MoE propietaria (no revelada)
- **Contexto:** 1M tokens
- **Licencia:** Propietaria
- **Precio:** $0.83/$2.50 por millón de tokens
- **Benchmarks:**
  - GPQA: 92.4%
  - SWE-bench: 80.4%
  - HLE: 41.4%
  - Artificial Analysis Index: 56.6
- **Notas:** Qwen3.7-Max es el modelo frontier propietario de Alibaba. GPQA 92.4% — igual a GPT-5.2 (92.4%) y cerca de Claude Opus 4.7 (94.2%). AA Index 56.6 — competitivo con GPT-5.5 y Claude Opus 4.6. El precio ($0.83/$2.50) es significativamente más barato que Claude Opus ($5/$25) y GPT-5.5 ($5/$30).

#### Otros modelos Qwen

| Modelo | Especialización |
|--------|----------------|
| Qwen2.5-Coder | Código — fine-tuning de Qwen2.5 para programación |
| Qwen2.5-Math-72B-Instruct | Matemáticas — 72B, instrucciones matemáticas |
| Qwen2.5-VL 72B | Visión-Lenguaje — 72B, comprensión multimodal |
| Qwen3-VL | Visión-Lenguaje — última generación |
| Qwen3-Coder-Next | Código — SWE-bench 70.6-71.3% |
| CodeQwen | Código — especializado |

---

### 9. Zhipu AI / GLM (China)

Zhipu AI ha logrado un hito geopolítico significativo: GLM-5 fue entrenado íntegramente en hardware doméstico chino (100,000 GPUs Huawei Ascend 910B, cero NVIDIA). GLM-5.1 alcanza 1471 Arena ELO (#19 global), convirtiéndose en uno de los modelos chinos más populares. La compañía también lidera en benchmarks agentic (Tau2-Bench 89.7%).

#### GLM-4
- **Arquitectura:** 130B parámetros (denso)
- **Notas:** Modelo fundacional de la serie GLM. Arquitectura transformer densa convencional.

#### GLM-5
- **Fecha de publicación:** 15 de febrero de 2026
- **Arquitectura:** MoE de 744B parámetros totales (40B activos) + **DSA (Dual Self-Attention) + MLA (Multi-head Latent Attention)**
- **Contexto:** 200K tokens
- **Licencia:** MIT
- **Entrenamiento:** 100,000 GPUs Huawei Ascend 910B — **cero NVIDIA**
- **Benchmarks:** GPQA 86.0%, SWE-bench 77.8%, AIME 2024 92.7%, **Tau2-Bench 89.7% (#1 agentic)**
- **Notas:** GLM-5 es un hito tecnológico y geopolítico. Tau2-Bench 89.7% — el puntaje más alto en benchmarks agentic, superando a Claude y GPT. El entrenamiento en Ascend 910B demuestra que China puede producir modelos frontier sin dependencia de hardware estadounidense.

#### GLM-5.1
- **Fecha de publicación:** Mayo 2026
- **Arquitectura:** Derivada de GLM-5
- **Contexto:** 203K tokens
- **Licencia:** MIT
- **Arena ELO:** 1471 (#19 global, #2 chino después de ERNIE 5.1)
- **Benchmarks:** SWE-bench Pro 58.4%, AIME 2024 95.3%, GPQA 86.2%, Terminal-Bench 63.5%
- **Notas:** GLM-5.1 es el modelo más popular de Zhipu en LMSYS Arena. AIME 95.3% — competitivo con los mejores. SWE-bench Pro 58.4% — sólido para tareas de ingeniería de software.

#### GLM-5 Air
- **Precio:** $0.30/$0.90 por millón de tokens
- **Arena ELO:** 1418
- **Notas:** Versión ligera y económica de GLM-5, posicionada para despliegue masivo.

---

### 10. Baidu / ERNIE (China)

Baidu ha logrado con ERNIE 5.1 la posición más alta para un modelo chino en LMSYS Arena (1473, #13 global). La compañía emplea una innovadora técnica de entrenamiento "Once-for-All" que permite elasticidad en el despliegue.

#### ERNIE 5.0
- **Fecha de publicación:** 22 de enero de 2026
- **Arquitectura:** 2.4T MoE (2.4 billones de parámetros)
- **Capacidad:** Nativo multimodal
- **Arena:** #8 en ese momento (aproximadamente 1460 ELO)
- **Notas:** ERNIE 5.0 fue el modelo más grande jamás entrenado por Baidu. 2.4T parámetros — compite con GPT-5.5 en escala.

#### ERNIE 5.1
- **Fecha de publicación:** 8 de mayo de 2026
- **Arquitectura:** ~800B MoE (reducción significativa respecto a 5.0, pero más eficiente)
- **Contexto:** 128K tokens
- **Metodología de entrenamiento:** **Once-for-All (OFA) elastic training** — entrenamiento elástico que permite ajustar el tamaño del modelo en tiempo de inferencia sin reentrenar
- **Arena ELO:** 1473 (#13 global, **#1 chino**)
- **Precio:** $0.59/$2.65 por millón de tokens
- **Notas:** ERNIE 5.1 es el modelo chino mejor clasificado en LMSYS Arena. La técnica OFA permite desplegar el mismo modelo a diferentes velocidades/precisión según las necesidades. El precio ($0.59/$2.65) es extremadamente competitivo.

---

### 11. Moonshot AI / Kimi (China)

Moonshot AI, creadora de Kimi, ha logrado hitos notables: Kimi K2.6 tiene la puntuación más alta en HLE (54.0%), superando a todos los modelos occidentales, y puede realizar sesiones de codificación autónoma de 13 horas.

#### Kimi K2
- **Fecha de publicación:** 3 de julio de 2025
- **Arquitectura:** MoE de 1.04T (32B activos) + **MLA (Multi-head Latent Attention)**
- **Contexto:** 128K tokens
- **Notas:** Primer modelo frontier de Moonshot. MLA permite procesamiento eficiente de contextos largos.

#### Kimi K2.5
- **Fecha de publicación:** 30 de enero de 2026
- **Arquitectura:** MoE de 1T (32B activos)
- **Contexto:** 256K tokens
- **Licencia:** Modified MIT (permisiva pero con restricciones menores)
- **Benchmarks:** GPQA 87.6%, AIME 2024 96.1%, SWE-bench 76.8%, HLE 30.1%
- **Notas:** AIME 96.1% — rendimiento de élite en matemáticas. HLE 30.1% — base sólida para tareas extremadamente difíciles.

#### Kimi K2.6
- **Fecha de publicación:** 21 de abril de 2026
- **Arquitectura:** MoE de 1T (32B activos)
- **Contexto:** 262K tokens
- **Benchmarks:**
  - GPQA: 90.5%
  - SWE-bench: 80.2% (58.6% Pro)
  - **HLE: 54.0% (#1 global)** — supera a todos los modelos occidentales
  - AIME 2024: 96.4%
- **Precio:** $0.60/M input
- **Capacidad distintiva:** Codificación autónoma de hasta **13 horas** sin intervención humana
- **Notas:** Kimi K2.6 es el líder indiscutible en HLE (Humanity's Last Exam), el benchmark más difícil existente. 54.0% supera a Claude Mythos (est.) y Gemini 3.1 Pro (51.4%). La capacidad de codificación autónoma de 13 horas sugiere que Moonshot ha resuelto problemas de consistencia a largo plazo en agentes de código.

---

### 12. ByteDance / Doubao (China)

ByteDance (matriz de TikTok) ha incursionado en IA con la familia Seed. Seed 2.0 supera a GPT-5.2 en SuperGPQA, un logro significativo para un modelo chino relativamente nuevo en el campo.

#### Seed 2.0
- **Fecha de publicación:** 14 de febrero de 2026
- **Contexto:** 256K tokens
- **Benchmark:** **SuperGPQA > GPT-5.2** (supera al modelo de OpenAI en este benchmark específico)
- **Notas:** SuperGPQA es una versión extendida de GPQA con preguntas aún más difíciles. Seed 2.0 superar a GPT-5.2 en esta métrica sugiere capacidades de razonamiento científico profundo.

#### Seed 1.6 Flash
- **Precio:** Desde $0.022/M output (extremadamente barato)
- **Notas:** Versión eficiente de Seed para despliegue a escala. Precios casi simbólicos para output.

---

### 13. MiniMax (China)

MiniMax ha apostado por innovación arquitectónica (Lightning Attention de complejidad lineal) y contextos masivos (4M tokens).

#### MiniMax-01
- **Arquitectura:** 456B parámetros totales (45.9B activos) + **Lightning Attention** (mecanismo de atención de complejidad lineal O(n))
- **Contexto:** **4M tokens** — el segundo contexto más largo del mercado (después de Llama 4 Scout con 10M)
- **Licencia:** Open-source
- **Notas:** Lightning Attention elimina la barrera cuadrática del transformer estándar, permitiendo procesar 4M tokens con recursos manejables. La arquitectura es particularmente adecuada para análisis de documentos ultra-largos.

#### MiniMax M2.5
- **Fecha de publicación:** Febrero 2026
- **Arquitectura:** MoE agent-native (diseñado para tareas de agencia)
- **Notas:** Competitivo con DeepSeek en benchmarks. Diseñado específicamente para aplicaciones agentic, sugiriendo optimizaciones en planificación, uso de herramientas y ejecución multi-paso.

---

### 14. Stepfun (China)

Stepfun ha logrado con Step-3.5-Flash lo que parecía imposible: el AIME más alto del mundo (97.3%) con solo 11B parámetros activos, estableciendo un récord de "intelligence density".

#### Step-3.5-Flash
- **Fecha de publicación:** 30 de enero de 2026
- **Arquitectura:** MoE de 196B parámetros totales (**11B activos**)
- **Contexto:** 256K tokens
- **Licencia:** Open-source
- **Benchmarks:**
  - **AIME 2024: 97.3%** — el puntaje AIME más alto registrado (supera a GPT-5.2 100% pero con AIME 2024, no 2025)
  - **3.4x más eficiente que DeepSeek V3.2** en términos de parámetros activos por unidad de rendimiento
- **Notas:** Step-3.5-Flash redefine el concepto de eficiencia. Con 11B parámetros activos (0.7% de los 1.6T de DeepSeek-V4 Pro), logra puntuaciones competitivas o superiores en matemáticas. La "intelligence density" — rendimiento por parámetro activo — es la más alta del mercado.

---

### 15. 01.AI / Yi (China)

Fundada por Kai-Fu Lee, 01.AI desarrolla la serie Yi de modelos. Información detallada de benchmarks no está disponible en las fuentes actuales, pero la compañía mantiene presencia en el ecosistema chino de IA.

---

### 16. Xiaomi / MiMo (China)

Xiaomi ha entrado agresivamente en el mercado de IA con MiMo V2.5 Pro, un modelo multimodal nativo con 1.02T parámetros MoE y licencia Apache 2.0.

#### MiMo V2.5 Pro
- **Fecha de publicación:** 22 de abril de 2026
- **Arquitectura:** MoE de 1.02T parámetros totales (42B activos)
- **Contexto:** 1M tokens
- **Licencia:** Apache 2.0
- **Capacidad:** Multimodal nativa — texto + imagen + video + audio
- **Arena ELO:** 1465 (comparable con Claude Sonnet 4.6 y GPT-5.4)
- **Notas:** Xiaomi ha logrado en menos de un año lo que otros laboratorios construyeron en años. 1M de contexto, multimodal nativo, Apache 2.0. Un actor a seguir de cerca.

---

### 17. Huawei / Pangu (China)

Huawei desarrolla la serie Pangu, entrenada íntegramente en hardware doméstico Ascend NPU. Pangu Ultra, con 135B densos y 94 capas, demuestra que China puede producir modelos competitivos sin GPUs NVIDIA.

#### Pangu Ultra
- **Arquitectura:** 135B parámetros densos con 94 capas transformer (arquitectura inusualmente profunda)
- **Contexto:** 128K tokens
- **Hardware:** Ascend NPUs (100% doméstico, cero dependencia NVIDIA)
- **Variante adicional:** Versión MoE de 718B parámetros
- **Notas:** Los 94 layers del modelo denso sugieren una arquitectión optimizada para profundidad en lugar de anchura, probablemente para maximizar el rendimiento en hardware Ascend. La variante MoE de 718B compite directamente con modelos frontier occidentales.

---

### 18. Tencent / Hunyuan (China)

Tencent contribuye al ecosistema open-source con Hunyuan Hy3, un modelo MoE de 295B parámetros con licencia abierta.

#### Hunyuan Hy3
- **Arquitectura:** MoE de 295B parámetros totales (21B activos)
- **Contexto:** 256K tokens
- **Licencia:** Open-source
- **Benchmarks:** GSM8K 95.37%, SWE-bench 74.4%
- **Notas:** GSM8K 95.37% — rendimiento sólido en razonamiento matemático. SWE-bench 74.4% — competitivo con Claude Sonnet 4.6 (79.6%) considerando que es open-source.

---

### 19. SenseTime (China)

SenseTime, conocida por su trabajo en visión por computadora, ha lanzado SenseNova U1 con una arquitectura innovadora que prescinde de encoder visual.

#### SenseNova U1
- **Fecha de publicación:** 29 de abril de 2026
- **Arquitectura:** **NEO-Unify** — no utiliza encoder visual separado
- **Licencia:** Open-source
- **Notas:** La arquitectura NEO-Unify integra la comprensión visual directamente en el transformer principal, eliminando la necesidad de un encoder visual separado (como CLIP o ViT). Esto podría simplificar el pipeline multimodal y reducir costos de inferencia.

---

### 20. Mistral AI (Francia / Europa)

Mistral AI es el laboratorio europeo más importante, conocido por sus modelos abiertos (licencia Apache 2.0) y su eficiencia arquitectónica. Mistral Large 3 (675B MoE, 41B activos) compite directamente con modelos frontier a precios significativamente más bajos ($0.50/$1.50).

#### Mistral Large 3
- **Fecha de publicación:** 2 de diciembre de 2025
- **Arquitectura:** MoE de 675B parámetros totales (41B activos)
- **Contexto:** 256K tokens
- **Licencia:** Apache 2.0
- **Precio:** $0.50/$1.50 por millón de tokens
- **Benchmarks:**
  - MMMLU: 85.5%
  - HumanEval: 92%
  - MATH-500: 93.6%
  - GPQA: 43.9% (significativamente bajo — posiblemente falta de razonamiento profundo)
  - Arena: 1418-1421
- **Notas:** Mistral Large 3 destaca por su eficiencia (41B activos de 675B totales) y licencia Apache 2.0. Sin embargo, GPQA 43.9% es inusualmente bajo, posiblemente porque Mistral Large 3 **no tiene modo de razonamiento (thinking mode)** — una omisión que lo deja en desventaja frente a competidores que sí lo tienen. MATH-500 93.6% y HumanEval 92% muestran fortaleza en matemáticas y código.

#### Mistral Small 3.2
- **Precio:** $0.10/$0.30 por millón de tokens
- **Contexto:** 128K tokens
- **Notas:** Modelo ligero para despliegue económico.

#### Mistral Medium 3.5
- **Fecha de publicación:** Abril 2026
- **Benchmarks:** SWE-bench 77.6%
- **Licencia:** Abierta
- **Notas:** Modelo de gama media con SWE-bench sorprendentemente alto (comparable con Claude Sonnet 4.6). Representa la incursión de Mistral en el espacio de modelos de código.

#### Codestral
- **Especialización:** Modelo de código
- **Notas:** Competidor directo de GPT-5.3 Codex, CodeLlama y DeepSeek-Coder-V2.

#### Mathstral 7B
- **Especialización:** Matemáticas
- **Tamaño:** 7B parámetros
- **Benchmarks:** MATH 57.8%
- **Notas:** Modelo pequeño especializado en matemáticas. MATH 57.8% para 7B es respetable pero superado por modelos chinos como rStar-Math.

#### Ministral 8B / 3B
- **Especialización:** Edge deployment / dispositivos móviles
- **Notas:** Modelos ultra-ligeros para inferencia en dispositivo.

---

### 21. Aleph Alpha (Alemania)

Aleph Alpha, con sede en Heidelberg, fue pionera en IA europea pero ha pivotado de modelos fundacionales a una plataforma empresarial.

#### Serie Luminous
- **Modelos:** Luminous Extended (13B), Luminous Performance (70B), Luminous Supreme (300B)
- **Licencia:** Propietaria
- **Notas:** Los modelos Luminous fueron de los primeros modelos europeos a gran escala, pero han sido superados por Mistral en rendimiento y adopción.

#### PhariaAI
- **Estrategia actual:** Aleph Alpha se ha reposicionado como plataforma empresarial (PhariaAI), abandonando el desarrollo de modelos fundacionales propios.
- **Modelo abierto:** Pharia-1-LLM-7B (7B parámetros, licencia abierta)
- **Notas:** El pivote hacia plataforma empresarial refleja la dificultad de competir con laboratorios estadounidenses y chinos en modelos frontier.

---

### 22. DeepL (Alemania)

DeepL domina el nicho de traducción automática con modelos transformer propietarios.

- **Cobertura:** 33 idiomas
- **Innovación:** 1.7x mejora en calidad respecto al modelo transformer clásico
- **Arquitectura:** Transformer propietario (no público)
- **Notas:** DeepL no compite en el espacio de LLMs generales, sino que se centra exclusivamente en traducción de alta calidad. Su modelo propietario supera significativamente a Google Translate y GPT-4/5 en tareas de traducción.

---

### 23. Helsing (Alemania)

Helsing es una empresa de defensa y seguridad que desarrolla IA para aplicaciones militares. No produce LLMs generales.

#### Proyectos:
- **HX-2:** Drone de combate con IA embarcada
- **Centaur:** IA para combate aéreo (piloto automático de cazas)
- **Lura:** Sistema de detección submarina (sonar + IA)
- **Notas:** Helsing representa la aplicación de IA a defensa, no al desarrollo de modelos de lenguaje. Incluido en este catálogo por completitud del ecosistema europeo.

---

### 24. LightOn (Francia)

LightOn desarrolla modelos especializados en OCR y visión, junto con la plataforma Paradigm.

#### Alfred-32B-VL
- **Tamaño:** 32B parámetros
- **Capacidad:** Visión-Lenguaje (VL)
- **Notas:** Modelo multimodal francés que compite en el segmento VL.

#### LightOnOCR-2-1B
- **Tamaño:** 1B parámetros
- **Benchmark:** **#1 en OCR** — el mejor modelo de reconocimiento óptico de caracteres
- **Notas:** LightOn domina el nicho de OCR con este modelo pequeño pero altamente especializado.

#### OriOn
- **Contexto:** 344K tokens
- **Notas:** Modelo con capacidad de contexto largo, posiblemente para procesamiento de documentos.

#### Paradigma / Paradigm Platform
- **Notas:** Plataforma de IA empresarial de LightOn, similar a PhariaAI de Aleph Alpha.

---

### 25. Silo AI (Finlandia)

Silo AI, ahora parte del grupo Silo, desarrolla modelos para lenguas nórdicas y europeas.

#### Poro
- **Tamaño:** 34B parámetros
- **Especialización:** Lenguas nórdicas (finés, sueco, noruego, danés, islandés)
- **Licencia:** Apache 2.0
- **Infraestructura:** Entrenado en supercomputadora LUMI (AMD, Finlandia)
- **Notas:** Poro es el modelo más importante para lenguas nórdicas. Apache 2.0 permite uso comercial y fine-tuning.

#### Viking
- **Tamaño:** 33B parámetros
- **Especialización:** Modelo multilingüe para lenguas europeas
- **Licencia:** Apache 2.0
- **Infraestructura:** LUMI supercomputer (AMD)
- **Notas:** Viking complementa a Poro con cobertura más amplia de lenguas europeas.

---

### 26. NVIDIA (EE.UU.)

NVIDIA ha desarrollado modelos propios (Nemotron) que aprovechan su experiencia en hardware y arquitecturas eficientes.

#### Nemotron 3 Nano
- **Tamaño:** 31.6B parámetros totales (3.2-3.6B activos)
- **Arquitectura:** **Hybrid Mamba-2 + Transformer MoE** — combina Mamba (estado-espacio) con atención transformer tradicional
- **Contexto:** 1M tokens
- **Licencia:** NVIDIA Open Model License
- **Arena ELO:** 1428
- **Notas:** Nemotron 3 Nano es un ejemplo de eficiencia extrema: 3.2B activos de 31.6B totales. La arquitectura híbrida Mamba-2 + Transformer representa una tendencia creciente hacia modelos que combinan atención state-space con atención clásica.

#### Nemotron Nano 2 (9B v2)
- **Tamaño:** 9B parámetros
- **Arquitectura:** Hybrid Mamba-2 + Transformer
- **Contexto:** 128K tokens
- **Característica:** Reasoning toggle — permite activar/desactivar razonamiento según la tarea
- **Notas:** Versión mejorada del Nano original con capacidad de razonamiento configurable. Ideal para GPU NVIDIA locales.

#### NV-Embed-v2
- **Especialización:** Embeddings
- **Dimensiones:** 4096d
- **Benchmark MTEB:** 62.65
- **Notas:** Modelo de embeddings competitivo con text-embedding-3-large (64.6) y BGE-en-ICL (67.8).

---

### 27. Apple (EE.UU.)

Apple ha incursionado en IA con modelos locales para sus dispositivos, aunque no compite directamente en el espacio de modelos frontier.

- **Estrategia:** Modelos pequeños y eficientes para inferencia en dispositivo (iPhone, iPad, Mac)
- **Enfoque:** Privacidad (procesamiento local), eficiencia energética, integración con sistema operativo
- **Notas:** Apple no ha lanzado modelos frontier comparables a GPT-5.5 o Claude Opus 4.7. Su fortaleza está en la integración vertical hardware-software-IA.

---

### 28. Amazon (EE.UU.)

Amazon ha desarrollado modelos a través de Amazon Web Services (AWS) y su plataforma Bedrock, aunque su presencia en benchmarks públicos es limitada.

- **Estrategia:** Proveedor de infraestructura (Bedrock, SageMaker) más que desarrollador de modelos frontier propios
- **Modelo propio:** Amazon Nova (familia de modelos multimodales)
- **Notas:** Amazon se beneficia del ecosistema de IA ofreciendo acceso a modelos de Anthropic, Meta, Mistral y otros a través de Bedrock, más que compitiendo directamente con modelos propios.

---

### 29. LAION (Alemania)

LAION (Large-scale Artificial Intelligence Open Network) es una organización sin fines de lucro alemana que desarrolla datasets y modelos abiertos.

- **Contribuciones:** LAION-5B (dataset de imágenes), Open Assistant, modelos de código abierto
- **Enfoque:** Investigación abierta, datasets masivos, democratización de IA
- **Notas:** LAION no produce modelos frontier, pero sus datasets (LAION-5B, LAION-COCO) son fundamentales para el entrenamiento de modelos de imágenes como Stable Diffusion.

---

## Modelos Especializados

---

### Modelos de Código

| Modelo | Laboratorio | Params | Benchmark Clave | Licencia |
|--------|-------------|--------|----------------|----------|
| GPT-5.3 Codex | OpenAI | — | SWE-bench Pro 56.8%, Terminal-Bench 77.3%, OSWorld 64.7% | Propietaria |
| DeepSeek-Coder-V2 | DeepSeek | 236B (21B act.) | HumanEval 90.2% | MIT |
| Codestral | Mistral | — | — | Apache 2.0 |
| CodeLlama | Meta | 7B-34B | — | Llama 2 Community |
| StarCoder2 | BigCode | 3B-15B | — | Apache 2.0 |
| CodeQwen | Alibaba | — | — | Apache 2.0 |
| Qwen2.5-Coder | Alibaba | — | — | Apache 2.0 |
| Qwen3-Coder-Next | Alibaba | — | SWE-bench 70.6-71.3% | Apache 2.0 |
| CodeGemma | Google | — | — | Apache 2.0 |

**Análisis:** El dominio del código se ha fragmentado. GPT-5.3 Codex lidera en benchmarks agentic (Terminal-Bench, OSWorld), mientras que DeepSeek-Coder-V2 sobresale en generación de código puro (HumanEval 90.2%). Qwen3-Coder-Next ofrece la mejor opción open-source (SWE-bench 70.6-71.3% con Apache 2.0). Codestral de Mistral es un contendiente open-source adicional.

---

### Modelos de Matemáticas

| Modelo | Laboratorio | Params | Benchmark Clave | Licencia |
|--------|-------------|--------|----------------|----------|
| Mathstral 7B | Mistral | 7B | MATH 57.8% | Apache 2.0 |
| DeepSeek-Math 7B (RL) | DeepSeek | 7B | MATH ~90% (est.) | MIT |
| Qwen2.5-Math-72B-Instruct | Alibaba | 72B | — | Apache 2.0 |
| rStar-Math (7B) | — | 7B | MATH 90%, AIME 53.3% | — |
| Step-3.5-Flash | Stepfun | 196B (11B act.) | AIME 97.3% | Open-source |
| GPT-5.2 | OpenAI | — | AIME 100% | Propietaria |
| Claude Opus 4.7 | Anthropic | — | GPQA 94.2% | Propietaria |
| Gemini 3 Pro | Google | MoE | AIME 95% (100% con código) | Propietaria |

**Análisis:** El liderazgo en matemáticas está disputado. Step-3.5-Flash tiene el AIME más alto entre modelos abiertos (97.3%) con solo 11B activos. GPT-5.2 logró AIME perfecto (100%). Qwen2.5-Math-72B-Instruct es la mejor opción open-source para matemáticas generales.

---

### Modelos de Razonamiento

| Modelo | Laboratorio | Arquitectura | Benchmark Razonamiento | Licencia |
|--------|-------------|-------------|----------------------|----------|
| o1 | OpenAI | Thinking chain | AIME 74.3%, GPQA 78% | Propietaria |
| o3 | OpenAI | Thinking chain | AIME 96.7%, ARC-AGI 87.5% | Propietaria |
| o4-mini | OpenAI | Thinking chain | AIME 93.4%, HumanEval 97.5% | Propietaria |
| DeepSeek-R1 | DeepSeek | RL + Chain-of-Thought | AIME 79.8%, MATH-500 97.3% | MIT |
| QwQ-32B | Alibaba | Thinking dual-mode | — | Apache 2.0 |
| Kimi K2 Thinking | Moonshot | Thinking mode | — | Modified MIT |
| Claude 3.7 Sonnet Thinking | Anthropic | Hybrid reasoning | GPQA 84.8% thinking | Propietaria |
| Gemini Thinking | Google | Deep Think | ARC-AGI-2 77.1% | Propietaria |
| Qwen3 Thinking mode | Alibaba | Dual-mode | — | Apache 2.0 |

**Análisis:** El razonamiento se ha convertido en una capacidad estándar. DeepSeek-R1 (MIT) democratizó el razonamiento de nivel frontier con licencia abierta. o3 sigue siendo el rey del razonamiento puro (Codeforces 2727). QwQ-32B (Apache 2.0) es la mejor opción abierta para razonamiento general.

---

### Modelos Multimodales / Visión

| Modelo | Laboratorio | Params | Benchmark | Licencia |
|--------|-------------|--------|-----------|----------|
| GPT-4V | OpenAI | — | — | Propietaria |
| GPT-5.5 (omnimodal) | OpenAI | — | MMLU 92.4% | Propietaria |
| Claude 3.5 Vision | Anthropic | — | — | Propietaria |
| Claude Opus 4.7 (2576px) | Anthropic | — | CharXiv 82.1% | Propietaria |
| Gemini Pro Vision | Google | MoE | — | Propietaria |
| Qwen2.5-VL 72B | Alibaba | 72B | — | Apache 2.0 |
| Qwen3-VL | Alibaba | — | — | Apache 2.0 |
| Llama 4 Maverick/Scout Vision | Meta | 17B act. | — | Open-weight |
| DeepSeek-VL2 27B | DeepSeek | 27B | — | MIT |
| Janus-Pro-7B | DeepSeek | 7B | — | MIT |
| MiniCPM-V 4.5 8B | OpenBMB | 8B | OpenCompass 77.0 (supera GPT-4o) | — |
| Phi-4-multimodal | Microsoft | — | — | — |
| SmolVLM 2.2B | HuggingFace | 2.2B | — | Apache 2.0 |
| Alfred-32B-VL | LightOn | 32B | — | — |
| SenseNova U1 (NEO-Unify) | SenseTime | — | — | Open-source |

**Análisis:** MiniCPM-V 4.5 8B es notable por superar a GPT-4o en OpenCompass (77.0) con solo 8B parámetros. Claude Opus 4.7 ofrece la resolución de visión más alta (2576px). SenseNova U1 introduce la innovadora arquitectura NEO-Unify sin encoder visual.

---

### Modelos de Embedding

| Modelo | Laboratorio | Dimensiones | MTEB Score | Precio /M tokens | Contexto Máximo |
|--------|-------------|------------|-----------|-----------------|-----------------|
| text-embedding-3-large | OpenAI | 3072 | 64.6 | $0.13 | — |
| text-embedding-3-small | OpenAI | 1536 | 64.2 | $0.02 | — |
| Gemini Embedding | Google | 3072 | 67.71 | — | — |
| NV-Embed-v2 | NVIDIA | 4096 | 62.65 | — | — |
| BGE-en-ICL | BAAI | 4096 | 67.8 | — | — |
| **GTE-Qwen2-7B** | Alibaba | 3584 | **71.5** | — | **131K** |
| voyage-3.1-large | Voyage AI | 2048 | 67.4 | $0.05 | — |
| Jina Embeddings v4 | Jina AI | 1024 | 66.81 | — | — |
| Cohere Embed v4 | Cohere | 256-1536 | 65.2 | $0.12 | — |
| E5-mistral-7b | Microsoft | 4096 | 66.6 | — | — |
| mxbai-embed-large-v1 | Mixedbread | 1024 | 64.7 | — | — |

**Análisis:** GTE-Qwen2-7B de Alibaba domina el mercado de embeddings con MTEB 71.5 y soporte de contexto de 131K tokens — el más largo entre modelos de embedding. BGE-en-ICL (67.8) y Gemini Embedding (67.71) son alternativas sólidas. text-embedding-3-small ($0.02/M) es la opción más económica para aplicaciones sensibles al costo.

---

### Modelos de Voz / Audio

| Modelo | Laboratorio | Params | Lenguas | Benchmark | Licencia |
|--------|-------------|--------|---------|-----------|----------|
| Whisper large-v3 | OpenAI | 1.55B | 96 | WER 8.11% | MIT |
| Whisper turbo | OpenAI | 809M | 96 | 8x más rápido que large-v3 | MIT |
| Canary-1B | NVIDIA | 1B | — | WER supera a Whisper | — |
| Parakeet-TDT | NVIDIA | 0.6B | — | 239x tiempo real | — |
| SeamlessM4T-v2 | Meta | — | 100+ | Speech-to-speech | MIT |
| Gemma 4 E4B | Google | — | — | Audio nativo | Apache 2.0 |

**Análisis:** Whisper large-v3 sigue siendo el estándar de facto para ASR (WER 8.11%, 96 lenguas). Parakeet-TDT ofrece la inferencia más rápida (239x tiempo real). Canary-1B de NVIDIA supera a Whisper en WER. SeamlessM4T-v2 de Meta permite traducción speech-to-speech en 100+ lenguas.

---

### Modelos de Generación de Imágenes

| Modelo | Laboratorio | Arquitectura | ELO Arena | Licencia |
|--------|-------------|-------------|-----------|----------|
| FLUX.2 Pro | Black Forest Labs | 12B DiT | **1265** | Propietaria |
| gpt-image-1 | OpenAI | — | 1264 | Propietaria |
| FLUX.1 Dev | Black Forest Labs | 12B DiT | — | — |
| FLUX.1 Schnell | Black Forest Labs | 12B DiT | — | Apache 2.0 |
| FLUX.1 Pro | Black Forest Labs | 12B DiT | — | Propietaria |
| Stable Diffusion 3.5 Large | Stability AI | 8.1B MMDiT | — | — |
| Midjourney v7 | Midjourney | — | ~1240 | Propietaria |
| DALL-E 3 | OpenAI | — | 1200 | Propietaria |
| Imagen 4 Ultra | Google | — | — | Propietaria |

**Análisis:** FLUX.2 Pro (1265 ELO) y gpt-image-1 (1264 ELO) están prácticamente empatados en el liderazgo. FLUX.1 Schnell, con licencia Apache 2.0, es la mejor opción open-source para generación de imágenes. Stable Diffusion 3.5 Large (8.1B MMDiT) compite en el segmento abierto.

---

### Modelos de Generación de Video

| Modelo | Laboratorio | Capacidad Máxima | Notas |
|--------|-------------|-----------------|-------|
| Sora 2 | OpenAI | — | En proceso de cierre |
| Runway Gen-4 | Runway | — | Generación de video profesional |
| Pika 2.2 | Pika Labs | — | Generación de video creativo |
| Kling 2.1 | Kuaishou | **2 minutos** | Video más largo del mercado |
| Vidu 2.0 | Shengshu | — | Competidor chino |
| Veo 3 | Google | — | Modelo de video de Google |

**Análisis:** Kling 2.1 lidera en duración de video (2 minutos). Sora 2 de OpenAI está en proceso de cierre, lo que deja un vacío en el mercado. Veo 3 de Google es el principal competidor empresarial.

---

### Modelos de Música

| Modelo | Laboratorio | Capacidad Máxima | Notas |
|--------|-------------|-----------------|-------|
| MusicGen | Meta | 1.5B / 3.3B | Modelo abierto de generación musical |
| Suno v4.5 | Suno | **8 minutos** | Generación de música con letra |
| Udio v1.5 | Udio | — | Generación musical de alta calidad |

**Análisis:** Suno v4.5 lidera en duración (8 minutos) y calidad de letra. MusicGen de Meta es la opción open-source. Udio v1.5 compite en calidad musical.

---

## Benchmarks: Todos los Scores

### Matriz Completa Modelo x Benchmark

| Modelo | MMLU | GPQA | AIME | SWE-bench | HLE | HumanEval | MATH-500 | MMMLU | ARC-AGI-2 | Arena ELO |
|--------|------|------|------|-----------|-----|-----------|----------|-------|-----------|-----------|
| **Claude Opus 4.7** | — | **94.2%** | — | **87.6%** | — | — | — | 91.5% | — | 1501 |
| **Claude Opus 4.6** | — | 91.3% | — | 80.8% | — | — | — | 91.1% | 68.8% | 1502 |
| **Claude Mythos** | — | 94.6% | — | 93.9% | — | — | — | — | — | — |
| **Gemini 3.1 Pro** | — | 94.3% | — | 80.6% | 51.4% | — | — | 92.6% | **77.1%** | 1490 |
| **Gemini 3 Pro** | 91.8% | 91.9% | 95% | 76.2% | 37.5% | — | — | — | 31.1% | 1486 |
| **Gemini 3 Flash** | — | 90.4% | 99.7% | 78% | — | — | — | — | — | 1474 |
| **GPT-5.5** | 92.4% | — | — | 88.7% | — | — | — | — | — | 1476 |
| **GPT-5.4** | — | — | — | ~80% | — | — | — | — | — | 1467 |
| **GPT-5.2** | — | 92.4% | **100%** | 80% | — | — | — | — | 52.9% | 1477 |
| **GPT-5.1** | — | 88.1% | 94% | 76.3% | — | — | — | 89.5% | — | — |
| **GPT-5** | — | — | 94.6% | 74.9% | — | — | — | — | — | — |
| **o3** | — | 87.7% | 96.7% | — | — | — | — | — | 87.5% | — |
| **o1** | 92.3% | 78% | 74.3% | — | — | — | — | — | — | — |
| **DeepSeek-V4 Pro** | — | 90.1% | 95.2% | 80.6% | 37.7% | — | — | — | — | — |
| **DeepSeek-V4 Flash** | — | 88.1% | — | 79.0% | — | — | — | — | — | — |
| **DeepSeek-R1** | 90.8% | 71.5% | 79.8% | 49.2% | — | — | 97.3% | — | — | — |
| **DeepSeek-V3** | 88.5% | — | — | — | — | 82.6% | — | — | — | — |
| **Qwen3.7-Max** | — | 92.4% | — | 80.4% | 41.4% | — | — | — | — | — |
| **Qwen3.6** | — | 87.8% | 94.1% | 77.2% | — | — | — | — | — | — |
| **Qwen3.5** | — | 81.0% | 91.3% | 76.4% | — | — | — | — | — | — |
| **Kimi K2.6** | — | 90.5% | 96.4% | 80.2% | **54.0%** | — | — | — | — | — |
| **Kimi K2.5** | — | 87.6% | 96.1% | 76.8% | 30.1% | — | — | — | — | — |
| **GLM-5.1** | — | 86.2% | 95.3% | 77.8% | — | — | — | — | — | — |
| **GLM-5** | — | 86.0% | 92.7% | 77.8% | — | — | — | — | — | — |
| **ERNIE 5.1** | — | — | — | — | — | — | — | — | — | 1473 |
| **Grok 4.20** | 86.6% | 88% | — | — | 24.5% | — | — | — | — | 1479 |
| **Mistral Large 3** | — | 43.9% | — | — | — | 92% | 93.6% | 85.5% | — | 1418 |
| **Claude Opus 4** | — | 74.9% | — | 72.5% | — | — | — | — | — | — |
| **Claude 3.7 Sonnet** | — | 62.1% | 73.6% | 62.3% | — | — | — | — | — | — |
| **Gemini 2.5 Pro** | — | 84.4% | 88% | 59.6% | — | — | — | — | — | 1470 |
| **Step-3.5-Flash** | — | — | 97.3% | — | — | — | — | — | — | — |

---

## Análisis de Especialización

### Mejor modelo para CÓDIGO

**Ganador Absoluto: Claude Mythos Preview** — SWE-bench Verified 93.9%, SWE-bench Pro 77.8%

**Recomendación práctica:**
- **Uso general (SWE-bench):** Claude Opus 4.7 (87.6%) o GPT-5.5 (88.7%)
- **Terminal / scripts:** GPT-5.3 Codex (Terminal-Bench 77.3%)
- **Open-source:** DeepSeek-Coder-V2 (HumanEval 90.2%) o Qwen3-Coder-Next (SWE-bench 71.3%)
- **Costo-beneficio:** DeepSeek-V4 Flash ($0.0028/$0.14) con SWE-bench 79.0%
- **Agentes de código autónomos:** Kimi K2.6 (13 horas de codificación autónoma)

### Mejor modelo para MATEMÁTICAS

**Ganador Absoluto: GPT-5.2** — AIME 2024 100% (perfecto)

**Recomendación práctica:**
- **Open-source:** Step-3.5-Flash (AIME 97.3%, 11B activos)
- **Matemáticas generales:** DeepSeek-V4 Pro (AIME 95.2%)
- **Matemáticas de competencia (USAMO):** Claude Mythos (97.6% en USAMO 2026)
- **Razonamiento matemático con código:** Gemini 3 Pro (AIME 95% / 100% con código)
- **Modelo pequeño especializado:** rStar-Math 7B (MATH 90%, AIME 53.3%)

### Mejor modelo para RAZONAMIENTO

**Ganador Absoluto: Gemini 3.1 Pro Preview** — ARC-AGI-2 77.1%, HLE 51.4%

**Recomendación práctica:**
- **Razonamiento científico (GPQA):** Claude Opus 4.7 (94.2%) o Claude Mythos (94.6%)
- **Razonamiento abstracto (ARC-AGI-2):** Gemini 3.1 Pro (77.1%)
- **Razonamiento extremo (HLE):** Kimi K2.6 (54.0%)
- **Razonamiento transparente (open-source):** DeepSeek-R1 (MIT)
- **Codeforces / programación competitiva:** o3 (2727 rating)

### Mejor modelo para VISIÓN

**Ganador Absoluto: Claude Opus 4.7** — 2576px de resolución, CharXiv 82.1%

**Recomendación práctica:**
- **Comprensión visual general:** GPT-5.5 (omnimodal nativo)
- **Open-source:** Qwen2.5-VL 72B o MiniCPM-V 4.5 8B (supera GPT-4o en OpenCompass 77.0)
- **OCR:** LightOnOCR-2-1B (#1 en OCR)
- **Sin encoder visual (innovación):** SenseNova U1 (NEO-Unify)

### Mejor modelo para LENGUAJE NATURAL

**Ganador Absoluto: Claude Opus 4.6 Thinking** — Arena ELO 1502 (#1)

**Recomendación práctica:**
- **Conversación general:** Claude Sonnet 4.6 (1467 ELO, $3/$15)
- **Escritura creativa:** Claude Opus 4.6 Thinking (1502 ELO)
- **Multilingüe (201 idiomas):** Qwen3.5 (Apache 2.0)
- **Traducción:** DeepL (33 idiomas, 1.7x mejora respecto a transformer clásico)
- **Costo ultra-bajo:** DeepSeek-V4 Flash ($0.0028/M input)

### Mejor modelo CALIDAD/PRECIO

**Ganador Absoluto: DeepSeek-V4 Flash** — $0.0028/$0.14 (promocional), GPQA 88.1%, SWE-bench 79.0%

**Recomendaciones por rango de precio:**
- **Ultra-budget (< $0.50/M input):** DeepSeek-V4 Flash ($0.0028), GLM-5 Air ($0.30)
- **Budget ($0.50-$1/M input):** Gemini 3 Flash ($0.50), Mistral Large 3 ($0.50), ERNIE 5.1 ($0.59)
- **Mid-range ($1-$3/M input):** Gemini 3 Pro ($2), Qwen3.7-Max ($0.83), GPT-5.4 ($2.50)
- **Premium ($3-$5/M input):** Claude Sonnet 4.6 ($3), GPT-5.5 ($5), Claude Opus 4.7 ($5)
- **Enterprise (> $5/M input):** Claude Mythos ($25), o1 legacy ($15)

### Mejor modelo OPEN-SOURCE

**Ganador Absoluto: DeepSeek-V4 Pro** — MIT License, GPQA 90.1%, SWE-bench 80.6%

**Recomendaciones por licencia:**
- **MIT:** DeepSeek-V4 Pro (GPQA 90.1%, SWE-bench 80.6%)
- **Apache 2.0:** Qwen3.7-Max (GPQA 92.4%, SWE-bench 80.4%)
- **Apache 2.0 (ligero):** Qwen3.6 (3B activos, GPQA 87.8%)
- **Open-weight:** Llama 4 Scout (10M contexto, $0.11/$0.34)
- **Sin NVIDIA (Ascend nativo):** GLM-5 (MIT, entrenado en Huawei Ascend)

### Mejor modelo para AGENTES

**Ganador Absoluto: GLM-5** — Tau2-Bench 89.7% (#1 agentic)

**Recomendación práctica:**
- **Benchmarks agentic:** GLM-5 (Tau2-Bench 89.7%)
- **Computer use (OSWorld):** GPT-5.4 (75%, supera humanos 72.4%)
- **MCP / herramientas:** Gemini 3.5 Flash (MCP Atlas 83.6%)
- **Navegación web (BrowseComp):** Gemini 3.1 Pro (85.9%)
- **Ciberseguridad (Cybench):** Claude Mythos (100%)
- **Autonomous coding (larga duración):** Kimi K2.6 (13 horas)

---

## Recomendaciones para KAOS

### Estrategia de Ruteo Multi-Modelo

KAOS debe implementar un sistema de ruteo inteligente que seleccione el modelo óptimo para cada tarea basándose en:
1. **Tipo de tarea** (código, matemáticas, razonamiento, visión, lenguaje natural)
2. **Requisitos de contexto** (longitud del input)
3. **Restricciones de costo** (presupuesto por tarea)
4. **Requisitos de licencia** (open-source vs propietario para redistribución)
5. **Latencia requerida** (tiempo real vs batch)

### Tabla de Ruteo por Tipo de Tarea

| Tipo de Tarea | Modelo Primario | Modelo Secundario | Modelo Open-Source | Costo Esperado |
|---------------|----------------|-------------------|-------------------|----------------|
| **Código general** | Claude Opus 4.7 | GPT-5.5 | DeepSeek-V4 Pro | $5-25/M |
| **Código (terminal/scripts)** | GPT-5.3 Codex | — | DeepSeek-Coder-V2 | $2.50-15/M |
| **Código (autónomo multi-hora)** | Kimi K2.6 | — | — | $0.60/M input |
| **Matemáticas** | GPT-5.2 | Gemini 3 Pro | Step-3.5-Flash | $1.75-14/M |
| **Razonamiento científico** | Claude Opus 4.7 | Gemini 3.1 Pro | DeepSeek-V4 Pro | $2-25/M |
| **Razonamiento abstracto** | Gemini 3.1 Pro | — | DeepSeek-R1 | $2-12/M |
| **Visión / imágenes** | Claude Opus 4.7 | GPT-5.5 | Qwen2.5-VL 72B | $5-25/M |
| **Lenguaje natural** | Claude Sonnet 4.6 | GPT-5.5 | Qwen3.5 | $3-15/M |
| **Traducción** | DeepL | Gemini 3 Flash | Qwen3.5 | $0.50-3/M |
| **Embeddings** | GTE-Qwen2-7B | text-embedding-3-large | GTE-Qwen2-7B | $0.02-0.13/M |
| **Audio (ASR)** | Whisper large-v3 | Canary-1B | Whisper large-v3 | — |
| **Agentes** | GLM-5 | Gemini 3.5 Flash | — | $0.30-2/M |
| **Bajo costo (< $1/M)** | DeepSeek-V4 Flash | GLM-5 Air | DeepSeek-V4 Flash | $0.0028-0.30/M |

### Modelos Recomendados por Modalidad

**Código**: Claude Opus 4.7 → GPT-5.5 → DeepSeek-V4 Pro
**Matemáticas**: GPT-5.2 → Gemini 3 Pro → Step-3.5-Flash
**Razonamiento**: Claude Opus 4.7 → Gemini 3.1 Pro → DeepSeek-R1
**Visión**: Claude Opus 4.7 → GPT-5.5 → Qwen2.5-VL 72B
**Lenguaje**: Claude Sonnet 4.6 → GPT-5.5 → Qwen3.5
**Embeddings**: GTE-Qwen2-7B → BGE-en-ICL → text-embedding-3-large
**Audio**: Whisper large-v3 → Canary-1B → SeamlessM4T-v2
**Imágenes**: FLUX.2 Pro / gpt-image-1 → FLUX.1 Schnell (open)
**Video**: Kling 2.1 → Veo 3 → Runway Gen-4
**Música**: Suno v4.5 → MusicGen (open)

### Estrategia de Costos

**Capa 1 — Ultra-Económica ($0.0028-$0.50/M input)**
Para tareas de alto volumen y baja criticidad: DeepSeek-V4 Flash, GLM-5 Air, Gemini 3 Flash

**Capa 2 — Balance ($0.50-$3/M input)**
Para tareas estándar con buena relación calidad/precio: Claude Sonnet 4.6, Gemini 3 Pro, Qwen3.7-Max, Mistral Large 3

**Capa 3 — Premium ($3-$15/M input)**
Para tareas críticas que requieren máxima calidad: Claude Opus 4.7, GPT-5.5, Gemini 3.1 Pro

**Capa 4 — Investigación ($25+/M input)**
Para tareas experimentales o de máxima exigencia: Claude Mythos Preview

### Arquitectura de Integración

KAOS debe implementar:
1. **Router inteligente** basado en clasificador de tareas (posiblemente un modelo pequeño como Qwen3.6 o Nemotron Nano 2)
2. **Caché de respuestas** para consultas repetitivas (reducir costos hasta 80%)
3. **Fallback automático**: Si el modelo primario falla o excede tiempo, degradar al secundario
4. **Monitor de costos**: Tracking en tiempo real del gasto por modelo y por tarea
5. **Logging de calidad**: Evaluación post-hoc de respuestas para ajustar el ruteo (contextual bandit feedback)

---

## Fuentes

- **LMSYS Chatbot Arena:** arena.ai — Clasificación ELO de modelos de lenguaje
- **Artificial Analysis:** artificialanalysis.ai — Análisis independiente de rendimiento y precios
- **SWE-bench:** swebench.com — Benchmark de ingeniería de software
- **HuggingFace Open LLM Leaderboard:** huggingface.co/spaces/open-llm-leaderboard — Ranking de modelos abiertos
- **Vellum Open-Source LLM Leaderboard:** vellum.ai — Comparativa de modelos open-source
- **CodeSOTA:** codesota.com — Benchmark de modelos de código
- **BenchLM:** benchlm.ai — Plataforma de benchmarks multi-modelo
- **Presenc AI:** presenc.ai — Análisis de rendimiento de IA
- **Swfte:** swfte.com — Benchmarks técnicos
- **Documentación oficial de API:** OpenAI, Anthropic, Google DeepMind, Meta, xAI, DeepSeek, Alibaba Cloud, Zhipu AI, Baidu, Moonshot AI, ByteDance, MiniMax, Stepfun, Xiaomi, Huawei, Tencent, SenseTime, Mistral AI, NVIDIA
- **Papers técnicos:** Publicaciones oficiales de cada laboratorio
- **Anthropic System Card (Claude Mythos):** 244 páginas de documentación técnica
- **Google I/O 2026:** Anuncios de Gemini 3.5 Flash y Gemma 4

---

> **Nota final:** Este catálogo se actualizará periódicamente a medida que nuevos modelos y benchmarks estén disponibles. La fecha de corte es el 24 de mayo de 2026. Los precios y puntuaciones pueden variar según la región y el proveedor de API.
