# Knowledge Tour Generator — SKILL

## Descripción
Genera guías de aprendizaje topológicas del vault de conocimiento usando VaultGraph (NetworkX DiGraph). Produce un documento markdown ordenado por dependencias con secciones Start Here → Core Concepts → Advanced Topics.

## Algoritmo
1. Build VaultGraph from wikilinks (via `lib.wikilinks.build_graph()`)
2. Apply Kahn's algorithm for topological sort → `topological_layers()`
3. Detect cycles → `detect_cycles()`
4. Assign learning levels (0 = Start, medium = Core, max = Advanced)
5. Generate markdown with frontmatter, Mermaid diagram, and per-level tables

## Comando
`/knowledge-tour [topic]`

## Output
Guarda en `.memory/wiki/guides/knowledge-tour-{slug}.md`

## Integración
Disponible para Kosmos. Feature flag: `use_knowledge_tour`

## Ejemplo
```
/knowledge-tour kaos-architecture
→ .memory/wiki/guides/knowledge-tour-kaos-architecture.md
→ 3 niveles, 12 nodos, 0 ciclos
```
