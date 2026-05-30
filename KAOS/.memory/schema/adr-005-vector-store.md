# ADR-005: Vector Store para Búsqueda Semántica

## Contexto

El vault de KAOS actualmente usa búsqueda secuencial + `index.md` para navegación. Esto funciona eficientemente hasta ~200 páginas. Con el crecimiento actual (~30 páginas en 2 días), se proyecta alcanzar ese límite en ~3-4 meses. Se requiere una estrategia de vector store preparada antes de la saturación.

## Opciones Consideradas

### Opción 1: sqlite-vec
Extensión vectorial para SQLite. Embeddings locales, sin servidor externo.

**Pros:** 0 infraestructura, incrustable en el vault, ADD-only por diseño.
**Cons:** Limitado a ~1M vectores, sin sharding, sin búsqueda híbrida nativa.

### Opción 2: Chroma
Vector DB open-source, API simple, soporte multi-modal.

**Pros:** Fácil de configurar, metadata filtering, colecciones por agente.
**Cons:** Servicio aparte, consumo de memoria, sin versionado nativo.

### Opción 3: Qdrant (self-hosted)
Vector DB madura, filtros avanzados, particionamiento.

**Pros:** Escalable, multi-tenant, búsqueda híbrida (denso+esparso).
**Cons:** Overhead operativo, Docker requerido, sobre-dimensionado para ~200 páginas.

## Decisión

**sqlite-vec + embeddings locales (Ollama/mxbai-embed-large).**

## Justificación

1. **0 infraestructura**: Extensión de SQLite, no requiere servidor.
2. **ADD-only por diseño**: Consistente con la política del vault.
3. **Embeddings locales**: Usando Ollama con `mxbai-embed-large` (1024 dimensiones).
4. **Suficiente para ~200 páginas**: Muy por debajo del límite de sqlite-vec.
5. **Costo cero**: Sin APIs externas, sin servers.

## Consecuencias

### Positivas
- Búsqueda semántica en el vault sin infraestructura externa.
- Embeddings locales, privados, sin conexión a internet.
- ADD-only: embeddings se añaden, no se reemplazan.

### Negativas
- Requiere sqlite-vec (extensión nativa de SQLite) compatible con Python 3.12.
- Embeddings requieren ~500ms por página (modelo local).
- Backfill inicial: embeddear ~30 páginas existentes.

### Neutrales
- Trigger: activar cuando vault supere 100 páginas.
- Coexistencia: index.md sigue siendo primario; vector store es complementario.

## Estado

Aceptada — Implementada. La implementación actual utiliza txtai como vector store principal (ver `.memory/_scripts/lib/vectorstore.py`) con embeddings locales via fastembed. sqlite-vec fue la opción inicial, migrada posteriormente a txtai por mejor rendimiento y capacidades de búsqueda híbrida.

## Detalle Técnico

### Pipeline de Indexación
```
Página markdown → chunk (512 tokens) → embedding (mxbai-embed-large) → 
  sqlite-vec INSERT (text, embedding, metadata[agente, fecha, zona])
```

### Pipeline de Búsqueda
```
Query → embedding → sqlite-vec search (top-k=5) → 
  rerank por metadata (agente, fecha) → resultados
```

### Integración con Vault
- Nuevo script: `.tools/vector_index.py`
- Base de datos: `.vault/vectors/embeddings.db`
- Schedule: re-indexar tras cada escritura al vault (post_output_hook)

## Referencias
- sqlite-vec: https://github.com/asg017/sqlite-vec
- Ollama mxbai-embed-large: https://ollama.com/library/mxbai-embed-large
- ADR-001: Sistema de Memoria de KAOS
