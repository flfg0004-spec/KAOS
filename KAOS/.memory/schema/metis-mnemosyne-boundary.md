# Metis ↔ Mnemosyne: Boundary y Guardrails

## Propósito
Definir los límites de responsabilidad entre Metis (agente de estrategia y calidad) y Mnemosyne (curadora de memoria y conocimiento) para evitar duplicación y conflictos en la gestión del conocimiento de KAOS.

## Matriz de Decisión

| Actividad | Responsable | Justificación |
|-----------|-------------|---------------|
| **Autoevaluación de calidad** (BCG, scores) | Metis | Metis tiene `post_output_hook.py`, `monitor.py`, `bcg_evaluator` |
| **Curación de entidades wiki** (frontmatter, links, tags) | Mnemosyne | Mnemosyne tiene `wiki_lifecycle_*`, `crossref_*`, `crystallize_*` |
| **Dashboard de calidad** (scores, tendencias, alertas) | Metis | Metis tiene `dashboard_populate.py`, `recommendation_tracker.py` |
| **Memoria a largo plazo** (archivado, compresión, dedup) | Mnemosyne | Mnemosyne tiene `memory_lifecycle.py`, `mnemobeam.py` |
| **Registro de sesiones** en `.memory/wiki/entities/` | Metis genera → Mnemosyne cura | Metis produce el output, Mnemosyne lo estructura y enlaza |
| **Detección de knowledge gaps** (vault graph topology) | Mnemosyne | Mnemosyne tiene `gaps.py` con `GapDetector` |
| **Knowledge gaps estratégicos** (para Aletheia) | Metis | Metis tiene `gap_service.py` con `dispatch()` a Aletheia |
| **Reportes semanales de calidad** | Metis | Metis tiene SKILL.md Quality Workflow Fase 6 |
| **Actualización de `modified`/`updated` fields** | Mnemosyne | Mnemosyne tiene `wiki_lifecycle` para tracking de cambios |
| **Limpieza de entidades huérfanas o stale** | Mnemosyne | Mnemosyne tiene `cleaner.py`, `garbage.py` |

## Reglas

1. **Metis NO escribe directamente en wiki entities** sin pasar por Mnemosyne. El output de Metis se deposita en `.memory/transfers/metis_to_mnemosyne/` para que Mnemosyne lo procese.

2. **Mnemosyne NO evalúa calidad estratégica** (BCG scores, OKR health). Eso es responsabilidad exclusiva de Metis.

3. **Mnemosyne SÍ cura las entidades que Metis genera**: actualiza frontmatter, agrega wikilinks, tags, y asegura consistencia con el grafo de conocimiento.

4. **Si ambos detectan un gap de conocimiento**:
   - Mnemosyne: gap estructural en el grafo del vault (nota faltante entre A y C)
   - Metis: gap de información estratégica (dato que necesita Aletheia)
   - No hay conflicto — operan en dominios diferentes

5. **Post-sesión de Metis**: Metis ejecuta `post_output_hook` + `monitor.poll` + `dashboard_populate`. Luego invoca a Mnemosyne para curación. Mnemosyne NO re-ejecuta las verificaciones de Metis.

## Guardrails

- Metis no debe modificar archivos en `.memory/wiki/` directamente (excepto su propia entidad `metis.md` para actualizaciones menores de estado)
- Mnemosyne no debe ejecutar `post_output_hook.py`, `monitor.py`, ni `gap_service.py`
- Ambos pueden leer de `.memory/cache/` pero solo Metis escribe en `alerts/`, `recommendations/`, `gaps/`
- Mnemosyne escribe en `wiki/`, `transfers/`, `raw/`
- Si hay conflicto de escritura en `.memory/cache/`, usar `file_lock.py` para coordinación

## Tool Overlap Analysis

| Tool | Metis | Mnemosyne | Notas |
|------|-------|-----------|-------|
| `vault_*` | ✅ Lectura/escritura de reportes | ✅ Lectura/escritura de entidades | Mismo vault, propósitos distintos |
| `sequential-thinking_*` | ✅ Descomposición estratégica | ✅ Análisis de grafo de conocimiento | Uso diferente, sin conflicto |
| `mcp-obsidian-cli_*` | ✅ Lectura durante análisis | ✅ Escritura post-curación | Mnemosyne escribe más seguido |
