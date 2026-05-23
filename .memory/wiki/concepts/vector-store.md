---
type: concept
source: KAOS
related: [rag-architecture, txtai, compile-then-query, adr]
tags: [adr, adr-005, embeddings, mcp, rag, semsearch, txtai, vectorstore]
---

# Vector Store

**Tipo**: concepto técnico
**Tags**: #vectorstore #embeddings #semsearch #adr-005

Propuesto en ADR-005 para cuando el vault supere ~100 páginas. Implementación con `sqlite-vec` + Ollama embeddings (mxbai-embed-large). Por ahora, el txtai MCP con TF-IDF (sentence-transformers) es suficiente para 40 conceptos actuales.

**Relacionado con**: [[rag-architecture]], [[txtai]], [[compile-then-query]]


## Referencias Cruzadas
- Relacionado: [[adr]]
