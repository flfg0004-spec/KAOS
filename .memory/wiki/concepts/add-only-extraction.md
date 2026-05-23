---
type: concept
source: Mem0 — arXiv:2504.19413
related: [memory-blocks, compile-then-query]
---

# ADD-only Extraction

Patrón de memoria donde los nuevos facts se acumulan junto a los viejos — nada se sobreescribe. Inspirado en el pipeline de [[arxiv-2504-19413-mem0]].

## Características
- **Preserva historia temporal**: ambos facts (viejo y nuevo) sobreviven
- **Contexto para cambios**: permite entender cómo evolucionó la información
- **Rollback natural**: siempre se puede volver al fact anterior

## Pipeline Mem0
1. Store New Memories → Context Lookup → Distill Memories (ADD-only, single step LLM) → Deduplicate + Embed → Entity Linking

## Multi-signal retrieval
Combinación de:
- **Semantic Search**: Similaridad vectorial
- **Keyword Search**: BM25 con lematización
- **Entity Search**: Entity graph matching

## Aplicación en KAOS
El vault `.memory/` usa ADD-only: raw/ es inmutable, log.md es append-only. A futuro: implementar multi-signal retrieval.
[[aletheia]] implementa este pipeline ADD-only al recolectar fuentes inmutables en raw/.


## Referencias Cruzadas
- Relacionado: [[pipeline-maid]]
- Relacionado: [[estado-memoria-sesion]]
- Relacionado: [[fuentes-consultadas]]
- Relacionado: [[memory-blocks]]
- Relacionado: [[context-nivel-1]]
- Relacionado: [[vault]]
- Relacionado: [[duplicidad-de-funcionalidad]]
