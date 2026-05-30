# ADR-015: Estrategia Multi-Modelo para Reducción de Sesgo Cognitivo

## Estado
Aceptado

## Fecha
2026-05-25

## Agentes Involucrados
Aletheia, Metis, Kosmos, Kratos

## Contexto

KAOS opera actualmente sobre DeepSeek V4 Flash como modelo único a través de OpenCode Go (~158K req/mes por $10/mes). Los 6 agentes (Aletheia, Kosmos, Kratos, Metis, Mnemosyne, Kronos) usan el mismo modelo subyacente para todas las tareas.

La investigación de Aletheia identificó que:

1. **Sesgo cognitivo medible**: todos los agentes heredan el mismo bias de output, patrones de error, y estilo de razonamiento. La cadena de verificación Aletheia→Kosmos→Metis pierde efectividad porque todos comparten el mismo "sistema cognitivo".
2. **Fortalezas distribuidas**: DeepSeek V4 Flash sobresale en coding (LiveCodeBench 91.6%) pero tiene conocimiento factual limitado (SimpleQA 34.1%). Kimi K2.6 lidera en coding agéntico (SWE-Bench Pro 58.6%) y razonamiento (GPQA 90.5%).
3. **Costo incremental mínimo**: La diferencia entre usar un solo modelo y una estrategia multi-modelo es de ~$1.91/mes para el volumen actual de KAOS.
4. **OpenCode Go como gateway único**: Todos los modelos están disponibles vía OpenCode Go, simplificando la integración sin necesidad de API keys adicionales.

## Opciones Consideradas

### Opción 1: Status quo — DeepSeek V4 Flash para todos los agentes
- **Pros**: Sin cambios, costo predecible $10/mes
- **Cons**: Sesgo cognitivo en todos los agentes, factual accuracy limitada (SimpleQA 34.1%), sin verificación cruzada independiente

### Opción 2: Multi-modelo vía API directa (DeepSeek + Kimi Moonshot + Google Gemini)
- **Pros**: Control total, cache pricing de DeepSeek ($0.0028/M)
- **Cons**: 3 API keys, 3 proveedores, 3 integraciones, overhead operativo

### Opción 3: Multi-modelo vía OpenCode Go (SELECCIONADA)
- **Pros**: Una sola API key, un solo proveedor, acceso a 10+ modelos, integración inmediata, costo fijo $10/mes
- **Cons**: Sin cache pricing diferenciado, cuotas de "valor de cómputo" opacas

## Decisión

**Opción 3: Estrategia multi-modelo en 3 capas vía OpenCode Go, implementada como extensión de DSOL (Router Multi-Modelo).**

### Capas de la Estrategia

| Capa | Modelo | % Tráfico | Agentes | Task Types |
|------|--------|-----------|---------|------------|
| Base | DeepSeek V4 Flash (go-flash) | 85% | Kosmos, Kratos (tareas simples), Mnemonysne, Kronos | lint, extract, health, hydrate, wikilinks, curation, code_gen, general |
| Calidad | DeepSeek V4 Pro (go-pro) | 10% | Aletheia | research, analyze, synthesize, adr, factual |
| Diversidad | Kimi K2.6 (go-kimi-latest) | 5% | Metis, Kratos (coding agéntico), verificación cruzada | strategy, verify, cross_check, code_agentic, diversity |

### Reglas de Ruteo

| task_type | Modelo | Thinking | Agente primario |
|-----------|--------|----------|-----------------|
| lint | go-flash | None | Kosmos |
| extract | go-flash | None | Mnemosyne |
| health | go-flash | None | Mnemosyne |
| hydrate | go-flash | None | Mnemosyne |
| wikilinks | go-flash | None | Mnemosyne |
| curation | go-flash | None | Mnemosyne |
| code_gen | go-flash | None | Kratos |
| code_simple | go-flash | None | Kratos |
| general | go-flash | None | Kronos |
| research | go-pro | high | Aletheia |
| analyze | go-pro | high | Kosmos |
| synthesize | go-pro | xmax | Aletheia |
| adr | go-pro | high | Kosmos |
| factual | go-pro | high | Aletheia |
| strategy | go-kimi-latest | None | Metis |
| verify | go-kimi-latest | None | Metis (verificación cruzada) |
| cross_check | go-kimi-latest | None | Cualquier agente |
| code_agentic | go-kimi-latest | None | Kratos |
| diversity | go-kimi-latest | None | Metis |

## Consecuencias

### Positivas
- **Reducción de sesgo**: Los 6 agentes ya no comparten el mismo sesgo cognitivo; Metis (Kimi) y Kosmos (Flash) producen perspectivas complementarias
- **Verificación cruzada efectiva**: Si Aletheia (Pro) produce un output, Kosmos (Flash) verifica, Metis (Kimi) valida — 3 modelos diferentes = 3 perspectivas independientes
- **Especialización por tarea**: Cada modelo optimizado para su fortaleza (Flash: velocidad/eficiencia, Pro: profundidad factual, Kimi: razonamiento estratégico)
- **Costo casi neutro**: +$1.91/mes sobre la línea base de $2.45/mes = ~$4.36/mes total
- **Sin complejidad operativa**: Todo via OpenCode Go, una API key, una integración

### Negativas
- **Cuotas opacas de OpenCode Go**: Si el tráfico multi-modelo excede los límites del plan, pueden aplicar cargos adicionales no transparentes
- **Kimi K2.6 via OCGo**: Posible throttling o latencia adicional vs API directa de Moonshot
- **Cache no compartido**: Cada modelo tiene su propio cache; no hay beneficio de cache cross-modelo

### Neutrales
- **Backward compatibility**: agent_llm_call() sin task_type sigue funcionando como antes
- **Migración gradual**: Los agentes se actualizan uno por uno para usar task_type
- **Circuit breaker**: Protege contra fallos de modelo sin intervención manual

## Métricas de Éxito

| Métrica | Línea base | Target | Cómo se mide |
|---------|-----------|--------|-------------|
| Sesgo entre agentes | Outputs estilísticamente similares | Diversidad detectable | Comparación cualitativa de outputs de Metis (Kimi) vs Kratos (Flash) vs Aletheia (Pro) |
| Score de verificación | 88.6 | >92 | La verificación cruzada con modelos diferentes debería detectar más errores |
| Tasa de error factual (Aletheia) | SimpleQA 34.1% (Flash) | >50% | Pro para tareas factuales mejora accuracy |
| Costo total | $2.45/mes (solo Flash) | <$6/mes | TokenTracker de DSOL |
| % tráfico por modelo | 100% Flash | 85% Flash, 10% Pro, 5% Kimi | TokenTracker.get_model_breakdown() |
| Circuit breaker events | N/A | <1 apertura/semana | CircuitBreaker.get_status() |

## Referencias
- ADR-004: DeepSeek Optimization Layer para Agentes KAOS
- raw/analisis-proveedores-api-tokens.md (investigación de Aletheia)
- raw/informe-estrategico-proveedores-llm.md (investigación de Aletheia)
- [[sesgo-cognitivo-en-agentes]] (concepto)
