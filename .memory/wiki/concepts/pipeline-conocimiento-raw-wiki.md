---
type: concept
source: Investigación pipeline conocimiento Aletheia
related: [compile-then-query, add-only-extraction]
---

# Pipeline de Conocimiento raw→wiki→schema

Proceso de conversión de investigaciones de Aletheia en conocimiento arquitectónico perdurable para Kosmos y Metis.

## Etapas
1. **raw/**: Investigación completa, inmutable, ADD-only
2. **wiki/concepts/**: Conceptos destilados con [[wikilinks]]
3. **wiki/sources/**: Fuentes con metadata
4. **wiki/entities/**: Entidades del sistema
5. **schema/**: ADRs y decisiones arquitectónicas

## Métricas actuales
- Conversión completa: 40%
- Enlaces rotos: 0
- Tiempo promedio: ~15 min
- Cross-referencia: pendiente de automatizar

## Mejora propuesta
Automatizar destilación raw→wiki via post_output_hook con extracción de conceptos y cross-linking automático.


## Referencias Cruzadas
- Relacionado: [[conversión-parcial]]
- Relacionado: [[compile-then-query]]
- Relacionado: [[pipeline-maid]]
- Relacionado: [[investigacion-pipeline-conocimiento]]
