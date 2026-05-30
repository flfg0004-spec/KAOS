# Investigación: Configuración OpenCode y Optimización de Permisos

**Investigador**: Aletheia
**Fecha**: 2026-05-20
**Dominio**: OpenCode Configuration, Permissions
**Confianza general**: Alta

## Resumen Ejecutivo

Se auditaron todas las capacidades de configuración de OpenCode (agents, permissions, tools, skills, MCP, compaction, LSP, commands) contra la configuración actual de KAOS. Se identificaron 8 oportunidades de mejora: (1) externalizar prompts a archivos, (2) agregar agent colors, (3) limitar steps por agente, (4) ajustar permisos de bash, (5) agregar `external_directory`, (6) explorar LSP tool, (7) crear custom commands, (8) optimizar compaction.

---

## 1. Auditoría de Configuración Actual

### Agents
| Aspecto | Estado Actual | Recomendación |
|---------|--------------|---------------|
| Prompts | Embebidos en archivos .md | ✅ Correcto (frontmatter + body) |
| Colors | No configurados | ⚠️ Agregar: Aletheia=#4A90D9, Kosmos=#7B68EE, Metis=#E8A87C |
| Steps | No configurados | ⚠️ Aletheia=15 (investigación profunda), Kosmos=10, Metis=8 |
| Temperature | No configurada | ⚠️ Aletheia=0.3, Kosmos=0.1, Metis=0.4 |
| Mode | subagent (correcto) | ✅ |
| Hidden | No aplica | ✅ |

### Permissions
| Agente | Hallazgo | Recomendación |
|--------|---------|---------------|
| Aletheia | bash: solo curl/wget/_scripts | ✅ Adecuado. Considerar agregar `py *` para scripts Python |
| Kosmos | bash: git, npx, uvx, _scripts + wildcard ask | ⚠️ Demasiado permisivo. Restringir `*: ask` incluye npx/uvx |
| Metis | bash: solo _scripts | ✅ Adecuado. Considerar `py *` para report generator |

### MCP
| Hallazgo | Impacto | Acción |
|----------|---------|--------|
| 13 MCPs todos enabled globalmente | Alto consumo de tokens | Restringir por agente |
| Sin timeout configurado | Default 5s puede ser bajo | Agregar timeout: 10000 para MCPs lentos |

### Tools
| Tool | Estado | Recomendación |
|------|--------|---------------|
| websearch | allow en Aletheia/Metis | ✅ |
| webfetch | allow en todos | ✅ |
| question | allow solo en Metis | ✅ |
| task | allow en todos | ✅ |
| skill | allow en todos | ✅ |
| todowrite | no configurado | ⚠️ Habilitar para Metis |

## 2. Oportunidades de Mejora

### 2.1 Externalización de Prompts
OpenCode soporta `"prompt": "{file:./prompts/build.txt}"`. Podemos externalizar los prompts de los 3 agentes a archivos .txt para mejor mantenibilidad y reutilización.

### 2.2 Agent Colors
Diferenciación visual en la UI:
- Aletheia (investigación): azul `#4A90D9`
- Kosmos (arquitectura): púrpura `#7B68EE`  
- Metis (estrategia): coral `#E8A87C`

### 2.3 Steps Limit
Control de iteraciones para evitar loops:
- Aletheia: 15 steps (investigación profunda necesita más iteraciones)
- Kosmos: 10 steps (análisis acotado)
- Metis: 8 steps (síntesis rápida)

### 2.4 Temperature
- Aletheia: 0.3 (balance creatividad-precisión para investigación)
- Kosmos: 0.1 (máxima precisión para arquitectura)
- Metis: 0.4 (creatividad estratégica controlada)

### 2.5 External Directory
Si queremos que los agentes accedan a otros proyectos o archivos fuera de KAOS:
```json
"external_directory": {
  "~/projects/**": "allow",
  "~/.config/opencode/**": "allow"
}
```

### 2.6 LSP Tool (Experimental)
`OPENCODE_EXPERIMENTAL_LSP_TOOL=true` habilita navegación de código (goToDefinition, findReferences). Kosmos podría usarlo para análisis arquitectónico.

### 2.7 Custom Commands
OpenCode soporta `/commands` custom. Propuesta:
- `/quality` → ejecuta smoke check
- `/investigate` → invoca Aletheia con tema
- `/architect` → invoca Kosmos con contexto
- `/strategy` → invoca Metis con contexto

### 2.8 Compaction Optimization
Para sesiones largas de Aletheia:
```json
"compaction": {
  "auto": true,
  "tail_turns": 5,
  "preserve_recent_tokens": 8000,
  "reserved": 4000
}
```

## 3. Config Propuesta (Fragmentos)

### Sección agent con colores, steps, temperature
```json
"agent": {
  "aletheia": {
    "color": "#4A90D9",
    "steps": 15,
    "temperature": 0.3
  },
  "kosmos": {
    "color": "#7B68EE",
    "steps": 10,
    "temperature": 0.1
  },
  "metis": {
    "color": "#E8A87C",
    "steps": 8,
    "temperature": 0.4
  }
}
```

### Sección compaction optimizada
```json
"compaction": {
  "auto": true,
  "tail_turns": 5,
  "preserve_recent_tokens": 8000,
  "reserved": 4000
}
```

## Fuentes
- OpenCode Agents docs: https://opencode.ai/docs/agents
- OpenCode Permissions docs: https://opencode.ai/docs/permissions
- OpenCode Config schema: https://opencode.ai/config.json
- OpenCode Tools docs: https://opencode.ai/docs/tools
- OpenCode LSP docs: https://opencode.ai/docs/lsp
- OpenCode Commands docs: https://opencode.ai/docs/commands

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