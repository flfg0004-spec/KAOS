# ADR-003b: Protocolo de Verificación Cruzada entre Agentes
> **Nota**: Comparte número ADR-003 con `adr-003-zonas-autonomia.md`. Identificado como ADR-003b para evitar ambigüedad.

## Contexto

El sistema de scores (ADR-002) define cómo medir la calidad de outputs individuales, pero no establece cómo los agentes **verifican los outputs de otros agentes**. Sin verificación cruzada, cada agente es juez y parte de su propio trabajo — no hay garantía de objetividad.

Se requiere un protocolo donde:
1. Cada output de un agente sea verificado por otro agente.
2. La verificación produzca un score almacenable en el vault.
3. La cadena de verificación sea triangular (A→K→M→A), no jerárquica.
4. Cada verificación incluya: score, discrepancias encontradas, evidencia.

## Opciones Consideradas

### Opción 1: Auto-verificación (cada agente verifica su propio output)
Simple pero con sesgo de confirmación. No hay objetividad.

### Opción 2: Verificación por humano
Precisa pero no escala. Los agentes no pueden operar autónomamente.

### Opción 3: Verificación cruzada triangular (Seleccionada)
Cada agente verifica al siguiente en el ciclo, cerrando el triángulo. Distribuye la carga, elimina sesgo, y aprovecha las fortalezas de cada agente.

## Decisión

**Verificación Cruzada Triangular** con el siguiente protocolo:

## Justificación

1. **Objetividad**: Cada output es evaluado por un agente con perspectiva y skill diferente.
2. **Sin sesgo**: Ningún agente se verifica a sí mismo.
3. **Fortalezas complementarias**: Aletheia verifica factual, Kosmos verifica técnico, Metis verifica estratégico.
4. **Distribución de carga**: Cada agente verifica una vez por ciclo, no hay bottleneck.
5. **Almacenable**: Cada verificación produce un JSON con score, discrepancias y evidencia.

## Consecuencias

### Positivas
- Calidad verificada por pares sin necesidad de supervisión humana.
- Cada verificación genera datos que mejoran el score del sistema.
- Las discrepancias documentadas sirven como feedback para mejorar outputs futuros.

### Negativas
- Overhead de ~10s por verificación (L2).
- Requiere que todos los agentes estén disponibles en el ciclo de verificación.
- El agente verificador debe tener acceso al mismo contexto que el agente original.

### Neutrales
- El protocolo es asíncrono (post-output), no bloquea al agente original.
- Las verificaciones se almacenan en el vault y son auditables.

## Estado

Aceptada

## Detalle Técnico

### Cadena de Verificación

```
Aletheia ──(output)──→ Kosmos ────────────────────→ Score V, C
                          │
                          │ (output)
                          ▼
Kosmos   ──(output)──→ Metis  ────────────────────→ Score CP, U
                          │
                          │ (output)
                          ▼
Metis    ──(output)──→ Aletheia ──────────────────→ Score V, R
```

### Formato de Verificación

Cada verificación genera un archivo JSON en `.vault/quality/verifications/`:

```json
{
  "verification_id": "v-20260519-001",
  "claim_id": "aletheia-2026-05-19-memoria-01",
  "agent_origin": "aletheia",
  "agent_verifier": "kosmos",
  "timestamp": "2026-05-19T21:00:00Z",
  "profile": "desarrollo",
  "scores": {
    "veracidad": 85,
    "coherencia": 78
  },
  "evaluations": {
    "veracidad": "pass",
    "coherencia": "pass"
  },
  "discrepancies": [
    "Afirmación X citada como fuente primaria pero es fuente secundaria"
  ],
  "evidence_hash": "sha256:abc123...",
  "verifier_notes": "El output es sólido pero recomiendo verificar la fuente de la afirmación Y"
}
```

### Protocolo L2 (Anti-alucinación por verificación)

1. Agente B recibe el output del Agente A.
2. Agente B reproduce el claim independientemente (sin ver el output de A).
3. Agente B compara su resultado con el de A.
4. Score de Reproducibilidad = 1 - (divergencia / total_claims).
5. Si divergencia > 0.3, se marca como discrepancia y se escala a L3.

## Referencias
- ADR-001: Sistema de Memoria de KAOS
- ADR-002: Sistema de Scores y Pesos Dinámicos
- DeepEval HallucinationMetric para L1
- MARCH pattern (multi-agent verification) para L3
