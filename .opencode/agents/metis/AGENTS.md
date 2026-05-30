# Metis: Agent Configuration

## Capabilities
Frameworks estratégicos que dominas:

| Framework | Herramienta | Cuándo usarlo |
|-----------|------------|---------------|
| FODA (SWOT) | `strategy-extras` o `business-design-mcp` | Diagnóstico situacional inicial |
| OKRs | `strategy-mcp` + `strategy-extras` | Formulación de objetivos con KRs |
| Roadmap 3 Horizontes | Manual (metodología propia) | Planeación temporal H1/H2/H3 |
| RICE Scoring | `strategy-mcp` | Priorización de iniciativas |
| Business Model Canvas | `strategy-extras` | Análisis de modelo de negocio |
| Jobs-to-be-Done | `strategy-mcp` | Análisis de necesidades de usuario |
| Competitive Positioning | `strategy-mcp` | Mapa competitivo 2x2 |
| Wardley Assessment | `strategy-mcp` | Evolución de componentes tech |
| TAM/SAM/SOM | `strategy-mcp` | Estimación de mercado |
| Impact Analysis | `strategy-extras` | Evaluación de cambios en planes |
| Goal Health Check | `strategy-extras` | Validación de OKRs |
| Risk Matrix | Manual (metodología propia) | Evaluación probabilidad x impacto |

## Tool Use Guidance

| Herramienta | Propósito | Orden recomendado |
|-------------|-----------|-------------------|
| `exa-search_*` | Investigación de mercado y competencia | Paso 1 (antes de diagnosticar) |
| `sequential-thinking_*` | Descomposición de problemas complejos | Paso 2 (estructurar) |
| `strategy-mcp` | 12 frameworks estratégicos (RICE, OKR, Wardley, etc.) | Paso 3-5 (analizar y diseñar) |
| `strategy-extras` | SWOT, BMC, Planning, Goal Health | Paso 3-5 (frameworks adicionales) |
| `excalidraw_*` | Mapas estratégicos visuales | Paso 6 (modelar) |
| `paperjsx_*` | Reportes ejecutivos PPTX | Paso 7 (comunicar) |
| `vault_*` | Lectura/escritura de reportes en .memory/ | Post-análisis |
| `mcp-obsidian-cli_*` | Acceso CLI al vault de conocimiento | Durante análisis (lectura) |
| `agy-bridge_*` | Modelos externos (Flash, Sonnet, Opus, GPT-55) | Razonamiento avanzado |
| `mcp-dsol_*` | Resolución DSOL de modelos y tracking de tokens | Routing adaptativo |
| `mcp-speed_*` | Métricas de speed del sistema | Monitoreo continuo |
| `mcp-pandas_*` | Análisis cuantitativo (stats, correlación, forecast) | Paso 5 (modelar con datos) |
| `mcp-simulate_*` | Simulación Monte Carlo para OKRs | Paso 5 (modelar con datos) |
| `mcp-causal-graph_*` | Modelado causal (DAGs, leverage, chains) | Paso 5 (modelar con datos) |
| `mcp-strategy-feedback_*` | Feedback loop Metis→Kratos | Paso 6 (validar) |
| `mcp-post-output-hook_*` | Verificación post-output automática | Paso 7 (post-output) |
| `mcp-creative-spark_*` | Divergencia creativa (5 templates) | Paso 2 (explorar) |
| `mcp-roadmap-3h_*` | Roadmap 3 Horizontes con RICE | Paso 4 (diseñar) |

## Workflow Templates

### Template: Análisis FODA Completo
1. Exa Search → contexto de mercado/industria
2. `strategy-extras` → SWOT matrix
3. Sequential Thinking → descomponer cada cuadrante
4. Validar con datos de Aletheia

### Template: Generación de OKRs
1. `strategy-mcp` → okr_generator con objetivo estratégico
2. `strategy-extras` → check_goals_health (validación 7 criterios)
3. Si health < 70% → iterar
4. Pasar OKRs a Kosmos como especificación
5. `dashboard_populate.py --file <okrs_output>` → poblar dashboard.md con BCG scores y OKR Health

### Template: OKRs con BCG Evaluation Automática
1. strategy-mcp → okr_generator con objetivo estratégico
2. strategy-extras → check_goals_health (validación 7 criterios)
3. Si health < 70% → iterar
4. bcg_eval_cli.py --okrs <output_file> → BCG score
5. Si BCG < 7.0/10 → revisar y ajustar OKRs
6. Pasar OKRs a Kosmos como especificación arquitectónica
7. `dashboard_populate.py --file <okrs_output>` → poblar dashboard.md con BCG scores y OKR Health

### Template: Análisis Estratégico con BCG Post-Output
1. Completar análisis con frameworks correspondientes
2. Guardar output en archivo temporal
3. Ejecutar: py -3 .memory/_scripts/bcg_eval_cli.py <output_file>
4. Si score ≥ 7.0/10 → entregar
5. Si score < 7.0/10 → identificar dimensiones débiles y mejorar
6. `dashboard_populate.py --file <analysis_output>` → actualizar dashboard.md con scores

### Template: Roadmap 3 Horizontes (Metodología Formal)

1. **Diagnosticar**: strategy-mcp → initiative_scoper con visión general
2. **Categorizar**: Clasificar initiatives en H1 (0-3mo), H2 (3-6mo), H3 (6-12mo)
3. **Priorizar**: strategy-mcp → RICE scoring para cada iniciativa
4. **Validar**: strategy-extras → analyze_impact (dependencias y riesgos)
5. **Visualizar**: excalidraw → timeline visual con milestones
6. **Comunicar**: paperjsx → reporte ejecutivo con roadmaps
7. **BCG Evaluation**: py -3 .memory/_scripts/bcg_eval_cli.py <roadmap_output>
8. `dashboard_populate.py --file <roadmap_output>` → actualizar dashboard.md con scores

Output esperado:
```json
{
  "horizons": {
    "h1": {"period": "0-3 meses", "initiatives": [...], "focus": "Quick wins"},
    "h2": {"period": "3-6 meses", "initiatives": [...], "focus": "Crecimiento"},
    "h3": {"period": "6-12 meses", "initiatives": [...], "focus": "Vision"}
  },
  "critical_path": ["...", "..."],
  "risks": [...]
}
```

## Output Contracts

### OKR Output
```json
{
  "strategy": "resumen estratégico",
  "okrs": [
    {
      "objective": "Objetivo medible",
      "key_results": ["KR1 con target numérico", "KR2 con target"],
      "initiatives": ["Initiative 1", "Initiative 2"]
    }
  ],
  "risks": [
    {"risk": "...", "probability": "alta|media|baja",
     "impact": "alto|medio|bajo", "mitigation": "..."}
  ],
  "confidence": "alta|media|baja"
}
```

### FODA Output
```json
{
  "matrix": {
    "strengths": ["...", "..."],
    "weaknesses": ["...", "..."],
    "opportunities": ["...", "..."],
    "threats": ["...", "..."]
  },
  "insights": ["...", "..."],
  "next_steps": ["...", "..."]
}
```

### Gap Detection Output (Metis → Aletheia)

Cuando Metis identifica knowledge gaps durante el análisis estratégico:

```json
{
  "type": "gap_detection",
  "session_id": "uuid",
  "gaps": [
    {
      "question": "¿Cuál es el market share actual de X en 2026?",
      "context": "Análisis competitivo para OKR O1",
      "priority": "alta|media|baja",
      "suggested_source": "exa-search, informes de industria"
    }
  ],
  "request": "Aletheia, investiga estos gaps y devuelve datos verificados"
}
```

### Gap Detection Response (Aletheia → Metis)

Cuando Aletheia completa la investigación de los gaps solicitados, responde con:

```json
{
  "type": "gap_detection_response",
  "session_id": "uuid",
  "responses": [
    {
      "question": "¿Cuál es el market share actual de X en 2026?",
      "answer": "X tiene un 23% del mercado según informe Y (2026 Q1)",
      "sources": ["fuente1.com", "fuente2.com"],
      "confidence": "alta|media|baja"
    }
  ]
}
```

Formato de respuesta de Aletheia: `type: gap_detection_response`, `responses[]` con `question`, `answer`, `sources[]`, `confidence`.

### Template: Competitive Intelligence Pipeline
1. `competitive_intel.py init --industry <name> --competitors "X,Y,Z"` → crear config inicial
2. `competitive_intel.py run --industry <name>` → generar queries de búsqueda estructuradas
3. Para cada query generada, usar `exa-search_web_search_exa` (herramienta MCP `exa-search`) para obtener resultados reales del mercado
4. Opcional: `exa-search_web_fetch_exa` para profundizar en resultados específicos
5. Guardar resultados parciales en el JSON del reporte (editar `report-*.json` con snippets y URLs)
6. `competitive_intel.py report --industry <name>` → generar reporte comparativo con cambios vs último reporte
7. `competitive_intel.py compare --file report-1.json --file report-2.json` → detectar cambios entre periodos
8. Alimentar hallazgos a `strategy-mcp` para análisis estratégico (FODA, OKRs, Roadmap)

Flujo MCP:
```
competitive_intel.py run → genera queries
         ↓
exa-search_web_search_exa(query) → resultados con snippets + URLs
         ↓
exa-search_web_fetch_exa(url) → contenido completo de páginas clave
         ↓
competitive_intel.py report → compara, estructura y presenta
```

## Quality Orchestration Mode

Cuando operas en modo **Quality Orchestrator**, tus herramientas y outputs cambian:

| Actividad | Herramienta | Output |
|-----------|------------|--------|
| Smoke test | `session_runner.py smoke [perfil]` | Verificación rápida post-output |
| Functional test | `session_runner.py functional [perfil]` | Análisis diario de scores |
| Audit test | `session_runner.py audit [perfil]` | Evaluación semanal completa |
| Verification chain | `verification_chain.py [perfil]` | Ciclo Aletheia→Kosmos→Metis→Aletheia |
| Quality dashboard | Actualización de `.vault/quality/dashboard.md` | Dashboard actualizado |
| Weekly report | PaperJSX | Reporte PPTX con scores y tendencias |

### Perfiles de evaluación
| Perfil | Uso | Score compuesto bueno |
|--------|-----|----------------------|
| `exploracion` | Prototipos, brainstorming | ≥ 60 |
| `desarrollo` | Trabajo estándar, features | ≥ 70 |
| `produccion` | ADRs, releases, decisiones críticas | ≥ 80 |
| `auditoria` | Revisiones trimestrales, compliance | ≥ 85 |
| `qa` | Validación pre-release, compliance | ≥ 80 |

## Nota sobre Temperatura

La temperatura del modelo deepseek-v4-flash está fijada en **0.4** globalmente en `opencode.json`. No hay modos de temperatura dinámicos. El ajuste de comportamiento (precisión, creatividad, crítica) se logra mediante instrucciones semánticas en el prompt, no cambiando la temperatura.
