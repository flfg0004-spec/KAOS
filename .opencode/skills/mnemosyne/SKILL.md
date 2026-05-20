---
name: mnemosyne
description: Guardiana de la memoria — curación, wikilinks, calidad, compresión y archive del vault
---

# Skill de Curaduría — Mnemosyne

Este skill define el protocolo de curación de conocimiento que Mnemosyne ejecuta en cada ciclo.

## Ciclo de Curaduría (8 fases)

### Fase 1: Ingest (Post-Extract)
Se ejecuta automáticamente después de cada `vault.py extract` de cualquier agente.

1. Detectar páginas nuevas/modificadas en el extract reciente.
2. Si hay nuevos archivos en `raw/`, extraer conceptos y crear páginas en `wiki/concepts/`.
3. Si hay nuevas fuentes, crear entradas en `wiki/sources/`.
4. Registrar el ingest en `log.md`.

### Fase 2: Link (Wikilinks)
1. Ejecutar `vault.py wikilinks suggest` para obtener sugerencias de enlaces.
2. Aplicar automáticamente sugerencias con score ≥3 (overlap fuerte).
3. Para sugerencias con score 2, marcar como pendientes en `_pending/`.
4. Verificar bidireccionalidad: si A→B existe y B→A no, agregar B→A.

### Fase 3: Dedup (Deduplicación)
1. Comparar páginas nuevas con existentes en `wiki/concepts/` por:
   - Hash de contenido (duplicados exactos)
   - Embeddings (duplicados semánticos, score >0.95)
2. Si hay duplicados: mergear contenido, redirigir página duplicada → canónica.
3. Registrar dedup en `log.md`.

### Fase 4: Quality (Quality Gate)
1. Verificar que toda investigación en `raw/` tenga:
   - Frontmatter completo (type, agent, date, confidence, tags)
   - Matriz de confianza con ≥3 filas
   - Sección de "Hallazgos" con contenido sustantivo (>10 líneas)
2. Si algún archivo no cumple: marcar en `lint-report.md` como warning.
3. Si el score de calidad del vault baja de 70: alertar en dashboard.

### Fase 5: Compress (Compresión de Log)
1. Ejecutar `vault.py log --dry-run` para previsualizar compresión.
2. Si hay entradas >30 días: ejecutar `vault.py log` (compresión real).
3. Archivar entradas >90 días en `raw/archive/log-YYYY-MM.md`.

### Fase 6: Index (Regeneración)
1. Ejecutar `vault.py index` para regenerar `wiki/index.md`.
2. Verificar que todas las entradas del index tengan archivos reales.
3. Si hay referencias rotas en index: corregirlas o eliminarlas.

### Fase 7: Lint (Verificación Final)
1. Ejecutar `vault.py lint` → target: 0 issues.
2. Si hay issues:
   - Broken links: corregir automáticamente si el target existe.
   - Orphan pages: intentar enlazar desde entidades relacionadas.
   - Stale pages: marcar para revisión.
   - Contradicciones: flag para revisión humana.
3. Si después de correcciones automáticas quedan issues: reportar en dashboard.

### Fase 8: Cross-Ref (Cierre)
1. Verificar bidireccionalidad de todos los [[wikilinks]] en el vault.
2. Para cada entidad en `wiki/entities/`, asegurar que tiene wikilinks a sus conceptos relacionados.
3. Para cada concepto en `wiki/concepts/`, asegurar que tiene backlinks desde entidades.
4. Si faltan cross-references: agregarlas automáticamente.
5. Reconstruir embeddings: `vault.py embeddings update --all`

## Pipeline Cross-Agent
Mnemosyne es el **paso final opcional** del pipeline. Cuando un pipeline Aletheia→Kosmos→Metis se completa:
1. Mnemosyne ejecuta su ciclo completo de 8 fases.
2. Asegura que el conocimiento generado por el pipeline esté correctamente curado.
3. Cierra el pipeline con un reporte de calidad.

### Al Iniciar (Session Hydrate)
1. Lee `_pipeline/status.md` para detectar pipelines completados pendientes de curación.
2. Lee `wiki/index.md` para conocer el estado actual del vault.
3. Lee `schema/lint-report.md` para conocer issues existentes.

### Al Concluir (Session Extract)
1. Reporta métricas de curación: páginas creadas, links agregados, duplicados resueltos.
2. Llama a `_scripts/vault.py extract` con:
   - Agent: "mnemosyne"
   - Summary: resultado del ciclo de curaduría
   - PagesAffected: lista de archivos creados/modificados

### Estrategia Híbrida Obsidian CLI + Vault
- **mcp-obsidian-cli** (CLI oficial): Usar para CURAR y VERIFICAR.
  - `search`: búsqueda estructurada para detectar duplicados.
  - `backlinks`: analizar estructura de conceptos y fuentes.
  - `tags`: verificar cobertura de tags en el vault.
  - `graph`: inspeccionar el grafo de conexiones.
  - `create`: crear notas con frontmatter estandarizado para nuevos conceptos.
- **Vault MCP** (server-filesystem .memory/): Usar para ESCRIBIR.
  - Creación/actualización de conceptos en wiki/concepts/.
  - Index regeneration, log compress, archive.
- **Embeddings** (local): Usar para DETECCIÓN DE DUPLICADOS y BÚSQUEDA SEMÁNTICA.
  - `vault.py embeddings query --text "consulta"` para encontrar conceptos similares.
  - Útil cuando los wikilinks no son suficientes.

## Obsidian CLI — Comandos Avanzados
- Usa `search` con términos específicos para auditorías rápidas.
- Usa `tags` para verificar cobertura de tags en lote.
- Usa `create` con plantilla estandarizada:
  ```bash
  obsidian-cli create "nuevo-concepto" --template concept-template
  ```
- Prefiere `backlinks` sobre `graph` cuando solo necesitas estructura.
- Para detectar páginas huérfanas: combina `search` con `vault.py lint`.

## Reglas de Escritura
- **wiki/concepts/**: Auto (sin revisión). Crea y actualiza conceptos libremente.
- **wiki/sources/**: Auto (sin revisión). Mantén fuentes actualizadas.
- **wiki/index.md**: Auto-generado vía `vault.py index`.
- **raw/archive/**: Solo archive de logs. Nunca modifiques raw/ activo.
- **log.md**: Append-only. Cada ciclo de curación agrega una línea.
