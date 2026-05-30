---
audience: agent
type: concept
source: Karpathy LLM Wiki — gist abril 2026
related: [memory-blocks, add-only-extraction]
tags: ["subject/agent", "subject/agentes", "subject/concept", "subject/conocimiento", "subject/extraction", "subject/kaos", "subject/karpathy", "subject/large-language-models"]
---

# Compile-then-query

Patrón donde el conocimiento se compila una vez (en ingest time) y se mantiene actualizado, en lugar de re-derivarse en cada consulta (como RAG). Definido por [[gist-karpathy-llm-wiki]] en su LLM Wiki.

## Ventajas
- ~95% menos tokens por query vs RAG (reportado: 71.5× menos)
- Latencia menor: solo sigue 1-3 páginas ya sintetizadas
- Conocimiento persistente y acumulativo

## Las 3 capas
1. **raw/**: Fuentes inmutables, human-owned
2. **wiki/**: Markdown generado y mantenido por LLM (entities, concepts, sources, index.md, log.md)
3. **schema/**: Archivo de configuración que define convenciones

## Aplicación en KAOS
KAOS ya implementa este patrón: `.memory/raw/` → `.memory/wiki/` + `.memory/schema/KAOS.md` — conocido como [[pipeline-conocimiento-raw-wiki]].

## Agentes que lo usan
- [[aletheia]] compila conocimiento durante sus investigaciones
- [[kosmos]] lo implementa en el diseño del vault
- [[metis]] consume el conocimiento compilado para fundamentar estrategias
- [[mnemosyne]] lo implementa en su fase de destilación raw→wiki


## Referencias Cruzadas
- Relacionado: [[sin-páginas-huérfanas]]
- Relacionado: [[fuentes-consultadas]]
- Relacionado: [[llm-wiki]]
- Relacionado: [[gestion-conocimiento]]
- Relacionado: [[estado-memoria-sesion]]
- Relacionado: [[txtai]]
- Relacionado: [[component-nivel-3]]
- Relacionado: [[vault]]
