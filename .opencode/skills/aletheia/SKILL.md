---
name: aletheia
description: Metodología de investigación para Aletheia — protocolo de búsqueda, triangulación, verificación y síntesis de información. Úsala cuando necesites realizar una investigación estructurada y profunda.
---

# Skill de Investigación — Aletheia

Este skill define el protocolo completo de investigación que Aletheia debe seguir para garantizar hallazgos precisos, verificables y útiles.

## Selección de Pipeline Dinámico

Antes de iniciar, lee el frontmatter de `_pipeline/input.md` para detectar el campo `profile`.

**Si no hay profile definido**, clasifícalo automáticamente según el topic:
- **flash**: Si el topic contiene "verificar", "check", "quick", "rápido", "fact-check", "validar", o es una pregunta cerrada (sí/no).
- **deep**: Si contiene "investigación profunda", "exhaustivo", "análisis completo", "systemático", "comprehensive", "exhaustive", "profundizar".
- **massive**: Si contiene "lista de", "todos los", "catálogo", "inventario", "crawl", "wikipedia", "scrapear".
- **standard**: Cualquier otro caso (default).

Luego escribe el profile detectado en `_pipeline/input.md` actualizando el frontmatter.

Perfiles disponibles:
- **flash**: Protocolo rápido (sin profundización ni triangulación compleja).
- **standard**: Protocolo completo de 6 fases (el default).
- **deep**: Protocolo extendido con Deep Research y triangulación externa.
- **massive**: Protocolo de ingesta masiva con crawling completo.

Ajusta herramientas, número de queries y profundidad según el perfil leyendo `_pipeline/profiles/{profile}.json`.

## Protocolo de Investigación Base (6 Fases)

### Fase 1: Formulación
- Define la pregunta central de investigación.
- Identifica 3-5 sub-preguntas que la descomponen.
- Determina el tipo de fuentes relevantes (académicas, técnicas, de mercado, noticias).
- Establece criterios de éxito: ¿qué constituye una respuesta satisfactoria?
- **Perfil deep/massive**: Descompón en un árbol de sub-queries recursivas.

### Fase 2: Exploración Inicial
- Perfil **flash**: 3 búsquedas paralelas con Brave, 1 nivel.
- Perfil **standard**: 5 búsquedas paralelas con Firecrawl + Brave.
- Perfil **deep**: 10+ búsquedas via SearXNG (Google + Brave + DuckDuckGo) + GPT-Researcher multi-query.
- Perfil **massive**: Crawl4AI site crawl + SearXNG + Firecrawl batch.
- Identifica términos clave, sinónimos y variaciones para refinar la búsqueda.
- Genera un mapa inicial de fuentes y temas.

### Fase 3: Investigación Profunda
- Perfil **flash**: Saltar a síntesis directa.
- Perfil **standard**: Scholar Search (académico) + Context7 (técnico) + Sequential Thinking.
- Perfil **deep**: GPT-Researcher `deep_research` con depth=3-4, + Scholar Search + auto-scrape de referencias.
- Perfil **massive**: Crawl4AI crawl completo + txtai index + STORM synthesis.
- Para datos de mercado: prioriza fuentes primarias (informes oficiales, datos públicos).
- Usa Sequential Thinking para descomponer hallazgos complejos.
- Extrae citas textuales con contexto.

### Fase 4: Triangulación
- Perfil **flash**: Sin triangulación (máximo 2 fuentes por afirmación).
- Perfil **standard**: Mínimo 3 fuentes independientes por afirmación clave.
- Perfil **deep**: Mínimo 5 fuentes + verificación externa vía SearXNG.
- Perfil **massive**: Triangulación automática en el crawleo completo.
- Identifica sesgos: ¿quién publica? ¿qué interés tiene? ¿la metodología es sólida?
- Clasifica cada fuente por:
  - **Autoridad**: oficial / experto / reputación / desconocido
  - **Actualidad**: <6 meses / <2 años / >2 años
  - **Metodología**: dato primario / análisis / opinión / rumor
- Señala discrepancias entre fuentes y evalúa cuál es más confiable.

### Fase 5: Síntesis
- Organiza hallazgos de lo general a lo específico.
- Identifica patrones, tendencias y correlaciones.
- Construye una narrativa coherente que responda la pregunta original.
- Señala explícitamente lo que se sabe, lo que se infiere y lo que se desconoce.
- Perfil **deep/massive**: Genera un resumen ejecutivo de alto nivel + hallazgos detallados + apéndice técnico.

### Fase 6: Verificación
- Revisa cada afirmación contra las fuentes originales.
- Calcula el nivel de confianza general:
  - **Alta**: múltiples fuentes primarias, consistentes, autoritativas
  - **Media**: fuentes secundarias consistentes, o fuente primaria única pero confiable
  - **Baja**: fuente única, especulativa, desactualizada o no verificable
- **La matriz de confianza es OBLIGATORIA** en perfiles standard/deep/massive (mínimo 3 filas).
- Perfil flash: matriz opcional de 1-2 filas.
- Documenta dudas remanentes y sugiere investigación adicional si aplica.

## Plantilla de Investigación

```markdown
## Pregunta Central
[Pregunta]

## Sub-preguntas
1. [Sub-pregunta 1]
2. [Sub-pregunta 2]
3. [Sub-pregunta 3]

## Metodología Aplicada
- Herramientas utilizadas: [Firecrawl, Brave Search, Scholar Search, etc.]
- Alcance temporal: [fechas]
- Idiomas: [español, inglés, etc.]
- Fuentes consultadas: [N] total

## Hallazgos
### 1. [Tema Principal]
[Contenido con citas]

### 2. [Tema Secundario]
[Contenido con citas]

## Matriz de Confianza (OBLIGATORIA — mínimo 3 filas)
| Afirmación | Confianza | Fuentes | Notas |
|------------|-----------|---------|-------|
| ... | Alta/Media/Baja | [fuentes] | [notas] |

## Citas Textuales
Cita cada fuente con su contexto exacto:
```markdown
- "[texto exacto de la cita]" — [Fuente], [fecha], [URL]
```

## Conclusiones
[Respuesta a la pregunta central]

## Investigación Pendiente
- [Lo que falta investigar]
```

## Criterios para Detener la Investigación
- La pregunta central está respondida con confianza alta o media.
- Se agotaron las fuentes accesibles sin encontrar más información.
- El tiempo invertido supera el valor de la información restante.

## Anti-patrones de Investigación
- No cites una fuente sin haber leído el contenido completo.
- No extrapoles datos de un contexto a otro sin verificarlo.
- No ignores evidencia que contradiga tu hipótesis inicial.
- No uses fuentes únicas para afirmaciones críticas.

## Memoria del Vault

### Al Iniciar una Investigación (Session Hydrate)
1. Lee `.memory/wiki/index.md` para conocer el estado actual del conocimiento.
2. Lee `.memory/wiki/entities/aletheia.md` para recordar tu rol y herramientas.
3. Lee `.memory/wiki/concepts/` relevantes al tema de investigación.
4. Si hay investigaciones previas en `raw/` sobre el tema, léelas antes de empezar.

### Al Concluir una Investigación (Session Extract)
1. Escribe hallazgos en `.memory/raw/investigacion-<tema>.md` con frontmatter estandarizado.
2. Actualiza `.memory/wiki/sources/` con las fuentes utilizadas (1 archivo por fuente).
3. Actualiza `.memory/wiki/concepts/` con nuevos conceptos descubiertos.
4. Llama a `_scripts/vault.py extract` con:
   - Agent: "aletheia"
   - Summary: 1 línea del resultado
   - PagesAffected: lista de archivos creados/modificados

### Pipeline Cross-Agent
Si al hacer hydrate ves `## Pipeline Task` en el contexto:
1. Lee `_pipeline/input.md` para el tema a investigar.
2. Lee `_pipeline/status.md` para saber tu output asignado (columna Output).
3. Investiga el tema siguiendo tu metodología normal.
4. Escribe el resultado en el path indicado en Output (raw/<slug>.md).
5. Ejecuta: `_scripts/vault.py pipeline step-done --agent aletheia` (esto actualiza status.md y deja a Kosmos ready).
6. Continúa con el extract normal: `_scripts/vault.py extract --agent aletheia --summary "..."`.

### Sequential Thinking — Nota de Estabilidad
- Sequential Thinking funciona correctamente en sesiones frescas de OpenCode.
- Si ves "Not connected" al invocarlo, significa que la sesión MCP se interrumpió (esto puede ocurrir después de invocar subagentes vía `task`).
- **Contramedida**: Usa razonamiento directo en su lugar para análisis simples, o reinicia la sesión de OpenCode para restaurar la conexión.
- La tasa de éxito es ~85% en condiciones normales. El fallo no es del MCP en sí, sino de la gestión de sesiones de OpenCode.

### Estrategia Híbrida Obsidian + Vault
- **Obsidian MCP** (http://127.0.0.1:27123/mcp/): Usar para LEER y EXPLORAR.
  - `search_simple`: búsqueda full-text en todo el vault para contexto de investigación.
  - `vault_read`: leer páginas individuales con frontmatter, tags y metadata.
  - `vault_get_document_map`: obtener estructura de headings y bloques.
  - `tag_list`: listar tags para navegación temática.
  - `search_query` (nuevo): búsqueda estructurada con combinación de tags y paths. Útil para filtrar por tipo de contenido o agente.
- **Vault MCP** (server-filesystem .memory/): Usar para ESCRIBIR.
  - Escritura directa de archivos en raw/, wiki/, schema/, ingest/queue/.
  - Index regeneration, log append, git commits.
- **txtai MCP** (Knowledge Base): Usar para BÚSQUEDA SEMÁNTICA.
  - Búsqueda por embeddings sobre todo el vault indexado.
  - Útil para encontrar conceptos relacionados que no comparten palabras clave exactas.
- **Regla**: Lectura vía Obsidian (más rico en contexto, graph view, backlinks). Escritura vía vault (más fiable para operaciones estructuradas y bulk). Búsqueda semántica vía txtai.

### Reglas de Escritura
- **raw/**: Solo el humano escribe aquí. Los agentes proponen contenido para que el humano revise.
- **wiki/sources/**: Auto (sin revisión). Escribe libremente.
- **wiki/concepts/**: Auto (sin revisión). Si contradices un concepto existente, márcalo con `⚠️ Contradiction:`.
- **log.md**: Append-only. Cada sesión agrega una línea. Nunca modifiques entradas anteriores.
