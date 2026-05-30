# Strategic Consolidation Plan: PDF Report Generation System

**Status:** Draft · **Date:** 2026-05-28 · **Author:** Metis · **Version:** 1.0

---

## Resumen Ejecutivo

El sistema de generación de reportes PDF en KAOS alcanzó **8.0/10** post-fixes, con los 6 generadores agente-específicos produciendo PDFs válidos. La consolidación requiere cerrar 5 brechas: tests automatizados (P1), 3 funciones de chart sin validar (P2), 5 templates faltantes (P2), charts en pipeline reports (P3) e interfaz abstracta (P3).

**North Star:** *Every KAOS interaction produces a polished, distributable report — automatically.*

---

## 1. Strategic Vision (3-6 Month Horizon)

| Horizonte | Estado | Descripción |
|-----------|--------|-------------|
| **Hoy** (Semana 1-3) | MVP funcional | 6 generadores, 1 template custom, charts básicos |
| **3 meses** | Estandarización | Todos los agentes producen PDFs con templates específicos, tests, pipeline integrado |
| **6 meses** | Distribución | PDFs se envían automáticamente vía Hermes (Telegram/Email/Discord), dashboard de reportes |

### Fit with KAOS

```
[Agent Pipeline] → [PDF Report Generator] → [Knowledge Vault (.vault/reports/)]
                                          → [Hermes Workspace] → [Telegram / Email / Web]
```

### Regla de Formato
- **Markdown** para máquinas (logs, vault interno)
- **PDF** para humanos (distribución externa, stakeholders)
- **HTML** para dashboards interactivos

---

## 2. Phase Planning — 3 Sprints

### Sprint 1: Foundation Hardening (Week 1)
**Objetivo:** Pasar de 8.0 → 9.0/10 con tests y validación

| Item | Esfuerzo |
|------|:--------:|
| Test suite para `pdf_chart_engine.py` (7/7 chart types) | 3h |
| Test suite para `pdf_report_generator.py` (mock Playwright) | 4h |
| Test suite para Jinja2 templates (render con datos mock) | 2h |
| Validar radar, heatmap, waterfall (3 funciones P2) | 2h |
| CI workflow (GitHub Actions) | 2h |
| Mock Playwright en CI | 1h |

### Sprint 2: Agent Templates (Week 2)
**Objetivo:** 6/6 agentes con templates específicos

| Template | Líneas | Dificultad |
|----------|:------:|:----------:|
| aletheia.html (Research) | ~120 | Baja |
| kosmos.html (Architecture) | ~100 | Baja |
| kratos.html (Code) | ~150 | Media |
| mnemosyne.html (Curation) | ~100 | Baja |
| kronos.html (Pipeline) | ~130 | Media |

### Sprint 3: Integration & Polish (Week 3)
**Objetivo:** Pipeline completos, interfaz abstracta, documentación

| Item | Esfuerzo |
|------|:--------:|
| Charts en pipeline report (waterfall timeline, cost bar, quality radar) | 4h |
| Abstract ReportInterface | 4h |
| Documentation (API, template guide, demo script) | 6h |
| report_engine.py alignment | 2h |

---

## 3. Resource & Cost Analysis

| Item | Costo |
|------|:-----:|
| Playwright Chromium (disk) | ~350 MB (one-time) |
| Reports disk | ~100 MB / 1000 reports |
| **Total infra** | **~$0** (todo local) |
| Dev cost (48h @ $50/h) | **$2,400** |
| Maintenance | **~$600/año** |

**ROI break-even:** 4 meses (20 reports/mes × 2h ahorro en formateo)

---

## 4. Risk Register

| # | Riesgo | Prob | Impacto | Mitigación |
|---|--------|:----:|:-------:|------------|
| 1 | Playwright compatibility rot | Media | Alto | Pin version, test CI semanal, fallback HTML |
| 2 | Template complexity growth | Media | Medio | Design system con `_components/`, max 3 bloques únicos/template |
| 3 | No ownership post-implementation | Alta | Medio | Owner rotativo Kronos→Kratos, runbook |
| 4 | Performance regression (PDF slowing pipeline) | Baja | Alto | 30s timeout, feature flag, async background gen |
| 5 | Scope creep (infografías, dashboards embebidos) | Alta | Bajo | Principio Pareto: 80% valor con 20% complejidad |

### Playwright Exit Strategy
Si Playwright falla: migrar a **WeasyPrint** (misma entrada HTML, diferente backend). La abstracción `ReportInterface` facilita el swap.

---

## 5. OKRs

### Objective 1: Production-Ready Reliability
| KR | Baseline | Target |
|----|:--------:|:------:|
| Chart functions validated | 4/7 | **7/7 (100%)** |
| Code coverage on PDF modules | ~0% | **>80%** |
| Security vulnerabilities | ? | **0 critical** |
| CI pipeline status | ❌ | **✅ Green** |

### Objective 2: Full Agent Coverage
| KR | Baseline | Target |
|----|:--------:|:------:|
| Agent-specific templates | 1/6 | **6/6** |
| Pipeline runs with reports | 0% | **100%** |
| Avg generation time p95 | ~2-5s | **<5s** |

### Objective 3: Developer Adoption
| KR | Baseline | Target |
|----|:--------:|:------:|
| API documentation | ❌ | **✅ docs/pdf-report-system.md** |
| Template design guide | ❌ | **✅ docs/pdf-template-guide.md** |
| Demo script | ❌ | **✅ all 6 agent types** |
| ReportInterface abstract | ❌ | **✅ implemented** |

---

## 6. Competitive Landscape

| Sistema | Output | Charts | Templates | Multi-agent |
|---------|--------|:------:|:---------:|:-----------:|
| **KAOS** (target) | PDF + HTML + MD | ✅ 7 types | ✅ 6 agents | **✅ Unificado** |
| AutoGPT | JSON/text | ❌ | ❌ | ❌ |
| CrewAI | Markdown | ❌ | ❌ | ❌ |
| ChatGPT Canvas | Rich text | ✅ inline | ❌ | ❌ |

**Diferenciador clave:** Ningún otro sistema multi-agente produce un reporte unificado con charts, branding y distribución vía vault/Hermes.

---

## 7. Decision Framework

```
¿Salida final para humanos?
├── Sí → ¿Imprimible/compartible?
│   ├── Sí → PDF (Playwright)
│   └── No → ¿Interactivo?
│       ├── Sí → HTML (dashboard)
│       └── No → Markdown (vault)
└── No → Markdown/JSON (logs, machine)
```

---

## 8. Strategic Recommendations

### Do Now (Sprint 1)
1. Escribir tests (chart validation → generator mock → template render)
2. Validar radar, heatmap, waterfall (2h)
3. Set up CI

### Do Next (Sprint 2)
4. Diseñar 5 templates faltantes (prioridad: Kratos → Aletheia → Kronos → Kosmos → Mnemosyne)
5. Documentar template design guide

### Do Later (Sprint 3+)
6. Implementar ReportInterface
7. Charts en pipeline report
8. Hermes integration

### Don't Do
- ❌ Reemplazar `report_engine.py` (propósitos distintos)
- ❌ Añadir más chart types hasta validar los 7 existentes
- ❌ Interactive PDFs (lo interactivo va en HTML)

---

## 9. File Structure (Target State)

```
.memory/_scripts/lib/pdf_templates/
├── base.html               # Base (shared)
├── _components/             # Shared partials (NEW)
├── aletheia.html            # Research (NEW)
├── kosmos.html              # Architecture (NEW)
├── metis.html               # Strategy (done)
├── kratos.html              # Code (NEW)
├── mnemosyne.html           # Curation (NEW)
└── kronos.html              # Pipeline (NEW)

.memory/_scripts/tests/pdf/  # Test suite (NEW)
docs/pdf-report-system.md     # Architecture docs (NEW)
docs/pdf-template-guide.md    # Template guide (NEW)
examples/pdf_report_demo.py   # Demo script (NEW)
```
