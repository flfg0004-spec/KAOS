# ADR-002b: Sistema de Scores y Pesos Dinámicos de KAOS
> **Nota**: Comparte número ADR-002 con `adr-002-aislamiento-memoria.md`. Identificado como ADR-002b para evitar ambigüedad.

## Contexto

El sistema de memoria de KAOS (ADR-001) permite persistir conocimiento entre sesiones, pero no existe un mecanismo para **evaluar la calidad** de los outputs de cada agente ni para **verificar** que el conocimiento almacenado es preciso, coherente y accionable.

Se requiere un sistema que:
1. Mida la calidad de cada output del agente en **5 dimensiones** (veracidad, coherencia, completitud, reproducibilidad, utilidad).
2. Calcule un **score compuesto** con pesos ajustables por contexto.
3. Almacene scores como **serie temporal** para trackear evolución.
4. Permita **perfiles de contexto** con estrictitud ajustable (exploración/desarrollo/producción/auditoría).
5. Provea un **dashboard** de calidad auto-generado.

## Opciones Consideradas

### Opción 1: LangSmith
Framework completo de evaluación con dashboard, comparación de ejecuciones, evaluadores personalizados.

**Pros:** Maduro, dashboard visual, integración con múltiples LLMs.
**Cons:** Dependencia externa, costo, no es local-first.

### Opción 2: DeepEval
Framework open-source con 50+ métricas, pytest nativo, umbrales configurables.

**Pros:** 0 dependencias externas, 50+ métricas incluyendo HallucinationMetric, pytest nativo, umbrales configurables, integrable con cualquier LLM local.
**Cons:** Sin dashboard visual nativo (lo compensamos con vault markdown).

### Opción 3: Custom scoring engine
Implementación propia desde cero.

**Pros:** Control total, cero dependencias.
**Cons:** Reinventar la rueda, sin benchmarks validados, sin anti-alucinación probada.

## Decisión

**DeepEval + Custom Engine**, donde DeepEval provee las métricas validadas (HallucinationMetric, etc.) y el engine custom (`score_engine.py`) orquesta la fórmula compuesta, perfiles dinámicos y almacenamiento en vault.

## Justificación

1. **DeepEval** provee 50+ métricas validadas académicamente sin requerir APIs externas.
2. El **custom engine** en Python permite la fórmula compuesta con pesos dinámicos que DeepEval no soporta nativamente.
3. **Local-first**: todo corre sin conexión a internet, usando modelos locales.
4. **Vault como DB**: los scores se almacenan como archivos JSON en `.vault/quality/`, consistentes con la arquitectura ADD-only.
5. **Perfiles YAML**: separación de configuración (pesos, umbrales) del código.

## Consecuencias

### Positivas
- Scores replicables y auditables (cada score tiene timestamp + perfil + firmas).
- Sin dependencias externas ni costos recurrentes.
- Perfiles intercambiables sin modificar código.
- Serie temporal almacenada en vault para análisis de tendencias.
- Compatible con DeepEval HallucinationMetric para anti-alucinación L1.

### Negativas
- DeepEval requiere Python 3.9+ (ya instalado).
- El dashboard markdown no tiene visualizaciones interactivas (solo tablas).
- Engine no probado a escala >1000 verificaciones.

### Neutrales
- Perfiles definidos en YAML — pueden evolucionar sin cambiar el engine.
- DeepEval se actualiza independientemente; el engine solo usa su API de métricas.

## Estado

Aceptada

## Detalle Técnico

### Fórmula del Score Compuesto

```
ScoreCompuesto = Σ(w_i · score_i) / Σ(w_i)

Dimensiones:
- V: Veracidad (precisión factual vs fuentes)
- C: Coherencia (consistencia lógica interna)
- CP: Completitud (cobertura de factores relevantes)
- R: Reproducibilidad (¿otro agente obtiene el mismo resultado?)
- U: Utilidad (valor accionable para downstream)

Perfiles (pesos):
| Perfil | wV  | wC  | wCP | wR  | wU  |
|--------|-----|-----|-----|-----|-----|
| Exploración  | 0.15 | 0.15 | 0.20 | 0.15 | 0.35 |
| Desarrollo   | 0.20 | 0.20 | 0.20 | 0.20 | 0.20 |
| Producción   | 0.30 | 0.25 | 0.20 | 0.15 | 0.10 |
| Auditoría    | 0.35 | 0.25 | 0.25 | 0.10 | 0.05 |
```

### Pipeline Anti-alucinación (3 niveles)

| Nivel | Herramienta | Latencia | Gatillo |
|-------|-------------|----------|---------|
| L1 | DeepEval HallucinationMetric | <1s | Cada sesión de test |
| L2 | Cross-agent verification | ~10s | Si L1 falla |
| L3 | Verificación por agente par ciego | ~30s | Si L2 confirma fallo |

### Almacenamiento

```
.vault/quality/
├── sessions/          ← Resultados de cada sesión de test
├── timeseries/        ← Serie temporal de scores compuestos
├── verifications/     ← Resultados de verificación cruzada
└── dashboard.md       ← Dashboard auto-generado
```

## Referencias
- DeepEval: https://docs.confident-ai.com
- ADR-001: Sistema de Memoria de KAOS
- Perfiles: `schema/eval-profile.yaml`
- Engine: `.tools/score_engine.py`
