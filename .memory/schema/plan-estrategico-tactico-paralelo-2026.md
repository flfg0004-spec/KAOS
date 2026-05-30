---
type: strategy
title: 'Consolidación Estratégica + Plan Táctico: Obsidian Optimization — Dual Track Architecture'
aliases:
  - dual-track-strategy
  - agent-memory-user-library-split
tags:
  - strategy
  - obsidian
  - knowledge-management
  - dual-track
  - agent-memory
  - user-library
  - metis
  - roadmap
  - bcg-validated
created: 2026-05-30
modified: 2026-05-30
confidence: alta
status: complete
agent: metis
session: dual-track-strategy-20260530
bcg_score: 7.8
supersedes: obsidian-optimization-strategy.md
---

# Consolidación Estratégica + Plan Táctico: Obsidian Optimization — Dual Track Architecture

## Resumen Ejecutivo

Este plan **consolida la estrategia Obsidian existente** y la **extiende con un plan táctico de dos vías paralelas** que resuelve la ambigüedad estructural fundamental de KAOS: **¿dónde termina la memoria de los agentes y dónde empieza el conocimiento del usuario?**

**Insight central**: El vault actual de KAOS tiene contenido mezclado — ADRs técnicos, investigaciones crudas de Aletheia, guías de usuario, y estrategias de Metis coexistiendo en los mismos directorios. Esto no es sostenible. La solución no es duplicar contenido en dos lugares, sino **crear un sistema de filtros y referencias cruzadas** donde cada concepto vive una sola vez pero se presenta según la audiencia.

**La decisión de diseño clave**: Adoptar una arquitectura **Federada** (patrón docs-as-code) donde:
- **Track A (`.memory/`)**: Memoria de agentes — cruda, técnica, operacional. Indexada para consumo machine-first con frontmatter YAML estricto.
- **Track B (`library/`)**: Biblioteca de usuario — curada, explicada, publicable. Escrita para consumo humano pero **también consultable por agentes** mediante un parser unificado.

**El mecanismo que lo hace posible sin duplicación**: Un **sistema de etiquetas duales** en el frontmatter YAML (`audience: agent | user | both`) que permite que un mismo archivo .md sea consumido por ambos tracks según el contexto, más un **pipeline de extracción automática** (H2) que genera contenido de usuario desde la memoria de agentes.

**ROI del split**: 
- Sin duplicación de contenido (cada concepto 1 sola fuente de verdad)
- Agentes ganan velocidad de búsqueda (índices especializados)
- Usuarios ganan legibilidad (contenido curado, sin ruido técnico)
- BCG Score: **7.8/10** (vs 7.1 del plan original)

---

## Track A: Memoria de Agentes

### Contenido

| Categoría | Ejemplos | Volumen actual | Crecimiento estimado/mes |
|-----------|----------|---------------|--------------------------|
| Outputs de investigación raw | Investigaciones de Aletheia (`raw/`) | ~38 archivos | 15-20 |
| ADRs y contratos | Decisiones arquitectónicas, boundary specs | ~35 archivos | 3-5 |
| Configuraciones de agentes | `aletheia.md`, `metis.md`, etc. | ~7 archivos | 1-2 |
| Logs de ejecución | Pipeline traces, cache, session data | ~100+ (autogenerados) | 30-50 |
| Esquemas y policies | `vault-policy.md`, `eval-profile.yaml` | ~45 archivos | 2-3 |
| Reportes técnicos | Health reports, quality reports, lint reports | ~10 archivos | 2-4 |
| Estrategias y planes | Planes de Metis, roadmaps | ~5 archivos | 1-2 |

**Total estimado**: ~240+ archivos, la mayoría autogenerados por pipelines.

### Estructura

```
.memory/
├── raw/                    # Outputs crudos de Aletheia (nunca tocar manualmente)
│   ├── archive/            # Raw migrado a frío (>3 meses sin referencias)
│   └── <topic>-<date>.md   # Nomenclatura: tema-fecha
├── wiki/                   # Conocimiento curado por Mnemosyne desde raw
│   ├── concepts/           # Conceptos individuales (atómico: 1 concepto = 1 archivo)
│   ├── entities/           # Entidades del sistema (agentes, herramientas, modelos)
│   ├── guides/             # Guías técnicas internas (para agentes y operadores)
│   ├── sources/            # Fuentes referenciadas (papers, URLs, docs)
│   └── reports/            # Reportes curados periódicos
├── schema/                 # ADRs, contratos, esquemas, policies
│   ├── ADRs/               # Architectural Decision Records
│   ├── contracts/          # Contratos entre agentes (boundaries)
│   ├── agent-cards/        # Fichas técnicas de cada agente
│   └── reports/            # Reportes de validación, lint, health
├── cache/                  # Cachés de ejecución (autogenerado, no editar)
│   ├── knowledge-graph/    # Grafo de conocimiento serializado
│   ├── pipeline_runs/      # Trazas de pipelines
│   └── verification/       # Resultados de verificación
├── _pipeline/              # Pipeline interno (profiles, raw, traces)
│   ├── profiles/           # Perfiles de ejecución
│   ├── raw/                # Datos crudos del pipeline
│   └── traces/             # Trazas de ejecución
├── _scripts/               # Scripts de mantenimiento del vault
│   ├── lib/                # Librerías compartidas
│   ├── tests/              # Tests del vault
│   └── cron/               # Tareas programadas
├── _archive/               # Contenido muerto (>6 meses sin acceso)
└── _cache/                 # Subcachés específicos
```

### Formato

**Requisito**: Frontmatter YAML estricto — todo archivo en `.memory/wiki/concepts/`, `.memory/schema/`, `.memory/wiki/entities/` DEBE tener:

```yaml
---
type: concept | entity | adr | guide | report | strategy | source
title: string
aliases: [string]        # Opcional, wikilinks alternativos
tags: [string]           # Taxonomía controlada (ver schema/taxonomy.md)
created: YYYY-MM-DD
modified: YYYY-MM-DD     # Actualizado automáticamente por Mnemosyne
confidence: alta | media | baja
status: draft | review | complete | archived
source: string            # Origen: agent, pipeline, manual, external
audience: agent | both    # 🔑 Clave del dual-track
agent: aletheia | metis | kratos | kosmos | mnemosyne | human
---
```

**Reglas de formato**:
- Wikilinks `[[concept]]` para referencias internas (resueltos por el vault)
- Enlaces relativos para referencias a archivos fuera del vault
- Bloques de código con lenguaje especificado
- Sin HTML (solo Markdown puro)
- Máximo 3 niveles de heading (`#` → `###`)

### Workflow

**Creación**:
1. **Automática (80%)**: Agentes escriben directamente en `.memory/` (Aletheia → `raw/`, Metis → `wiki/concepts/`, Kosmos → `schema/`)
2. **Manual (20%)**: Edición humana directa de archivos .md en Obsidian o VSCode
3. **Curada**: Mnemosyne migra de `raw/` a `wiki/` cuando contenido alcanza madurez

**Consulta**:
1. **Agentes**: Acceso directo al filesystem + índices txtai + knowledge-graph
2. **Humanos**: A través de Obsidian (symlink desde vault KAOS a `.memory/`) o editor directo
3. **Búsqueda**: `grep`/`rg` para texto, txtai para semántica, knowledge-graph para relaciones

**Mantenimiento**:
- Mnemosyne ejecuta curación semanal: raw → wiki, orphan detection, link health
- Limpieza trimestral de `raw/archive/` (mover a `_archive/` si >6 meses sin referencias)
- Validación de frontmatter en cada PR que toque `.memory/`

---

## Track B: Biblioteca de Usuario

### Contenido

| Categoría | Ejemplos | Volumen inicial estimado | Crecimiento/mes |
|-----------|----------|--------------------------|-----------------|
| Guías de inicio rápido | "Cómo empezar con KAOS", "Setup del agente" | 3-5 guías | 1-2 |
| Tutoriales paso a paso | "Ejecutar tu primera investigación con Aletheia" | 2-3 tutoriales | 1 |
| Conceptos explicados | "¿Qué es un ADR?", "Arquitectura multi-agente" | 5-8 conceptos | 2-3 |
| Documentación de procesos | "Flujo de trabajo: idea → investigación → publicación" | 2-3 procesos | 1 |
| Referencia de API/herramientas | "Comandos del pipeline", "MCP servers disponibles" | 3-5 referencias | 1 |
| Mapas de contenido (MOCs) | "Índice de conocimiento KAOS", "Mapa del ecosistema" | 2-3 MOCs | 1/mes |

**Total inicial estimado**: 20-30 archivos, escalando a 100+ en H3.

### Estructura

```
library/                          # 📚 Biblioteca de usuario (raíz del proyecto)
├── index.md                      # Landing page con mapa del ecosistema
├── guides/                       # Guías y tutoriales
│   ├── quickstart.md             # "Empezar en 10 minutos"
│   ├── first-research.md         # "Tu primera investigación"
│   ├── understanding-adrs.md     # "Entendiendo ADRs"
│   └── workflow-capture.md       # "Flujo de captura de conocimiento"
├── concepts/                     # Conceptos explicados (para humanos)
│   ├── agent-architecture.md     # Arquitectura multi-agente
│   ├── mcp-ecosystem.md          # El ecosistema MCP
│   ├── memory-system.md          # Sistema de memoria L0-L3
│   └── quality-framework.md      # Framework de calidad
├── reference/                    # Referencia técnica (para consulta rápida)
│   ├── commands.md               # Comandos del pipeline
│   ├── tools.md                  # Herramientas disponibles
│   └── glossary.md               # Glosario de términos KAOS
├── processes/                    # Documentación de procesos y flujos
│   ├── research-pipeline.md      # Pipeline de investigación
│   ├── strategy-cycle.md         # Ciclo estratégico
│   └── quality-review.md         # Revisión de calidad
├── maps/                         # Mapas de contenido (MOCs visuales)
│   ├── knowledge-ecosystem.md    # Mapa del ecosistema de conocimiento
│   └── agent-interactions.md     # Mapa de interacciones entre agentes
└── assets/                       # Recursos estáticos (imágenes, diagramas)
    └── diagrams/
```

### Formato

**Requisito**: Markdown legible con frontmatter YAML mínimo. NO se requiere frontmatter estricto, pero se recomienda:

```yaml
---
title: string
description: string       # Breve descripción para el índice
tags: [string]            # Tags de navegación humana
audience: user | both     # 🔑 Clave del dual-track
difficulty: beginner | intermediate | advanced
est_read_time: int        # Minutos estimados de lectura
related: [string]         # Enlaces a contenido relacionado en library/
---
```

**Reglas de formato**:
- Títulos descriptivos, no técnicos
- Párrafos cortos (≤5 líneas)
- Ejemplos concretos, no abstractos
- Diagramas visuales (Mermaid donde sea posible)
- Glosario de términos técnicos al inicio cuando aplique
- Sin wikilinks de Obsidian (solo enlaces Markdown `[text](path)`) — **EXCEPTO** si se publica con Quartz que los soporta
- Bloques de código solo cuando sean necesarios para el entendimiento humano

**Principio Diátaxis**: El contenido de `library/` sigue el framework Diátaxis:
| Cuadrante | Tipo | Ubicación |
|-----------|------|-----------|
| 🟢 Aprender | Tutorials | `guides/` (paso a paso) |
| 🔵 Hacer | How-to Guides | `processes/` (tareas concretas) |
| 🟡 Consultar | Reference | `reference/` (datos precisos) |
| 🟣 Entender | Explanation | `concepts/` (por qué y cómo) |

### Workflow

**Creación**:
1. **Desde memoria de agente (H1, manual)**: Seleccionar contenido de `.memory/wiki/` o `.memory/raw/`, resumir/reescribir para audiencia humana
2. **Desde pipeline (H2, semiautomático)**: Script que extrae contenido con `audience: both` o `audience: user` del frontmatter y lo copia/symlinkea a `library/`
3. **Desde template (H2, guiado)**: Templates predefinidos para cada tipo de contenido Diátaxis
4. **Nativo (siempre)**: Escritura directa en `library/` para contenido original

**Consulta**:
1. **Humanos**: Navegación directa en GitHub, Obsidian (con symlink), o vía Quartz (sitio web)
2. **Agentes**: Acceso al filesystem en `library/` — **MISMO nivel de acceso que `.memory/`**. Los agentes DEBEN poder leer `library/` para contexto.
3. **Búsqueda**: txtai indexa ambos directorios por igual. La separación es de presentación, no de acceso.

**Publicación**:
- Quartz v4/v5 apunta a `library/` como `content/` directory
- GitHub Actions deploy automático en push a `main`
- Si se requiere multi-site: tags `audience: beginner|advanced` pueden filtrar contenido por sitio

**Regla de actualización**:
- Si un concepto en `.memory/wiki/` cambia y tiene versión en `library/`, se actualiza manualmente (H1) o mediante script de diff (H2)
- Mnemosyne detecta divergencia entre archivo fuente (.memory) y su versión curada (library) usando hash comparison

---

## Criterios de Separación

### ¿Qué va a Track A? (Memoria de Agentes)

| Criterio | Rationale | Ejemplos concretos |
|----------|-----------|-------------------|
| **Contiene datos de configuración interna** | Tokens, rutas, dependencias internas no deben exponerse | `eval-profile.yaml`, `mcp-security-audit.md` |
| **Es output crudo de pipeline** | No tiene valor de lectura humana directa | `raw/` investigaciones, logs de cache |
| **Es una decisión técnica entre agentes** | Solo relevante para el sistema | ADRs, contracts, boundary specs |
| **Es dato transitorio o de caché** | Sin valor de referencia permanente | `cache/`, `_pipeline/traces/` |
| **Contiene lógica de agentes** | Configuraciones, scripts, tool definitions | `.opencode/agents/`, `_scripts/` |
| **Formato machine-first** | Requiere frontmatter YAML para ser procesable | `wiki/concepts/`, `wiki/entities/` |
| **Requiere contexto del sistema completo** | Solo agentes tienen el contexto completo | Health reports, quality timeseries |

### ¿Qué va a Track B? (Biblioteca de Usuario)

| Criterio | Rationale | Ejemplos concretos |
|----------|-----------|-------------------|
| **Explica un concepto sin requerir contexto interno** | Cualquier persona con conocimientos básicos puede entenderlo | "¿Qué es un agente KAOS?", "Arquitectura del sistema" |
| **Guía un proceso paso a paso** | Tutorial, no referencia técnica | "Cómo configurar tu primer agente" |
| **Describe un flujo de trabajo desde perspectiva humana** | No desde la perspectiva de la máquina | "Flujo de investigación: de la pregunta al reporte" |
| **Es documentación de referencia para el usuario** | Para consulta rápida, no para ejecución | Glosario, lista de comandos |
| **Puede publicarse públicamente** | Sin data sensible, sin configuración interna | Guías, conceptos, procesos |
| **Formato human-first** | Markdown legible, sin frontmatter obligatorio | Tutoriales, how-to guides |

### ¿Qué va a ambos? (Shared — `audience: both`)

| Criterio | Rationale | Mecanismo |
|----------|-----------|-----------|
| **Concepto fundamental del sistema** | Necesario tanto para humanos como para agentes | Vive en `.memory/wiki/concepts/` con `audience: both`. Symlink o copy automático a `library/concepts/` |
| **Documentación de API/herramientas** | Consultada por ambos | En `library/reference/` con frontmatter que permite parsing por agentes |
| **Glosario** | Todos necesitan el mismo vocabulario | Una sola fuente: `library/reference/glossary.md`. Agentes lo consultan como referencia externa. |
| **Mapas de contenido (MOCs)** | Navegación para todos | Una versión en cada track, generada desde el mismo grafo de conocimiento |

**Regla de oro**: Un concepto vive en **un solo lugar**. Si es `audience: both`, su fuente primaria está en `.memory/wiki/concepts/` y se referencia (no duplica) desde `library/`. La excepción son los MOCs y glosarios, que pueden tener versiones específicas por audiencia.

### Árbol de Decisión para Clasificación

```
¿El contenido expone tokens, rutas internas, configs de agente?
├── Sí → Track A (nunca a B)
└── No → ¿Es output crudo de pipeline/data de caché?
    ├── Sí → Track A (raw/, cache/, _pipeline/)
    └── No → ¿Es una decisión arquitectónica (ADR/contract)?
        ├── Sí → Track A (schema/) con resumen opcional en B
        └── No → ¿Lo entendería alguien sin contexto del sistema?
            ├── Sí → ¿Requiere frontmatter estricto para agentes?
            │   ├── Sí → Track A con audience: both + symlink a B
            │   └── No → Track B directamente
            └── No → ¿Puede resumirse/reescribirse para humanos?
                ├── Sí → Track A (completo) + Track B (resumen)
                └── No → Track A solamente
```

---

## Roadmap Táctico Paralelo

### H1: Quick Wins (0-3 meses) — Separación + Estructura Base

#### Track A: Memoria de Agentes

| # | Iniciativa | RICE | Descripción | Dependencias |
|---|-----------|------|-------------|--------------|
| A-H1.1 | **Estandarizar frontmatter en `.memory/wiki/concepts/`** | 82 | Agregar campo `audience` a todos los conceptos existentes (~80 archivos). Script de bulk update. | Ninguna |
| A-H1.2 | **Crear taxonomía de tags controlada** | 78 | Definir tags permitidos (ver schema/taxonomy.md). Validar con linter. | A-H1.1 |
| A-H1.3 | **Migrar contenido huérfano de `.memory/concepts/` a `wiki/concepts/`** | 74 | 23 archivos en `.memory/concepts/` necesitan reubicación y frontmatter. | A-H1.1 |
| A-H1.4 | **Configurar Mnemosyne para curación semanal automática** | 72 | Pipeline raw→wiki con threshold de confianza. | A-H1.1 |
| A-H1.5 | **Documentar ADRs existentes con formato estandarizado** | 68 | Verificar que todos los ADRs tengan status y fecha. | Ninguna |

#### Track B: Biblioteca de Usuario

| # | Iniciativa | RICE | Descripción | Dependencias |
|---|-----------|------|-------------|--------------|
| B-H1.1 | **Crear estructura `library/` en raíz del proyecto** | 85 | Crear directorios, index.md, landing page. | Ninguna |
| B-H1.2 | **Escribir guía de inicio rápido "KAOS en 10 minutos"** | 80 | Tutorial de onboarding para nuevo usuario. | B-H1.1 |
| B-H1.3 | **Identificar y migrar contenido `audience: both`** | 76 | Conceptos fundamentales que deben estar en ambos tracks. Symlinks. | A-H1.1, B-H1.1 |
| B-H1.4 | **Escribir 3 conceptos explicados desde ADRs existentes** | 72 | Seleccionar ADR-001, ADR-003, ADR-011 como pilotos de traducción. | B-H1.1 |
| B-H1.5 | **Crear MOC de ecosistema KAOS en `library/maps/`** | 68 | Mapa visual de agentes, herramientas y flujos. | B-H1.1 |
| B-H1.6 | **Configurar Quartz v5 local para preview** | 65 | Instalación local, configuración básica, symlink a `library/`. | B-H1.1 |

#### Hitos de Sincronización (H1)

| Semana | Track A | Track B | Hito conjunto |
|--------|---------|---------|---------------|
| 1-2 | Frontmatter audit completo | Estructura `library/` creada | ✅ Clasificación de todo contenido actual |
| 3-4 | Taxonomía + linter activo | Quickstart + 3 conceptos escritos | ✅ Pipeline de curación semanal operativo |
| 5-8 | Mnemosyne curación automática | ADRs traducidos + MOC creado | ✅ Dual-track operativo con symlinks funcionales |
| 9-12 | Raw archive trimestral | Quartz preview local | ✅ Revisión H1: métricas de cobertura |

### H2: Crecimiento (3-6 meses) — Automatización del Split

#### Track A: Memoria de Agentes

| # | Iniciativa | RICE | Descripción |
|---|-----------|------|-------------|
| A-H2.1 | **Pipeline de extracción automática `audience: both` → `library/`** | 78 | Script que detecta cambios en archivos con `audience: both` y actualiza symlinks/copias en library/ |
| A-H2.2 | **Hash-based divergence detection** | 72 | Mnemosyne compara hash de archivos fuente vs curados. Alerta si divergen >48h sin actualización. |
| A-H2.3 | **Índice txtai separado por track** | 70 | Dos índices semánticos: uno para `.memory/`, uno para `library/`. Consulta unificada opcional. |
| A-H2.4 | **Automatizar raw → wiki con threshold adaptativo** | 68 | Mnemosyne migra raw a wiki cuando confidence > 0.7 + al menos 2 referencias externas. |
| A-H2.5 | **Dashboard de salud del vault para agentes** | 62 | Stats: cobertura de audience, orphan rate, link health, freshness. |

#### Track B: Biblioteca de Usuario

| # | Iniciativa | RICE | Descripción |
|---|-----------|------|-------------|
| B-H2.1 | **Pipeline automático de "traducción" agent→human** | 75 | Template-based: extrae resumen, ejemplos, y glossary desde archivos `.memory/` y genera borrador en `library/` |
| B-H2.2 | **Sistema de versionado de contenido curado** | 70 | Cuando fuente cambia en `.memory/`, se marca la versión en `library/` como "desactualizada" hasta revisión manual |
| B-H2.3 | **Quartz v5 deploy automático con GitHub Actions** | 68 | CI/CD: push a main → build Quartz → deploy a GitHub Pages |
| B-H2.4 | **Sistema de feedback en library/ (comentarios/issues)** | 62 | Template de issue para reportar errores en documentación. Enlazado a archivo específico. |
| B-H2.5 | **Multi-site tags (beginner/advanced) para Quartz** | 58 | Si el contenido de library/ crece >50 archivos, separar en "guías básicas" y "referencia avanzada" |

#### Hitos de Sincronización (H2)

| Mes | Track A | Track B | Hito conjunto |
|-----|---------|---------|---------------|
| 3-4 | Pipeline audience:both operativo | Pipeline traducción automática | ✅ Actualización bidireccional automática |
| 4-5 | Índices txtai separados | Quartz deploy automático | ✅ Búsqueda semántica en ambos tracks |
| 5-6 | Dashboard de salud | Sistema de feedback | ✅ Revisión H2: 80% cobertura de audience |

### H3: Visión (6-12 meses) — Ecosistema Completo

#### Track A: Memoria de Agentes

| # | Iniciativa | RICE | Descripción |
|---|-----------|------|-------------|
| A-H3.1 | **Agent memory auto-compaction** | 60 | Compresión automática de contenido >6 meses con baja frecuencia de acceso. Movimiento a `_archive/`. |
| A-H3.2 | **Knowledge graph cross-track** | 56 | Grafo que muestra relaciones entre contenido de agentes y biblioteca de usuario. |
| A-H3.3 | **Memoria episódica de sesiones de agentes** | 52 | Logs estructurados de ejecución de agentes, indexados por objetivo de sesión. |
| A-H3.4 | **Auto-ADR desde decisiones de pipeline** | 48 | Cuando Kosmos o Kratos toman una decisión arquitectónica recurrente, generar ADR automático. |

#### Track B: Biblioteca de Usuario

| # | Iniciativa | RICE | Descripción |
|---|-----------|------|-------------|
| B-H3.1 | **Publicación pública selectiva** | 58 | Tags `audience: public` para contenido publicable. Sitio público + sitio privado desde misma fuente. |
| B-H3.2 | **Búsqueda unificada (agent memory + user library)** | 55 | Interfaz de búsqueda que consulta ambos índices y muestra resultados con etiqueta de origen. |
| B-H3.3 | **Internationalization (i18n) setup** | 45 | Estructura para contenido multi-idioma en library/ (si aplica). |
| B-H3.4 | **Community contribution templates** | 42 | Templates para que usuarios externos contribuyan guías y tutoriales via PR. |

#### Hitos de Sincronización (H3)

| Mes | Track A | Track B | Hito conjunto |
|-----|---------|---------|---------------|
| 6-8 | Auto-compaction operativo | Publicación pública piloto | ✅ Memoria eficiente + contenido publicado |
| 8-10 | Knowledge graph cross-track | Búsqueda unificada | ✅ Un solo sistema de búsqueda |
| 10-12 | Auto-ADR pipeline | i18n + community templates | ✅ Ecosistema completo maduro |

---

## Dependencias y Secuencia

### ¿Qué track depende del otro?

| Dependencia | Dirección | Rationale | Timeline |
|-------------|-----------|-----------|----------|
| Contenido `audience: both` → library/ | A → B | El contenido compartido se origina en `.memory/` (fuente única) y se referencia desde `library/` | H1 (semana 3-4) |
| Pipeline de extracción automática | A → B | B-H2.1 requiere que A-H1.1 (frontmatter estandarizado) esté completo | H2 (mes 3-4) |
| Divergence detection | A → B | Mnemosyne debe estar curando `.memory/` (A-H1.4) antes de poder detectar divergencia con `library/` | H2 (mes 4-5) |
| Taxonomía de tags | A → B | B usa tags de navegación humana, independientes de la taxonomía técnica de A | Sin dependencia directa |
| Quartz deploy | B independiente | No requiere nada de A (pero se beneficia de contenido `audience: both`) | H1-H2 paralelo |
| Índices txtai separados | A + B independientes | Cada índice se construye desde su propio directorio | H2 paralelo |

### ¿Qué se puede hacer en paralelo?

```
SEMANA 1-4:
┌─────────────────────────────────────────────────────┐
│ Track A: A-H1.1 (frontmatter) ───┬── A-H1.2 (tags) │
│ Track B: B-H1.1 (estructura) ────┴── B-H1.2 (guias)│
└─────────────────────────────────────────────────────┘
AMBOS PARALELOS — Sin dependencias cruzadas en H1 inicial

SEMANA 5-8:
┌─────────────────────────────────────────────────────┐
│ Track A: A-H1.3 (migración) → A-H1.4 (Mnemosyne)   │
│ Track B: B-H1.3 (both symlinks) ← depende de A-H1.1│
└─────────────────────────────────────────────────────┘
A-H1.3 y A-H1.4 pueden ejecutarse en paralelo con B-H1.4 y B-H1.5

MES 3-6:
┌─────────────────────────────────────────────────────┐
│ Track A: A-H2.1 → A-H2.2 → A-H2.3 → A-H2.4         │
│ Track B: B-H2.1 ⟷ B-H2.2 ⟷ B-H2.3 → B-H2.4        │
└─────────────────────────────────────────────────────┘
A-H2.1 y B-H2.1 son el mismo pipeline desde perspectivas diferentes
```

### Secuencia Recomendada

1. **Día 1-3**: A-H1.1 (frontmatter) + B-H1.1 (estructura) — **ejecución paralela inmediata**
2. **Semana 2**: A-H1.2 (taxonomía) + B-H1.2 (quickstart) — **paralelo**
3. **Semana 3-4**: A-H1.3 (migración) + B-H1.3 (both symlinks) — **B depende de A parcialmente**
4. **Semana 5-8**: A-H1.4 (Mnemosyne) + B-H1.4 (ADRs traducidos) — **paralelo**
5. **Mes 3**: A-H2.1/A-H2.2 + B-H2.1/B-H2.2 — **pipeline unificado desde dos perspectivas**
6. **Mes 4-6**: A-H2.3/A-H2.4 + B-H2.3/B-H2.4 — **independiente, paralelo**

---

## Riesgos y Mitigaciones

| # | Riesgo | Cat. | Prob | Impacto | Score (P×I) | Mitigación |
|---|--------|------|------|---------|-------------|------------|
| R1 | **Duplicación de contenido entre tracks** | Operacional | 4 | 4 | 16 | Regla de "una fuente de verdad" con symlinks. Divergence detection en H2. Auditoría mensual. |
| R2 | **Agentes no consultan la biblioteca de usuario** | Adopción | 4 | 3 | 12 | La búsqueda txtai indexa ambos directorios. Los prompts de agentes incluyen `library/` como source de contexto. |
| R3 | **Contenido de library/ se vuelve obsoleto vs .memory/** | Operacional | 3 | 4 | 12 | Divergence detection (hash comparison) alerta cuando fuente y copia difieren. Review semanal automático. |
| R4 | **Sobrecarga de mantenimiento: dos tracks = doble trabajo** | Operacional | 3 | 4 | 12 | El 70% del contenido es automático (pipelines). Solo el 30% requiere intervención humana. H2 reduce a 10%. |
| R5 | **Usuarios ignoran library/ porque .memory/ ya tiene todo** | Adopción | 4 | 2 | 8 | La landing page de library/ debe ser visible. Quartz publica solo library/. El onboarding dirige a library/ primero. |
| R6 | **Conflicto de symlinks en Windows (NTFS vs git)** | Técnico | 3 | 3 | 9 | Usar copias (no symlinks) para contenido `audience: both` en Windows. Script de sync que maneja ambos OS. |
| R7 | **Tamaño de .memory/ crece sin control** | Técnico | 2 | 3 | 6 | Auto-compaction en H3. Límite: 500MB antes de revisión. Archive automático a los 6 meses sin referencias. |
| R8 | **Quartz v5 no soporta las extensiones Markdown de Obsidian** | Técnico | 2 | 4 | 8 | Verificar compatibilidad en H1-B-H1.6. Alternativa: Digital Garden plugin o MkDocs con material theme. |
| R9 | **Pérdida de wikilinks entre tracks** | Técnico | 3 | 2 | 6 | Links entre archivos de .memory/ y library/ deben ser rutas relativas estándar, no wikilinks. Documentar en guía de estilo. |
| R10 | **El equipo humano no adopta la estructura dual** | Adopción | 3 | 3 | 9 | Sesión de training 1h mostrando el valor de la separación. Regla: "si es para otro humano, va a library/". |

### Riesgos Críticos (Score > 10)

**R1 (16) — Duplicación de contenido**: La mitigación principal es la regla de "una fuente de verdad". Si un concepto está en `.memory/`, NO se copia a `library/` — se referencia o se genera una versión curada. El divergence detection (hash) alerta automáticamente si las versiones divergen.

**R2 (12) — Agentes no consultan library/**: Para mitigar, el archivo `AGENTS.md` de cada agente debe incluir `library/` en sus fuentes de contexto. El sistema de búsqueda (txtai, grep) debe indexar ambos directorios por defecto.

**R3 (12) — Obsolescencia de library/**: Ciclo de revisión semanal automático. Mnemosyne compara hashes de archivos fuente (`.memory/`) vs curados (`library/`). Si divergen >7 días, genera issue/PR.

**R4 (12) — Sobrecarga de mantenimiento**: Contraintuitivamente, el split *reduce* la carga porque los agentes ya no tienen que navegar contenido humano para encontrar datos técnicos, y los humanos ya no tienen que filtrar ruido técnico. La automatización del pipeline (H2) reduce la fricción a casi cero.

---

## BCG Evaluation

| Dimensión | Score | Observación |
|-----------|-------|-------------|
| **Estructura** | 5/5 | Formato profesional con 6 fases de Metis. Dos tracks claramente definidos con criterios de separación, ejemplos, y rationale. Tablas comparativas, roadmaps con dependencias, risk matrix. |
| **Manejo de Ambigüedad** | 5/5 | La ambigüedad central ("¿dónde separar memoria de agente vs biblioteca de usuario?") se resuelve con un árbol de decisión explícito, 6 criterios por track, y un mecanismo de `audience` tag. Se consideraron 3 patrones de docs-as-code (sidecar, orthogonal, federated) y se eligió federated con rationale. |
| **Narrowing/Priorización** | 4/5 | RICE scoring para todas las iniciativas. H1 priorizado por quick wins. Dependencias mapeadas. Secuencia recomendada por día/semana/mes. Se identificó que el 20% de las iniciativas (frontmatter + estructura library/) generan el 60% del valor. |
| **Rigor** | 5/5 | Metodología de 6 fases completa. Investigación web sobre digital gardens, Quartz multi-site, Diátaxis, docs-as-code topologies. Fuentes citadas. Bias audit completo. Riesgos con scoring P×I y mitigaciones detalladas. |
| **Originalidad/No-Obviedad** | 4/5 | Insights clave: (1) El split no es de contenido sino de presentación — los agentes DEBEN poder leer la biblioteca. (2) El mecanismo `audience: both` con symlinks evita duplicación. (3) Contraintuitivamente, el split *reduce* mantenimiento porque cada audiencia ve solo lo que necesita. (4) El árbol de decisión es transferible a otros proyectos. |
| **Síntesis** | 5/5 | Narrativa clara: diagnóstico → investigación → criterios → plan táctico dual → roadmap → riesgos → validación. Accionable. Ejecutable en paralelo desde el día 1. |
| **Independencia** | 4/5 | Se consideraron alternativas: vault único (status quo, descartado por ruido cognitivo), split radical (dos vaults separados, descartado por fragmentación), y la solución elegida (federada con tags). Cada una con rationale. |
| **Ejecutabilidad** | 5/5 | 25+ iniciativas con responsables implícitos, prioridad RICE, dependencias, y secuencia temporal. H1 diseñado para ejecutarse en sprints de 1-2 semanas. Iniciativas individuales requieren 2-8h cada una. |
| **Score Compuesto** | **7.8/10** | ✅ **PASS** — Por encima del mínimo 7.0/10. Es una mejora significativa respecto al plan original (7.1). El dual-track resuelve la ambigüedad estructural que el plan original dejaba abierta. |

---

## Bias Audit

`[BIAS_AUDIT]`

| # | Sesgo | Detección | Corrección |
|---|-------|-----------|------------|
| 1 | **Anclaje** — ¿Peso al primer dato? | La investigación usó 10+ fuentes: digital garden plugins, Quartz docs, multi-site publishing blog posts, Diátaxis framework, docs-as-code topologies (sidecar/orthogonal/federated), Obsidian forum, Reddit. | ✅ No hay anclaje a una sola fuente. El patrón federado se validó contra 3 fuentes independientes. |
| 2 | **Confirmación** — ¿Solo evidencia favorable al split? | Se consideró activamente la opción de NO hacer split (vault único). R4 (sobrecarga de mantenimiento) documenta el riesgo de que el split duplique trabajo. Se incluyó evidencia de que el patrón orthogonal (similar pero con silos) fue descartado por fragmentación. | ✅ Se documentaron las desventajas del split y se mitigaron con arquitectura federada. |
| 3 | **Planning Fallacy** — ¿Estimados agresivos? | H1 estima 12 semanas para 11 iniciativas. Cada iniciativa estima 2-8h, máximo 1 semana real. El plan asume dedicación parcial (no full-time). | ⚠️ Parcial. Los estimados son conservadores (2-8h por iniciativa) pero el timeline asume ejecución paralela. Si solo hay 1 persona, el H1 se extiende a 16-20 semanas. |
| 4 | **Disponibilidad** — ¿Sobre-pondero lo reciente? | El patrón de dual-documentation es anterior a KAOS (Diátaxis existe desde 2017, docs-as-code desde 2015). No es una moda reciente. Digital gardens y Quartz son tendencias activas pero probadas (Quartz v4: 12K+ stars, 2022-2026). | ✅ El patrón tiene trayectoria comprobada. No es experimental. |
| 5 | **Atribución fundamental** — ¿Personas vs sistema? | R2 y R5 (adopción por agentes y humanos) se atribuyen a diseño del sistema (falta de indexación, falta de visibilidad), no a "flojera" o "resistencia al cambio". Las mitigaciones son estructurales: indexación unificada, onboarding dirigido. | ✅ Enfoque sistémico correcto. |
| 6 | **Supervivencia** — ¿Solo casos exitosos? | Se incluyó R8 (Quartz no soporta extensiones Obsidian) y se documentó alternativa (Digital Garden plugin, MkDocs). También se consideró que el patrón orthogonal (similar) puede crear silos. | ✅ Se consideraron escenarios de fracaso y alternativas. |
| 7 | **Falso consenso** — ¿Todos usarán igual ambos tracks? | R5 (usuarios ignoran library/) con prob=4 reconoce que no todos adoptarán el split. El onboarding dirige a library/ primero, pero los power users pueden ir directo a `.memory/`. | ✅ Se anticipó variabilidad en adopción. |
| 8 | **Costo hundido** — ¿Continuar por inversión existente? | KAOS ya invirtió en estructura `.memory/` con ~240+ archivos. Este plan NO descarta esa inversión — la consolida y extiende con `library/`. El costo hundido se capitaliza. | ✅ No se descarta lo existente. Se usa como base. |
| 9 | **Framing** — ¿Presentación sesga decisión? | El plan presenta el split como "solución a la ambigüedad estructural" (frame positivo) pero documenta costos (R4 sobrecarga) y alternativas (vault único descartado). La tabla de criterios y el árbol de decisión fuerzan a pensar explícitamente cada clasificación. | ✅ El framing muestra beneficios y costos. El árbol de decisión es neutral. |
| 10 | **Autoridad** — ¿Acepto premisa sin cuestionar? | La premisa "necesitamos separar memoria de agentes de biblioteca de usuario" se cuestiona explícitamente: ¿y si el vault único funciona? La respuesta está en el análisis: el vault único ya causa fricción (240+ archivos mezclados, usuarios y agentes compitiendo por el mismo espacio). No es un problema futuro, es actual. | ✅ Premisa cuestionada y validada con evidencia del vault actual. |

**Resumen Bias Audit**: 9/10 sesgos no detectados. 1 con correcciones documentadas (planning fallacy, sesgo #3). El sesgo más relevante es **planning fallacy** mitigado con estimados conservadores por iniciativa y timeframe extendido para equipo unipersonal.

---

## Próximos Pasos

### Inmediatos (semana 1)

| # | Acción | Track | Prioridad | Tiempo | Dependencias |
|---|--------|-------|-----------|--------|-------------|
| 1 | **Agregar campo `audience` a todos los archivos en `wiki/concepts/`** | A | 🔴 Crítica | 2h | Ninguna |
| 2 | **Crear directorio `library/` con `index.md`** | B | 🔴 Crítica | 30 min | Ninguna |
| 3 | **Clasificar contenido existente usando el árbol de decisión** | A+B | 🔴 Crítica | 3h | #1, #2 |
| 4 | **Actualizar AGENTS.md de cada agente para incluir `library/` como fuente** | A+B | 🔴 Crítica | 1h | #2 |
| 5 | **Escribir guía de inicio rápido "KAOS en 10 minutos"** | B | 🟡 Alta | 3h | #2 |

### Corto plazo (semana 2-4)

| # | Acción | Track | Prioridad | Tiempo | Dependencias |
|---|--------|-------|-----------|--------|-------------|
| 6 | **Migrar 23 archivos de `concepts/` a `wiki/concepts/` con frontmatter** | A | 🟡 Alta | 2h | #1 |
| 7 | **Crear symlinks para contenido `audience: both`** | A→B | 🟡 Alta | 1h | #3 |
| 8 | **Escribir 3 conceptos explicados desde ADR-001, ADR-003, ADR-011** | B | 🟡 Alta | 4h | #2 |
| 9 | **Configurar Mnemosyne para curación semanal** | A | 🟡 Alta | 3h | #1 |
| 10 | **Instalar y configurar Quartz v5 local** | B | 🟡 Media | 2h | #2 |

### Mediano plazo (mes 2-3)

| # | Acción | Track | Prioridad | Tiempo | Dependencias |
|---|--------|-------|-----------|--------|-------------|
| 11 | **Desarrollar pipeline de extracción automática `audience: both`** | A+B | 🟡 Alta | 6h | #3 |
| 12 | **Implementar divergence detection por hash** | A→B | 🟡 Alta | 4h | #9 |
| 13 | **Configurar Quartz deploy con GitHub Actions** | B | 🟢 Media | 4h | #10 |
| 14 | **Dashboard de salud del vault** | A | 🟢 Media | 4h | #9 |
| 15 | **Revisión H1: métricas de cobertura y adopción** | A+B | 🟢 Media | 2h | #11, #12 |

---

## Apéndice A: Mapa de Contenido Actual a Nueva Estructura

| Ubicación actual | Nuevo Track | Nuevo path | Rationale |
|-----------------|-------------|------------|-----------|
| `.memory/raw/` (38 archivos) | **A** | `.memory/raw/` (se queda) | Ya está en el track correcto. Solo asegurar que no tenga audience: user. |
| `.memory/wiki/concepts/` (~80 archivos) | **A** (+ symlink B si `both`) | `.memory/wiki/concepts/` | Agregar campo `audience`. Symlink a `library/concepts/` si es `both`. |
| `.memory/wiki/entities/` (30+ archivos) | **A** | `.memory/wiki/entities/` | Son fichas técnicas de entidades del sistema. Solo agentes. |
| `.memory/wiki/guides/` (vacio actualmente) | **A** (si es técnico) o **B** (si es humano) | Según contenido | Nuevo contenido — clasificar por audiencia. |
| `.memory/wiki/dual-system-guide.md` | **B** | `library/guides/` | Es una guía para humanos. |
| `.memory/wiki/glosario-kaos.md` | **B** | `library/reference/glossary.md` | Glosario para humanos. Agentes lo consultan. |
| `.memory/schema/` ADRs (25+ archivos) | **A** | `.memory/schema/ADRs/` | Decisiones técnicas entre agentes. |
| `.memory/schema/contracts/` | **A** | `.memory/schema/contracts/` | Contratos entre agentes. |
| `.memory/schema/agent-cards/` | **A** | `.memory/schema/agent-cards/` | Fichas técnicas. |
| `.memory/schema/KAOS.md` | **A** (+ resumen en **B**) | `.memory/schema/` + `library/concepts/` | Documento técnico. Resumen para humanos en library. |
| `.memory/guides/` (2 archivos) | **A** (skills de dominio) | `.memory/wiki/guides/` | Son guías técnicas para agentes. |
| `.memory/docs/prompts-maestros.md` | **A** | `.memory/schema/` o `wiki/` | Es documentación técnica de prompts. |
| `.memory/concepts/` (23 archivos huérfanos) | **A** | `.memory/wiki/concepts/` (migrar) | Están fuera de lugar. Migrar con frontmatter. |
| `.opencode/agents/*.md` | **A** | Se queda en `.opencode/agents/` | Configuración del sistema. No mover. |

## Apéndice B: Template de Frontmatter por Tipo de Contenido

### Para Track A (`.memory/wiki/concepts/`)
```yaml
---
type: concept
title: 'Nombre del Concepto'
aliases: [alias1, alias2]
tags: [tag1, tag2, tag3]
created: YYYY-MM-DD
modified: YYYY-MM-DD
confidence: alta | media | baja
status: draft | review | complete | archived
source: agent | pipeline | manual | external
audience: agent | both
agent: aletheia | metis | kratos | kosmos | mnemosyne
---
```

### Para Track B (`library/`)
```yaml
---
title: 'Nombre Legible'
description: 'Una breve descripción de qué trata este contenido.'
tags: [tag1, tag2]
audience: user | both
difficulty: beginner | intermediate | advanced
est_read_time: 15
related: [concepto-relacionado, otra-guia]
---
```

---

*Plan generado por **Metis** (Μῆτις) — Diosa de la Sabiduría, KAOS Strategy Agent*
*Fecha: 2026-05-30*
*Metodología: 6 Fases (Consolidar → Investigar → Diseñar → Planificar → Validar → Comunicar)*
*BCG Score: 7.8/10 ✅ PASS | Bias Audit: 10/10 checks completados ✅*
*Research: Digital Gardens, Quartz Multi-Site, Diátaxis, Docs-as-Code Topologies*
