---
type: adr
title: 'ADR-003: Zonas de Autonomía del Vault'
aliases:
- adr-003-zonas-autonomia
tags:
- adr
created: '2026-05-19'
modified: '2026-05-19'
confidence: media
status: draft
---

# ADR-003: Zonas de Autonomía del Vault

## Contexto

El vault `.memory/` es el repositorio de conocimiento compartido entre los 3 agentes OpenCode (Aletheia, Kosmos, Metis). Originalmente, el diseño asumía supervisión humana constante para escribir, revisar y mantener el contenido.

Sin embargo, la experiencia muestra que:
1. El humano no siempre está disponible para responder "edit ask" en tiempo real.
2. La calidad del vault se degrada si el mantenimiento depende exclusivamente del humano.
3. El sistema necesita operar autónomamente para ser útil.

Se requiere una política formal de autonomía que defina:
- Qué puede escribir cada agente sin revisión.
- Qué requiere aprobación humana.
- Qué sucede cuando el humano no responde.
- Cómo se recupera el sistema de decisiones autónomas incorrectas.

## Opciones Consideradas

### Opción 1: Todo requiere aprobación humana

Cada escritura al vault pasa por "edit ask". Sin respuesta humana, el agente espera indefinidamente.

**Pros:** Control total humano sobre el vault.
**Cons:** El sistema se bloquea si el humano no está. Derrota el propósito de tener agentes autónomos.

### Opción 2: Autonomía total de los agentes

Los agentes escriben libremente al vault sin supervisión. La revisión es a posteriori.

**Pros:** Máxima fluidez operativa. Sin bloqueos.
**Cons:** Riesgo de corrupción del vault. Contradicciones no detectadas. Sin control de calidad.

### Opción 3: Zonas de autonomía según tipo de contenido (Seleccionada)

El vault se divide en zonas, cada una con un nivel de autonomía diferente según el riesgo de la operación.

**Pros:** Balance entre velocidad y control. Las zonas de bajo riesgo son 100% autónomas. Las de alto riesgo requieren humano con timeout. Las revisiones diferidas permiten operar sin bloqueo.

**Cons:** Complejidad de definir y mantener las zonas. Riesgo de clasificación incorrecta.

## Decisión

**Opción 3: Zonas de Autonomía**.

## Justificación

1. **Balance óptimo**: Las zonas de bajo riesgo (concepts, sources, log) son 100% autónomas → sin fricción. Las de alto riesgo (ADRs, policy) requieren humano → control de calidad. Las intermedias (entities) tienen revisión diferida → operación continua + supervisión.

2. **Timeout de 30 minutos**: Basado en el principio de que es mejor una decisión imperfecta pero reversible que un sistema bloqueado. Git permite revertir cualquier cambio.

3. **ADD-only**: Como política fundamental, nada se sobreescribe. Incluso los cambios autónomos incorrectos preservan la versión anterior en git. El riesgo real es bajo.

4. **Deferred review**: Las zonas "auto + flag" escriben inmediatamente pero dejan registro en `_pending/`. El humano puede revisar cuando tenga tiempo, sin presión.

## Consecuencias

### Positivas
- El sistema opera autónomamente 24/7 sin depender de disponibilidad humana.
- Las decisiones importantes (ADRs, políticas) mantienen supervisión humana.
- Las decisiones autónomas incorrectas son reversibles vía git.
- La cola de revisión diferida (`_pending/`) da visibilidad al humano sin bloquear el sistema.

### Negativas
- Riesgo de que cambios autónomos de baja calidad se acumulen antes de ser revisados.
- El timeout de 30 min puede ser demasiado corto para decisiones complejas.
- La clasificación de zonas debe mantenerse actualizada.

### Neutrales
- Las zonas pueden re-clasificarse según madurez del sistema (nuevos ADRs pueden ajustar la política).
- El humano puede cambiar temporalmente una zona de "auto" a "human approves" si detecta problemas de calidad.

## Estado

Aceptada

## Referencias

- ADR-002: Aislamiento del Vault de Memoria para OpenCode
- `schema/vault-policy.md`: Definición detallada de zonas y reglas
- `_pending/README.md`: Protocolo de revisión diferida

