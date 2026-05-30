# ADR-022: Estrategia de Gateway de Agentes — Extender Hermes vs Integrar AIephant

**Estado:** Propuesto  
**Fecha:** 2026-05-30  
**Contexto:** Decisión arquitectónica sobre gateway de agentes (identidad, routing, telemetría, payments)

## Contexto

KAOS necesita una capa de **gateway de agentes** que proporcione:

1. **Agent Identity**: identificar qué agente (workspace/project/agent/user/session) hace cada llamada.
2. **Routing con failover**: enrutamiento de requests al modelo/proveedor correcto (Aether ya resuelve esto a nivel LLM, pero no a nivel de agente).
3. **Telemetría unificada**: tracking de uso por agente, sesión, tarea.
4. **Auth y rate limiting**: control de acceso entre agentes internos y externos.
5. **Futuro: payments/margins**: registro de costos por agente para accountability.

La investigación de Aletheia identificó **AIephant Agent Gateway** (Rust, 72⭐, beta 0.2.0) como competidor directo. Sin embargo, KAOS ya invierte en **Hermes Gateway** (v0.15.2, kanban, MCP serve, Telegram notifications) como backbone de comunicación.

La pregunta arquitectónica es: ¿extender Hermes para cubrir estos gaps, integrar AIephant, o construir un gateway propio?

## Opciones Consideradas

### Opción 1: Integrar AIephant Agent Gateway

Gateway agent-first en Rust con Axum + PostgreSQL + Redis + Qdrant. Ofrece agent identity, x402/MPP (micropayments), agent margin ledger.

- **Pros**: Agent identity nativo, x402/MPP listo, arquitectura en Rust (performance), Qdrant para memoria vectorial.
- **Cons**: **72⭐, beta 0.2.0** — inmaduro, riesgo de abandono. Stack Rust no alineado con Python/TypeScript de KAOS. Dependencia de PostgreSQL + Redis + Qdrant. Overhead operativo significativo.

### Opción 2: Extender Hermes Gateway Existente

Hermes ya provee: MCP serve, kanban dispatch, Telegram notifications, provider chain. Faltan: agent identity estructurado, telemetría por sesión, rate limiting.

- **Pros**: Ya integrado, stack TypeScript compatible, madurez probada (v0.15.2), sin nueva infraestructura. Costo incremental bajo.
- **Cons**: Hermes no fue diseñado como gateway de agentes. Las extensiones de identity y telemetría serían "pegadas". x402/MPP no disponible.

### Opción 3: Gateway Propio en Python

Construir un gateway minimalista sobre el stack existente (Aether para routing, Hermes para notificaciones, SQLite para telemetría).

- **Pros**: Control total, stack 100% Python, integración profunda con Aether/QualityStore, sin dependencias externas.
- **Cons**: Mayor esfuerzo inicial, duplicación de funcionalidad con Hermes, riesgo de reinvento.

### Opción 4: Híbrido — Aether como Gateway Lógico + Hermes como Gateway de Comunicación

Usar Aether como gateway lógico (identity + routing + telemetría) y Hermes como gateway de comunicación (MCP serve + notificaciones). Sin capa de gateway explícita.

- **Pros**: Máxima reutilización, sin nueva infraestructura, Aether ya tiene quality-aware routing y tracking.
- **Cons**: Acoplamiento Aether-Hermes, agent identity no estructurado, sin rate limiting explícito.

## Decisión

**Opción 2 — Extender Hermes para identidad de agente y telemetría.**

No se integrará AIephant (inmaduro, stack no alineado). No se construirá gateway propio (duplicación). La estrategia es:

1. **Agent Identity en Hermes**: Extender el MCP serve de Hermes para incluir metadatos de agente (workspace, project, agent, user, session) en cada request.
2. **Telemetría en Hermes**: Hijack de hooks de Hermes para registrar métricas de uso por agente en el QualityStore SQLite existente.
3. **Rate Limiting**: Implementar rate limiting por agente en el bridge MCP.
4. **x402/MPP**: No implementar en esta fase. Monitorear madurez de AIephant para posible integración futura (v1.0+).

### Arquitectura Extendida

```
                    ┌──────────────────────────────────────────────┐
                    │           Hermes Gateway Extendido            │
                    │  ┌─────────────────┐  ┌──────────────────┐   │
                    │  │ MCP Serve v2     │  │ Agent Identity    │   │
                    │  │ (con metadata    │  │ Registry         │   │
                    │  │  de agente)      │  │ workspace/project │   │
                    │  └─────────────────┘  │ agent/user/session│   │
                    │                       └──────────────────┘   │
                    │  ┌─────────────────┐  ┌──────────────────┐   │
                    │  │ Telemetry Hook   │  │ Rate Limiter      │   │
                    │  │ → QualityStore   │  │ per agent/session │   │
                    │  └─────────────────┘  └──────────────────┘   │
                    │  ┌─────────────────┐  ┌──────────────────┐   │
                    │  │ Kanban (exist.) │  │ Notifications    │   │
                    │  │ Dispatch 60s    │  │ Telegram/Discord │   │
                    │  └─────────────────┘  └──────────────────┘   │
                    └──────────────────────────────────────────────┘
```

## Consecuencias

### Positivas
+ **Cero nueva infraestructura**: Hermes ya está desplegado y configurado.
+ **Costo incremental bajo**: ~2-3 días de desarrollo para agent identity + telemetría.
+ **Reversibilidad inmediata**: las extensiones son hooks, no modifican el core de Hermes.
+ **Alineación con ADR-011**: Hermes-first, fallback-always.

### Negativas
- **x402/MPP no disponible**: si se necesita en futuro, habrá que migrar.
- **Agent identity no nativo**: son metadatos pegados, no diseño original de Hermes.
- **Rendimiento**: Hermes en Node.js, no en Rust; posible bottleneck a alta concurrencia.

### Riesgos y Mitigaciones

| Riesgo | Probabilidad | Impacto | Mitigación |
|--------|-------------|---------|------------|
| Hermes no soporta hooks de telemetría | Media | Medio | Hooks custom via MCP post-output existente |
| Agent identity no persiste entre sesiones | Baja | Bajo | Store en SQLite vía QualityStore |
| Necesidad futura de x402/MPP | Media | Medio | Reevaluar AIephant v1.0+ |
| Rate limiting complejo sin Redis | Baja | Medio | Rate limiter en memoria + SQLite persistente |

## Referencias
- AIephant Agent Gateway: Rust, 72⭐, beta 0.2.0
- Hermes Agent v0.15.2: ya integrado en KAOS (ADR-011)
- ADR-018: Consolidación de Aether (quality-aware routing)
- ADR-011: Hermes Integration Strategy
