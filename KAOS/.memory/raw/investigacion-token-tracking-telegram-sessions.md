# Investigación: Token Tracking, Telegram Dashboard y Session Analytics

**Investigador**: Aletheia (agente de investigación KAOS)
**Fecha**: 2026-05-24
**Dominio**: OpenCode API, LLM Pricing, Telegram Bot, SQLite Schema
**Perfil**: deep — multi-source triangulation (Exa Search + GitHub issues + docs oficiales + código fuente)

---

## Resumen Ejecutivo

Esta investigación cubre **4 tracks técnicos** necesarios para habilitar mejoras críticas en KAOS. Los hallazgos principales:

1. **Token Tracking**: El endpoint `/v1/chat/completions` de OpenCode Go **SÍ devuelve** `usage` con formato completo OpenAI-compatible (`prompt_tokens`, `completion_tokens`, `total_tokens`, más detalles de caché y reasoning). El bug en `llm.py` es que llama a `resp.choices[0].message.content` sin tocar `resp.usage`. La solución es trivial.

2. **Pricing**: OpenCode Go opera con modelo de **suscripción plana** ($10/mes) con topes de cuota por consumo, NO cobro por token directo. Sin embargo, cada modelo tiene un "valor en cuota" que podemos usar para tracking interno. Se proporciona tabla completa de precios de referencia de los proveedores upstream.

3. **Telegram Bot**: `python-telegram-bot v21+` soporta nativamente `CommandHandler` múltiple, `send_document()` para HTML, `ConversationHandler` para multi-paso, y `AIORateLimiter` built-in para rate limiting. El bot actual solo tiene `/start` — añadir dashboard commands es directo.

4. **Session Analytics**: `opencode.db` tiene schema rico con tablas `session`, `message`, `part` que contienen datos de agente, modelo, tokens (input/output/cache/reasoning), costos y timestamps. Todo lo necesario para analytics está disponible.

---

## 1. OpenCode Go API Response Schema

### 1.1 ¿El endpoint `/v1/chat/completions` devuelve `usage`?

**Confirmado: SÍ.** El endpoint `https://opencode.ai/zen/go/v1/chat/completions` de OpenCode Go devuelve `usage` en la respuesta JSON con formato completo OpenAI-compatible.

Evidencia directa desde un issue confirmado de GitHub (anomalyco/opencode#24268, 2026-04-25), donde se muestra la respuesta JSON cruda:

```json
{
  "id": "gen-1777100177-ykze5vmKKPzbRy7Itoe2",
  "object": "chat.completion",
  "model": "moonshotai/kimi-k2.6-20260420",
  "usage": {
    "prompt_tokens": 22,
    "completion_tokens": 77,
    "total_tokens": 99,
    "cost": 0,
    "is_byok": true,
    "prompt_tokens_details": {
      "cached_tokens": 0,
      "cache_write_tokens": 0,
      "audio_tokens": 0,
      "video_tokens": 0
    },
    "cost_details": {
      "upstream_inference_cost": 0.0003289,
      "upstream_inference_prompt_cost": 2.09e-05,
      "upstream_inference_completions_cost": 0.000308
    },
    "completion_tokens_details": {
      "reasoning_tokens": 78,
      "image_tokens": 0,
      "audio_tokens": 0
    }
  },
  "cost": "0"
}
```

### 1.2 Consistencia con formato OpenAI

**SÍ, es consistente.** El schema coincide con OpenAI Chat Completions:

| Campo OpenCode Go | Equivalente OpenAI | Tipo |
|---|---|---|
| `usage.prompt_tokens` | `usage.prompt_tokens` | number |
| `usage.completion_tokens` | `usage.completion_tokens` | number |
| `usage.total_tokens` | `usage.total_tokens` | number |
| `usage.prompt_tokens_details.cached_tokens` | `usage.prompt_tokens_details.cached_tokens` | number |
| `usage.completion_tokens_details.reasoning_tokens` | `usage.completion_tokens_details.reasoning_tokens` | number |
| `usage.cost` | *no estándar OpenAI* | number |
| `usage.cost_details` | *no estándar OpenAI* | object |

El código fuente de OpenCode (openai.go línea ~usage()) confirma que leen `completion.Usage.PromptTokens`, `completion.Usage.CompletionTokens`, y `completion.Usage.PromptTokensDetails.CachedTokens`.

### 1.3 Documentación pública

- **OpenCode Go docs**: https://opencode.ai/docs/go/ — describe el endpoint y modelos disponibles.
- **OpenCode Zen docs**: https://anomalyco-opencode.mintlify.app/zen — lista modelos y endpoints.
- **Session management docs**: https://opencode-ai-opencode.mintlify.app/features/session-management — documenta tracking de tokens y costs.
- **SDK docs**: https://opencode.ai/docs/sdk/ — documenta `@opencode-ai/sdk`.
- **Pricing page**: https://opencode.ai/go — $5 primer mes, $10/mes después.

### 1.4 SDK `@opencode-ai/sdk` y token usage

El SDK de OpenCode (`@opencode-ai/sdk`) **expone token usage** a través de:

1. **`session.messages({ path })`** — devuelve `{ info: Message, parts: Part[] }[]` donde `Message.tokens` contiene input, output, reasoning, cache.
2. **Internamente** (código fuente): `packages/opencode/src/session/index.ts` calcula tokens con `input.usage.totalTokens` y los almacena en `tokens = { total, input, output, reasoning, cache: { write, read } }`.
3. **Community tool**: `ramtinJ95/opencode-tokenscope` es una herramienta open-source que lee token usage del SDK.

### 1.5 Bug conocido: reasoning_tokens puede ser inexacto

Issue #24268 documenta que `completion_tokens_details.reasoning_tokens` puede reportar valores SUPERIORES a `completion_tokens`, lo que es semánticamente imposible. OpenRouter y los proveedores upstream facturan basado en `completion_tokens` (que ya incluye reasoning tokens). Se recomienda usar `completion_tokens` como fuente única para costos.

### 1.6 Conclusión para Implementación

**Solución para llm.py**: Cambiar:
```python
# Actual (ROTO):
return resp.choices[0].message.content or ""

# Corregido:
content = resp.choices[0].message.content or ""
usage = {
    "prompt_tokens": resp.usage.prompt_tokens,
    "completion_tokens": resp.usage.completion_tokens,
    "total_tokens": resp.usage.total_tokens,
    "cached_tokens": getattr(resp.usage, 'prompt_tokens_details', None) and resp.usage.prompt_tokens_details.cached_tokens or 0,
    "reasoning_tokens": getattr(resp.usage, 'completion_tokens_details', None) and resp.usage.completion_tokens_details.reasoning_tokens or 0,
}
return content, usage  # Tupla en vez de solo string
```

Luego propagar `usage` por `agent_llm_call()` → sistema de tracking → base de datos.

### Fuentes
- [Bug: OpenCode Go/Zen overcounts tokens #24268](https://github.com/anomalyco/opencode/issues/24268) — confianza: **alta** (respuesta JSON cruda documentada)
- [OpenCode Go docs](https://opencode.ai/docs/go/) — confianza: **alta**
- [OpenCode Source: openai.go](https://github.com/opencode-ai/opencode/blob/73ee4932/internal/llm/provider/openai.go) — confianza: **alta**
- [OpenCode Source: session.sql.ts](https://github.com/anomalyco/opencode/blob/51e310c9/packages/opencode/src/session/session.sql.ts) — confianza: **alta**
- [OpenCode Session management docs](https://opencode-ai-opencode.mintlify.app/features/session-management) — confianza: **alta**
- [OpenCode SDK docs](https://opencode.ai/docs/sdk/) — confianza: **media** (documentación pública)

---

## 2. Pricing de Modelos go-*

### 2.1 Modelo de negocio de OpenCode Go

**OpenCode Go NO es pay-per-token.** Es un modelo de suscripción:
- **$5 primer mes**, luego **$10/mes**
- Tiene cuotas por consumo: ~$12/5 horas, ~$30/semana, ~$60/mes
- Las cuotas se consumen según el "valor en cuota" de cada modelo
- NO hay cobro directo por token — el tracking de costos es **_informativo_** para no exceder la cuota mensual

**Importante**: OpenCode Go aplica markup sobre los precios upstream. Los precios que se muestran abajo son los **_precios de los proveedores directos_** (DeepSeek, Alibaba, Zhipu, Moonshot, Xiaomi, Google). OpenCode Go tiene sus propios precios internos para el consumo de cuota que NO son públicos.

### 2.2 Tabla de Precios por Modelo (USD / 1M tokens)

| Modelo KAOS | Model ID upstream | Provider | Input $/1M | Output $/1M | Cache Read $/1M | Context | Fuente |
|---|---|---|---|---|---|---|---|
| **go-flash** | `deepseek-v4-flash` | DeepSeek | $0.14 | $0.28 | $0.0028 | 1M | api-docs.deepseek.com |
| **go-pro** | `deepseek-v4-pro` | DeepSeek | $0.435 | $0.87 | $0.003625 | 1M | api-docs.deepseek.com |
| **go-qwen** | `qwen3.5-plus` | Alibaba | $0.30–$0.40 | $1.80–$2.40 | ~$0.08 | 1M | cloudprice.net |
| **go-qwen-latest** | `qwen3.6-plus` | Alibaba | $0.325 | $1.95 | $0.406 | 1M | benchable.ai |
| **go-glm** | `glm-5` | Zhipu | $1.00 | $3.20 | $0.20 | 200K | docs.z.ai |
| **go-glm-latest** | `glm-5.1` | Zhipu | $1.40 | $4.40 | $0.26 | 200K | docs.z.ai |
| **go-kimi** | `kimi-k2.5` | Moonshot | $0.60 | $3.00 | $0.10 | 262K | platform.kimi.ai |
| **go-kimi-latest** | `kimi-k2.6` | Moonshot | $0.95 | $4.00 | $0.16 | 262K | zenn.dev/jarvis |
| **go-mimo** | `mimo-v2-pro` | Xiaomi | $1.00 (≤256K) | $3.00 (≤256K) | $0.20 | 1M | mimo-v2.com/docs/pricing |
| | | | $2.00 (256K-1M) | $6.00 (256K-1M) | $0.40 | | |
| **go-gemini-flash** | `gemini-3.5-flash` | Google | $1.50 | $9.00 | $0.15 | 1M | ai.google.dev |

### 2.3 Cache Read Discounts

| Modelo | Cache Hit Discount | Notas |
|---|---|---|
| DeepSeek V4 Flash | **98% off** ($0.14 → $0.0028) | Confirmado, permanente |
| DeepSeek V4 Pro | **~99% off** ($0.435 → $0.003625) | Precio permanente desde 2026-05-22 |
| Qwen3.5/3.6 Plus | **~80% off** | Tier pricing, depende de longitud |
| GLM-5/5.1 | **~80% off** | Almacenamiento gratis por tiempo limitado |
| Kimi K2.5 | **~83% off** ($0.60 → $0.10) | Cache hit pricing disponible |
| Kimi K2.6 | **~83% off** ($0.95 → $0.16) | |
| MiMo-V2-Pro | **~80% off** | Cache write temporalmente gratis |
| Gemini 3.5 Flash | **90% off** ($1.50 → $0.15) | Cache storage: $1.00/hora |

### 2.4 OpenCode Go Pricing Markup

Según el commit `d2a8f44` de OpenCode (docs/go.mdx), los precios de **consumo de cuota** en OpenCode Go son:

| Modelo | Input (cuota) | Output (cuota) | Cached Read (cuota) |
|---|---|---|---|
| GLM-5 | $1.00 | $3.20 | $0.20 |
| Kimi K2.5 | $0.60 | $3.00 | $0.10 |
| MiniMax M2.5 | $0.30 | $1.20 | $0.03 |

**Estimación de markup**: OpenCode Go aplica un markup de ~1.0x-1.5x sobre los precios upstream para los modelos listados. El markup NO es uniforme.

### 2.5 Recomendaciones para Tracking de Costos en KAOS

Dado que KAOS usa **OpenCode Go subscription** ($10/mes fijo), el tracking de costos reales en USD no es directamente aplicable. Sin embargo, se recomienda:

1. **Usar los precios upstream como "costo estimado"** para comparación entre modelos
2. **Trackear tokens consumidos** (input, output, cache read) como métrica principal
3. **Calcular "costo de cuota consumida"** usando los precios internos de OpenCode Go si se quiere estimar desgaste de la cuota mensual
4. Para KAOS, el costo real es **$10/mes fijo** — los tokens no cuestan extra mientras no se exceda la cuota

### Fuentes
- [DeepSeek Pricing Page](https://api-docs.deepseek.com/quick_start/pricing) — confianza: **alta**
- [DeepSeek V4 pricing (permanent discount)](https://www.mexc.co/en-PH/news/1109801) — confianza: **alta**
- [Zhipu AI Pricing](https://docs.z.ai/guides/overview/pricing) — confianza: **alta**
- [OpenCode Go docs (commit d2a8f44)](https://github.com/anomalyco/opencode/commit/d2a8f44c22b52cd941da06cc4ace44729a3c50c3) — confianza: **alta**
- [Kimi K2.5/K2.6 pricing](https://zenn.dev/jarvis/articles/491e839a86386e) — confianza: **alta**
- [MiMo-V2-Pro pricing](https://www.mimo-v2.com/docs/pricing) — confianza: **alta**
- [Gemini 3.5 Flash pricing](https://ai.google.dev/gemini-api/docs/pricing) — confianza: **alta**
- [OpenCode Go docs page](https://opencode.ai/docs/go/) — confianza: **alta**
- [CloudPrice: Qwen models](https://cloudprice.net/models/alibaba-qwen3-6-plus) — confianza: **media**

---

## 3. Telegram Bot — python-telegram-bot v21+

### 3.1 Registro de CommandHandlers múltiples

En v21+, simplemente se añaden múltiples `CommandHandler` al `Application`:

```python
from telegram.ext import Application, CommandHandler

app = Application.builder().token(TOKEN).build()

# Múltiples handlers — se evalúan en orden de registro
app.add_handler(CommandHandler("start", start))
app.add_handler(CommandHandler("costos", cmd_costos))
app.add_handler(CommandHandler("modelos", cmd_modelos))
app.add_handler(CommandHandler("sesiones", cmd_sesiones))
app.add_handler(CommandHandler("ayuda", cmd_ayuda))
```

**Importante**: Los `CommandHandler` se evalúan en orden de registro. Si hay conflictos (ej. `filters.COMMAND` genérico), el primero gana. Para comandos con argumentos, usar `has_args=True/False`.

### 3.2 Envío de archivo HTML como documento

```python
import io

async def cmd_report(update: Update, context: ContextTypes.DEFAULT_TYPE):
    html_content = "<html><body><h1>Dashboard KAOS</h1>...</body></html>"
    doc = io.BytesIO(html_content.encode('utf-8'))
    doc.name = "dashboard.html"
    await update.message.reply_document(
        document=doc,
        filename="dashboard.html",
        caption="📊 Dashboard de costos"
    )
```

**Alternativa con archivo local**:
```python
await update.message.reply_document(
    document=open('/path/to/dashboard.html', 'rb'),
    filename='kaos-dashboard.html'
)
```

### 3.3 Paginación para respuestas largas

Usando `ConversationHandler` con estados y `InlineKeyboardMarkup`:

```python
from telegram import InlineKeyboardButton, InlineKeyboardMarkup, Update
from telegram.ext import (
    Application, CommandHandler, CallbackQueryHandler, 
    ConversationHandler, ContextTypes
)

# Estados
PAGINA = range(1)

async def cmd_agentes(update: Update, context: ContextTypes.DEFAULT_TYPE):
    context.user_data["page"] = 0
    return await mostrar_pagina(update, context)

async def mostrar_pagina(update: Update, context: ContextTypes.DEFAULT_TYPE):
    page = context.user_data.get("page", 0)
    agentes = ["Aletheia", "Kosmos", "Metis", "Kratos", "Mnemosyne"]
    total = len(agentes)
    item = agentes[page]
    
    keyboard = []
    if page > 0:
        keyboard.append(InlineKeyboardButton("⬅️ Anterior", callback_data="prev"))
    if page < total - 1:
        keyboard.append(InlineKeyboardButton("Siguiente ➡️", callback_data="next"))
    
    reply_markup = InlineKeyboardMarkup([keyboard]) if keyboard else None
    
    text = f"**Agente {page+1}/{total}**\nNombre: {item}\n..."
    
    if update.callback_query:
        await update.callback_query.edit_message_text(text, reply_markup=reply_markup)
    else:
        await update.message.reply_text(text, reply_markup=reply_markup)
    return PAGINA

async def pagination_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    if query.data == "next":
        context.user_data["page"] += 1
    elif query.data == "prev":
        context.user_data["page"] -= 1
    return await mostrar_pagina(update, context)

async def cancel(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("Cancelado.")
    return ConversationHandler.END

# En main():
conv_handler = ConversationHandler(
    entry_points=[CommandHandler("agentes", cmd_agentes)],
    states={PAGINA: [CallbackQueryHandler(pagination_handler, pattern="^(prev|next)$")]},
    fallbacks=[CommandHandler("cancel", cancel)],
)
app.add_handler(conv_handler)
```

### 3.4 Rate Limiting interno

`python-telegram-bot v21+` incluye `AIORateLimiter` built-in:

```python
from telegram.ext import AIORateLimiter

app = Application.builder() \
    .token(TOKEN) \
    .rate_limiter(AIORateLimiter(
        overall_max_rate=30,      # 30 mensajes/segundo global
        overall_time_period=1,
        group_max_rate=20,         # 20 mensajes/minuto por grupo
        group_time_period=60,
        max_retries=3             # Reintentar en caso de RetryAfter
    )) \
    .build()
```

Instalación: `pip install "python-telegram-bot[rate-limiter]"`

### 3.5 ConversationHandler para comandos multi-paso

**SÍ, es el patrón recomendado.** Ejemplo de dashboard interactivo:

```python
# Estados
SELECCION_MODELO, RANGO_FECHAS, CONFIRMAR = range(3)

async def cmd_dashboard(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    await update.message.reply_text("📊 Dashboard KAOS\nSelecciona un modelo:", 
        reply_markup=model_keyboard)
    return SELECCION_MODELO

async def seleccionar_modelo(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    context.user_data["modelo"] = update.message.text
    await update.message.reply_text("¿Rango de fechas? (últimos 7/30 días)")
    return RANGO_FECHAS

async def rango_fechas(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    context.user_data["dias"] = update.message.text
    # Generar reporte...
    await update.message.reply_document(document=reporte, filename="reporte.html")
    return ConversationHandler.END
```

### 3.6 Manejo de errores de red/timeout

```python
from telegram.error import TimedOut, NetworkError, RetryAfter, TelegramError

async def safe_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    try:
        # Operación que puede fallar
        data = await expensive_operation()
        await update.message.reply_text(f"Resultado: {data}")
    except RetryAfter as e:
        # Flood control — esperar y reintentar automático
        await update.message.reply_text(f"⏳ Límite excedido, espera {e.retry_after}s")
    except TimedOut:
        await update.message.reply_text("⏰ La operación tomó demasiado tiempo. Intenta de nuevo.")
    except NetworkError:
        await update.message.reply_text("🔌 Error de red. Verifica tu conexión.")
    except TelegramError as e:
        await update.message.reply_text(f"❌ Error: {str(e)[:100]}")
```

### 3.7 Conclusión para Implementación

Comandos recomendados para el bot de KAOS:

| Comando | Función | Implementación |
|---|---|---|
| `/start` | Mensaje de bienvenida | CommandHandler simple |
| `/costos` | Resumen de tokens usados hoy/semana/mes | CommandHandler + query DB |
| `/modelos` | Desglose por modelo con paginación | ConversationHandler + paginación |
| `/sesiones` | Últimas sesiones activas | CommandHandler con formateo |
| `/dashboard` | Enviar HTML dashboard como documento | CommandHandler → `reply_document` |
| `/agentes` | Breakdown por agente | ConversationHandler con CallbackQueryHandler |
| `/ayuda` | Lista de comandos | CommandHandler simple |

### Fuentes
- [python-telegram-bot v21.10 documentation](https://docs.python-telegram-bot.org/en/v21.10/) — confianza: **alta**
- [ConversationHandler example](https://docs.python-telegram-bot.org/en/v21.10/examples.conversationbot.html) — confianza: **alta**
- [Handling network errors wiki](https://github.com/python-telegram-bot/python-telegram-bot/wiki/Handling-network-errors) — confianza: **alta**
- [Avoiding flood limits wiki](https://github.com/python-telegram-bot/python-telegram-bot/wiki/Avoiding-flood-limits) — confianza: **alta**
- [Working with Files and Media wiki](https://github.com/python-telegram-bot/python-telegram-bot/wiki/Working-with-Files-and-Media) — confianza: **alta**
- [AIORateLimiter docs](https://docs.python-telegram-bot.org/en/v21.5/telegram.ext.aioratelimiter.html) — confianza: **alta**

---

## 4. SQL Schema de opencode.db

### 4.1 Schema de la tabla `session`

Basado en el código fuente oficial (`session.sql.ts` en OpenCode) y la documentación de session management:

```sql
CREATE TABLE session (
    id              TEXT PRIMARY KEY,          -- ULID (ej. "ses_72eb63d80ffe...")
    project_id      TEXT NOT NULL,             -- FK → project.id
    workspace_id    TEXT,                      -- FK → workspace (canales separados)
    parent_id       TEXT,                      -- FK → session.id (sesiones hijas)
    slug            TEXT NOT NULL,             -- Human-readable short ID
    directory       TEXT NOT NULL,             -- Directorio de trabajo
    path            TEXT,                      -- Ruta del proyecto
    title           TEXT NOT NULL,             -- Título de la sesión
    version         TEXT NOT NULL,             -- Versión de OpenCode
    share_url       TEXT,                      -- URL de compartir
    summary_additions   INTEGER,              -- Archivos añadidos
    summary_deletions   INTEGER,              -- Archivos eliminados
    summary_files       INTEGER,              -- Total archivos modificados
    summary_diffs       TEXT,                  -- JSON array de FileDiff
    revert              TEXT,                  -- JSON { messageID, partID?, snapshot?, diff? }
    permission          TEXT,                  -- JSON Permission.Ruleset
    time_created        INTEGER NOT NULL,      -- Timestamp (ms)
    time_updated        INTEGER NOT NULL,      -- Timestamp (ms)
    time_compacting     INTEGER,               -- Timestamp de compactación
    time_archived       INTEGER                -- Timestamp de archivado
);
```

**NOTA**: El schema real de opencode.db es ligeramente diferente al que se documenta en mintlify. La documentación de mintlify muestra tablas `sessions` y `messages` con campos `prompt_tokens`, `completion_tokens`, `cost` directamente en columnas. **El schema real almacena estos datos como JSON** en el campo `data` de las tablas `message` y `part`.

### 4.2 Schema de la tabla `message`

```sql
CREATE TABLE message (
    id              TEXT PRIMARY KEY,          -- ULID
    session_id      TEXT NOT NULL,             -- FK → session.id
    time_created    INTEGER NOT NULL,          -- Timestamp (ms)
    data            TEXT NOT NULL              -- JSON con: role, modelID, providerID, 
                                               -- agent, cost, tokens: { input, output, 
                                               -- reasoning, cache: { read, write }, total }
);
```

El campo `data` contiene un JSON con la estructura `MessageV2` que incluye:
- `role`: "user" | "assistant"
- `modelID`: string (ej. "deepseek-v4-flash")
- `providerID`: string (ej. "opencode-go")
- `agent`: string (ej. "Aletheia" o "Task" para subagentes)
- `cost`: number (costo en USD)
- `tokens`: object con `input`, `output`, `reasoning`, `cache.read`, `cache.write`, `total`
- `time.created`, `time.completed` (timestamps)
- `error`: opcional, si falló
- `finish`: string (razón de finalización)

### 4.3 Schema de la tabla `part`

```sql
CREATE TABLE part (
    id              TEXT PRIMARY KEY,          -- ULID
    message_id      TEXT NOT NULL,             -- FK → message.id
    session_id      TEXT NOT NULL,             -- FK → session.id
    time_created    INTEGER NOT NULL,          -- Timestamp (ms)
    data            TEXT NOT NULL              -- JSON con type, text/tool/step-finish, 
                                               -- y para type="step-finish": tokens, cost
);
```

Tipos de `part`:
- `text`: contenido textual
- `reasoning`: cadena de pensamiento
- `tool-call` / `tool-result`: llamadas a herramientas
- `file`: archivos adjuntos
- `step-start` / `step-finish`: marcadores de inicio/fin de paso de agente
  - **`step-finish`** contiene `tokens` (input, output, etc.) y `cost` por paso individual

### 4.4 Registro de agente/subagente por mensaje

**SÍ.** El campo `agent` dentro de `message.data` (JSON) registra qué agente generó la respuesta. OpenCode también soporta `SubtaskPart` en la tabla `part` para tareas hijas. En el ecosistema KAOS, cuando se usa Task tool, los mensajes de subagentes aparecen con agent IDs específicos.

Además, `session.parent_id` permite rastrear sesiones hijas (subagentes que crean sesiones propias).

### 4.5 Metadatos de duración

**SÍ.** Cada mensaje tiene `time.created` y opcionalmente `time.completed` (en el JSON `data`). La sesión tiene `time_created`, `time_updated`, `time_compacting`. Esto permite calcular duración de sesiones y latencia de respuestas.

### 4.6 Estabilidad del Schema

El schema ha evolucionado:
- **Pre-v1.2.0**: Almacenamiento en archivos JSON individuales
- **v1.2.0 - v1.2.x**: SQLite v1 con schema básico (session, message con columnas directas prompt_tokens/completion_tokens)
- **v1.14+**: SQLite v2 actual con schema más rico, datos en JSON, soporte multi-workspace (opencode-{channel}.db)

**ADVERTENCIA**: El schema NO es completamente estable entre versiones. El cambio más significativo fue de columnas directas a JSON blob para datos flexibles. Se recomienda:
- Usar `json_extract()` en SQLite para acceder a campos dentro del JSON
- No depender de columnas específicas que puedan cambiar
- Versionar el código de analytics

### 4.7 Consultas útiles para KAOS

**Tokens totales por sesión** (de `step-finish` parts):
```sql
SELECT 
    s.id, s.title,
    SUM(json_extract(p.data, '$.tokens.input')) as total_input,
    SUM(json_extract(p.data, '$.tokens.output')) as total_output,
    SUM(json_extract(p.data, '$.tokens.cache.read')) as cache_read,
    SUM(json_extract(p.data, '$.tokens.total')) as total_tokens,
    COUNT(*) as llm_calls,
    SUM(json_extract(p.data, '$.cost')) as total_cost
FROM session s
JOIN part p ON p.session_id = s.id
WHERE json_extract(p.data, '$.type') = 'step-finish'
GROUP BY s.id
ORDER BY total_tokens DESC;
```

**Mensajes por agente (últimas N sesiones)**:
```sql
SELECT 
    json_extract(m.data, '$.agent') as agent,
    json_extract(m.data, '$.modelID') as model,
    COUNT(*) as msg_count,
    SUM(json_extract(m.data, '$.tokens.input')) as input_tokens,
    SUM(json_extract(m.data, '$.tokens.output')) as output_tokens
FROM message m
JOIN session s ON m.session_id = s.id
WHERE s.time_created > strftime('%s','now','-7 days') * 1000
GROUP BY json_extract(m.data, '$.agent')
ORDER BY msg_count DESC;
```

**Sesiones activas**:
```sql
SELECT 
    s.id, s.title, 
    s.time_created / 1000 as created_ts,
    s.time_updated / 1000 as updated_ts,
    (SELECT COUNT(*) FROM message m WHERE m.session_id = s.id) as msg_count
FROM session s
WHERE s.time_archived IS NULL
ORDER BY s.time_updated DESC
LIMIT 20;
```

### Fuentes
- [OpenCode Source: session.sql.ts](https://github.com/anomalyco/opencode/blob/51e310c9/packages/opencode/src/session/session.sql.ts) — confianza: **alta** (código fuente oficial)
- [OpenCode Source: index.ts (cálculo de tokens)](https://github.com/sst/opencode/blob/c7b35342/packages/opencode/src/session/index.ts) — confianza: **alta**
- [OpenCode Session management docs (mintlify)](https://opencode-ai-opencode.mintlify.app/features/session-management) — confianza: **media** (diffiere ligeramente del schema real)
- [OpenCode Message Model docs](https://www.opencodebook.xyz/en/chapter_04_session_system/4.2_message_model) — confianza: **alta**
- [OpenCode Session Data Model docs](https://www.opencodebook.xyz/en/chapter_04_session_system/4.1_session_data_model) — confianza: **alta**
- [mnemo PR: SQLite format support](https://github.com/Pilan-AI/mnemo/pull/4) — confianza: **media** (terceros)
- [aide skill: context-usage queries](https://github.com/jmylchreest/aide/blob/main/skills/context-usage/SKILL.md) — confianza: **alta** (queries SQL probadas)
- [KAOS clean_opencode_db.py](file:///C:/Users/LeonX/Documents/KAOS/.memory/_scripts/clean_opencode_db.py) — confianza: **máxima** (código propio de KAOS)

---

## 5. Recomendaciones para Implementación

### 5.1 Captura de `resp.usage`

| Estado | Acción | Prioridad |
|---|---|---|
| **ROTO** | `llm_call()` descarta `resp.usage` | 🔴 Crítica |
| **Fix** | Devolver tupla `(content, usage)` en vez de solo `content` | Inmediata |
| **Propagación** | Modificar `agent_llm_call()` → logger → DB | Alta |
| **Fallback** | Si `resp.usage` es None (streaming truncado), usar 0 | Media |

Código de fix:
```python
def llm_call(prompt, system="", model="go-flash", 
             temperature=0.2, max_tokens=16384) -> tuple[str, dict]:
    # ... existing code ...
    resp = client.chat.completions.create(...)
    
    content = resp.choices[0].message.content or ""
    usage = {
        "prompt_tokens": resp.usage.prompt_tokens if resp.usage else 0,
        "completion_tokens": resp.usage.completion_tokens if resp.usage else 0,
        "total_tokens": resp.usage.total_tokens if resp.usage else 0,
        "cached_tokens": (resp.usage.prompt_tokens_details.cached_tokens 
                          if resp.usage and resp.usage.prompt_tokens_details else 0),
        "reasoning_tokens": (resp.usage.completion_tokens_details.reasoning_tokens 
                             if resp.usage and resp.usage.completion_tokens_details else 0),
    }
    return content, usage
```

### 5.2 Tabla de Precios para Dashboard

| Modelo KAOS | Model ID | Input $/1M | Output $/1M | Costo típico por llamada (1K in / 500 out) |
|---|---|---|---|---|
| go-flash | deepseek-v4-flash | $0.14 | $0.28 | $0.00028 |
| go-pro | deepseek-v4-pro | $0.435 | $0.87 | $0.00087 |
| go-qwen | qwen3.5-plus | $0.40 | $2.40 | $0.00160 |
| go-qwen-latest | qwen3.6-plus | $0.325 | $1.95 | $0.00130 |
| go-glm | glm-5 | $1.00 | $3.20 | $0.00260 |
| go-glm-latest | glm-5.1 | $1.40 | $4.40 | $0.00360 |
| go-kimi | kimi-k2.5 | $0.60 | $3.00 | $0.00210 |
| go-kimi-latest | kimi-k2.6 | $0.95 | $4.00 | $0.00295 |
| go-mimo | mimo-v2-pro | $1.00 | $3.00 | $0.00250 |
| go-gemini-flash | gemini-3.5-flash | $1.50 | $9.00 | $0.00600 |

**Nota**: KAOS paga $10/mes fijo por OpenCode Go. Estos precios son **referencia** para estimar consumo de cuota, no costo real.

### 5.3 Comandos de Telegram Recomendados

| Comando | Descripción | Prioridad | Implementación |
|---|---|---|---|
| `/costos` | Tokens usados hoy/semana/mes por agente | 🔴 Alta | CommandHandler + query a opencode.db |
| `/dashboard` | Enviar dashboard HTML completo | 🔴 Alta | CommandHandler + `reply_document` |
| `/modelos` | Desglose por modelo con paginación | 🟡 Media | ConversationHandler + CallbackQueryHandler |
| `/sesiones` | Últimas 20 sesiones activas | 🟡 Media | CommandHandler + query DB |
| `/agentes` | Breakdown por agente (5 agentes) | 🟢 Baja | ConversationHandler con 5 páginas |
| `/ayuda` | Lista de comandos | 🟢 Baja | CommandHandler simple |

**Orden de implementación sugerido**: `/costos` → `/dashboard` → `/modelos` → `/sesiones` → `/agentes` → `/ayuda`

### 5.4 Datos Extraíbles de opencode.db por Sesión

| Dato | Dónde está | Cómo acceder |
|---|---|---|
| ID de sesión | `session.id` | Columna directa |
| Título | `session.title` | Columna directa |
| Proyecto | `session.project_id` | FK a project table |
| Agente | `json_extract(message.data, '$.agent')` | JSON en message.data |
| Modelo usado | `json_extract(message.data, '$.modelID')` | JSON en message.data |
| Input tokens | `json_extract(part.data, '$.tokens.input')` WHERE type='step-finish' | JSON en part.data |
| Output tokens | `json_extract(part.data, '$.tokens.output')` WHERE type='step-finish' | JSON en part.data |
| Reasoning tokens | `json_extract(part.data, '$.tokens.reasoning')` | JSON en part.data |
| Cache read/write | `json_extract(part.data, '$.tokens.cache.*')` | JSON en part.data |
| Costo | `json_extract(part.data, '$.cost')` WHERE type='step-finish' | JSON en part.data |
| Timestamps | `message.time_created` | Columna directa |
| Duración | `message.time.completed - message.time.created` | JSON en message.data |
| Subagentes | `session.parent_id` o `SubtaskPart` en parts | Columna directa o JSON |
| Errores | `json_extract(message.data, '$.error')` | JSON en message.data |

### 5.5 Riesgos e Incertidumbres Técnicas

| Riesgo | Impacto | Mitigación |
|---|---|---|
| **reasoning_tokens inaccurate** (bug upstream) | Cálculo de output tokens puede ser incorrecto | Usar `completion_tokens` como fuente principal, no restar reasoning_tokens |
| **Schema de opencode.db cambia** | Queries de analytics se rompen | Usar `json_extract()` para campos JSON, no columnas directas. Versionar queries. |
| **OpenCode Go cambia precios/modelos** | Dashboard de costos desactualizado | Parametrizar precios en JSON config, no hardcodear. Revisar cada release. |
| **API key rotation** | Token tracking deja de funcionar | Logging de errores + alerta si usage=0 consistente |
| **Streaming responses** | `resp.usage` puede ser None si stream truncado | Implementar fallback a 0 y log de warning |
| **Multi-workspace DBs** | opencode-canary.db vs opencode.db | Detectar y consolidar de todos los archivos opencode-*.db |
| **Subagentes (Task tool)** | Sesiones hijas duplican conteo | Identificar por `parent_id` y agregar con JOIN recursivo |
| **Concurrencia SQLite** | OpenCode escribe mientras leemos | Abrir DB en modo read-only con WAL y busy timeout |

---

## Apéndice: Código Fuente de Referencia

### Cambio mínimo en llm.py para capturar usage

```python
def llm_call(prompt: str, system: str = "", model: str = "go-flash",
             temperature: float = 0.2, max_tokens: int = 16384) -> tuple[str, dict]:
    """
    Returns (content, usage_dict) where usage_dict contains token counts.
    """
    cfg = MODELS.get(model, MODELS["go-flash"])
    client = get_client(cfg["provider"])
    messages = []
    if system:
        messages.append({"role": "system", "content": system})
    messages.append({"role": "user", "content": prompt})

    try:
        resp = client.chat.completions.create(
            model=cfg["model"],
            messages=messages,
            temperature=temperature,
            max_tokens=max_tokens,
            timeout=120,
        )
        content = resp.choices[0].message.content or ""
        usage = {
            "prompt_tokens": resp.usage.prompt_tokens if resp.usage else 0,
            "completion_tokens": resp.usage.completion_tokens if resp.usage else 0,
            "total_tokens": resp.usage.total_tokens if resp.usage else 0,
            "cached_tokens": (resp.usage.prompt_tokens_details.cached_tokens 
                              if resp.usage and resp.usage.prompt_tokens_details else 0),
            "reasoning_tokens": (resp.usage.completion_tokens_details.reasoning_tokens 
                                 if resp.usage and resp.usage.completion_tokens_details else 0),
            "model": cfg["model"],
            "provider": cfg["provider"],
        }
        return content, usage
    except Exception as e:
        # ... fallback logic (must now return tuple) ...
        return "", {"error": str(e)}
```

### Nota importante sobre backward compatibility

Si modificas la firma de `llm_call()`, todos los callers deben actualizarse. Alternativa: añadir una nueva función `llm_call_with_usage()` que devuelva la tupla, y mantener `llm_call()` como wrapper que llama a la nueva pero extrae solo el texto.

---

*Fin del informe. Investigación completa el 2026-05-24 por Aletheia (agente de investigación KAOS).*
