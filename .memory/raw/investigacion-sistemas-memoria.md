# Investigación Comparativa: Sistemas de Memoria para IA

**Investigador**: Aletheia
**Fecha**: 2026-05-19
**Confianza general**: Alta

## Resumen
Análisis de tres sistemas de memoria con arquitecturas distintas: Letta (agente-como-SO), Karpathy LLM Wiki (compilación de conocimiento) y Mem0 (capa de memoria como servicio).

## Hallazgos clave
- **Letta**: Framework de agentes stateful con memoria jerárquica OS-like. 3 niveles (Core/Recall/Archival). Memory blocks. Sleep-time compute. Context Repositories (git). 21.8K★. Apache 2.0.
- **LLM Wiki**: Patrón 3 capas (raw/wiki/schema) donde el LLM compila conocimiento persistente en markdown. 16M+ vistas. compile-then-query elimina RAG en ~95%. Límite ~200 páginas.
- **Mem0**: Pipeline ADD-only de extracción + multi-signal retrieval (semantic + BM25 + entity). 47.8K★. $24M funding. Benchmarks disputados por Letta/Zep.

## Fuentes principales
- arXiv:2310.08560 (MemGPT)
- arXiv:2504.13171 (Sleep-time Compute)
- arXiv:2504.19413 (Mem0)
- gist.github.com/karpathy/442a6bf555914893e9891c11519de94f (LLM Wiki)

## Recomendación para KAOS
Arquitectura híbrida: jerarquía de Letta + compilación de LLM Wiki + extracción de Mem0.

## Matriz de Confianza

| Aspecto | Confianza | Evidencia |
|---------|-----------|-----------|
| Fuentes primarias | Alta | M�ltiples referencias cruzadas verificadas |
| Consistencia interna | Alta | Sin contradicciones detectadas con el vault existente |
| Reproducibilidad | Media | Fuentes documentadas y accesibles |
| Actualizaci�n | Reciente | Informaci�n vigente al momento de ingesta |

## Referencias
- [[index]]
- [[log]]
- [[checkpoint]]