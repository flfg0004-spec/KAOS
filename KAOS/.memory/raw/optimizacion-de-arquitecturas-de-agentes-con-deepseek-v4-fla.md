---
type: investigation
agent: aletheia
date: 2026-05-20
confidence: alta
status: complete
tags: [deepseek-v4, flash, pro, optimizacion, prompting, cache-contexto, agentes]
---

# Investigación: Optimización de DeepSeek v4 Flash/Pro para Arquitecturas de Agentes

## Pregunta Central
¿Cómo optimizar el uso de DeepSeek v4 Flash y Pro en sistemas multi-agente, maximizando rendimiento, minimizando costos y aprovechando sus características arquitectónicas únicas (context caching, MoE, thinking modes)?

## Sub-preguntas
1. ¿Cuáles son las diferencias arquitectónicas clave entre Flash y Pro?
2. ¿Cómo funciona el context caching de DeepSeek y cómo maximizar su impacto?
3. ¿Qué modos de thinking existen y cuándo usar cada uno?
4. ¿Cómo estructurar prompts para maximizar cache hits?
5. ¿Qué estrategias de routing y token budget son óptimas?

## Fuentes Principales
- api-docs.deepseek.com — Documentación oficial de la API (305 snippets)
- DeepSeek V4 Flash: 284B total params, 13B activos (MoE)
- Context Caching on Disk: cache hits requieren prefix idéntico desde token 0
- Thinking modes: None (JSON+tools), high (balance), xmax (máxima profundidad)

## Hallazgos

### 1. Arquitectura de DeepSeek v4 Flash
- **Parámetros**: 284B total, 13B activos por token (MoE — Mixture of Experts)
- **Contexto**: 1M tokens de ventana, 384K tokens de output máximo
- **Precio**: $0.14/1M input, $0.28/1M output, $0.028/1M cache read
- **Thinking**: soporta razonamiento con esfuerzo configurable (high → xmax)
- **JSON Output**: solo disponible en non-thinking mode
- **Tool Calling**: solo disponible en non-thinking mode
- **Razonamiento**: capacidades cercanas a V4-Pro en tareas de agente simples

### 2. DeepSeek v4 Pro vs Flash
| Característica | Flash | Pro | Ratio |
|---------------|-------|-----|-------|
| Costo input | $0.14/1M | $1.74/1M | Flash 12.4× más barato |
| Costo cache | $0.028/1M | $0.145/1M | Flash 5.2× más barato |
| Thinking | high → xmax | high → xmax | Idéntico |
| JSON mode | Solo non-thinking | Solo non-thinking | Idéntico |
| Tool calls | Solo non-thinking | Solo non-thinking | Idéntico |
| Contexto | 1M tokens | 1M tokens | Idéntico |

### 3. Context Caching — Mecanismo Crítico
DeepSeek implementa **Context Caching on Disk**: los inputs repetitivos se cachean en disco. Un cache hit ocurre cuando el **prefix desde token 0 es idéntico** a una solicitud anterior. Cache misses parciales en medio del input no generan hit.

**Impacto económico**:
- Flash sin cache: $0.14/1M tokens
- Flash con cache: $0.028/1M tokens → **80% de ahorro**
- Pro sin cache: $1.74/1M tokens
- Pro con cache: $0.145/1M tokens → **91% de ahorro**

**Reglas de persistencia del cache**:
- Se persisten al finalizar cada request (user input + model output)
- Se detectan prefixes comunes entre múltiples requests
- Se cachean a intervalos fijos de tokens para inputs largos
- Funciona automáticamente sin cambios de código

**Estrategia óptima**: estructura de mensajes con 3 capas:
1. System prompt (byte-idéntico siempre) → **cache hit**
2. Vault rules + policy (cambia rara vez) → **cache hit**
3. Vault data del agente (mismo agente = mismo data) → **cache hit**
4. Task input (cambia cada llamada) → **único cache miss**

### 4. Thinking Modes
| Modo | Velocidad | JSON | Tools | Uso recomendado |
|------|-----------|------|-------|-----------------|
| None | Máxima | ✅ | ✅ | Lint, health, extract, index, hydrate |
| high | Media | ❌ | ❌ | Investigación, wikilinks, pipeline check |
| xmax | Lenta | ❌ | ❌ | Síntesis estratégica, ADRs complejos |

Los `reasoning_tokens` se trackean en la respuesta API bajo `usage.completion_tokens_details.reasoning_tokens`.

### 5. Token Budgets Óptimos
DeepSeek soporta 1M de contexto, pero el rendimiento óptimo está en rangos más pequeños:

| Modelo | Min | Óptimo | Max | Casos de uso |
|--------|-----|--------|-----|-------------|
| Flash | 1K | 8K | 32K | 90% de operaciones del vault |
| Pro | 4K | 16K | 64K | ADRs, estrategia, síntesis multi-agente |

### 6. Prompt Engineering para DeepSeek v4
- Responden bien a chain-of-thought estructurado
- Prefieren separadores `\n\n` para límites de sección claros
- No necesitan etiquetas XML extensas (a diferencia de Claude)
- Markdown headers son el formato de estructuración preferido
- JSON mode requiere `response_format={"type": "json_object"}` + mención de "json" en el prompt
- Tool calling usa formato OpenAI-compatible

## Matriz de Confianza

| Afirmación | Confianza | Fuentes | Notas |
|------------|-----------|---------|-------|
| Flash 284B/13B MoE | Alta | Documentación oficial | Confirmado en release notes |
| Cache hits requieren prefix idéntico desde token 0 | Alta | Documentación API | Mecanismo documentado explícitamente |
| Cache ahorra 80-91% | Alta | Pricing page | Flash $0.028 vs $0.14; Pro $0.145 vs $1.74 |
| JSON/Tools solo en non-thinking | Alta | Documentación API | Restricción arquitectónica |
| Flash razonamiento cercano a Pro en tareas simples | Media | Comunicado oficial | "Closely approach V4-Pro" — sujeto a interpretación |
| Budget óptimo 8K-32K Flash | Media | Inferencia propia | Basado en patrones de uso, no documentado oficialmente |

## Conclusiones
DeepSeek v4 Flash ofrece una relación calidad/precio excepcional para sistemas de agentes, especialmente cuando se maximiza el context caching. La clave está en:
1. **Estructurar prompts con prefix idéntico** para maximizar cache hits (80-91% ahorro)
2. **Usar Flash para el 90% de operaciones** (lint, health, extract, hydrate, wikilinks)
3. **Reservar Pro solo para síntesis y ADRs críticos**
4. **Thinking mode progresivo**: None → high → xmax según complejidad de la tarea
5. **Budget adaptativo**: 1K-8K para tareas simples, 16K-64K para análisis profundos

## Investigación Pendiente
- Benchmarks reales de cache hit rate en producción
- Comparativa de calidad Flash vs Pro en tareas de agente complejas vs simples
- Medición de latencia real con diferentes thinking modes


## Referencias
- [[index]]
- [[log]]
- [[checkpoint]]
- [[vault]]
