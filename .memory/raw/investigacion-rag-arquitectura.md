---
type: investigacion
agent: aletheia
date: 2026-05-20
confidence: alta
tags: [rag, arquitectura, llm, recuperacion, generacion]
fuentes: [wikipedia, ibm, arxiv]
---

# Investigación: Arquitectura RAG (Retrieval-Augmented Generation)

## Resumen
RAG es una técnica que permite a LLMs recuperar e incorporar información nueva desde fuentes externas. Combina un modelo paramétrico (LLM) con una memoria externa no paramétrica accedida mediante recuperación en tiempo de inferencia.

## Etapas Clave
1. Indexación: documentos → embeddings → vector database
2. Recuperación: query → retriever → top-k documentos relevantes
3. Aumento: documentos recuperados + query original → prompt aumentado
4. Generación: LLM genera respuesta basada en el prompt aumentado

## Mejoras
- Encoder: sparse vectors, dense vectors, hybrid search
- Retriever: Inverse Cloze Task, supervised optimization, reranking
- Language Model: Retro, Retro++ con in-context RAG
- Chunking: fixed-length, syntax-based, format-based

## Aplicaciones
- Chatbots con acceso a documentación interna
- Sistemas de pregunta-respuesta sobre dominios específicos
- Asistentes empresariales de conocimiento
- Generación de contenido con fuentes verificables

## Limitaciones
- No elimina alucinaciones completamente
- Puede malinterpretar contexto de fuentes correctas
- RAG poisoning: fuentes factualmente correctas pero engañosas
- Dependencia de calidad de chunking y retrieval

## Referencias
- Lewis et al. (2020): Retrieval-Augmented Generation for Knowledge-Intensive NLP Tasks
- IBM Research: What is retrieval-augmented generation?
- Ars Technica: Can RAG keep AI models from making stuff up?
