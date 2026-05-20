---
name: kosmos
description: Metodología de análisis arquitectónico para Kosmos — framework C4, ADRs, evaluación de salud arquitectónica y documentación de sistemas. Úsala para análisis y diseño de arquitectura de software.
---

# Skill de Arquitectura — Kosmos

Este skill define el framework de análisis y diseño arquitectónico que Kosmos debe seguir.

## Framework de Análisis Arquitectónico

### 1. Descubrimiento del Sistema

#### Análisis Estructural
- Usa `glob` y `grep` para mapear la estructura del proyecto.
- Identifica lenguaje(s), frameworks, patrones y convenciones.
- Determina la arquitectura de alto nivel: monolito, microservicios, híbrido, etc.
- Usa Depwire para obtener:
  - Grafo de dependencias completo
  - Health score arquitectónico (0-100)
  - Clasificación de roles de cada símbolo (entry point, core, utility, adapter, dead)

#### Análisis de Comportamiento
- Identifica flujos principales: entrada → procesamiento → salida
- Mapea signal chains (cómo fluye una request HTTP a través del sistema)
- Identifica side effects: llamadas a BD, APIs externas, file system, colas

### 2. Modelado C4 (Structurizr)

#### Nivel 1 — Contexto
- Sistema y sus actores externos (usuarios, sistemas, APIs)
- Relaciones e interfaces principales
- Tecnologías visibles desde fuera

#### Nivel 2 — Contenedores
- Aplicaciones, servicios, bases de datos, colas, caches
- Responsabilidades de cada contenedor
- Protocolos de comunicación entre contenedores

#### Nivel 3 — Componentes
- Módulos principales dentro de cada contenedor
- Interfaces y dependencias entre componentes
- Patrones usados (MVC, hexagonal, DDD, etc.)

#### Nivel 4 — Código (opcional)
- Solo para componentes críticos o de alta complejidad
- Clases/funciones principales y relaciones

### 3. Análisis de Salud Arquitectónica

Usa Depwire para estas mediciones:

| Métrica | Descripción | Objetivo |
|---------|-------------|----------|
| Health Score | Evaluación general 0-100 | >70 |
| Complejidad ciclomática | Complejidad por módulo | <15 por función |
| Acoplamiento | Dependencias entre módulos | Bajo entre módulos no relacionados |
| Cohesión | Relación interna de cada módulo | Alta dentro del mismo dominio |
| Código muerto | Símbolos no referenciados | 0 |
| Ciclos de dependencia | Dependencias circulares | 0 |
| Deuda técnica estimada | Esfuerzo para refactorizar | Gestionable |

### 4. Decisiones Arquitectónicas (ADRs)

Cada ADR debe incluir:

```markdown
# ADR-[N]: [Título descriptivo]

## Contexto
[Problema o situación que motiva la decisión]

## Opciones Consideradas
1. [Opción A] — [pros/cons]
2. [Opción B] — [pros/cons]
3. [Opción C] — [pros/cons]

## Decisión
[Opción seleccionada]

## Justificación
[Por qué esta opción es la mejor dadas las restricciones]

## Consecuencias
- Positivas: [lista]
- Negativas: [lista]
- Neutrales: [lista]

## Estado
Aceptada | Propuesta | Deprecada | Reemplazada por ADR-[N]
```

### 5. Visualización

- **Bocetos rápidos**: Excalidraw para diagramas exploratorios e interactivos.
- **C4 formal**: Structurizr para modelos arquitectónicos que evolucionan con el código.
- **Diagramas en documentación**: PlantUML o Mermaid para incluir en archivos markdown.

### 6. Documentación de Arquitectura

```markdown
# Arquitectura de [Sistema]

## Visión General
[Propósito y contexto del sistema]

## Principios Arquitectónicos
1. [Principio 1]
2. [Principio 2]

## Diagrama de Contexto
[Diagrama C4 Nivel 1]

## Diagrama de Contenedores
[Diagrama C4 Nivel 2]

## Decisiones Clave
- [ADR-001: Título]
- [ADR-002: Título]

## Guías de Evolución
- [Cómo agregar una nueva feature]
- [Cómo modificar un componente existente]
- [Cómo deprecar un componente]

## Glossary
- [Término]: [definición]
```

## Anti-patrones Arquitectónicos a Señalar
- Dependencias circulares entre módulos
- Componentes con múltiples responsabilidades (Dioses)
- Acoplamiento excesivo entre capas
- Falta de fronteras entre contextos delimitados
- APIs internas que filtran detalles de implementación
- Base de datos como integración (muchos servicios acceden a la misma BD)
- Ausencia de manejo de errores en fronteras del sistema

## Memoria del Vault

### Al Iniciar un Análisis (Session Hydrate)
1. Lee `.memory/wiki/index.md` para conocer el estado actual del conocimiento.
2. Lee `.memory/schema/` (todos los ADRs) para decisiones arquitectónicas previas.
3. Lee `.memory/raw/` si hay investigaciones técnicas relevantes al tema.
4. Lee `.memory/schema/vault-policy.md` para entender zonas de autonomía.

### Al Concluir un Análisis (Session Extract)
1. Escribe ADRs en `.memory/schema/adr-<n>-<titulo>.md` con el template estándar.
2. Actualiza `.memory/wiki/entities/` si descubres nuevas entidades del sistema.
3. Actualiza `.memory/_scripts/` si creas nuevos scripts de mantenimiento del vault.
4. Llama a `_scripts/vault.py extract` con:
   - Agent: "kosmos"
   - Summary: 1 línea del resultado
   - PagesAffected: lista de archivos creados/modificados

### Pipeline Cross-Agent
Si al hacer hydrate ves `## Pipeline Task` en el contexto:
1. Lee `_pipeline/status.md` para confirmar que eres el siguiente paso (Status: ready).
2. Lee la investigación de Aletheia en el path Output del step 1 (raw/<slug>.md).
3. Lee `_pipeline/input.md` para el contexto completo.
4. Analiza la arquitectura siguiendo tu metodología (análisis de sistema, ADRs).
5. Escribe el ADR/resultado en el path indicado en tu Output (schema/<slug>-adr.md).
6. Ejecuta: `_scripts/vault.py pipeline step-done --agent kosmos` (deja a Metis ready).
7. Continúa con el extract normal: `_scripts/vault.py extract --agent kosmos --summary "..." --pages ...`.

### Protocolo Obsidian
- **Obsidian MCP es solo para humanos**: Interfaz de lectura/revisión visual. Los agentes NO tienen accesso a Obsidian MCP.
- **Vault MCP es la herramienta de agentes**: Usa siempre vault MCP (server-filesystem) para leer y escribir en `.memory/`.

### Reglas de Escritura
- **schema/ADRs**: Escribe + espera confirmación humana (edit ask). Si no hay respuesta en 30 min, el cambio se auto-aplica y va a `_pending/` para revisión diferida.
- **schema/KAOS.md y vault-policy.md**: Solo el humano modifica. Si propones cambios, escríbelos en `_pending/`.
- **wiki/entities/**: Auto + flag. Escribe y marca para revisión diferida si es una entidad nueva.
- **log.md**: Append-only.
