---
type: investigation
agent: aletheia
date: 2026-05-20
confidence: alta
status: complete
tags: [testing, evaluation, audit, strategy, planning, kosmos, metis]
---

# Investigación: Herramientas Open-Source para Testing, Evaluación, Auditoría y Estrategia

## Resumen Ejecutivo
1. **Para Kosmos (Testing/Evaluación):** DeepEval (15.6K⭐) y LangFuse (27.6K⭐) lideran para testing LLM y observabilidad.
2. **Para Metis (Estrategia):** Leantime (9.9K⭐) es el mejor fit OKR open-source. Quarto (5.7K⭐) para reportes multi-formato.
3. **Brecha:** No hay herramientas open-source maduras para BMC, scenario planning o árboles de decisión estratégicos.

## Recomendaciones para KAOS

### Prioridad Alta
- **Kosmos → DeepEval**: Testing tipo pytest para agentes multi-paso. RAG + Agent + Multi-turn metrics. Apache 2.0.
- **Kosmos → LangFuse**: Observabilidad total. Self-hosted Docker. MIT.
- **Kosmos → Mermaid.js**: Diagramas versionables en Markdown. 88.2K⭐.
- **Metis → Quarto**: Reportes PDF+PPTX+HTML desde una fuente. Único.
- **Metis → Leantime**: OKRs con jerarquía Goal→Milestone→Todo. Self-hosted.
- **Metis → Metabase**: BI para ejecutivos no técnicos. 47.4K⭐.

### Prioridad Media
- **Kosmos → RAGAS**: Evaluación RAG especializada. 14K⭐.
- **Kosmos → DSPy**: Optimización de prompts. 34.5K⭐.
- **Kosmos → Structurizr**: Modelado C4. DSL-based.
- **Metis → OpenProject**: Roadmaps con Gantt enterprise.

## Stack Recomendado
```
KOSMOS: DeepEval + LangFuse + Mermaid + RAGAS + DSPy + Structurizr + SonarQube
METIS:  Leantime + Quarto + Metabase + Mermaid + Excalidraw + OpenProject
```

## Matriz de Confianza
| Afirmación | Confianza | Notas |
|------------|-----------|-------|
| DeepEval es Apache 2.0 y pip-installable | Alta | Verificado en GitHub |
| LangFuse es #1 en estrellas LLM obs (27.6K) | Alta | Verificado ranking GitHub |
| Leantime es mejor fit OKR open-source | Alta | Único con Goal→Milestone→Todo |
| Quarto produce PDF+PPTX+HTML desde una fuente | Alta | CLI `quarto render` |


## Referencias
- [[index]]
- [[log]]
- [[checkpoint]]
- [[vault]]
