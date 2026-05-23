# ADR-001: Arquitectura de Memoria de KAOS

## Contexto

KAOS es un sistema compuesto por tres agentes subagent (Aletheia, Kosmos, Metis) que operan dentro de OpenCode. Cada agente tiene capacidades, herramientas y permisos distintos, pero comparten un problema fundamental: **no existe un mecanismo estructurado para que el conocimiento generado por un agente persista entre sesiones y sea accesible por los demás**.

Actualmente:
- Cada agente inicia cada sesión sin memoria de interacciones previas.
- Los hallazgos de investigación de Aletheia se pierden al cerrar la sesión.
- Las decisiones arquitectónicas de Kosmos no persisten para futuras consultas.
- Los análisis estratégicos de Metis no tienen un repositorio compartido.
- El vault `.memory/` existe como estructura de directorios con archivos semilla, pero sin un flujo definido de operación ni reglas de gobernanza entre agentes.

Se requiere una arquitectura de memoria que:
1. **Persista el conocimiento** entre sesiones de todos los agentes.
2. **Jerarquice la información** en niveles según su volatilidad y frecuencia de acceso.
3. **Defina flujos claros** de escritura/lectura entre agentes.
4. **Escale** desde el volumen actual (~10 páginas) hasta cientos de páginas.
5. **Sea transparente** — los agentes deben entender qué información existe y dónde encontrarla.

## Opciones Consideradas

### Opción 1: Letta (Framework completo de agentes stateful)

Letta (ex-MemGPT) es un framework de agentes con memoria jerárquica OS-like (Core/Recall/Archival), memory blocks, sleep-time compute y context repositories con backend git.

**Pros:**
- Arquitectura madura con 21.8K★ en GitHub.
- Memoria jerárquica bien definida (3 niveles).
- Context Repositories con git para persistencia.
- Sleep-time compute para consolidación entre sesiones.
- Memory pressure signals para gestión de contexto.

**Cons:**
- Framework completo que substituiría la arquitectura actual de subagents.
- Requiere integrar un runtime externo (no es compatible con el modelo subagent de OpenCode).
- Overhead operativo significativo para el tamaño actual del proyecto.
- Dependencia de un proyecto externo con su propio ciclo de releases.
- La integración con MCP no está probada.

### Opción 2: LLM Wiki (Patrón de compilación de conocimiento en markdown)

Patrón popularizado por Andrej Karpathy donde el LLM mantiene un wiki en markdown con estructura 3-capas (raw/wiki/schema). El conocimiento se compila en el momento de ingesta (compile-then-query), eliminando la necesidad de RAG en ~95% de los casos.

**Pros:**
- Extremadamente simple — solo requiere archivos markdown.
- compile-then-query elimina latencia de RAG.
- Transparencia total — humanos y LLMs leen el mismo formato.
- Sin infraestructura adicional (no requiere BD vectorial inicialmente).
- Escala hasta ~200 páginas sin problemas de rendimiento.
- Compatible con MCP server-filesystem.

**Cons:**
- Sin búsqueda semántica nativa (se vuelve necesario un vector store >200 páginas).
- Sin memoria jerárquica explícita (todo es "archival").
- Sin mecanismo de memory pressure (el contexto del LLM se gestiona manualmente).
- Sin entity linking automático.
- El mantenimiento del índice (index.md) es manual.

### Opción 3: Mem0 (Capa de memoria como servicio)

Mem0 es una capa de memoria para LLMs con pipeline ADD-only, multi-signal retrieval (semantic + BM25 + entity), 47.8K★ y $24M en funding.

**Pros:**
- Pipeline de extracción robusto (ADD-only, entity linking, multi-signal).
- API simple y bien documentada.
- Benchmarks de rendimiento en retrieval.
- Soporte para memoria a largo plazo.

**Cons:**
- Servicio externo con dependencia de API.
- Sin control sobre los datos (privacidad).
- Costos recurrentes a escala.
- Benchmarks disputados por Letta/Zep.
- Sin jerarquía de memoria (todo es plano).
- No resuelve el problema de compilación de conocimiento estructurado.

### Opción 4: Arquitectura Híbrida (Seleccionada)

Combinación de los tres patrones:
- **Jerarquía de Letta**: Core Memory (en contexto) + Working Memory (scratchpad FIFO) + Archival Memory (vault git).
- **Compilación de LLM Wiki**: Estructura raw/wiki/schema con compile-then-query.
- **Extracción de Mem0**: Pipeline ADD-only, entity linking, multi-signal retrieval (para cuando se necesite vector store).

## Decisión

**Arquitectura Híbrida**, combinando los patrones de Letta (jerarquía), LLM Wiki (compilación) y Mem0 (extracción), implementada sobre el vault `.memory/` con protocolo MCP.

## Justificación

La arquitectura híbrida es la opción correcta por las siguientes razones:

1. **Alineación con la arquitectura existente**: Los agentes ya están definidos como subagents de OpenCode con permisos granularizados. La arquitectura híbrida respeta esta estructura sin requerir un framework externo.

2. **Simplicidad inicial, potencia a escala**: Comenzamos con markdown vault (LLM Wiki) que escala a ~200 páginas sin infraestructura adicional. Cuando el volumen lo requiera, añadimos vector store (Mem0-inspired) sin cambiar la estructura fundamental.

3. **Jerarquía explícita**: La división Core/Working/Archival (Letta-inspired) resuelve el problema real de gestión de contexto limitado de los LLMs, sin la complejidad de un framework completo.

4. **compile-then-query**: Este patrón elimina la latencia y el costo de RAG en el 95% de los casos, porque el conocimiento se estructura al ingestar, no al consultar.

5. **ADD-only + git**: Ningún conocimiento se pierde. El vault es un repositorio git con historial completo. Las contradicciones se marcan explícitamente, no se sobrescriben.

6. **MCP como protocolo**: El vault MCP server (`@modelcontextprotocol/server-filesystem`) ya está configurado. La comunicación entre agentes y memoria es a través de este protocolo estándar.

7. **Permisos granularizados**: Cada agente tiene permisos específicos sobre el vault (edit deny/ask), lo que previene corrupción accidental del conocimiento compartido.

## Consecuencias

### Positivas
- **Persistencia inmediata**: El conocimiento generado por cualquier agente persiste entre sesiones.
- **Costo cero de infraestructura**: Sin dependencias externas (BD, APIs, servicios cloud).
- **Transparencia total**: Humanos y agentes leen el mismo formato markdown.
- **Evolución orgánica**: La arquitectura escala añadiendo componentes (vector store) sin cambiar la base.
- **Git como fuente de verdad**: Historial completo, diffs, rollbacks.
- **Flujo definido**: Cada agente sabe qué leer y dónde escribir.

### Negativas
- **Mantenimiento manual del índice**: index.md y log.md requieren que los agentes los actualicen disciplinadamente.
- **Sin enforcements automáticos**: Los permisos (edit deny/ask) dependen de la configuración de OpenCode, no hay validación del lado del vault.
- **Latencia de compilación**: El compile-then-query tiene costo en el momento de ingesta (el LLM debe procesar y estructurar el conocimiento).

### Neutrales
- **Límite de ~200 páginas**: Antes de necesitar vector store, el vault operará eficientemente con búsqueda secuencial + index.md.
- **Curva de aprendizaje**: Los agentes deben aprender a navegar el vault (index.md primero, luego wikilinks).
- **Gobernanza manual**: La revisión de calidad del contenido del vault depende de la supervisión humana.

## Estado

Aceptada

## Detalle Técnico de la Arquitectura

### Jerarquía de Memoria (Letta-inspired)

```
Core Memory (volátil, por sesión)
  ├── Tarea actual del agente
  ├── Preferencias del humano
  ├── Persona del agente
  └── Contexto inmediato (~4K tokens)
        ↓ (cuando se excede capacidad)
Working Memory (volátil, por sesión)
  ├── Historial reciente de acciones
  ├── Scratchpad de razonamiento
  ├── FIFO queue con presión al 70%
  └── Buffer de ~8K tokens
        ↓ (al finalizar sesión o en ingest explícita)
Archival Memory (persistente, entre sesiones)
  ├── Vault Markdown (raw/ → wiki/ → schema/)
  │   ├── raw/   — Investigaciones inmutables (Aletheia)
  │   ├── wiki/  — Conocimiento compilado (todos)
  │   │   ├── entities/ — Páginas de agentes/entidades
  │   │   ├── concepts/ — Conceptos con [[wikilinks]]
  │   │   ├── sources/  — Fuentes con metadata
  │   │   ├── index.md  — Catálogo de navegación
  │   │   └── log.md    — Bitácora cronológica
  │   └── schema/ — ADRs y reglas del vault
  ├── Git Backend (historial, diffs, rollbacks)
  └── Vector Store (futuro — embeddings + multi-signal)
```

### Flujo de Datos entre Agentes

```
┌──────────────┐     ┌──────────────┐     ┌──────────────┐
│   Aletheia   │     │    Kosmos    │     │    Metis     │
│ (Research)   │     │(Architecture)│     │ (Strategy)   │
└──────┬───────┘     └──────┬───────┘     └──────┬───────┘
       │                     │                     │
       │ 1. Investiga        │                     │
       │    (web, papers)    │                     │
       ▼                     │                     │
┌──────────────┐             │                     │
│   raw/       │────────────►│ 2. Lee raw/ + wiki/ │
│ (inmutable)  │             │    para contexto     │
└──────────────┘             ▼                     │
                       ┌──────────────┐             │
                       │   schema/    │────────────►│ 3. Lee raw/ + wiki/
                       │ (ADRs, reglas)│            │    + schema/ para
                       └──────────────┘            │    análisis estratégico
                                                    ▼
                                            ┌──────────────┐
                                            │   wiki/      │
                                            │ (reportes)   │
                                            │ PaperJSX     │
                                            └──────────────┘
                               │
                               │ 4. En cada ciclo:
                               ▼
                    ┌─────────────────────┐
                    │  index.md update    │
                    │  log.md append      │
                    └─────────────────────┘
```

### Reglas de Acceso por Agente

| Agente    | raw/       | wiki/      | schema/    | Fuentes externas |
|-----------|------------|------------|------------|------------------|
| Aletheia  | Escribe    | Lee        | —          | web, papers, RSS |
| Kosmos    | Lee        | Lee        | Escribe    | git, código      |
| Metis     | Lee        | Escribe    | Lee        | —                |

### Pipeline de Ingesta (compile-then-query)

```
1. Nueva fuente externa (web, paper, RSS)
       │
       ▼
2. Aletheia investiga → raw/investigacion-<tema>.md
       │  (formato libre, preservación completa)
       ▼
3. Extracción ADD-only (Mem0-inspired)
       │  - Extraer entidades, conceptos, claims
       │  - Preservar versiones anteriores
       │  - Marcar contradicciones con ⚠️
       ▼
4. Compilación a wiki/ (LLM Wiki-inspired)
       │  - entities/<entidad>.md
       │  - concepts/<concepto>.md
       │  - sources/<fuente>.md
       ▼
5. Kosmos analiza → schema/adr-<n>.md (si aplica)
       │
       ▼
6. index.md se actualiza con nuevo contenido
       │
       ▼
7. log.md se actualiza con registro cronológico
```

### Estrategia de Vector Store (Futuro — cuando vault >150 páginas)

- **Trigger**: Cuando index.md exceda ~150 entradas o la búsqueda secuencial sea lenta.
- **Implementación**: Embeddings locales (sqlite-vec o chroma) sobre las páginas del vault.
- **Retrieval**: Multi-signal (semántico + BM25 + entity matching, inspirado en Mem0).
- **ADD-only**: Los embeddings se añaden, no se reemplazan (consistente con la política del vault).
- **Backfill**: Cuando se active, se embedcean todas las páginas existentes del vault.

## Referencias

- LLM Wiki (Karpathy): https://gist.github.com/karpathy/442a6bf555914893e9891c11519de94f
- Letta/MemGPT: arXiv:2310.08560
- Mem0: arXiv:2504.19413
- Sleep-time Compute: arXiv:2504.13171
- Investigación completa en: `raw/investigacion-sistemas-memoria.md`
