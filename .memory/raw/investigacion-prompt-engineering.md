---
type: investigacion
agent: aletheia
date: 2026-05-20
confidence: alta
tags: [prompt-engineering, llm, ingenieria-prompts, tecnicas]
fuentes: [wikipedia, arxiv, ieee]
---

# Investigaci贸n: Prompt Engineering

## Concepto
Proceso de estructurar entradas de lenguaje natural para producir salidas espec铆ficas de un modelo generativo de IA. Incluye context engineering: gesti贸n de metadatos, tools, tokens y system prompts.

## T茅cnicas Principales
- **Multi-shot (few-shot)**: incluir ejemplos en el prompt para aprendizaje en contexto
- **Chain-of-Thought (CoT)**: resolver problemas como serie de pasos intermedios
- **Tree-of-Thought (ToT)**: m煤ltiples l铆neas de razonamiento en paralelo con backtracking
- **Self-consistency**: m煤ltiples rollouts CoT, seleccionar conclusi贸n m谩s com煤n
- **Role assignment**: asignar un rol/personalidad al modelo
- **Context engineering**: gesti贸n de system prompts, retrieved knowledge, tool definitions

## Automatizaci贸n
- RAG: recuperaci贸n autom谩tica de documentos relevantes
- GraphRAG: uso de knowledge graphs para conectar informaci贸n dispersa
- Auto-CoT: generaci贸n autom谩tica de ejemplos CoT
- DSPy: optimizaci贸n program谩tica de prompts
- Gradient descent: b煤squeda de embeddings 贸ptimos

## Context Engineering
- System instructions, retrieved knowledge, tool definitions
- Token budgeting, provenance tags, versioning
- Observability y regression tests para contextos
- Runtime orchestration (LangChain, DSPy, FlowPrompt)

## Riesgos
- Prompt injection: ataques que manipulan el comportamiento del modelo
- Sensibilidad a variaciones m铆nimas en formato y redacci贸n
- Hasta 76 puntos de diferencia en accuracy seg煤n formato del prompt

## Referencias
- Wei et al. (2022): Chain-of-Thought Prompting Elicits Reasoning in LLMs
- Schulhoff et al. (2024): The Prompt Report - Systematic Survey
- IEEE Spectrum: AI Prompt Engineering is Dead? (2024)

## Matriz de Confianza

| Aspecto | Confianza | Evidencia |
|---------|-----------|-----------|
| Fuentes primarias | Alta | M鷏tiples referencias cruzadas verificadas |
| Consistencia interna | Alta | Sin contradicciones detectadas con el vault existente |
| Reproducibilidad | Media | Fuentes documentadas y accesibles |
| Actualizaci髇 | Reciente | Informaci髇 vigente al momento de ingesta |

## Referencias
- [[index]]
- [[log]]
- [[checkpoint]]