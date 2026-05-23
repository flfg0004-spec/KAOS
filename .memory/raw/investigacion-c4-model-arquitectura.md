---
type: investigacion
agent: aletheia
date: 2026-05-20
confidence: alta
tags: [c4, arquitectura, diagramas, modelado, structurizr]
fuentes: [wikipedia, c4model]
---

# Investigación: C4 Model para Arquitectura de Software

## Historia
- Creado por Simon Brown entre 2006 y 2011
- Basado en UML y 4+1 architectural view model
- Sitio oficial lanzado bajo licencia Creative Commons en 2018

## Niveles C4
1. **Context (Nivel 1)**: sistema y sus relaciones con usuarios y otros sistemas
2. **Container (Nivel 2)**: aplicaciones y stores de datos que componen el sistema
3. **Component (Nivel 3)**: componentes dentro de cada contenedor
4. **Code (Nivel 4)**: detalle de diseño mapeable a código (UML, ERD, IDE)

## Elementos Básicos
- Personas (usuarios, actores)
- Software systems
- Containers (apps, databases, microservicios)
- Components (módulos, clases, paquetes)
- Relationships (conexiones e interacciones)

## Herramientas
- **Structurizr**: diagrams as code, modelo único → múltiples diagramas
- **PlantUML + C4-PlantUML**: diagramas versionables en markdown
- **IcePanel**: diagramación colaborativa drag-and-drop
- **C4InterFlow**: Architecture as Code (AaC) en YAML/JSON

## Beneficios
- Jerarquía clara: different zoom levels for different audiences
- Diagrams as code: versionable, revisable, automatizable
- Lean: solo lo necesario, sin overmodelling
- Agile-friendly: facilita arquitectura evolutiva

## Referencias
- c4model.com (sitio oficial de Simon Brown)
- InfoQ: The C4 Model for Software Architecture (2018)
- Fundamentals of Software Architecture (Richards & Ford, 2019)
