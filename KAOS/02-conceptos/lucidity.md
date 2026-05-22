---
type: concept
title: Lucidity
aliases:
- lucidity
tags:
- concept
created: '2026-05-20'
modified: '2026-05-21'
confidence: media
status: draft
---

# Lucidity

**Tipo**: concepto técnico
**Tags**: #lucidity #calidad-codigo #analisis #codereview

Servidor MCP para análisis de calidad de código AI-generated. Analiza 10 dimensiones: complejidad innecesaria, abstracciones pobres, código eliminado accidentalmente, componentes alucinados, inconsistencias de estilo, vulnerabilidades de seguridad, problemas de rendimiento, duplicación, errores de manejo, cobertura de tests. Implementado vía `analyze_changes`. Instalado desde `github.com/hyperb1iss/lucidity-mcp` (Apache 2.0). Reemplaza al entry previo con `npx` que no funcionaba por ser proyecto Python, no npm.

**Nota**: Originalmente se intentó instalar via `npx -y lucidity-mcp` que falló porque el paquete es Python, no Node.js. Se instaló correctamente desde GitHub con pip.

**Relacionado con**: [[kosmos]], [[evaluacion]], [[cadena-verificacion]]


## Referencias Cruzadas
- Relacionado: [[github-mcp-oficial]]
- Relacionado: [[lucidity-mcp]]

