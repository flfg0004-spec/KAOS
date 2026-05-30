# 🏛️ KAOS Plan Estratégico-Táctico Paralelo 2026

> **Generado por**: Metis (Μῆτις) — Diosa de la Sabiduría y la Estrategia  
> **Fecha**: 2026-05-25  
> **Basado en**: Investigación de Aletheia (10 temas estratégicos) + Análisis de alternativas cloud gratuitas  
> **Score de Calidad Actual**: 88.5/100  
> **Costo Mensual Actual**: ~$4.36/mes (DeepSeek V4 Flash + V4 Pro + Kimi K2.6)  

---

## Parte 1: Investigación Oyama — Hallazgo Crítico y Redirección Estratégica

### ⚠️ Oyama (oyama.ai) NO EXISTE COMO PRODUCTO

Tras una investigación forense exhaustiva (Aletheia, 10+ búsquedas, scraping directo, LinkedIn, CB Insights, Tracxn, redes sociales):

| Hallazgo | Detalle |
|----------|---------|
| **Dominio oyama.ai** | Landing page estática de GoDaddy Website Builder |
| **Contenido real** | Un tagline "Empowering Intelligence, Transforming Futures" + formulario de contacto |
| **API, modelos, precios** | ❌ No existe ningún producto real |
| **Infraestructura** | ❌ Cero evidencia de servidores, endpoints, o plataforma LLM |
| **Empresa real "Oyama"** | Startup finlandés de salud mental → soft skills training → **getoyama.com** |
| **Funding real** | ~$141K USD (Pre-Seed, Feb 2020) — una sola ronda |
| **Empleados** | 4 |
| **Estado** | Bootstrapped, no pudo levantar más capital, pivoteó |

**Veredicto**: Cero inversión en Oyama. No hay nada que integrar.

### ✅ Alternativas Reales: Modelos Cloud Gratis (Mayo 2026)

Reemplazo estratégico para la necesidad del usuario — "modelos cloud gratis" — con plataformas REALES:

| Proveedor | Free Tier | Sin Tarjeta | Modelos Disponibles | OpenAI Compat |
|-----------|:---------:|:-----------:|:-------------------:|:-------------:|
| **Google Gemini** | ✅ Ilimitado (rate-limited) | ✅ Sí | Gemini 2.5 Flash, 2.5 Pro, 3.5 Flash, 3 Flash | ⚠️ SDK propio |
| **OpenRouter** | 25+ modelos gratis, 50 req/día | ✅ Sí | DeepSeek R1, Qwen3 Coder, Llama 3.3 70B, Llama 4 Scout | ✅ Completa |
| **DeepSeek** | 5M tokens gratis (one-time) | ✅ Sí (teléfono) | deepseek-v4-flash, deepseek-v4-pro | ✅ Nativa |
| **Groq** | 30 RPM, 6K TPM | ✅ Sí | Llama 3.1 8B (840 TPS), Llama 3.3 70B, Qwen3 32B | ✅ Completa |
| **Cerebras** | 1M tokens/día, 30 RPM | ✅ Sí | Llama 3.3 70B, Qwen3 235B | ✅ Completa |
| **Mistral AI** | 1B tokens/mes, 1 req/s | ✅ Sí | Mistral Large 3, Small 3.1 | ✅ Completa |

### 🏆 Recomendación: Estrategia "Free Tier Triada" para KAOS

En lugar de "Oyama Integration" (proyecto muerto), el nuevo proyecto es:

**Proyecto A': Multi-Provider Free Model Strategy**

| Capa | Proveedor | Modelo | Costo | Propósito |
|------|-----------|--------|:-----:|-----------|
| **Capa 1: Desarrollo** | Gemini Free | Gemini 2.5 Flash | **$0** | Desarrollo, prototipado, flujo principal |
| **Capa 2: Diversidad** | OpenRouter Free | DeepSeek R1 (free) + Qwen3 Coder | **$0** | Razonamiento profundo + código |
| **Capa 3: Producción** | DeepSeek (paid) | DeepSeek V4 Flash | ~$2.45/mes | Producción, alta concurrencia |
| **Capa 4: Velocidad** | Groq Free | Llama 3.1 8B | **$0** | Tareas simples ultra-rápidas |

**Impacto**: Reduce el costo de API de **$4.36/mes → ~$2.45/mes** al mover desarrollo y tareas no críticas a tiers gratuitos. Mantiene DeepSeek solo para producción real.

---

## Parte 2: Mapa Estratégico General Integrado

### Estado Actual de KAOS (Línea Base)

```
┌─────────────────────────────────────────────────────────────┐
│                    KAOS Ecosystem Map                        │
│  Score: 88.5/100 │ Costo: ~$4.36/mes │ Throughput: ~1/hr   │
├─────────────────────────────────────────────────────────────┤
│                                                              │
│  [User] → OpenCode CLI → LangGraph Orchestrator              │
│                              ├── Aletheia (Research)         │
│                              ├── Kosmos (Architecture)       │
│                              ├── Kratos (Code)              │
│                              ├── Metis (Strategy)            │
│                              └── Mnemosyne (Memory)          │
│                                                              │
│  Memory L0-L3: txtai (3,682 chunks) → Sleep Cycle v2        │
│  Multi-Model: ADR-015 (85% Flash, 10% Pro, 5% Kimi)         │
│  Infra: Docker Compose + SQLite + DeepEval + Langfuse       │
│                                                              │
└─────────────────────────────────────────────────────────────┘
```

### Los 6 Proyectos Priorizados (Refinados)

| # | Proyecto | Track | Esfuerzo | Impacto | Dependencias |
|---|----------|-------|:--------:|:-------:|-------------|
| **A'** | **Multi-Provider Free Strategy** (reemplaza Oyama) | Provider | 🟢 Bajo | 🟢 Medio | Ninguna |
| **B** | **Open WebUI + MCPO** (interfaz visual) | UI | 🟡 Medio | 🟢 Alto | MCP Gateway |
| **C** | **LightRAG** (L2 semántico) | Memoria | 🟡 Medio | 🟢 Alto | txtai |
| **D** | **Sleep Cycle Nocturno** (NREM/REM real) | Memoria | 🟢 Bajo | 🟡 Medio | sleep_cycle_v2.py |
| **E** | **Ollama Pilot** (modelo local) | Provider | 🟡 Medio | 🟡 Medio | GPU? |
| **F** | **A2A Re-eval** (interoperabilidad) | Protocolo | 🔴 Alto | 🟡 Medio | Monitoreo |

### Matriz Impacto-Esfuerzo

```
                        ALTO IMPACTO
                            │
                ┌───────────┼───────────┐
                │           │           │
                │  B. OWUI  │  C.       │
                │  A'. Free │  LightRAG │
                │  Models   │           │
                │           │           │
    BAJO ───────┼───────────┼───────────┼──── ALTO
   ESFUERZO     │           │           │  ESFUERZO
                │  D. Sleep │  E.       │
                │  Cycle    │  Ollama   │
                │  Night    │  Pilot    │
                │           │  F. A2A   │
                └───────────┼───────────┘
                            │
                        BAJO IMPACTO
```

### Diagrama de Dependencias entre Proyectos

```
A' (Free Models) ── independiente ──→ ✅ arranque inmediato
                        │
B (Open WebUI) ────────┤
                        └── depende de MCP Gateway (ya existe)
                        └── depende de modelos funcionales (A')
                        │
C (LightRAG) ──────────┤
                        └── depende de txtai embeddings (ya existe)
                        │
D (Sleep Cycle Night) ──┤
                        └── depende de sleep_cycle_v2.py (ya existe)
                        │
E (Ollama Pilot) ──────┤
                        └── depende de GPU disponible (riesgo)
                        └── evaluación de calidad vs API
                        │
F (A2A Re-eval) ───────┤
                        └── depende de monitoreo de ecosistema
```

**Ruta crítica**: A' (Free Models) y D (Sleep Cycle Night) son independientes → se ejecutan en paralelo inmediato. B (OWUI) y C (LightRAG) son dependientes de infra existente → pueden arrancar en paralelo también.

---

## Parte 3: Tres Escenarios Tácticos

---

### Escenario A: "Máxima Velocidad" ⚡ (2-3 días)

**Enfoque**: Solo lo que da más valor inmediato. Sin GPU, sin modelos locales.

#### Arquitectura

```
Día 1                    Día 2                    Día 3
│                        │                        │
A' ── Config Gemini ────┤                        │
Free API Key (15min)     │                        │
│                        │                        │
D ── Habilitar sleep ────┤                        │
cycle nocturno (30min)   │                        │
│                        │                        │
B ── Validar OWUI ───────┼──── End-to-end ────────┤
    E2E Flow (2hrs)      │    Test (3hrs)         │
                         │                        │
                         │ Tests + Docs (4hrs)    │
```

#### Tracks Paralelizables

| Track | Contenido | Tiempo | ¿Paralelo? |
|-------|-----------|:------:|:----------:|
| A'.1 | Configurar Gemini Free API en agente de desarrollo | 15 min | ✅ Sí |
| A'.2 | Configurar OpenRouter Free para tareas de diversidad | 15 min | ✅ Sí |
| A'.3 | Configurar Groq Free para tareas rápidas | 15 min | ✅ Sí |
| B.1 | Validar OWUI + MCPO bridge E2E | 2 hrs | ✅ Sí |
| B.2 | Probar acceso a agentes vía OWUI | 2 hrs | ✅ Sí (tras B.1) |
| D.1 | Activar sleep cycle nocturno automático | 30 min | ✅ Sí |

#### Ruta Crítica

Ninguna — todos los tracks son independientes.

#### Riesgos por Track

| Track | Riesgo | Probabilidad | Impacto | Mitigación |
|-------|--------|:-----------:|:-------:|------------|
| A'.1 | Gemini bloquea IP de Windows | Media | Bajo | Usar API key estándar |
| A'.2 | OpenRouter rate limit (50 req/día) | Alta | Medio | Comprar $10 de crédito (lifetime → 1000 req/día) |
| B.1 | OWUI no conecta con MCP Gateway | Media | Alto | Debuggear config MCPO bridge |
| D.1 | sleep_cycle_v2 conflicto con pipeline activo | Baja | Medio | Programar en ventana de inactividad |

#### Criterios GO/NO-GO

- **GO**: Gemini Free responde + OWUI carga agentes + sleep cycle ejecuta dry-run sin error
- **NO-GO**: Gemini Free no disponible en la región → fallback a Groq Free; OWUI no conecta → diferir a Escenario B

#### Costo Estimado

| Recurso | Costo |
|---------|:-----:|
| Tiempo desarrollador | ~8-12 horas |
| API calls | $0 (tiers gratuitos) |
| Infra adicional | $0 |
| **Total** | **~$0 + tiempo** |

---

### Escenario B: "Completo Acelerado" 🚀 (1-2 semanas)

**Enfoque**: Todo en paralelo donde sea posible. 4 tracks simultáneos.

#### Arquitectura

```
Semana 1                        Semana 2
│                               │
A'. Free Models ────┬───────────┤ ✅ Completado
                    │           │
B. Open WebUI ──────┼──┬────────┤ ✅ E2E Validado
                    │  │        │
C. LightRAG ────────┤  ├────────┤ ✅ Integrado con txtai
                    │  │        │
D. Sleep Cycle ─────┤  └────────┤ ✅ Nocturno operativo
                    │           │
Tests ──────────────┴───────────┤ Tests + Benchmarks
```

#### Tracks Paralelizables

| Track | Contenido | Tiempo | ¿Paralelo? |
|-------|-----------|:------:|:----------:|
| **Track A'** | Multi-Provider Free Strategy | 2-3 días | ✅ Semana 1 |
| A'.1 | Gemini Free: configurar ChatGoogleGenerativeAI en LangChain | 2 hrs | ✅ |
| A'.2 | OpenRouter Free: configurar OpenAI-compatible endpoint | 1 hr | ✅ |
| A'.3 | Groq Free: configurar para tareas ultra-rápidas | 1 hr | ✅ |
| A'.4 | Router dinámico: qué tarea va a qué proveedor | 4 hrs | ❌ Depende de A'.1-3 |
| A'.5 | Failover automático entre proveedores | 3 hrs | ❌ Depende de A'.4 |
| **Track B** | Open WebUI + MCPO | 3-4 días | ✅ Semana 1 |
| B.1 | Validar conexión OWUI → MCPO → MCP Gateway | 2 hrs | ✅ |
| B.2 | Configurar autenticación OWUI | 2 hrs | ✅ |
| B.3 | Probar cada agente vía OWUI (Aletheia, Kosmos, etc.) | 4 hrs | ❌ Depende de B.1 |
| B.4 | Documentar boundary OWUI vs Obsidian | 2 hrs | ✅ |
| **Track C** | LightRAG Integration | 4-5 días | ✅ Semana 1-2 |
| C.1 | Instalar LightRAG + configurar embeddings | 2 hrs | ✅ |
| C.2 | Indexar wiki de KAOS (106 conceptos) | 2 hrs | ✅ |
| C.3 | Integrar con pipeline de Mnemosyne | 4 hrs | ❌ Depende de C.1-2 |
| C.4 | Evaluar mejora en recuperación vs txtai solo | 3 hrs | ❌ Depende de C.3 |
| **Track D** | Sleep Cycle Nocturno | 1-2 días | ✅ Semana 1 |
| D.1 | Migrar sleep_cycle_v2 a ejecución nocturna automática | 2 hrs | ✅ |
| D.2 | Configurar pipeline de NREM diario | 2 hrs | ✅ |
| D.3 | Configurar REM semanal | 1 hr | ✅ |
| D.4 | Dashboard de consolidación de memoria | 3 hrs | ❌ Depende de D.1-3 |

#### Ruta Crítica

- **Ninguna bloqueante**: todos los tracks son ortogonales
- **Cuello de botella**: Capacidad del usuario para probar cada integración (estimado: 2-3 hrs/día)

#### Riesgos por Track

| Track | Riesgo | Prob | Impacto | Mitigación |
|-------|--------|:----:|:-------:|------------|
| A' | Gemini cambia términos de free tier | Baja | Alto | Tener fallback a OpenRouter/Groq |
| B | MCPO bridge incompatible con versión de OWUI | Media | Alto | Usar docker image fija |
| C | LightRAG requiere >2GB RAM para indexación | Media | Medio | Usar modo incremental, no full |
| C | Embeddings de LightRAG no alineados con txtai | Baja | Medio | Mantener ambos, cada uno para su caso |
| D | Sleep cycle nocturno interfiere con pipeline | Baja | Medio | Programar a las 3 AM, verificar colisión |

#### Criterios GO/NO-GO

- **GO**: Todos los tracks pasan pruebas unitarias + al menos 2 tracks pasan integración E2E
- **NO-GO**: Si LightRAG no indexa correctamente → posponer a Escenario C
- **NO-GO**: Si OWUI no conecta con MCP Gateway real → usar solo en modo local

#### Costo Estimado

| Recurso | Costo |
|---------|:-----:|
| Tiempo desarrollador | ~40-60 horas |
| API calls | ~$2.45 (DeepSeek producción) |
| OpenRouter crédito | $10 (one-time, eleva límite a 1000 req/día) |
| Infra adicional | $0 |
| **Total** | **~$12.45 + tiempo** |

---

### Escenario C: "Megastack" 🏗️ (3-4 semanas)

**Enfoque**: Todo lo anterior + Ollama local + A2A re-eval + benchmarks completos.

#### Arquitectura

```
Semana 1           Semana 2           Semana 3           Semana 4
│                  │                  │                  │
A' ────────────────┼──────────────────┼──────────────────┤ ✅ Free Models
B ────────────────┤                   │                  │ ✅ OWUI
C ────────────────┼───────────────────┤                   │ ✅ LightRAG
D ────────────────┤                   │                  │ ✅ Sleep Cycle
│                  │                  │                  │
E. Ollama ─────────┼─────── Evaluación ──────── Decisión ─┤ ⏳ Pilot
│                  │        Quality Gap                  │
F. A2A ────────────┼─────── Diseño ──────────────────────┤ ⏳ Re-eval
│                  │        Agent Card Schema            │
│                  │                  │                  │
Benchmarks ────────┴──────────────────┴──────────────────┤ 📊 Reporte
```

#### Tracks Adicionales (sobre Escenario B)

| Track | Contenido | Tiempo | Dependencias |
|-------|-----------|:------:|:------------|
| **Track E** | Ollama Pilot (modelo local) | 5-7 días | GPU disponible |
| E.1 | Instalar Ollama + descargar Qwen2.5-7B | 1 hr | ✅ Independiente |
| E.2 | Configurar LangChain con Ollama endpoint local | 2 hrs | ✅ Independiente |
| E.3 | Benchmark calidad: Ollama vs DeepSeek Flash | 4 hrs | ❌ Depende de E.2 |
| E.4 | Decisión: ¿Ollama para Mnemosyne? | 1 hr | ❌ Depende de E.3 |
| **Track F** | A2A Protocol Re-evaluation | 3-4 días | Monitoreo |
| F.1 | Investigar estado actual de A2A (Mayo 2026) | 2 hrs | ✅ Independiente |
| F.2 | Diseñar Agent Card Schema para KAOS | 4 hrs | ✅ Independiente |
| F.3 | Decidir: implementar A2A bridge o esperar | 2 hrs | ❌ Depende de F.1-2 |
| **Benchmarks** | Reporte completo de calidad | 3-4 días | Todos los tracks |
| BM.1 | Score de cada agente con cada proveedor | 4 hrs | ❌ Depende de A', E |
| BM.2 | Comparativa costos: antes vs después | 2 hrs | ✅ Parcial |
| BM.3 | Reporte ejecutivo con PaperJSX | 4 hrs | ❌ Depende de BM.1-2 |

#### Ruta Crítica

- **E.3 (Evaluación Ollama)**: Bloquea decisión de migración a modelos locales
- **BM.1 (Benchmarks)**: Bloquea reporte ejecutivo final

#### Riesgos por Track

| Track | Riesgo | Prob | Impacto | Mitigación |
|-------|--------|:----:|:-------:|------------|
| E | GPU insuficiente → Ollama inusable (i5-11400F sin GPU dedicada) | **Alta** | **Crítico** | Usar CPU GGUF (Q4_K_M, ~5 t/s aceptable para Mnemosyne) |
| E | Quality gap >30% vs DeepSeek Flash | Media | Alto | No migrar; mantener API-based |
| F | A2A protocolo aún inmaduro | Media | Bajo | Solo diseño, no implementación |
| BM | Datos insuficientes para benchmark significativo | Baja | Bajo | Benchmark cualitativo + muestras |

#### Criterios GO/NO-GO

- **E.3 GO**: Ollama Qwen2.5-7B quality gap < 15% vs DeepSeek Flash → **Migrar Mnemosyne** a local
- **E.3 NO-GO**: Gap > 30% → **No migrar**, mantener API-based
- **F.3 GO**: A2A SDK estable + adopción >200 orgs → **Diseñar implementación**
- **F.3 NO-GO**: A2A aún inmaduro → **Archivar diseño para Q4 2026**

#### Costo Estimado

| Recurso | Costo |
|---------|:-----:|
| Tiempo desarrollador | ~80-120 horas |
| API calls | ~$2.45 (DeepSeek producción) |
| OpenRouter crédito | $10 (one-time) |
| Ollama | $0 (open source) |
| GPU/CPU | $0 (existente) |
| **Total** | **~$12.45 + tiempo** |

---

## Parte 4: Matriz de Riesgos Total

### Matriz Consolidada

| ID | Riesgo | Track | Probabilidad | Impacto | Severidad | Mitigación | Plan de Contingencia |
|:--:|--------|-------|:-----------:|:-------:|:---------:|------------|---------------------|
| **R1** | Gemini Free cambia términos/suspende free tier | A' | 🟡 Media | 🔴 Alto | **3.0** | Tener OpenRouter + Groq como fallback; no depender de un solo free tier | Migrar a OpenRouter Free + DeepSeek paid |
| **R2** | OpenRouter rate limit (50 req/día) insuficiente | A' | 🔴 Alta | 🟡 Medio | **2.5** | Comprar $10 crédito (eleva a 1000 req/día) | Usar API directa de DeepSeek |
| **R3** | OWUI incompatible con MCPO bridge | B | 🟡 Media | 🔴 Alto | **2.8** | Pin versión OWUI + MCPO compatibles; test en Docker | Usar OWUI sin MCPO (solo modelos directos) |
| **R4** | LightRAG no se integra bien con txtai | C | 🟡 Media | 🟡 Medio | **2.0** | Usar LightRAG como complemento, no reemplazo; mantener txtai como L0 primario | Cancelar LightRAG, reforzar txtai con mejor chunking |
| **R5** | Sleep cycle nocturno corrompe memoria activa | D | 🟢 Baja | 🔴 Alto | **2.5** | Ejecutar dry-run primero; checkpoint antes de sleep | Restaurar desde checkpoint git |
| **R6** | GPU insuficiente para Ollama (sin GPU dedicada) | E | 🔴 Alta | 🔴 Alto | **3.5** | Usar CPU con GGUF Q4_K_M (~5 t/s); limitar a Mnemosyne | No migrar; mantener API-based; considerar cloud GPU spot |
| **R7** | Quality gap Ollama >30% vs DeepSeek Flash | E | 🟡 Media | 🟡 Medio | **2.0** | Usar Qwen2.5-7B (mejor calidad/tamaño); benchmark previo | No migrar; mantener API |
| **R8** | A2A protocolo aún inmaduro (riesgo de adopción) | F | 🟡 Media | 🟢 Bajo | **1.5** | Solo diseño, no implementación; monitorear adopción | Archivar diseño; re-evaluar en Q4 2026 |
| **R9** | Usuario no adopta OWUI (sigue en OpenCode/Telegram) | B | 🟡 Media | 🟡 Medio | **2.0** | Definir boundary claro: OWUI = casual, Obsidian = trabajo profundo | No forzar uso; mantener ambos |
| **R10** | Costo API se dispara con multi-provider | A' | 🟢 Baja | 🟡 Medio | **1.5** | Monitoreo con TokenTracker + alerts semanales | Poner límite duro de $10/mes |
| **R11** | Latencia excesiva con free tiers | A' | 🟡 Media | 🟢 Bajo | **1.0** | Usar Groq (840 TPS) para velocidad; Gemini para desarrollo | DeepSeek paid para producción sensible a latencia |
| **R12** | Datos enviados a proveedores cloud (privacidad) | A' | 🟡 Media | 🟡 Medio | **2.0** | No enviar datos sensibles a free tiers; segregar por tipo de tarea | DeepSeek para datos internos; free tiers para investigación pública |

### Mapa de Calor de Riesgos

```
                    PROBABILIDAD
              Baja       Media       Alta
         ┌───────────┬───────────┬───────────┐
   Bajo  │           │    R8     │           │
         │           │    R11    │           │
 I       ├───────────┼───────────┼───────────┤
 M       │    R10    │    R4     │    R2     │
 P       │           │    R9     │    R6     │
 A  Media├───────────┼───────────┼───────────┤
 C       │           │    R1     │    R6     │
 T       │    R12    │    R3     │    R6     │
 O  Alto │           │    R5     │           │
         └───────────┴───────────┴───────────┘
```

**Riesgos Críticos a Mitigar Inmediatamente**: R6 (GPU), R1 (Gemini terms), R3 (OWUI compat)

---

## Parte 5: Recomendación Estratégica Final

### ✅ Escenario Recomendado: **B — "Completo Acelerado" (1-2 semanas)**

**Razones**:

1. **Riesgo controlado**: No depende de GPU (R6 mitigado), no invierte en A2A inmaduro
2. **Máximo valor por tiempo**: 4 tracks paralelos, todos independientes
3. **Costo mínimo**: ~$12.45 + tiempo de desarrollador
4. **Resultado concreto al final**: KAOS con 4 proveedores, interfaz visual, memoria semántica mejorada, consolidación nocturna
5. **Prepara el terreno**: Todo lo construido aquí es base para Escenario C si se desea después

### 🥇 Prioridad #1 Absoluta: **Track A' — Multi-Provider Free Model Strategy**

**Por qué**:

- **Impacto inmediato**: Reduce costo de $4.36 → ~$2.45/mes
- **Resiliencia**: Si DeepSeek falla, Gemini/OpenRouter/Groq toman el control
- **Velocidad variable**: Groq (840 TPS) para tareas simples, Gemini para desarrollo, DeepSeek para producción
- **Sin dependencias**: Puede empezar HOY sin esperar nada más
- **ROI**: 15 minutos de configuración → ahorro de ~$2/mes + redundancia gratuita

**Plan de acción inmediato**:

```
Hora 0:  Crear API key de Gemini Free (ai.google.dev)
Hora 0.5: Configurar ChatGoogleGenerativeAI en LangChain para agente de desarrollo
Hora 1:  Crear API key de OpenRouter (openrouter.ai/keys)
Hora 1.5: Configurar endpoint OpenAI-compatible para diversidad
Hora 2:  Crear API key de Groq (console.groq.com)
Hora 2.5: Configurar Groq para tareas rápidas
Hora 3:  Implementar router dinámico de proveedores
Hora 4:  Verificar failover automático
```

### ❌ ¿Qué NO HACER (y por qué)?

| Proyecto | Decisión | Razón |
|----------|:--------:|-------|
| **Oyama** (original) | ❌ **NO INVERTIR** | No existe como producto. Es una landing page de GoDaddy sin API, sin modelos, sin infraestructura. |
| **A2A Protocol** (ahora) | ❌ **NO IMPLEMENTAR** | Ecosistema aún inmaduro. Solo diseñar Agent Card Schema. Re-evaluar en Q4 2026. |
| **Ollama Pilot** (ahora) | ⏸️ **POSPONER** | El i5-11400F sin GPU dedicada hace que Ollama sea marginal (~5 t/s en CPU). Mejor esperar a tener GPU o usar cloud GPU spot. La evaluación de quality gap puede hacerse en Escenario C. |
| **Fine-Tuning** | ❌ **NO HACER** | ROI marginal. DSPy primero. Los free tiers actuales son suficientemente buenos. |
| **Mem0/Memobase** | ❌ **NO REEMPLAZAR txtai** | txtai con 3,682 chunks funciona bien. Mem0 sería overhead. |
| **LangGraph Cloud** | ❌ **NO COMPRAR** | Self-hosted es suficiente. Costo premium injustificado para single-user. |

### 🗺️ Roadmap Recomendado

```
Escenario B: Semana 1-2 (AHORA)
┌─────────────────────────────────────────────────────────┐
│ Día 1: A'.1-3 (Gemini + OpenRouter + Groq config)       │
│ Día 2: A'.4-5 (Router + failover) + D.1 (Sleep cycle)   │
│ Día 3: B.1-2 (OWUI conexión + auth)                     │
│ Día 4: C.1-2 (LightRAG install + index)                 │
│ Día 5: B.3-4 (Probar agentes + docs OWUI)              │
│ Semana 2: C.3-4 (Integración + eval) + D.2-4 (NREM/REM) │
└─────────────────────────────────────────────────────────┘

Escenario C: Semana 3-4 (OPCIONAL, si se desea)
┌─────────────────────────────────────────────────────────┐
│ Evaluar GPU/CPU para Ollama + benchmark                  │
│ A2A Agent Card Schema design                             │
│ Reporte ejecutivo completo                               │
└─────────────────────────────────────────────────────────┘
```

### 📊 Proyección de Impacto

| Métrica | Hoy (2026-05-25) | Post-Escenario B | Post-Escenario C |
|---------|:----------------:|:----------------:|:----------------:|
| **Costo mensual** | $4.36 | **$2.45** (-44%) | **$2.45** (sin cambio) |
| **Proveedores disponibles** | 1 (DeepSeek) | **4** (+3 free) | **5** (+Ollama local) |
| **Redundancia** | ❌ Ninguna | ✅ Failover automático | ✅ Total |
| **Interfaz visual** | ❌ Solo CLI | ✅ Open WebUI | ✅ Open WebUI |
| **Memoria semántica** | txtai (L0) | **txtai + LightRAG** (L0+L2) | **txtai + LightRAG** |
| **Consolidación** | Manual | **Sleep Cycle nocturno** | **Sleep Cycle nocturno** |
| **Calidad score** | 88.5/100 | **~92/100** (proyectado) | **~95/100** (proyectado) |
| **Throughput** | ~1/hr | **~2-3/hr** | **~3-5/hr** |

### Veredicto Final de Metis

> **Ejecutar Escenario B ("Completo Acelerado") a partir de HOY.**
>
> La prioridad #1 es configurar los **free tiers de Gemini + OpenRouter + Groq** en 3 horas. Esto no solo reduce costos sino que da a KAOS resiliencia ante fallos de cualquier proveedor. Paralelamente, el **Sleep Cycle Nocturno** puede activarse en 30 minutos y empezar a consolidar memoria automáticamente. **Open WebUI** y **LightRAG** se ejecutan en los días siguientes.
>
> Oyama NO existe como plataforma. No inviertas tiempo ni recursos ahí. Las alternativas reales (Gemini, OpenRouter, Groq) son superiores en todo aspecto: gratuitas, estables, con respaldo empresarial.
>
> El Escenario C (Ollama + A2A) queda como opcional para cuando haya GPU disponible o el ecosistema A2A madure.

---

## Apéndices

### A: Costo Detallado por Proveedor (Mayo 2026)

| Proveedor | Modelo | Input/1M | Output/1M | Costo/mes Estimado | Notas |
|-----------|--------|:--------:|:---------:|:------------------:|-------|
| DeepSeek V4 Flash | Producción | $0.14 | $0.28 | **$2.45** | Cache hits: $0.0028/M (50× descuento) |
| DeepSeek V4 Pro | Calidad (10%) | $0.435 | $0.87 | **$1.65** | Tareas de investigación |
| Kimi K2.6 (via OCGo) | Diversidad (5%) | ~$0.30 | ~$0.60 | **$0.26** | Estrategia + verificación |
| Gemini 2.5 Flash | Desarrollo | **$0** | **$0** | **$0.00** | Free tier, 250K TPM |
| OpenRouter Free | Diversidad | **$0** | **$0** | **$0.00** | 50 req/día (1000 si compras $10) |
| Groq (Llama 3.1 8B) | Rápido | **$0** | **$0** | **$0.00** | 30 RPM, 6K TPM |
| Ollama (local) | Mnemosyne | **$0** | **$0** | **$0.00** | Solo CPU si no hay GPU |
| **Total con free tiers** | | | | **~$2.45/mes** | Reducción del 44% |

### B: Arquitectura Multi-Provider Final

```
                     ┌─────────────────────────────┐
                     │     Agent LLM Call           │
                     │     with task_type            │
                     └──────────┬──────────────────┘
                                │
                     ┌──────────▼──────────┐
                     │   Router Multi-      │
                     │   Provider (DSOL)    │
                     └──────────┬──────────┘
                                │
        ┌───────────────────────┼───────────────────────┐
        │                       │                       │
        ▼                       ▼                       ▼
┌───────────────┐     ┌─────────────────┐     ┌───────────────┐
│  Development  │     │   Production     │     │  Diversity    │
│  Gemini Free  │     │  DeepSeek V4     │     │  OpenRouter   │
│  2.5 Flash    │     │  Flash / Pro     │     │  Free Models  │
│  250K TPM     │     │  2,500 concurrent│     │  50 req/día   │
└───────────────┘     └─────────────────┘     └───────────────┘
        │                       │                       │
        └───────────────────────┼───────────────────────┘
                                │
                     ┌──────────▼──────────┐
                     │   Circuit Breaker    │
                     │   Auto-failover      │
                     └─────────────────────┘
```

### C: Timeline de Sesiones de Calidad (Orquestación)

| Sesión | Perfil | Duración | Frecuencia | Gatillo |
|--------|:------:|:--------:|:----------:|---------|
| Smoke | Desarrollo 🟡 | 2 min | Post-cada output | post_output_hook |
| Funcional | Desarrollo 🟡 | 15 min | Diario | pipeline completo |
| Auditoría | Auditoría 🟣 | 60 min | Semanal | domingos 10 PM |
| Post-Escenario B | Producción 🔴 | 30 min | Al finalizar | verificación completa |

---

*Documento generado por Metis (Μῆτις). Basado en investigaciones de Aletheia, decisiones arquitectónicas de Kosmos (ADRs), y estado actual de KAOS. Fecha: 2026-05-25.*
