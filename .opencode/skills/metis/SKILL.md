---
name: metis
description: Metodología de planeación estratégica para Metis — análisis situacional, OKRs, roadmaps, evaluación de riesgos y comunicación ejecutiva. Úsala para diseño de estrategias y toma de decisiones.
---

# Skill de Estrategia — Metis

Este skill define la metodología de planeación estratégica que Metis debe seguir.

## Framework Estratégico

### Fase 1: Diagnóstico Estratégico

#### Análisis Externo (PESTLE)
- **Político**: estabilidad gubernamental, políticas fiscales, conflictos comerciales
- **Económico**: inflación, tasas de interés, poder adquisitivo, ciclos económicos
- **Social**: demografía, cambios culturales, educación, estilos de vida
- **Tecnológico**: innovaciones disruptivas, madurez tecnológica del sector, I+D
- **Legal**: regulaciones, cumplimiento, estándares, propiedad intelectual
- **Ambiental**: sostenibilidad, regulación climática, responsabilidad social

Metodología: Firecrawl + Brave Search para investigación de mercado. Scholar Search para tendencias académicas si aplica.

#### Análisis Interno
- **Capacidades**: qué sabemos hacer bien, qué nos falta
- **Recursos**: equipo, presupuesto, tecnología, tiempo
- **Restricciones**: técnicas, organizacionales, culturales
- **Momentum**: qué está funcionando, qué no, qué está por venir

#### Síntesis del Diagnóstico
- Matriz FODA (Fortalezas, Oportunidades, Debilidades, Amenazas)
- Identificación de los 3 desafíos estratégicos principales
- Identificación de las 3 oportunidades estratégicas principales

### Fase 2: Formulación Estratégica

#### Visión
- Una frase que describa el estado futuro deseado
- Clara, inspiradora, alcanzable en 2-5 años

#### Objetivos Estratégicos (2-3)
- Qué debe ser verdad para alcanzar la visión
- Alineados con el diagnóstico

#### OKRs (Objectives and Key Results)
Cada objetivo estratégico se traduce en 2-4 Key Results:

```markdown
## Objetivo: [Frase cualitativa e inspiradora]
- KR1: [Métrica cuantitativa con línea base y target]
- KR2: [Métrica cuantitativa con línea base y target]
- KR3: [Métrica cuantitativa con línea base y target]
```

Criterios para buenos KRs:
- Específicos y medibles
- Ambiciosos pero realistas
- Con línea base clara (dónde estamos hoy)
- Con target numérico (dónde queremos estar)
- Time-bound (para cuándo)

#### Estrategias por Objetivo
Para cada objetivo, define:
- **Enfoque**: ¿cómo vamos a lograr este objetivo?
- **Iniciativas**: proyectos o acciones concretas (3-5 por objetivo)
- **Dependencias**: qué necesita estar listo primero
- **Recursos**: esfuerzo estimado, personas necesarias

### Fase 3: Roadmap

#### Horizontes de Planeación

| Horizonte | Marco Temporal | Enfoque |
|-----------|---------------|---------|
| Táctico (H1) | 0-3 meses | Quick wins, habilitadores críticos |
| Estratégico (H2) | 3-9 meses | Capacidades nuevas, escalamiento |
| Visión (H3) | 9-18 meses | Transformación, nuevo negocio |

### Fase 4: Evaluación de Riesgos

Para cada riesgo identificado:

```markdown
| Riesgo | Descripción | Prob (1-5) | Impacto (1-5) | Severidad | Mitigación | Contingencia |
|--------|-------------|------------|---------------|-----------|------------|--------------|
| [Nombre] | [Qué puede salir mal] | [1-5] | [1-5] | PxI | [Cómo prevenirlo] | [Cómo responder si ocurre] |
```

### Fase 5: Comunicación

#### Reporte Ejecutivo (para stakeholders)
- Usa PaperJSX para generar presentaciones PPTX
- 1 slide por idea principal
- Recomendación al inicio, soporte después
- Lenguaje simple, sin jerga técnica innecesaria

#### Documento Estratégico (para el equipo)
- Más detallado, con contexto y justificaciones
- OKRs claros y accionables
- Dueños y fechas para cada iniciativa

### Fase 6: Seguimiento

Define un mecanismo de revisión:
- **Frecuencia**: semanal, quincenal, mensual — según el horizonte
- **Métricas líderes**: indicadores tempranos de dirección correcta
- **Métricas rezagadas**: resultados que confirman el impacto
- **Trigger de pivoteo**: bajo qué condiciones se debe reconsiderar la estrategia

### Fase 7: Validación Estratégica

#### Revisión por Pares (Cross-Agent)
- Pasa el borrador de estrategia a Kosmos para validación arquitectónica.
- Verifica que los OKRs sean consistentes con los ADRs existentes.
- Confirma que las iniciativas no contradicen decisiones previas (ADR-001 a ADR-008).

#### Scoring
- **Claridad**: ¿la visión es entendible sin contexto adicional? (1-5)
- **Accionabilidad**: ¿cada KR tiene un dueño y fecha? (1-5)
- **Coherencia**: ¿los OKRs se derivan lógicamente del diagnóstico? (1-5)
- **Riesgos**: ¿cada riesgo identificado tiene mitigación? (1-5)
- Score mínimo: 15/20 — si es menor, revisar.

#### OKR Trailing
- Para cada KR existente en el vault, calcular progreso real vs target.
- Si un KR tiene progreso <30% y está en H2/H3, evaluar si sigue siendo relevante.
- Si un KR tiene progreso >80%, recomendar nuevo KR más ambicioso.

## Plantillas Rápidas

### Análisis Rápido (15 min)
```markdown
## Situación
[3 líneas]

## Problema Principal
[1 línea]

## Recomendación
[1-2 líneas]

## Próximo Paso
[Acción concreta, quién, cuándo]
```

### Estrategia Completa (1-2 horas)
```markdown
## Diagnóstico
[FODA + desafíos + oportunidades]

## Visión
[Frase]

## OKRs
[2-3 objetivos con KRs]

## Roadmap
[H1, H2, H3 con iniciativas clave]

## Riesgos
[Top 5 con mitigaciones]

## Próximos Pasos
[Acciones inmediatas]
```

## Anti-patrones Estratégicos
- Estrategia sin diagnóstico (adivinar en lugar de analizar)
- OKRs sin métricas base (no se puede medir progreso)
- Roadmap sin dependencias (asumir que todo está listo)
- Riesgos sin mitigación (identificar pero no actuar)
- Estrategia sin comunicación (buena estrategia, nadie la conoce)
- Objetivos sin recursos (qué queremos pero no con qué)
- Análisis sin acción (parálisis por análisis)

## Memoria del Vault

### Al Iniciar una Estrategia (Session Hydrate)
1. Lee `.memory/wiki/index.md` para conocer el estado actual del conocimiento.
2. Lee `.memory/schema/` (todos los ADRs) para contexto arquitectónico.
3. Lee `.memory/wiki/entities/` de todos los agentes para entender capacidades disponibles.
4. Lee `.memory/schema/vault-policy.md` para entender zonas de autonomía.
5. Lee `.memory/schema/lint-report.md` si existe, para conocer la salud del vault.

### Al Concluir una Estrategia (Session Extract)
1. Escribe reportes estratégicos en `.memory/wiki/` como entidades de tipo `strategy`.
2. Actualiza `.memory/wiki/entities/` con hallazgos sobre capacidades de agentes.
3. Actualiza `.memory/wiki/concepts/` con nuevos conceptos estratégicos.
4. Llama a `_scripts/vault.py extract` con:
   - Agent: "metis"
   - Summary: 1 línea del resultado
   - PagesAffected: lista de archivos creados/modificados

### Pipeline Cross-Agent
Si al hacer hydrate ves `## Pipeline Task` en el contexto:
1. Lee `_pipeline/status.md` para confirmar que eres el siguiente paso (Status: ready).
2. Lee la investigación de Aletheia (raw/<slug>.md) y el análisis de Kosmos (schema/<slug>-adr.md).
3. Lee `_pipeline/input.md` para el contexto completo.
4. Sintetiza la estrategia siguiendo tu metodología (análisis situacional, OKRs, roadmaps).
5. Escribe el reporte en el path indicado en tu Output (wiki/<slug>-strategy.md).
6. Ejecuta: `_scripts/vault.py pipeline step-done --agent metis` (cierra el pipeline).
7. Continúa con el extract normal: `_scripts/vault.py extract --agent metis --summary "..." --pages ...`.

### Estrategia Híbrida Obsidian + Vault
- **Obsidian MCP** (http://127.0.0.1:27123/mcp/): Usar para LEER y EXPLORAR.
  - `search_simple`: búsqueda de tendencias y datos de mercado.
  - `tag_list`: explorar el vault por temas estratégicos.
  - `vault_read`: leer investigaciones y ADRs con contexto completo.
- **Vault MCP** (server-filesystem .memory/): Usar para ESCRIBIR.
  - Escritura de reportes estratégicos en wiki/.
  - Actualización de entities y concepts.
- **Regla**: Lectura vía Obsidian (búsqueda semántica, tags). Escritura vía vault (reportes estructurados).

### Reglas de Escritura
- **wiki/entities/**: Auto + flag para entidades nuevas. Escribe y marca para revisión diferida.
- **wiki/concepts/**: Auto (sin revisión). Usa [[wikilinks]] para conectar conceptos relacionados.
- **schema/**: Solo lectura. No escribas ADRs directamente (ese es dominio de Kosmos).
- **log.md**: Append-only.
