---
name: aletheia
description: Metodología de investigación para Aletheia — protocolo de búsqueda, triangulación, verificación y síntesis de información. Úsala cuando necesites realizar una investigación estructurada y profunda.
---

# Skill de Investigación — Aletheia

Este skill define el protocolo completo de investigación que Aletheia debe seguir para garantizar hallazgos precisos, verificables y útiles.

## Protocolo de Investigación en 6 Fases

### Fase 1: Formulación
- Define la pregunta central de investigación.
- Identifica 3-5 sub-preguntas que la descomponen.
- Determina el tipo de fuentes relevantes (académicas, técnicas, de mercado, noticias).
- Establece criterios de éxito: ¿qué constituye una respuesta satisfactoria?

### Fase 2: Exploración Inicial
- Lanza **5 búsquedas paralelas** con Firecrawl usando variaciones de la pregunta central.
- Usa Brave Search para una búsqueda web amplia con operadores avanzados.
- Usa Firecrawl para extraer contenido completo de las páginas más relevantes.
- Identifica términos clave, sinónimos y variaciones para refinar la búsqueda.
- Genera un mapa inicial de fuentes y temas.

### Fase 3: Investigación Profunda
- Para temas académicos: usa Scholar Search (arXiv + Semantic Scholar).
- Para temas técnicos: busca documentación oficial, repositorios y referencias.
- Para datos de mercado: prioriza fuentes primarias (informes oficiales, datos públicos).
- Usa Sequential Thinking para descomponer hallazgos complejos.
- Extrae citas textuales con contexto.

### Fase 4: Triangulación
- Para cada afirmación clave, busca al menos 3 fuentes independientes.
- Ejecuta auto-triangulación: corre `vault.py lint --check-coverage` para verificar que cada afirmación tiene ≥3 fuentes.
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

### Fase 6: Verificación
- Revisa cada afirmación contra las fuentes originales.
- Calcula el nivel de confianza general:
  - **Alta**: múltiples fuentes primarias, consistentes, autoritativas
  - **Media**: fuentes secundarias consistentes, o fuente primaria única pero confiable
  - **Baja**: fuente única, especulativa, desactualizada o no verificable
- **La matriz de confianza es OBLIGATORIA**: si no hay matriz con ≥3 filas, el extract falla con error de lint.
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

### Protocolo Obsidian
- **Obsidian MCP es solo para humanos**: Interfaz de lectura/revisión visual. Los agentes NO tienen accesso a Obsidian MCP.
- **Vault MCP es la herramienta de agentes**: Usa siempre vault MCP (server-filesystem) para leer y escribir en `.memory/`.
- **Separación**: Humanos exploran con Obsidian, agentes escriben/leen con vault MCP.

### Reglas de Escritura
- **raw/**: Solo el humano escribe aquí. Los agentes proponen contenido para que el humano revise.
- **wiki/sources/**: Auto (sin revisión). Escribe libremente.
- **wiki/concepts/**: Auto (sin revisión). Si contradices un concepto existente, márcalo con `⚠️ Contradiction:`.
- **log.md**: Append-only. Cada sesión agrega una línea. Nunca modifiques entradas anteriores.
