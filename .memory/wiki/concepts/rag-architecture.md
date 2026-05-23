---
type: concept
source: KAOS
related: [retrieval-augmented-generation, pipeline-conocimiento-raw-wiki, compile-then-query, vector-store]
tags: [arquitectura, conocimiento, embeddings, llm, metricas, pipeline, rag, recuperacion]
---

# RAG Architecture

**Tipo**: concepto técnico
**Tags**: #rag #arquitectura #llm #recuperacion

La arquitectura [[retrieval-augmented-generation]] (RAG) combina modelos paramétricos con memorias externas no paramétricas. Etapas: indexación (documentos→embeddings), recuperación (query→top-k), aumento (contexto+query), generación. Mejoras incluyen hybrid search, chunking strategies, reranking y Retro/Retro++.

**Relacionado con**: [[pipeline-conocimiento-raw-wiki]], [[compile-then-query]], [[vector-store]]
