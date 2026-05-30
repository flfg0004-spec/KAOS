# Domain Mapper — SKILL

## Descripción
Agrupa componentes técnicos del arch_graph en dominios de negocio (bounded contexts) usando clustering semántico. Produce un reporte markdown con matriz de dependencias, glosario y diagrama Mermaid coloreado por contexto.

## Algoritmo
1. Extract node features from arch_graph → `extract_node_features()`
2. Compute embeddings via txtai MCP → `compute_embeddings()`
3. Cluster with K-Means (sklearn) → `cluster_nodes()`
4. Name clusters by dominant node type → `name_clusters()`
5. Generate report with dependency matrix + glossary → `generate_report()`
6. Fallback: rule-based clustering by `node_type` when txtai unavailable

## Comando
`/domain-map [topic]`

## Output
Guarda en `.memory/wiki/reports/domain-map-{slug}.md`

## Integración
Disponible para Metis. Feature flag: `use_domain_mapper`

## Ejemplo
```
/domain-map kaos-system
→ .memory/wiki/reports/domain-map-kaos-system.md
→ 4 bounded contexts, matriz 4x4, 2 high-coupling detected
```

## Dependencias
- txtai MCP (embeddings) — fallback rule-based disponible
- scikit-learn (K-Means) — fallback rule-based disponible
- arch_graph con datos poblados
