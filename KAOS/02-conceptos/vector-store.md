---
type: concept
title: Vector Store
aliases:
- vector-store
tags:
- concept
created: '2026-05-20'
modified: '2026-05-21'
confidence: media
status: draft
---

# Vector Store

**Tipo**: concepto técnico
**Tags**: #vectorstore #embeddings #semsearch #adr-005

Propuesto en ADR-005 para cuando el vault supere ~100 páginas. Implementación con `sqlite-vec` + Ollama embeddings (mxbai-embed-large). Por ahora, el txtai MCP con TF-IDF (sentence-transformers) es suficiente para 40 conceptos actuales.

**Relacionado con**: [[rag-architecture]], [[txtai]], [[compile-then-query]]


## Referencias Cruzadas
- Relacionado: [[adr]]

