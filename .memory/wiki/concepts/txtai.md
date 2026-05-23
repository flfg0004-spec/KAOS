---
type: concept
source: KAOS
related: [vector-store, rag-architecture, mnemosyne, compile-then-query]
tags: [dedup, embeddings, mcp, rag, semsearch, txtai]
---

# txtai

**Tipo**: concepto técnico
**Tags**: #txtai #semsearch #embeddings #dedup

Servidor MCP local para búsqueda semántica y deduplicación sobre el vault. Usa `sentence-transformers/all-MiniLM-L6-v2` (TF-IDF + cosine similarity). Tools: `semantic_search(query, path, top_k)`, `deduplicate(path, threshold)`. Sin dependencias externas ni Docker. Implementado en `.memory/_scripts/mcp_txtai.py`. Reemplaza a `vault.py embeddings query` (deprecated).

**Relacionado con**: [[vector-store]], [[rag-architecture]], [[mnemosyne]]


## Referencias Cruzadas
- Relacionado: [[compile-then-query]]
