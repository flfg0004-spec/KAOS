---
type: adr
title: 'ADR-004: DeepSeek Optimization Layer para Agentes KAOS (→ Ether v2)'
aliases:
- adr-004-deepseek-optimization-layer
- adr-004-ether
tags:
- adr
- ether
created: '2026-05-20'
modified: '2026-05-26'
confidence: media
status: draft
---

# ADR-004: DeepSeek Optimization Layer para Agentes KAOS

## Contexto

KAOS opera sobre DeepSeek v4 Flash/Pro como modelo subyacente. La investigación de Aletheia (raw/optimizacion-de-arquitecturas-de-agentes-con-deepseek-v4-fla.md) identificó que:

1. **Context Caching** puede ahorrar 80-91% en costos de input si los prompts se estructuran con prefix idéntico desde token 0.
2. **Flash cuesta 12.4× menos que Pro** ($0.14 vs $1.74/1M tokens) pero sus capacidades de razonamiento se acercan a Pro en tareas de agente simples.
3. **JSON output y tool calling** solo están disponibles en non-thinking mode — una restricción arquitectónica que afecta el diseño de los skills.
4. **Thinking modes** (high → xmax) permiten escalar profundidad de razonamiento según complejidad de la tarea.
5. El vault actual no tiene un mecanismo sistemático para optimizar el uso del modelo — cada llamada estructura sus prompts independientemente, perdiendo oportunidades de cache.

Se requiere una capa de optimización que:
- Maximice cache hits estructurando prompts con prefijos idénticos.
- Routee tareas entre Flash y Pro según complejidad.
- Gestione thinking modes progresivamente.
- Asigne token budgets óptimos por tipo de tarea.

## Opciones Consideradas

### Opción 1: Sin capa de optimización (status quo)
Cada agente estructura prompts independientemente. Sin cache hits, sin routing, sin gestión de thinking.

- **Pros**: Sin cambios; cada agente tiene control total.
- **Cons**: 0% cache hits; Flash usado para todo (desperdicio de capacidad Pro) o Pro usado para todo (costo 12.4×).
- **Costo estimado**: $X por llamada (sin descuento por cache).

### Opción 2: Routing automático con switch Flash/Pro
Un router decide según tipo de tarea si usar Flash (rápido, barato) o Pro (profundo, caro).

- **Pros**: Ahorro inmediato: ~90% de tareas van a Flash.
- **Cons**: Sin optimización de cache; thinking mode fijo.
- **Costo estimado**: $0.14/1M para 90% de tareas, $1.74/1M para 10%.

### Opción 3: DSOL completo — cache + routing + thinking + budget (SELECCIONADA)
Capa unificada que:
- Construye prompts con estructura cacheable (prefix idéntico → 99.6% cacheable).
- Routea tareas según tipo: Flash para volumen, Pro para síntesis crítica.
- Escala thinking mode: None → high → xmax según profundidad requerida.
- Asigna token budget adaptativo: 1K-32K Flash, 4K-64K Pro.

## Decisión
**Opción 3: DSOL completo, implementado como `lib/dsol.py`.**

## Justificación
1. **Cache optimization es el driver económico**: 80-91% de ahorro en input tokens. La estructura de 4 mensajes (system + rules + data + task) maximiza el prefix compartido entre llamadas del mismo agente.
2. **Flash para volumen, Pro para valor**: El router envía lint/health/extract/hydrate/wikilinks a Flash ($0.14). Reserva Pro solo para ADRs, estrategia y síntesis ($1.74 cuando es necesario).
3. **Thinking progresivo**: None para operaciones rutinarias (JSON, tool calls disponibles). high para investigación. xmax para síntesis estratégica.
4. **Budget adaptativo**: Tareas simples usan 1K-4K tokens (rápido, barato). Tareas complejas escalan hasta 64K (profundo, caro solo cuando vale la pena).
5. **Ya implementado y verificado**: `lib/dsol.py` existe, produce 99.6% cache ratio estimado, y está integrado con `vault.py`.

## Consecuencias

### Positivas
- **Ahorro estimado**: 80-91% en input tokens por cache hits (proyectado).
- **Routing eficiente**: 90% de operaciones en Flash (barato), 10% en Pro (cuando es necesario).
- **Thinking escalable**: Cada tarea usa exactamente la profundidad de razonamiento que necesita.
- **Transparencia**: `vault.py dsol status` muestra configuración actual; `vault.py dsol estimate` proyecta cache ratio.
- **Integración existente**: DSOL ya está conectado a `hydrate.py` vía parámetro `--task` para búsqueda semántica.

### Negativas
- **Requiere disciplina**: Los prompts deben mantener la estructura de 4 mensajes para maximizar cache. Un cambio en system prompt invalida todo el cache.
- **Overhead de planificación**: Cada nueva tarea necesita clasificación (tipo, thinking level, budget).
- **Pro solo con thinking**: JSON mode y tool calling no están disponibles en thinking mode — las tareas Pro no pueden usar estas características.

### Neutrales
- **Cache hits no garantizados**: Dependen de que el prefix sea byte-idéntico. Cambios menores (espacios, puntuación) rompen el cache.
- **Métricas de cache**: `prompt_cache_hit_tokens` solo disponibles si se usa la API directamente — no aplica en el contexto de OpenCode donde el modelo es el entorno mismo.
- **DSOL sin routing**: La implementación actual no incluye routing Flash/Pro porque el modelo es único en el entorno OpenCode. El router está diseñado para cuando haya acceso multi-modelo.

## Estado
Aceptada — Implementada originalmente en `lib/dsol.py` (v1), migrada a `lib/ether/` (v2)

## Evolución: DSOL → Ether (v2.0 — Mayo 2026)

### ¿Qué cambió?
El sistema fue renombrado de **DSOL** (DeepSeek Optimization Layer) a **Ether** (Environment for Token Harmonization & Execution Regulation). Este cambio refleja que el sistema ya no optimiza solo para DeepSeek, sino que ruthea entre 3 modelos (Flash, Pro, Kimi) vía OpenCode Go.

### Cambios arquitectónicos
- **Monolito `lib/dsol.py` (807 líneas)** → **Paquete `lib/ether/`** con 6 módulos de responsabilidad única:
  - `config.py`: Constantes, mapas de modelos, env vars
  - `router.py`: `resolve_model()`, fallback chain
  - `circuit.py`: CircuitBreaker unificado con persistencia
  - `tracker.py`: EtherTracker con thread safety y atomic writes
  - `limiter.py`: RateLimiter
  - `client.py`: API client, chat, prompt building
- **CircuitBreaker unificado**: Fusión del CB de dsol.py (per-model, 3 estados) y cost_optimizer.py (per-provider). Persistencia compartida vía `.memory/cache/circuit_breaker.json`.
- **Thread safety**: `EtherTracker` usa `threading.Lock` y atomic writes (temp + rename).
- **`lib/dsol.py`** se mantiene como **fachada backward-compatible** que re-exporta de `lib/ether/` (eliminar en v3.0).

### Variables de entorno
- `ROUTER_*` → `ETHER_*` (nuevas; `ROUTER_*` funcionan como fallback)

### CLI y MCP
- `vault.py dsol` → `vault.py ether` (nuevo; `dsol` es alias deprecated)
- `mcp_dsol.py` → `mcp_ether.py` (nuevo; `mcp-dsol` eliminado)

### ADRs afectados
- ADR-004: Esta actualización
- ADR-010: Actualizar referencias DSOL → Ether
- ADR-015: Actualizar "DSOL (Router Multi-Modelo)" → "Ether"

### Timeline de deprecación
| Versión | Cambio |
|---------|--------|
| v1.0 (Mayo 2026) | Paquete `lib/ether/` creado. `lib/dsol.py` como fachada. `ETHER_*` y `ROUTER_*` coexisten. |
| v2.0 | `lib/dsol.py` emite DeprecationWarning. `ROUTER_*` emite advertencia. |
| v3.0 | `lib/dsol.py` eliminado. `ROUTER_*` ignorado. Código legacy eliminado. |

## Referencias
- ADR-001: Arquitectura de Memoria de KAOS (base del vault)
- ADR-002: Aislamiento del Vault para OpenCode
- ADR-003: Zonas de Autonomía del Vault
- ADR-012: Refactor Medio a Ether
- raw/optimizacion-de-arquitecturas-de-agentes-con-deepseek-v4-fla.md (investigación de Aletheia)
- [[optimizacion-de-arquitecturas-de-agentes-con-deepseek-v4-fla-strategy]] (estrategia de Metis)
- api-docs.deepseek.com (documentación oficial de context caching y pricing)

