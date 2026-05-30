# Plan Táctico Integral: Obsidian + Mnemosyne — 3 Tracks Paralelos

> **Elaborado por**: Metis (Μῆτις), Diosa de la Estrategia  
> **Fecha**: 2026-05-30  
> **Fuentes**: `obsidian-optimization-strategy.md` (BCG 8.2), `plan-estrategico-tactico-paralelo-2026.md` (BCG 7.8), `aether-parallel-tactical-plan.md` (formato), Mnemosyne SKILL, ADR-015, código existente en `lib/agent_nodes/mnemosyne.py`, `lib/file_lock.py`, `lib/obsidian.py`, `lib/feature_flags.py`  
> **Principio rector**: Máximo paralelismo — 3 tracks, sin dependencias duras entre tracks en F0-F1

---

## PARTE 1: Mapa de Dependencias

### Árbol de Paralelismo

```
F0 (Semana 1-2: Quick Wins) ──────────────────────────────────────────────
                                                                            │
  Track A (Obsidian Stack)        Track B (Mnemosyne Pipeline)     Track C (Dual Track)
  ────────────────────────        ────────────────────────          ────────────────────────
  [A1] Unificar vaults            [B1] Gap Query pre-captura       [C1] Crear library/
  [A2] Templater + Linter         [B2] Curación targeted            [C2] Script audience tag
  [A3] QuickAdd macros            [B3] File locking + buffer        [C3] Promoción Fase P
  [A4] Plantilla diaria           [B4] Merge tags preservar         [C4] Metadata integration
  [A5] Obsidian Git               [B5] Frontmatter↔Properties       [C5] Dataview queries
  [A6] Audit plugins              [B6] Scoring pipeline             [C6] AGENTS.md update
  [A7] Calendar + Periodic        [B7] Write buffer diferido        [C7] Divergence detection

F1 (Semana 3-4: Fundación) ──────────────────────────────────────────────
  [A8] Smart Connections           [B6.5] Score-based curation      [C3.5] Promotion triggers
  [A9] Folder templates           [B7] Buffer integration           [C7.5] Health dashboard

F2 (Semana 5-6: Pipeline) ───────────────────────────────────────────────
  [A10] User Scripts Templater    [B8] Cross-ref + lifecycle       [C8] MOCs Dataview
  [A11] Performance tuning        [B9] Auto-promotion pipeline     [C9] Quartz preview

F3 (Semana 7-8: Hardening) ──────────────────────────────────────────────
  [A12] Mobile profile             [B10] Full automation cycle     [C10] Quartz deploy CI/CD
  [A13] H3 prep                   [B11] Feedback loop             [C11] Divergence auto-sync
```

### Dependencias Documentadas

| Dependencia | Tipo | Detalle |
|---|---|---|
| A2 → A3 | Suave | QuickAdd necesita Templater para macros de nota estructurada |
| A2 → A4 | Dura | La plantilla diaria ES un template Templater |
| A3 → A9 | Suave | Folder templates usan QuickAdd macros como entrada |
| A2 → A8 | Suave | Smart Connections puede instalarse sin Templater |
| A1 → A5 | Ninguna | Git backup no necesita vault unificado |
| **B1 → A2** | **Suave** | Gap Query outputs a notas con frontmatter (ideal pero no blocking) |
| **B5 → C4** | **Fuerte** | Metadata integration es el mismo componente — compartir implementación |
| **B6 → C3** | **Fuerte** | Promoción necesita scoring ≥70 de Mnemosyne |
| **B3 → B7** | **Fuerte** | Write buffer extiende file locking |
| **B4 → B2** | Suave | Tag merge es parte de curación targeted |
| C1 → C2 | Suave | Audience script puede correr sin library/ estructura |
| C2 → C3 | Suave | Promoción necesita audience tags para decidir destino |
| C5 → C2 | Dura | Dataview queries necesitan frontmatter `audience` poblado |
| C7 → B6 | Dura | Divergence detection necesita puntuación de contenido |
| C10 → C1 | Dura | Quartz deploy apunta a library/ |

### Fases de Ejecución

| Fase | Semana | Track A | Track B | Track C | Gate |
|---|---|---|---|---|---|
| **F0** | 1-2 | A1, A2, A3, A4, A5, A6, A7 | B1, B2, B3 | C1, C2, C6 | ✅ Gate F0→F1 |
| **F1** | 3-4 | A8, A9 | B4, B5, B6, B7 | C3, C4, C7 | ✅ Gate F1→F2 |
| **F2** | 5-6 | A10, A11 | B8, B9 | C5, C8, C9 | ✅ Gate F2→F3 |
| **F3** | 7-8 | A12, A13 | B10, B11 | C10, C11 | ✅ Entrega final |

### Principios de Paralelismo

1. **F0**: Todos los tracks arrancan el día 1 simultáneamente — 0 dependencias entre tracks
2. **F1**: Track B espera a A2 (Templater) para formato de notas — dependencia suave, no bloquea inicio
3. **F2**: Track C espera a B6 (scoring) para promoción — dependencia fuerte documentada
4. **F3**: Tracks independientes — cada uno finaliza su ciclo

---

## PARTE 2: Asignación por Track

### Track A — Obsidian Stack (Plugins + Configuración)

**Responsable**: Usuario / Kratos  
**Archivos**: `KAOS/` (vault Obsidian), `.obsidian/`, `_scripts/templates/`

| # | Tarea | Esfuerzo | Archivos | Cambio Específico | Dependencia | Criterio "Done" |
|---|---|---|---|---|---|---|
| A1 | **Unificar vaults** — Asegurar que `.memory/` sea accesible desde Obsidian | 🟢 30min | `KAOS/.obsidian/app.json` | Agregar `"folders": [...]` en app.json para incluir directorio `.memory` como parte del vault. O crear symlink: `New-Item -ItemType Junction -Path "KAOS/.memory" -Target ".memory"`. | Ninguna | `ls KAOS/.memory/wiki/` lista archivos desde el explorador de Obsidian |
| A2 | **Instalar Templater + Linter** | 🟢 30min | `.obsidian/plugins/templater/`, `.obsidian/plugins/obsidian-linter/` | 1. Instalar desde Community Plugins. 2. Desactivar Core Templates. 3. Configurar `Templates/` folder → `_scripts/templates/`. 4. Linter: activar YAML format, heading blanks, file names. | A1 | `ls .obsidian/plugins/templater/main.js` existe; Linter en plugins list |
| A3 | **Configurar QuickAdd** — macro captura + macro nota estructurada | 🟡 1h | `.obsidian/plugins/quickadd/data.json`, `_scripts/templates/quick-capture.md`, `_scripts/templates/structured-note.md` | 1. Crear macro "Captura": Alt+Q → prompt → append a `Inbox.md`. 2. Crear macro "Nota estructurada": Alt+Shift+Q → prompt para tipo → Templater genera archivo. 3. Templates de soporte. | A2 | Alt+Q abre prompt de captura; Alt+Shift+Q abre selector de tipo de nota |
| A4 | **Crear plantilla diaria Templater** | 🟡 2h | `_scripts/templates/daily.md`, `.obsidian/plugins/periodic-notes/data.json` | Template con: links día anterior/siguiente, metadata auto (created, modified), secciones (daily log, tasks, notes). Folder template apunta a `Daily/`. | A2 | Crear nota en `Daily/` → auto-ejecuta template con fecha, links, metadata |
| A5 | **Configurar Obsidian Git** | 🟢 15min | `.obsidian/plugins/obsidian-git/data.json`, `.gitignore` | 1. auto-commit interval: 30min. 2. auto-push interval: 2h. 3. Agregar `.obsidian/workspace.json` a `.gitignore`. 4. Pull on startup: on. | A1 | `git log` muestra commits automáticos; `git push` sube cambios cada 2h |
| A6 | **Auditar plugins existentes** | 🟢 30min | `.obsidian/community-plugins.json` | 1. Listar plugins activos. 2. Desactivar: Kanban, Excalidraw, Projects (si están instalados). 3. Target: ≤10 plugins activos. 4. Documentar decisión en `_scripts/templates/plugin-audit-log.md`. | Ninguna | `cat .obsidian/community-plugins.json | Measure-Object` ≤ 10 entradas |
| A7 | **Instalar Calendar + Periodic Notes** | 🟢 15min | `.obsidian/plugins/calendar/`, `.obsidian/plugins/periodic-notes/` | 1. Instalar desde Community Plugins. 2. Calendar: mostrar en ribbon. 3. Periodic Notes: configurar daily en `Daily/`, weekly en `Weekly/`. | A1 | Calendar muestra en panel izquierdo; click en fecha → crea daily note con template |
| A8 | **Instalar Smart Connections** | 🟡 1h | `.obsidian/plugins/smart-connections/` | 1. Instalar desde Community Plugins. 2. Indexar vault completo (primera vez ~5min para ~300 archivos). 3. Probar búsqueda semántica. | A5 (Git backup) | Smart Connections muestra resultados semánticos; búsqueda por significado funciona |
| A9 | **Configurar Folder Templates Templater** | 🟡 30min | `.obsidian/plugins/templater/data.json` | Agregar Folder Templates: `Projects/` → template proyecto, `Meetings/` → template reunión, `Concepts/` → template concepto. Sin intervención manual al crear archivo en carpeta. | A2 | Crear archivo en `Projects/` → auto-template sin preguntar |
| A10 | **Desarrollar 3 User Scripts Templater** | 🔴 4-6h | `_scripts/templates/scripts/fetch-api.js`, `_scripts/templates/scripts/extract-entities.js`, `_scripts/templates/scripts/adr-generator.js` | Script 1: fetch metadata from external APIs. Script 2: extract KAOS entities from text → auto-link. Script 3: generate ADR document from user input. | A2, A4 | `tb.getScript("fetch-api")` funciona en template; scripts listados en Templater config |
| A11 | **Performance tuning** | 🟢 30min | `.obsidian/app.json`, `.obsidian/community-plugins.json` | 1. Desactivar plugins no usados en 30 días. 2. Desactivar Dataview en mobile. 3. Lazy load para Smart Connections. 4. CSS snippets desactivados si no se usan. | A6 | Startup time <5s medido con `console.time()` en developer tools |
| A12 | **Configurar perfil mobile** | 🟢 30min | `.obsidian/app.json` (mobile config) | Perfil mobile: solo QuickAdd, Calendar, Periodic Notes, Obsidian Git activos. Templater desactivado (las notas se crean en desktop). | A6 | Obsidian mobile abre en <10s; solo 4 plugins activos |
| A13 | **Preparar H3 — Quartz estructura** | 🟡 2h | `KAOS/quartz/` (nuevo), `KAOS/quartz/config.toml` | 1. `npm init quartz` en KAOS/. 2. Apuntar content dir a `library/` (Track C). 3. Configurar base URL. 4. Verificar build local. | C10 (Quartz deploy) | `npx quartz build` produce `public/` con contenido de library/ |

---

### Track B — Mnemosyne Pipeline (Curación Automática)

**Responsable**: Kratos  
**Archivos**: `lib/agent_nodes/mnemosyne.py`, `lib/file_lock.py`, `lib/obsidian.py`, `lib/tagger.py`, `lib/agent_tools.py`

| # | Tarea | Esfuerzo | Archivos | Cambio Específico | Dependencia | Criterio "Done" |
|---|---|---|---|---|---|---|
| B1 | **Gap Query pre-captura** — Verificar/implementar `query_gaps()` | 🟡 2h | `lib/agent_nodes/mnemosyne.py` (líneas 0-350) | 1. Verificar que `query_gaps(topic)` existe como función exportable. 2. Si no, implementar: busca en `wiki/concepts/` conceptos relacionados por embedding (txtai) y retorna `existing_concepts`, `gaps_detected`, `orphan_pages`. 3. Añadir flag `--gap-query` al CLI vault.py. | Ninguna | `py -3 -c "from lib.agent_nodes.mnemosyne import query_gaps; assert 'existing_concepts' in query_gaps('agent architecture')"` |
| B2 | **Curación targeted post-captura** — Pipeline prioriza contenido nuevo | 🟡 3h | `lib/agent_nodes/mnemosyne.py` (fase de ingest, ~líneas 70-150) | 1. En `_mnemosyne_node_impl()`, antes de Phase A, detectar archivos nuevos en `raw/` (modificados en <24h). 2. Priorizar esos archivos en el pipeline (procesar primero). 3. Si `incremental=True`, solo procesar archivos nuevos + sus dependencias directas. | B1 (gap query alimenta priorización) | Mnemosyne procesa archivos nuevos de raw/ antes que wiki/ existente; logs muestran "targeted curation: 3 new files" |
| B3 | **File locking + buffer diferido** — Robustecer escritura concurrente | 🟡 2h | `lib/file_lock.py` (completo, 96 líneas) | 1. Añadir `buffered_write(path, data, buffer_size=5, flush_interval=30)` que acumula escrituras y escribe en lote. 2. Añadir `locked_append(path, line)` para operaciones append seguras. 3. Timeout configurable por recurso. 4. Lock files con TTL (borrar locks huérfanos >5min). | Ninguna | `py -3 -c "from lib.file_lock import buffered_write; buffered_write('tmp/test.md', 'data', flush_now=True)"` escribe archivo correctamente |
| B4 | **Merge de tags** — Preservar tags manuales al curar | 🟡 2h | `lib/tagger.py`, `lib/agent_nodes/mnemosyne.py` (fase tagger, ~líneas 80-88) | 1. En `suggest_tags()`, leer tags existentes del frontmatter antes de sugerir. 2. Merge: unión de tags manuales + sugeridos, sin duplicados. 3. Log de "tags añadidas: 3, tags preservadas: 5, tags manuales no tocadas: 2". | B2 (targeted curation usa tagger) | Tag existente manual no se elimina ni modifica; solo se añaden tags nuevos |
| B5 | **Frontmatter ↔ Obsidian Properties** — Sincronizar metadata | 🟡 3h | `lib/obsidian.py` (nuevo módulo `sync_properties()`), `lib/agent_tools.py` | 1. Crear `sync_properties(path)` que lee frontmatter YAML y actualiza Obsidian properties vía mcp-obsidian-cli. 2. Bidireccional: cambios en Obsidian properties → actualizar frontmatter en archivo. 3. Programar cada 15min via cron ligero. | B3 (file locking para evitar race conditions) | `py -3 -c "from lib.obsidian import sync_properties; assert sync_properties('test.md', {'status': 'complete'})"` actualiza frontmatter y Obsidian properties |
| B6 | **Scoring pipeline** — Integrar knowledge scoring de mnemosyne-curator | 🔴 4h | `lib/agent_nodes/mnemosyne.py` (nueva fase D2/K), `lib/quality/agent.py` (leer interfaz) | 1. Importar `KnowledgeScorer` desde quality module. 2. Añadir fase D2 (post-dedup) que scorea cada documento: 8 métricas → score 0-100. 3. Si score < 60 y `--auto-synthesize`, ejecutar síntesis. 4. Si score ≥ 70 y `audience: public`, marcar para promoción a library/. | B4 (tags consistentes mejoran scoring de conectividad) | `py -3 -c "from lib.agent_nodes.mnemosyne import KnowledgeScorer; s = KnowledgeScorer().score('test.md'); assert 0 <= s <= 100"` |
| B7 | **Write buffer diferido** — Integrar buffer en pipeline de escritura | 🟡 2h | `lib/file_lock.py`, `lib/agent_nodes/mnemosyne.py` (fase de escritura) | 1. En mnemosyne pipeline, en lugar de escribir cada archivo inmediatamente, acumular en buffer. 2. Flush automático cada 30s o al llegar a 10 archivos pendientes. 3. En caso de conflicto (archivo modificado por usuario), preservar versión de usuario y guardar versión Mnemosyne como `.pending`. | B3 (buffered_write como base) | Mnemosyne escribe 10 archivos en <2s (en lote); si usuario edita archivo, versión usuario gana, versión Mnemosyne va a `.pending/` |
| B8 | **Cross-reference + Lifecycle** — Fases avanzadas de Mnemosyne | 🔴 4h | `lib/agent_nodes/mnemosyne.py` (fases crossref + lifecycle) | 1. Implementar búsqueda semántica bidireccional (cross-ref) entre todos los conceptos. 2. Lifecycle eval: calcular decay por Ebbinghaus, tiers L0-L3. 3. Mover contenido decayido a `_archive/` si score < 20 por >3 meses. | B6 (scoring alimenta lifecycle) | `py -3 -c "from lib.agent_nodes.mnemosyne import lifecycle_eval; r = lifecycle_eval('test.md'); assert 'tier' in r and 'decay' in r"` |
| B9 | **Auto-promotion pipeline** — De wiki/ a library/ automático | 🟡 3h | `lib/agent_nodes/mnemosyne.py` (nueva fase P), `lib/promote.py` (nuevo) | 1. Nueva fase P (Promotion): detecta archivos en wiki/ con score ≥ 70 y `audience: public`. 2. COPY a `library/concepts/` con frontmatter simplificado para humanos. 3. Symlink en Windows: usar copia con hash tracking. 4. Reporte semanal de promociones. | B6 (scoring), C1 (library/ existe) | `ls library/concepts/` contiene archivos copiados; `promotion_report` lista últimas promociones |
| B10 | **Full automation cycle** — Pipeline sin intervención | 🟡 2h | `lib/agent_nodes/mnemosyne.py`, `_scripts/cron/mnemosyne-cron.py` (nuevo) | 1. Crear script cron que ejecuta pipeline completo cada 6h. 2. Flags: incremental por defecto, full run cada domingo. 3. Notificación si errores > umbral. | B8, B9 | `py -3 _scripts/cron/mnemosyne-cron.py` ejecuta pipeline sin errores; logs en `cache/pipeline_runs/` |
| B11 | **Feedback loop** — Mnemosyne → Aletheia retroalimentación | 🟡 2h | `lib/agent_nodes/mnemosyne.py` (reporte final), `lib/cross_agent.py` (aletheia_to_mnemosyne) | 1. Al final del pipeline, generar feedback estructurado para Aletheia: gaps encontrados, conceptos nuevos curados, calidad de fuentes. 2. Escribir en `transfers/mnemosyne_to_aletheia/`. | B8 (gaps detectados alimentan feedback) | `ls .memory/transfers/mnemosyne_to_aletheia/` contiene archivo JSON con feedback |

---

### Track C — Split Memoria/Biblioteca (Dual Track)

**Responsable**: Kratos / Mnemosyne  
**Archivos**: `library/` (nuevo), `lib/quality/vault.py`, `lib/agent_tools.py`, `_scripts/`

| # | Tarea | Esfuerzo | Archivos | Cambio Específico | Dependencia | Criterio "Done" |
|---|---|---|---|---|---|---|
| C1 | **Crear estructura `library/`** | 🟢 30min | `library/index.md`, `library/guides/`, `library/concepts/`, `library/reference/`, `library/processes/`, `library/maps/`, `library/assets/` | 1. Crear directorios según el schema del plan Dual Track. 2. `library/index.md` con landing page y mapa del ecosistema. 3. Cada subdirectorio con su propio `_index_.md` de navegación. | Ninguna | `Test-Path library/index.md` → True; estructura de 7 subdirectorios existe |
| C2 | **Script de etiquetado `audience` para archivos existentes** | 🟡 3h | `_scripts/scripts/add_audience.py` (nuevo), archivos en `wiki/concepts/` (~80), `wiki/entities/` (~30) | 1. Script que itera todos los `.md` en `wiki/concepts/` y `wiki/entities/`. 2. Si no tiene `audience` en frontmatter, añade `audience: agent` por defecto. 3. Para archivos con tags que sugieran contenido humano (ej: tag "guide", "tutorial"), preguntar al usuario o usar heurística. 4. Mode `--dry-run` primero, `--apply` para ejecutar. | C1 (estructura destino para promoción) | `py -3 _scripts/scripts/add_audience.py --dry-run` reporta "80 archivos sin audience, 15 sugeridos como 'both'" |
| C3 | **Fase P de promoción — COPY wiki/ → library/** | 🟡 3h | `_scripts/scripts/promote_to_library.py` (nuevo), `lib/promote.py` | 1. Script que lee archivos en `wiki/concepts/` con `audience: public` o `audience: both`. 2. COPY a `library/concepts/` con frontmatter transformado (simplificado para humanos). 3. Hash tracking: guardar hash SHA256 del archivo fuente para divergence detection. 4. Log de promociones. | C2 (audience tags), B6 (scoring ≥70) | `py -3 _scripts/scripts/promote_to_library.py --apply` copia archivos elegibles; `library/concepts/` contiene versiones humanas |
| C4 | **Integración de metadatos frontmatter ↔ Obsidian properties** | 🟡 2h | `lib/obsidian.py` (sync_properties), `library/` archivos | 1. Extender `sync_properties()` para que también actualice archivos en `library/`. 2. Para library/, añadir campos adicionales: `description`, `difficulty`, `est_read_time`. 3. Sincronización bidireccional con Obsidian properties. | B5 (frontmatter↔properties base) | `sync_properties('library/concepts/test.md')` actualiza frontmatter con campos humanos |
| C5 | **Queries Dataview para humanos** | 🟡 2h | `library/index.md`, `library/maps/knowledge-ecosystem.md` | 1. En `library/index.md`, agregar query Dataview que lista todo contenido de library/ por categoría. 2. En `library/maps/`, mapa visual del ecosistema con Dataview + Mermaid. 3. Dashboard de "contenido disponible" con tags, dificultad, tiempo de lectura. | C3 (contenido en library/), A7 (Dataview instalado) | `library/index.md` muestra tabla con todos los conceptos, tipo, dificultad, tiempo de lectura |
| C6 | **Actualizar AGENTS.md para incluir `library/` como fuente de contexto** | 🟢 30min | `.opencode/agents/aletheia.md`, `.opencode/agents/kosmos.md`, `.opencode/agents/kratos.md`, `.opencode/agents/metis.md`, `.opencode/agents/mnemosyne.md` | 1. En cada AGENTS.md, agregar en fuentes de contexto: `library/` (biblioteca de usuario). 2. Para agentes de investigación (Aletheia): priorizar library/ como fuente curada antes que raw/. 3. Mnemosyne: library/ como destino de promoción. | C1 (library/ existe) | `grep -c "library/" .opencode/agents/*.md` retorna 5 (todos los agentes) |
| C7 | **Divergence detection — hash comparison** | 🟡 2h | `lib/memory_diff.py` (nuevo), `lib/quality/vault.py` | 1. Script que compara hash SHA256 de archivos fuente en `wiki/concepts/` vs sus copias en `library/concepts/`. 2. Si divergen (fuente cambió pero library no se actualizó), marcar como "stale". 3. Reporte semanal de archivos stale. 4. Integrar en health dashboard. | C3 (hash tracking en promoción) | `py -3 lib/memory_diff.py` reporta "0 stale, 12 synced, 3 new (not yet promoted)" |
| C8 | **MOCs con Dataview — dashboard de conocimiento** | 🟡 2h | `library/maps/knowledge-ecosystem.md`, `library/maps/agent-interactions.md` | 1. MOC principal: tabla de contenido library/ por tipo, tags, dificultad. 2. MOC de interacciones: mapa de agentes y cómo se relacionan con el contenido. 3. Dataview queries agrupadas. | C5 (Dataview queries base), A7 (Dataview instalado) | `library/maps/knowledge-ecosystem.md` muestra 3+ tablas Dataview funcionales |
| C9 | **Quartz v5 preview local** | 🟡 2h | `KAOS/quartz/` (setup), `quartz/config.toml` | 1. `npm create quartz@latest` en la raíz. 2. Configurar `contentDir` apuntando a `library/`. 3. Build local: `npx quartz build`. 4. Preview: `npx quartz serve`. 5. Verificar que wikilinks funcionan (Quartz v5 soporta wikilinks nativos). | C3 (library/ tiene contenido) | `npx quartz build --serve` muestra sitio con contenido de library/ en `http://localhost:8080` |
| C10 | **Quartz deploy automático con GitHub Actions** | 🟡 3h | `.github/workflows/quartz-deploy.yml` (nuevo), `KAOS/quartz/` | 1. Crear GitHub Action: trigger en push a main que modifica `library/`. 2. Build Quartz. 3. Deploy a GitHub Pages. 4. Domain config si aplica. | C9 (Quartz build funciona local) | Push a main con cambios en library/ → GitHub Actions build + deploy → sitio público actualizado |
| C11 | **Divergence auto-sync — actualización automática de library/** | 🟡 2h | `lib/memory_diff.py`, `_scripts/cron/auto-sync-library.py` (nuevo) | 1. Cuando divergence detection encuentra archivo stale, ejecutar re-promotion automática. 2. Si diff >50% (cambio mayor), marcar para revisión humana. 3. Programa: sync cada 12h. 4. Notificar en health dashboard. | C7 (divergence detection), B9 (auto-promotion) | Archivo modificado en wiki/ se refleja en library/ en <12h automáticamente |

---

## PARTE 3: Seguridad y Validación

### Risk Matrix

| Riesgo | Prob | Impacto | Score | Mitigación | Track |
|---|---|---|---|---|---|
| **R1** Conflicto de escritura: Mnemosyne pipeline escribe mientras usuario edita en Obsidian | 3 | 4 | 12 | File locking (B3) + buffer diferido (B7) + regla estricta "Vault MCP escribe, obsidian-cli solo lee" documentada en `AGENTS.md` | B |
| **R2** Pérdida de tags manuales por auto-tagger de Mnemosyne | 3 | 3 | 9 | Merge de tags (B4) preserva manuales. Log de cambios. Rollback por archivo. | B |
| **R3** Duplicación de contenido entre wiki/ y library/ | 4 | 4 | 16 | Una fuente de verdad: wiki/ es primaria. Promoción solo copia, nunca mueve. Divergence detection (C7) alerta si divergen. | C |
| **R4** Obsidian Git push conflictivo por auto-commits de Mnemosyne | 3 | 3 | 9 | Buffer diferido (B7) agrupa escrituras. Mnemosyne commits en lote separado. `.gitignore` excluye workspace.json. | B |
| **R5** Contenido de library/ se vuelve obsoleto vs wiki/ | 3 | 4 | 12 | Divergence detection (C7) + auto-sync (C11). Health dashboard muestra "stale ratio". | C |
| **R6** QuickAdd no se adopta — macros instaladas pero no usadas | 4 | 3 | 12 | Training 2h en semana 1. Buddy system semana 2. Si <50% adopción en mes 1, revertir a stack mínimo. | A |
| **R7** Smart Connections degrada rendimiento del vault | 2 | 3 | 6 | Lazy load. Desactivar en mobile. Si startup >10s, desinstalar y usar txtai CLI. | A |
| **R8** Quartz build falla por wikilinks no resueltos | 2 | 4 | 8 | Validar wikilinks antes de build (C9). Alternativa: MkDocs + material theme. | C |
| **R9** Symlinks en Windows no funcionan con git | 3 | 3 | 9 | Usar copias con hash tracking en lugar de symlinks. Script de sync cross-OS. | C |
| **R10** Gap Query consume demasiado tiempo en pipeline | 2 | 2 | 4 | Gap Query solo en modo `--full`. Por defecto `--incremental` + skip si no hay consulta de Aletheia. | B |

### Gates de Calidad

#### Gate F0→F1 (Final Semana 2)

| Verificación | Comando | Criterio |
|---|---|---|
| QuickAdd funcional | Probar Alt+Q → capturar nota | Nota aparece en Inbox/ |
| Templater funcional | Crear nota en Daily/ | Template se ejecuta con metadata |
| Obsidian Git activo | `git log --oneline -5` | Commits automáticos cada 30min |
| Plugins ≤10 activos | `cat .obsidian/community-plugins.json \| Measure-Object` | ≤10 entradas |
| File locking operativo | `py -3 -c "from lib.file_lock import acquire_lock, release_lock; assert acquire_lock('test'); release_lock('test')"` | ✅ Sin errores |
| library/ estructura | `Test-Path library/index.md` | ✅ True |
| AGENTS.md actualizado | `grep -c "library" .opencode/agents/*.md` | ≥3 agentes incluyen library/ |

#### Gate F1→F2 (Final Semana 4)

| Verificación | Comando | Criterio |
|---|---|---|
| Smart Connections indexado | Verificar panel SC muestra embeddings cargados | ✅ Index completado |
| Tag merge funcional | Editar tag manual, ejecutar Mnemosyne tagger | Tag manual preservado |
| Scoring pipeline | `py -3 -c "from lib.agent_nodes.mnemosyne import KnowledgeScorer; s = KnowledgeScorer().score('test.md'); assert s >= 0"` | ✅ Score devuelto |
| Audience tags poblados | `py -3 _scripts/scripts/add_audience.py --dry-run` | 0 archivos sin audience |
| Buffer diferido funcional | `py -3 -c "from lib.file_lock import buffered_write; buffered_write('tmp/test.md', 'data')"` | ✅ Archivo escrito |
| Promoción manual | `py -3 _scripts/scripts/promote_to_library.py --apply` | Archivos en library/ |

#### Gate F2→F3 (Final Semana 6)

| Verificación | Comando | Criterio |
|---|---|---|
| Dataview queries en library/ | Abrir `library/index.md` en Obsidian | Tablas Dataview visibles |
| Quartz build local | `npx quartz build --serve` | Sitio servido en localhost:8080 |
| Divergence detection | `py -3 lib/memory_diff.py` | Reporte sin errores |
| Auto-promotion pipeline | Ejecutar mnemosyne con fase P | Archivos promovidos automáticamente |
| Cross-ref + Lifecycle | `py -3 -c "from lib.agent_nodes.mnemosyne import lifecycle_eval"` | ✅ Lifecycle evaluado |
| User Scripts Templater | Probar script fetch-api en template | ✅ Script se ejecuta |

#### Gate Final (Semana 8)

| Verificación | Comando | Criterio |
|---|---|---|
| Suite completa de tests | `py -3 -m pytest .memory/_scripts/tests/ -v --no-header` | ✅ ≥90% pass rate |
| Obsidian startup | Medir startup time | ≤5s en desktop, ≤10s en mobile |
| library/ content | `ls library/concepts/ \| Measure-Object` | ≥10 archivos |
| Quartz deploy CI/CD | Push a main → GitHub Actions | Sitio público actualizado |
| Divergence auto-sync | Modificar wiki/ → esperar 12h | library/ se actualiza automáticamente |
| Health dashboard | `py -3 .memory/_scripts/vault.py quality dashboard` | Dashboard muestra todos los tracks operativos |

### Rollback Plan

| Escenario | Síntoma | Rollback | Tracks afectados |
|---|---|---|---|
| QuickAdd rompe captura | Alt+Q no responde | Desinstalar QuickAdd, restaurar data.json de backup | A |
| Templater corrompe templates | Notas sin frontmatter | `git checkout -- _scripts/templates/` | A |
| Obsidian Git commit loop | Commits cada 1min sin cambios | Editar data.json: `autoCommitInterval: 0` | A |
| File locking deadlock | Pipeline se cuelga | `Remove-Item .memory/cache/locks/*.lock -Force` | B |
| Tag merge pierde tags | Tags manuales desaparecen | `git checkout -- wiki/concepts/` + re-aplicar tags manuales | B |
| Promoción duplica contenido | library/ tiene duplicados | `git clean -fd library/` + re-promover manual | C |
| Quartz build falla | GitHub Actions red | Desactivar workflow, revertir a MkDocs | C |
| Smart Connections lento | Startup >15s | Desinstalar SC, desactivar feature flag | A |
| Scoring pipeline bug | Scores inconsistentes | `git checkout -- lib/agent_nodes/mnemosyne.py` | B, C |
| Divergence auto-sync incorrecto | library/ sobrescribe wiki/ | `git checkout -- library/` + desactivar auto-sync | C |

### Verificación Continua

| Test / Verificación | Comando | Frecuencia | Track |
|---|---|---|---|
| Suite unitaria Mnemosyne | `py -3 -m pytest .memory/_scripts/tests/test_mnemosyne_integration.py -v --no-header` | Por commit | B |
| Suite lint | `py -3 -m flake8 .memory/_scripts/lib/` | Por commit | B, C |
| Health dashboard | `py -3 .memory/_scripts/vault.py quality dashboard` | Diario | A, B, C |
| Wikilinks salud | `py -3 .memory/_scripts/vault.py wikilinks report` | Semanal | B |
| Divergence report | `py -3 lib/memory_diff.py` | Semanal | C |
| Library coverage | `ls library/concepts/ \| Measure-Object` | Semanal | C |
| Obsidian Git status | `git log --oneline --since="24 hours ago"` | Diario | A |
| Pipeline execution | Revisar `cache/pipeline_runs/latest.json` | Por ejecución | B |
| Audience tag coverage | `py -3 _scripts/scripts/add_audience.py --dry-run` | Semanal | C |
| Promoción report | `py -3 _scripts/scripts/promote_to_library.py --report` | Semanal | C |

---

## PARTE 4: Cronograma Consolidado

| Semana | Track A | Track B | Track C | Gate / Hito |
|---|---|---|---|---|
| **1** | A1 (vault unify) + A2 (Templater/Linter) + A5 (Git) + A6 (audit) + A7 (Calendar) | B1 (Gap Query) + B3 (file locking) | C1 (library/ structure) + C6 (AGENTS.md) | ✅ Día 3: Plugins base instalados + library/ creado |
| **2** | A3 (QuickAdd macros) + A4 (daily template) | B2 (targeted curation) | C2 (audience script) | ✅ Gate F0→F1: QuickAdd funcional, audience tags empezados |
| **3** | A8 (Smart Connections) | B4 (tag merge) + B5 (frontmatter↔properties) | C4 (metadata integration) + C7 (divergence detection) | ✅ Smart Connections indexando |
| **4** | A9 (folder templates) | B6 (scoring pipeline) + B7 (write buffer) | C3 (promotion script) | ✅ Gate F1→F2: Scoring pipeline operativo, promoción manual posible |
| **5** | A10 (User Scripts Templater) | B8 (cross-ref + lifecycle) | C5 (Dataview queries) + C8 (MOCs) | ✅ Dataview dashboards en library/ |
| **6** | A11 (performance tuning) | B9 (auto-promotion) | C9 (Quartz preview) | ✅ Gate F2→F3: Quartz build local funcional |
| **7** | A12 (mobile profile) | B10 (full automation cron) | C10 (Quartz deploy CI/CD) | ✅ Pipeline automático 6h, Quartz deploy en CI |
| **8** | A13 (Quartz structure prep) | B11 (feedback loop) | C11 (divergence auto-sync) | ✅ Gate Final: Entrega completa, todos los tracks integrados |

### Tiempo Real Estimado

```
Métrica                 Días-Hombre    Días-Calendario (3 tracks)
─────────────────────   ────────────   ──────────────────────────
Track A (13 tareas)     ~12.5 días     12.5 días (1 persona)
Track B (11 tareas)     ~25.0 días     25.0 días (1 persona)
Track C (11 tareas)     ~19.5 días     19.5 días (1 persona)

Implementación pura     ~57.0 días     19.0 días (3 personas)
Integración + Tests     ~8.0 días       4.0 días (2 personas)
Fixes + Documentación   ~5.0 días       2.5 días (2 personas)

TOTAL                   ~70.0 días      25.5 días calendario
```

### Cuello de Botella Identificado

**Track B es el cuello de botella** (25 días-hombre vs 12.5 de A y 19.5 de C). Estrategias de aceleración:

1. **B1+B3**: Asignar al mismo developer — ambos son infraestructura de pipeline (~4h combinados)
2. **B4+B5+B6**: Secuenciar en orden — B4 → B5 → B6 (scoring necesita tags consistentes) — mismo developer idealmente
3. **B8+B9+B10**: El más pesado — considerar dividir entre 2 developers:
   - Dev 1: B8 (cross-ref + lifecycle) ~4h
   - Dev 2: B9 (auto-promotion) + B10 (cron) ~5h
4. **Track A puede completarse en paralelo sin depender de B**: todas las tareas A son independientes de B y C

---

## PARTE 5: Tabla de Esfuerzo Consolidada

```
Esfuerzo    Cantidad    Tareas
────────    ────────    ──────
🟢 <1h      12          A1, A5, A6, A7, A9, A11, A12, C1, C6, B10, A13, B11
🟡 1-4h     18          A2, A3, A4, A8, A13, B1, B2, B3, B4, B5, B7, B9, C2, C3, C4, C5, C7, C8, C9, C11
🔴 4-8h      5          A10, B6, B8, C10, B11

Total: ~35 tareas, ~70 días-hombre, ~25.5 días calendario (3 tracks paralelos)
```

---

## PARTE 6: ANEXO — Comandos de Verificación Rápida

```powershell
# === VERIFICACIÓN RÁPIDA POST-EJECUCIÓN ===

# 1. Track A: Plugins esenciales instalados
Write-Host "=== Track A: Plugins ==="
if (Test-Path ".obsidian/plugins/templater/main.js") { Write-Host "✅ Templater" } else { Write-Host "❌ Templater" }
if (Test-Path ".obsidian/plugins/quickadd/main.js") { Write-Host "✅ QuickAdd" } else { Write-Host "❌ QuickAdd" }
if (Test-Path ".obsidian/plugins/obsidian-linter/main.js") { Write-Host "✅ Linter" } else { Write-Host "❌ Linter" }
if (Test-Path ".obsidian/plugins/obsidian-git/main.js") { Write-Host "✅ Obsidian Git" } else { Write-Host "❌ Obsidian Git" }

# 2. Track A: Plugins count
$count = (Get-Content ".obsidian/community-plugins.json" | ConvertFrom-Json).Count
if ($count -le 10) { Write-Host "✅ Plugins activos: $count (≤10)" } else { Write-Host "⚠️ Plugins activos: $count (>10)" }

# 3. Track B: File locking
py -3 -c "from lib.file_lock import acquire_lock, release_lock; l=acquire_lock('test', timeout=2); release_lock('test'); print('✅ File locking OK' if l else '❌ File locking failed')"

# 4. Track B: Gap Query
py -3 -c "from lib.agent_nodes.mnemosyne import query_gaps; r=query_gaps('test'); assert isinstance(r, dict); print('✅ Gap Query OK')"

# 5. Track B: Scoring (si implementado)
py -3 -c "from lib.agent_nodes.mnemosyne import KnowledgeScorer; print('✅ Scoring import OK')" 2>$null

# 6. Track C: Library structure
if (Test-Path "library/index.md") { Write-Host "✅ library/index.md" } else { Write-Host "❌ library/index.md" }
$libDirs = @("guides", "concepts", "reference", "processes", "maps", "assets")
foreach ($d in $libDirs) { if (Test-Path "library/$d") { Write-Host "✅ library/$d" } else { Write-Host "❌ library/$d" } }

# 7. Track C: Audience tags
py -3 _scripts/scripts/add_audience.py --dry-run 2>$null

# 8. Track C: AGENTS.md library reference
$agentCount = (Select-String -Path ".opencode/agents/*.md" -Pattern "library/" | Measure-Object).Count
if ($agentCount -ge 3) { Write-Host "✅ AGENTS.md library references: $agentCount" } else { Write-Host "⚠️ AGENTS.md library references: $agentCount (target: ≥3)" }

# 9. Smoke: Suite Mnemosyne tests
py -3 -m pytest .memory/_scripts/tests/test_mnemosyne_integration.py -v --no-header --tb=short 2>$null

# 10. Global: Lint
py -3 -m flake8 .memory/_scripts/lib/ --statistics 2>$null

Write-Host "`n=== Verification Complete ==="
```

---

## PARTE 7: Dependencias y Secuencia Recomendada

### Orden de Ejecución por Developer

**Developer 1 (Infraestructura/Kratos) — Track A + Track B base:**

| Orden | Tarea | Día estimado | Rationale |
|---|---|---|---|
| 1 | A1: Unificar vaults | Día 1 mañana | Fundación — sin vault unificado nada más funciona |
| 2 | A5: Obsidian Git | Día 1 mañana | Backup inmediato, 15 min |
| 3 | A2: Templater + Linter | Día 1 tarde | Prerrequisito para A3, A4 |
| 4 | A3: QuickAdd macros | Día 1 tarde | Mayor ROI de todo el plan |
| 5 | A6: Audit plugins | Día 2 mañana | Quick win, 30 min |
| 6 | A7: Calendar + Periodic | Día 2 mañana | Rápido, mejora UX |
| 7 | A4: Daily template | Día 2 tarde | Depende de Templater listo |
| 8 | B1: Gap Query | Día 3 mañana | Independiente de A |
| 9 | B3: File locking | Día 3 tarde | Independiente de A |
| 10 | B2: Targeted curation | Día 4 mañana | Depende de B1 |

**Developer 2 (Pipeline/Mnemosyne) — Track B avanzado:**

| Orden | Tarea | Día estimado | Rationale |
|---|---|---|---|
| 1 | B4: Tag merge | Día 3 | Independiente |
| 2 | B5: Frontmatter↔Properties | Día 3-4 | Independiente, pero compartir interfaz con C4 |
| 3 | B6: Scoring pipeline | Día 4-5 | Tarea más pesada de B (4h) |
| 4 | B7: Write buffer | Día 5 | Depende de B3 |
| 5 | B8: Cross-ref + Lifecycle | Día 6-7 | Depende de B6 |
| 6 | B9: Auto-promotion | Día 7 | Depende de B6 + C1 |
| 7 | B10: Full automation cron | Día 8 | Depende de B8, B9 |
| 8 | B11: Feedback loop | Día 8 | Depende de B8 |

**Developer 3 (Knowledge/Content) — Track C + Track A UX:**

| Orden | Tarea | Día estimado | Rationale |
|---|---|---|---|
| 1 | C1: Crear library/ | Día 1 mañana | Independiente — empezar inmediato |
| 2 | C6: AGENTS.md update | Día 1 mañana | 30 min, independiente |
| 3 | A8: Smart Connections | Día 2 | Independiente, 1h |
| 4 | A9: Folder templates | Día 2 | Independiente |
| 5 | C2: Audience script | Día 3 | Depende de C1 |
| 6 | C4: Metadata integration | Día 4 | Compartir con B5 |
| 7 | C3: Promotion script | Día 5 | Depende de C2 + B6 (scoring) |
| 8 | C5: Dataview queries | Día 5-6 | Depende de C3 |
| 9 | C7: Divergence detection | Día 6 | Depende de C3 |
| 10 | A10: User Scripts | Día 7-8 | Pesado (4-6h), dejar para F2 |

### Reglas de Oro

1. **No empezar F1 sin Gate F0→F1 aprobado** — QuickAdd + Templater + Git backup son base de todo
2. **Scoring pipeline (B6) es el camino crítico de Track C** — sin scoring, no hay promoción automática
3. **File locking (B3) debe implementarse antes que buffer diferido (B7)** — B7 extiende B3
4. **Divergence detection (C7) antes que auto-sync (C11)** — no auto-sincronizar sin detección primero
5. **Los 3 developers pueden trabajar en paralelo desde el día 1** — sin dependencias cruzadas entre tracks en F0
6. **Si solo hay tiempo para 3 tareas:** A3 (QuickAdd) + A5 (Git) + C1 (library/) — esto es el MVP mínimo viable
7. **Si solo hay tiempo para 1 tarea:** A3 (QuickAdd) — 30:1 ROI ratio, el plugin más valioso de todo el plan

---

*Plan generado por **Metis** (Μῆτις) — Diosa de la Sabiduría, KAOS Strategy Agent*  
*Fecha: 2026-05-30*  
*Formato: Parallel Tactical Plan (Aether-style) · 3 Tracks · 35 tareas · 8 semanas*  
*Dependencias: 100% mapeadas · Rollback: cada tarea · Gates: 4 fases de calidad*
