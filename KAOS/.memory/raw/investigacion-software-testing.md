---
type: investigacion
agent: aletheia
date: 2026-05-20
confidence: alta
tags: [testing, calidad, software, verification, validacion]
fuentes: [wikipedia, ieee, istqb]
---

# Investigación: Software Testing y Aseguramiento de Calidad

## Concepto
Acto de verificar que el software cumple sus objetivos y satisface las expectativas. Proporciona información objetiva sobre la calidad y el riesgo de fallo.

## Niveles de Testing
1. **Unit Testing**: verificación de componentes aislados (código fuente)
2. **Integration Testing**: verificación de interacciones entre componentes
3. **System Testing (E2E)**: verificación del sistema completo
4. **Acceptance Testing**: verificación contra requisitos del usuario

## Categorías Principales
- **Funcional vs No-Funcional**: qué hace vs cómo lo hace
- **Estático vs Dinámico**: revisión de código vs ejecución de pruebas
- **Caja Blanca vs Caja Negra**: conocimiento interno vs solo especificación
- **Manual vs Automatizado**: ejecución humana vs scripts
- **Regresión**: verificar que cambios no rompen funcionalidad existente
- **Smoke/Sanity**: verificación rápida post-cambio
- **Exploratorio**: aprendizaje y diseño simultáneo durante la ejecución

## Pirámide de Testing
```
    /\
   /E2E\
  /Integr\
 / Unit    \
/___________\
```

## Métricas de Calidad
- Code coverage: statement, branch, function, path
- Defect density: bugs por KLOC
- Mean time to failure (MTTF)
- Test pass rate
- Requirements coverage

## Automatización
- CI/CD integration: pruebas automáticas en cada commit
- Test automation frameworks: pytest, Jest, Selenium, Cypress
- Property-based testing: Hypothesis, QuickCheck
- Mutation testing: validar calidad de tests
- Fuzz testing: entradas aleatorias para encontrar fallos

## Verificación vs Validación
- **Verificación**: "are we building the product right?" (static)
- **Validación**: "are we building the right product?" (dynamic)

## Aplicación en KAOS
- Smoke check (2 min): verificación rápida post-output
- Functional (15 min): análisis diario de scores
- Audit (60 min): evaluación semanal completa
- Cross-agent verification: Aletheia→Kosmos→Metis→Aletheia

## Referencias
- Myers (1979): The Art of Software Testing
- ISTQB: International Software Testing Qualifications Board
- NIST (2002): The Economic Impacts of Inadequate Infrastructure for Software Testing

## Matriz de Confianza

| Aspecto | Confianza | Evidencia |
|---------|-----------|-----------|
| Fuentes primarias | Alta | M�ltiples referencias cruzadas verificadas |
| Consistencia interna | Alta | Sin contradicciones detectadas con el vault existente |
| Reproducibilidad | Media | Fuentes documentadas y accesibles |
| Actualizaci�n | Reciente | Informaci�n vigente al momento de ingesta |

## Referencias
- [[index]]
- [[log]]
- [[checkpoint]]