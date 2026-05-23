# Evaluación de Plugins del Ecosistema OpenCode para KAOS

**Investigador**: Aletheia
**Fecha**: 2026-05-20
**Método**: Análisis de repositorios GitHub + documentación oficial

## Resumen

Se evaluaron 4 plugins del ecosistema OpenCode para determinar su adopción en KAOS.
2 no están disponibles como paquetes npm (solo GitHub), 1 está archivado, 1 es el SDK oficial.

---

## 1. opencode-firecrawl

| Atributo | Valor |
|----------|-------|
| Repo | github.com/firecrawl/opencode-firecrawl |
| Stars | ~64 |
| npm | ❌ No disponible (solo GitHub) |
| Estado | Activo |

**Qué hace**: Integración nativa de Firecrawl CLI como skill de OpenCode.

**Evaluación**: Reemplazaría nuestro MCP firecrawl actual. El skill permite scrape, search, map, crawl desde OpenCode nativamente. Sin embargo, no está disponible como paquete npm — requiere instalación manual desde GitHub.

**Veredicto**: ⏳ Posponer — cuando esté disponible en npm, adoptar. Por ahora, el MCP firecrawl actual es suficiente.

## 2. opencode-supermemory

| Atributo | Valor |
|----------|-------|
| Repo | github.com/supermemoryai/opencode-supermemory |
| Stars | ~1,219 |
| npm | ❌ No disponible |
| Estado | Activo |

**Qué hace**: Memoria persistente entre sesiones de OpenCode. Usa API de Supermemory para almacenar/recuperar resúmenes de conversaciones.

**Evaluación**: Alta relevancia (8/10). Resolvería la memoria entre sesiones del agente principal (no del vault). Sin embargo: (1) No está en npm, (2) Requiere API key de Supermemory, (3) Es una dependencia externa.

**Veredicto**: ❌ No adoptar — KAOS ya tiene vault de memoria propio. Agregaría dependencia externa innecesaria.

## 3. opencode-background-agents

| Atributo | Valor |
|----------|-------|
| Repo | github.com/kdcokenny/opencode-background-agents |
| Stars | ~252 |
| npm | ❌ No disponible |
| Estado | Activo |

**Qué hace**: Delegación asíncrona de tareas a sub-agentes con contexto persistente.

**Evaluación**: Alta relevancia (9/10). El patrón async delegation es exactamente lo que necesita KAOS para tareas largas de investigación. Sin embargo, requiere instalación manual.

**Veredicto**: ⏳ Posponer — cuando esté disponible en npm. Por ahora, KAOS usa `task` tool nativa que ya tiene OpenCode para subagentes.

## 4. @opencode-ai/sdk

| Atributo | Valor |
|----------|-------|
| npm | ✅ @opencode-ai/sdk@1.15.5 |
| Stars | — (oficial) |
| Estado | Oficial, 7,431 versiones |

**Qué hace**: SDK TypeScript para interactuar con OpenCode programáticamente.

**Evaluación**: Crítico para Sprint 4 (POC SDK). Permite crear sesiones, enviar prompts, leer resultados vía API.

**Veredicto**: ✅ Adoptar — ya disponible en npm, se usará en Sprint 4 para el POC.

## Conclusiones

| Plugin | Veredicto | Razón |
|--------|-----------|-------|
| opencode-firecrawl | ⏳ Posponer | No en npm, MCP actual suficiente |
| opencode-supermemory | ❌ No adoptar | KAOS ya tiene vault, dependencia externa |
| opencode-background-agents | ⏳ Posponer | No en npm, task tool nativa suficiente |
| @opencode-ai/sdk | ✅ Adoptar | Oficial, en npm, necesario para Sprint 4 |

## Fuentes
- https://opencode.ai/docs/ecosystem#plugins
- https://github.com/firecrawl/opencode-firecrawl
- https://github.com/supermemoryai/opencode-supermemory
- https://github.com/kdcokenny/opencode-background-agents
- https://www.npmjs.com/package/@opencode-ai/sdk


## Matriz de Confianza
| Afirmación | Confianza | Fuentes | Notas |
|------------|-----------|---------|-------|
| Esta investigación | Alta | Fuentes primarias | Revisión general |


## Referencias
- [[index]]
- [[log]]
- [[checkpoint]]
- [[vault]]
