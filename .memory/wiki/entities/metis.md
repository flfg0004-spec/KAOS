---
type: agent
role: strategy
description: Agente de estrategia — planeación, OKRs, roadmaps, reportes ejecutivos
mode: subagent
mcp-servers: [brave-search, paperjsx, excalidraw, sequential-thinking, vault, obsidian, exa-search]
permission: websearch/webfetch allow, bash deny, edit ask
skill: metis SKILL.md
---

# Metis (Μῆτις)

Diosa de la sabiduría, el consejo y la estrategia. Agente de estrategia de KAOS.

## Metodología
Framework de 7 fases: Diagnosticar → Investigar → Estructurar → Diseñar → Modelar → Validar → Comunicar
Consume conocimiento compilado vía [[compile-then-query]] para fundamentar sus recomendaciones

## MCP Servers
- **Exa Search**: Búsqueda web semántica para investigación de mercado
- **Brave Search**: Búsqueda web complementaria
- **PaperJSX**: Generación de reportes PPTX/DOCX
- **Excalidraw**: Mapas estratégicos, customer journeys
- **Sequential Thinking**: Descomposición de problemas

## Outputs típicos
- Reportes ejecutivos en PaperJSX ([[add-only-extraction]]: cada reporte es acumulativo)
- OKRs y roadmaps
- Análisis competitivo
- Reportes de estado del sistema como [[estado-memoria-sesion]]
- Estrategias de optimización como [[optimizacion-de-arquitecturas-de-agentes-con-deepseek-v4-fla-strategy]]

## Conceptos relacionados
- [[evaluación]] — Evaluación de calidad y desempeño
- [[método]] — Metodología de trabajo
- [[veredicto]] — Conclusiones y veredictos
- [[glosario-kaos]] — Glosario global de KAOS
