---
type: investigacion
agent: aletheia
date: 2026-05-20
confidence: alta
tags: [prompt-engineering, llm, ingenieria-prompts, tecnicas]
fuentes: [wikipedia, arxiv, ieee]
---

# Investigación: Prompt Engineering

## Concepto
Proceso de estructurar entradas de lenguaje natural para producir salidas específicas de un modelo generativo de IA. Incluye context engineering: gestión de metadatos, tools, tokens y system prompts.

## Técnicas Principales
- **Multi-shot (few-shot)**: incluir ejemplos en el prompt para aprendizaje en contexto
- **Chain-of-Thought (CoT)**: resolver problemas como serie de pasos intermedios
- **Tree-of-Thought (ToT)**: múltiples líneas de razonamiento en paralelo con backtracking
- **Self-consistency**: múltiples rollouts CoT, seleccionar conclusión más común
- **Role assignment**: asignar un rol/personalidad al modelo
- **Context engineering**: gestión de system prompts, retrieved knowledge, tool definitions

## Automatización
- RAG: recuperación automática de documentos relevantes
- GraphRAG: uso de knowledge graphs para conectar información dispersa
- Auto-CoT: generación automática de ejemplos CoT
- DSPy: optimización programática de prompts
- Gradient descent: búsqueda de embeddings óptimos

## Context Engineering
- System instructions, retrieved knowledge, tool definitions
- Token budgeting, provenance tags, versioning
- Observability y regression tests para contextos
- Runtime orchestration (LangChain, DSPy, FlowPrompt)

## Riesgos
- Prompt injection: ataques que manipulan el comportamiento del modelo
- Sensibilidad a variaciones mínimas en formato y redacción
- Hasta 76 puntos de diferencia en accuracy según formato del prompt

## Referencias
- Wei et al. (2022): Chain-of-Thought Prompting Elicits Reasoning in LLMs
- Schulhoff et al. (2024): The Prompt Report - Systematic Survey
- IEEE Spectrum: AI Prompt Engineering is Dead? (2024)
