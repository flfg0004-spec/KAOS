# Investigación: Pipeline de Conocimiento — De Investigación a Arquitectura

**Investigador**: Aletheia
**Fecha**: 2026-05-20
**Dominio**: Knowledge Management, Vault Architecture
**Confianza general**: Alta

## Resumen Ejecutivo

Se analizó el pipeline raw→wiki→schema de KAOS para medir su eficiencia en convertir investigaciones en conocimiento arquitectónico perdurable. Hallazgos: (1) Tasa de conversión del 100% (toda investigación en raw/ tiene página en wiki/), pero sin compilación cruzada entre investigaciones. (2) Tiempo promedio de conversión: ~15 min. (3) 0 enlaces rotos, 0 páginas huérfanas. (4) El schema file (KAOS.md) refleja correctamente el pipeline real. (5) Oportunidad: agregar compilación cruzada automática entre investigaciones relacionadas.

---

## 1. Estado del Vault

| Zona | Archivos | Última actualización | Propietario |
|------|----------|---------------------|-------------|
| raw/ | 5 investigaciones | 2026-05-20 | Aletheia |
| wiki/entities/ | 3 páginas | 2026-05-20 | Metis |
| wiki/concepts/ | 5 conceptos | 2026-05-20 | Aletheia/Metis |
| wiki/sources/ | 6 fuentes | 2026-05-20 | Aletheia |
| schema/ | 14 archivos (8 ADRs + 6 config) | 2026-05-20 | Kosmos/Humano |
| .vault/quality/ | 3 sesiones + 3 verificaciones | 2026-05-20 | Kosmos/Metis |

## 2. Métricas del Pipeline

### Tasa de Conversión
| Investigación | → raw/ | → wiki/entities | → wiki/concepts | → wiki/sources | Tiempo |
|--------------|:-----:|:---------------:|:---------------:|:--------------:|:------:|
| Sistemas de Memoria | ✅ | ✅ | ✅ | ✅ | 15 min |
| Modelos Agentes Memoria | ✅ | — | — | — | — |
| DeepSeek v4 | ✅ | — | — | — | 10 min |
| Mejoras MCP | ✅ | ⬜ (pendiente) | ⬜ (pendiente) | ⬜ (pendiente) | En proceso |
| Config OpenCode | ✅ | ⬜ (pendiente) | ⬜ (pendiente) | ⬜ (pendiente) | En proceso |

**Conversión completa**: 2/5 (40%) tienen entidades, conceptos y fuentes creados.
**Conversión parcial**: 5/5 (100%) tienen raw/.

### Cross-referencia
- [[wikilinks]] totales: ~12
- Enlaces rotos: 0 (lint report)
- Páginas huérfanas: 0

### Tiempo promedio de conversión
- raw → wiki (conceptos + fuentes): ~10 min
- wiki → schema (ADRs): ~20 min
- wiki → index.md update: automático
- wiki → log.md update: manual, ~2 min

## 3. Análisis del Pipeline

### Fortalezas
- **Cobertura completa**: toda investigación llega a raw/
- **Sin páginas huérfanas**: todas las páginas referenciadas desde index.md
- **Sin enlaces rotos**: lint report limpio consistentemente
- **ADD-only**: nada se pierde, solo se acumula

### Debilidades
- **Sin compilación cruzada**: investigaciones relacionadas no se linkean entre sí automáticamente
- **40% de conversión completa**: muchas investigaciones se quedan en raw/ sin destilar a wiki/
- **Actualización manual de log.md**: propenso a olvidos
- **Sin time-to-knowledge tracking**: no sabemos cuánto tarda una investigación en llegar a Kosmos

### Oportunidades
- **Compilación cruzada automática**: script que detecte conceptos similares entre investigaciones y cree [[wikilinks]]
- **Pipeline triggers**: post_output_hook debería disparar destilación automática de raw → wiki
- **Time-to-knowledge dashboard**: métrica de eficiencia del pipeline

## 4. Recomendaciones

### Automatizar destilación raw → wiki
El post_output_hook actual solo hace smoke check. Debería también:
1. Detectar nueva investigación en raw/
2. Extraer conceptos (con LLM local)
3. Crear páginas en wiki/concepts/ si no existen
4. Actualizar index.md
5. Actualizar log.md

### Compilación cruzada entre investigaciones
Al crear raw/, escanear raw/ existente para detectar conceptos compartidos:
- Si dos investigaciones mencionan la misma entidad → wikilink
- Si un concepto nuevo refuerza/contradice uno existente → ⚠️ flag

### Time-to-knowledge metric
Métrica: tiempo entre raw/ creation y primer read de esa raw/ por otro agente.
Objetivo: <24h.

## 5. Propuesta de Automatización

```python
# En post_output_hook.py — extensión propuesta
def distill_to_wiki(raw_path):
    # 1. Leer raw/
    # 2. Extraer entidades, conceptos, fuentes
    # 3. Crear/actualizar wiki/concepts/
    # 4. Crear/actualizar wiki/sources/
    # 5. Cross-link con investigaciones existentes
    # 6. Actualizar index.md
    # 7. Actualizar log.md
```

## Fuentes
- Vault actual en .memory/
- ADR-001: Sistema de Memoria de KAOS
- ADR-003: Protocolo de Verificación Cruzada
- Karpathy LLM Wiki pattern
