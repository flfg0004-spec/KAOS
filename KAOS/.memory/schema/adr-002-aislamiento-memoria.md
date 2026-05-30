# ADR-002: Aislamiento del Vault de Memoria para OpenCode

## Contexto

KAOS tiene dos ecosistemas de agentes coexistiendo en el mismo repositorio:
- **OpenCode** (`.opencode/`): 3 subagentes (Aletheia, Kosmos, Metis) con skills, permisos y MCP servers configurados.
- **Antigravity 2.0** (`.agents/`): 7 agentes (Dédalo, Argos, Apolo, Hermes, Kenon, Metis, Talos) con su propia configuración aislada.

Ambos ecosistemas comparten el directorio raíz del proyecto, pero están aislados por diseño (Zero Cross-Talk, según AGENTS.md). El vault `.memory/` fue creado con estructura raw/wiki/schema y es accesible vía MCP server-filesystem.

Actualmente no está definido qué ecosistema posee el vault, quién escribe, quién lee, y si hay interacción entre ecosistemas a través de la memoria compartida.

## Opciones Consideradas

### Opción 1: Vault compartido con zonas por ecosistema

OpenCode escribe a `wiki/` y `raw/`. Antigravity escribe a `agents/` dentro del vault. Ambos leen todo.

**Pros:**
- Conocimiento unificado
- Antigravity agents pueden aprovechar investigaciones de Aletheia
- Sin duplicación de información

**Cons:**
- Complejidad de coordinación entre ecosistemas incompatibles
- Riesgo de conflictos de escritura
- Antigravity no tiene MCP vault server configurado
- Aumenta la superficie de permisos y gobernanza

### Opción 2: Vaults separados por ecosistema

Cada ecosistema tiene su propio vault de memoria. `.memory/` para OpenCode. Antigravity crea su propio sistema separado.

**Pros:**
- Aislamiento total, sin riesgo de conflictos
- Cada ecosistema evoluciona su memoria independientemente
- Sin dependencias entre ecosistemas
- Simplicidad operativa

**Cons:**
- Duplicación de esfuerzo si ambos investigan el mismo tema
- El humano debe mantener dos sistemas de memoria
- Oportunidad perdida de sinergia

### Opción 3: Vault de OpenCode como fuente primaria, Antigravity como lector (Seleccionada)

OpenCode posee y escribe al vault. Antigravity agents pueden leer (read-only) el vault vía filesystem, pero no escribir.

**Pros:**
- Conocimiento unificado con un solo escritor
- Antigravity puede beneficiarse de investigaciones de OpenCode
- Sin conflictos de escritura
- OpenCode mantiene la gobernanza del vault

**Cons:**
- Antigravity depende de OpenCode para generar conocimiento estructurado
- El humano podría esperar que Antigravity también contribuya
- Antigravity no tiene tools configuradas para leer el vault eficientemente

## Decisión

**Opción 2: Vaults separados por ecosistema**. `.memory/` es propiedad exclusiva de los agentes OpenCode (Aletheia, Kosmos, Metis). Antigravity 2.0 agents no leen ni escriben este vault. Si Antigravity necesita persistencia de memoria, implementará su propio sistema separado.

## Justificación

1. **Alineación con el principio existente**: AGENTS.md ya declara Zero Cross-Talk entre ecosistemas. Esta decisión refuerza ese principio en lugar de crear excepciones.

2. **Simplicidad operativa**: Un solo ecosistema escribiendo al vault = un solo conjunto de reglas, permisos y scripts de mantenimiento. Sin necesidad de coordinar dos sistemas de agentes con arquitecturas diferentes.

3. **Riesgo cero de corrupción**: Sin escritores múltiples, no hay riesgo de que un agente de Antigravity sobreescriba o corrompa datos de OpenCode, o viceversa.

4. **Evolución independiente**: OpenCode puede optimizar su sistema de memoria sin considerar compatibilidad con Antigravity. Antigravity puede diseñar su sistema de memoria con su propia arquitectura.

5. **Decisión reversible**: Si en el futuro se decide integrar, los vaults pueden fusionarse vía git. Es más fácil unir que separar.

## Consecuencias

### Positivas
- Aislamiento completo de memoria entre ecosistemas
- Gobernanza simple (OpenCode dueño único del vault)
- Sin conflictos de escritura
- OpenCode puede implementar su estrategia de memoria sin restricciones externas

### Negativas
- Duplicación potencial de investigación si Antigravity necesita memoria
- El humano debe gestionar dos sistemas si ambos ecosistemas están activos
- Oportunidad de sinergia postergada

### Neutrales
- Si Antigravity nunca implementa memoria, no hay duplicación
- La separación es transparente para el humano (cada ecosistema en su directorio)
- Git permite fusión futura si se decide

## Estado

Aceptada

## Referencias

- AGENTS.md: Zero Cross-Talk policy
- ADR-001: Arquitectura de Memoria de KAOS
- `.agents/config.json`: strict isolation mode
