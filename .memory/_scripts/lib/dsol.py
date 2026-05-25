"""
DeepSeek Optimization Layer v2 — API client, token tracking, cache optimization.
Lee DEEPSEEK_API_KEY del entorno. Trackea tokens en .memory/cache/token-usage.json
"""
import json
import logging
import os
import re
from datetime import datetime, date
from pathlib import Path

_LOG = logging.getLogger(__name__)

BASE = (Path(__file__).resolve().parent.parent.parent)  # .memory/
KAOS_ROOT = BASE.parent  # KAOS project root
TOKEN_CACHE = KAOS_ROOT / ".memory" / "cache" / "token-usage.json"

SYSTEM_PROMPT = """You are KAOS, an intelligent agent operating in a memory-augmented vault system. You have access to a persistent knowledge base stored in markdown files. Rules:
1. Always cite sources using [[wikilinks]].
2. Use ADD-only: never overwrite, always append.
3. Flag contradictions with "⚠️ Contradiction:".
4. When extracting a session, write to log.md, update index, and commit.
5. The vault is your persistent memory between sessions."""

VAULT_RULES_TEMPLATE = """The vault at {{VAULT_PATH}} contains:
- raw/: Immutable investigations (human/Aletheia-written)
- wiki/: Compiled knowledge (entities, concepts, sources, index, log)
- schema/: Configuration, ADRs, policies
- _scripts/: Maintenance scripts
- _pipeline/: Cross-agent pipeline coordination
Access via vault.py CLI or direct file operations."""

THINKING_CONFIG = {
    None:   {"description": "No thinking — fastest, JSON mode, tool calls available"},
    "high": {"description": "Thinking enabled — balanced speed vs depth"},
    "xmax": {"description": "Maximum thinking — deepest reasoning, slowest"},
}

BUDGETS = {
    "flash": {"min": 1024, "optimal": 8192, "max": 32768},
    "pro":   {"min": 4096, "optimal": 16384, "max": 65536},
    "kimi":  {"min": 4096, "optimal": 16384, "max": 65536},
}

# ── Multi-Model Router Constants ──────────────────────────────

TASK_MODEL_MAP = {
    # Flash tier (85%)
    "lint":         {"model": "go-flash",        "thinking": None,  "tier": "flash"},
    "extract":      {"model": "go-flash",        "thinking": None,  "tier": "flash"},
    "health":       {"model": "go-flash",        "thinking": None,  "tier": "flash"},
    "hydrate":      {"model": "go-flash",        "thinking": None,  "tier": "flash"},
    "wikilinks":    {"model": "go-flash",        "thinking": None,  "tier": "flash"},
    "curation":     {"model": "go-flash",        "thinking": None,  "tier": "flash"},
    "code_gen":     {"model": "go-flash",        "thinking": None,  "tier": "flash"},
    "code_simple":  {"model": "go-flash",        "thinking": None,  "tier": "flash"},
    "general":      {"model": "go-flash",        "thinking": None,  "tier": "flash"},
    # Pro tier (10%)
    "research":     {"model": "go-pro",          "thinking": "high", "tier": "pro"},
    "analyze":      {"model": "go-pro",          "thinking": "high", "tier": "pro"},
    "synthesize":   {"model": "go-pro",          "thinking": "xmax", "tier": "pro"},
    "adr":          {"model": "go-pro",          "thinking": "high", "tier": "pro"},
    "factual":      {"model": "go-pro",          "thinking": "high", "tier": "pro"},
    # Kimi tier (5%)
    "strategy":     {"model": "go-kimi-latest", "thinking": None,   "tier": "kimi"},
    "verify":       {"model": "go-kimi-latest", "thinking": None,   "tier": "kimi"},
    "cross_check":  {"model": "go-kimi-latest", "thinking": None,   "tier": "kimi"},
    "code_agentic": {"model": "go-kimi-latest", "thinking": None,   "tier": "kimi"},
    "diversity":    {"model": "go-kimi-latest", "thinking": None,   "tier": "kimi"},
}

MODEL_TIERS = {
    "flash": {"description": "Base — alta velocidad, bajo costo", "target_pct": 85},
    "pro":   {"description": "Calidad — razonamiento profundo, factual", "target_pct": 10},
    "kimi":  {"description": "Diversidad — pensamiento estratégico", "target_pct": 5},
}

AGENT_DEFAULT_TASK = {
    "aletheia":  "research",
    "kosmos":    "analyze",
    "metis":     "strategy",
    "kratos":    "code_gen",
    "mnemosyne": "curation",
    "kronos":    "general",
    "critic":    "verify",
    "planner":   "general",
}

MODEL_FALLBACK_CHAIN = {
    "go-flash":        ["go-flash", "go-pro", "go-kimi-latest"],
    "go-pro":          ["go-pro", "go-flash", "go-kimi-latest"],
    "go-kimi-latest":  ["go-kimi-latest", "go-pro", "go-flash"],
}

DEEPSEEK_API_URL = "https://api.deepseek.com/v1/chat/completions"


# ── Prompt Cache Optimizer ─────────────────────────────────
# NOTA: build_prompt() está deprecated para uso en OpenCode.
# Usa build_optimized_context() para construir contextos de
# hydratación optimizados para cache dentro de OpenCode.

def build_prompt(task: str, vault_data: str, task_input: str, agent: str = "") -> list[dict]:
    """DEPRECATED — llama a api.deepseek.com directamente.
    Usa build_optimized_context() para hydratación dentro de OpenCode."""
    system = SYSTEM_PROMPT
    rules = VAULT_RULES_TEMPLATE.replace("{{VAULT_PATH}}", str(KAOS_ROOT / ".memory"))
    return [
        {"role": "system", "content": system},
        {"role": "user",   "content": rules},
        {"role": "user",   "content": vault_data},
        {"role": "user",   "content": task_input},
    ]


def build_optimized_context(agent: str, task: str, existing_context: dict = None) -> str:
    """Construye contexto de hydratación optimizado para cache dentro de OpenCode.
    - Prioriza contenido por relevancia al agente
    - Evita duplicados si existing_context tiene files_read
    - Mantiene prefix byte-idéntico entre llamadas
    """
    priority_map = {
        "aletheia":   ["raw/", "wiki/sources/", "wiki/concepts/"],
        "kosmos":     ["schema/", "wiki/entities/", "wiki/concepts/"],
        "metis":      ["schema/", "wiki/entities/", "raw/"],
        "mnemosyne":  ["wiki/", "schema/lint-report.md", "schema/health-report.md"],
    }
    prefixes = priority_map.get(agent, ["wiki/"])
    content = []

    # Preámbulo byte-idéntico para cache prefix (siempre primero)
    content.append(f"# Context for {agent}\n")

    # Archivos ya leídos por agentes anteriores (saltar)
    skip_files = set()
    if existing_context:
        skip_files = set(existing_context.get("files_read", []))

    for prefix in prefixes:
        for path in sorted(KAOS_ROOT.glob(f".memory/{prefix}**/*.md")):
            rel = str(path.relative_to(KAOS_ROOT))
            if rel in skip_files:
                continue
            try:
                text = path.read_text(encoding="utf-8", errors="replace")[:2000]
                if text.strip():
                    content.append(f"\n---\n[{rel}]\n{text}")
            except Exception:
                pass

    # Contexto compartido del pipeline (si existe)
    if existing_context and existing_context.get("context_summary"):
        content.append("\n---\n## Pipeline Context\n")
        for agent_name, summary in existing_context["context_summary"].items():
            content.append(f"### From {agent_name}:")
            for finding in summary.get("key_findings", []):
                content.append(f"- {finding}")
            if summary.get("sources_used"):
                content.append(f"  Sources: {', '.join(summary['sources_used'])}")

    content.append(f"\n---\n## Tarea\n{task}")
    return "\n".join(content)


def estimate_cache_ratio(prompt: list[dict]) -> dict:
    total = sum(len(m["content"]) for m in prompt)
    cacheable = sum(len(m["content"]) for m in prompt[:-1])
    estimated_total = round(total / 3)
    estimated_cacheable = round(cacheable / 3)
    return {
        "total_chars": total,
        "cacheable_chars": cacheable,
        "cacheable_ratio": round(cacheable / total * 100, 1) if total > 0 else 0,
        "estimated_total_tokens": estimated_total,
        "estimated_cache_hit_tokens": estimated_cacheable,
        "estimated_miss_tokens": estimated_total - estimated_cacheable,
    }


# ── Thinking Mode ───────────────────────────────────────────

def configure_thinking(level: str | None) -> dict:
    if level is None:
        return {}
    return {"thinking": {"type": "enabled"}, "reasoning_effort": level}


# ── Circuit Breaker ─────────────────────────────────────────

class CircuitBreaker:
    """Circuit breaker por modelo — evita llamar modelos que fallan repetidamente."""

    def __init__(self, failure_threshold=3, reset_timeout=300, half_open_max=1):
        self._failure_threshold = failure_threshold
        self._reset_timeout = reset_timeout
        self._half_open_max = half_open_max
        self._state = {}

    def _ensure(self, model: str):
        if model not in self._state:
            self._state[model] = {"failures": 0, "last_failure": 0.0, "state": "closed"}

    def is_available(self, model: str) -> bool:
        self._ensure(model)
        s = self._state[model]
        if s["state"] == "closed":
            return True
        if s["state"] == "open":
            import time
            if time.time() - s["last_failure"] > self._reset_timeout:
                s["state"] = "half-open"
                s["failures"] = 0
                return True
            return False
        return s["failures"] < self._half_open_max

    def record_success(self, model: str):
        self._ensure(model)
        self._state[model] = {"failures": 0, "last_failure": 0.0, "state": "closed"}

    def record_failure(self, model: str):
        self._ensure(model)
        s = self._state[model]
        s["failures"] += 1
        s["last_failure"] = __import__("time").time()
        if s["failures"] >= self._failure_threshold:
            s["state"] = "open"
            _LOG.warning("Circuit breaker OPEN for model=%s after %d failures", model, s["failures"])

    def get_status(self) -> dict:
        return dict(self._state)


_CIRCUIT_BREAKER = CircuitBreaker()


# ── Router: Resolución de Modelo ────────────────────────────

def resolve_model(task_type=None, agent="", model_override=None):
    """Resuelve qué modelo OCGo usar para una tarea.

    Orden: model_override > TASK_MODEL_MAP > AGENT_DEFAULT_TASK > default go-flash
    Returns: {"model": str, "thinking": str|None, "tier": str, "resolved_by": str}
    """
    if model_override and model_override.startswith("go-"):
        return {"model": model_override, "thinking": None, "tier": "override", "resolved_by": "explicit"}

    if task_type and task_type in TASK_MODEL_MAP:
        rule = TASK_MODEL_MAP[task_type]
        if _CIRCUIT_BREAKER.is_available(rule["model"]):
            return {**rule, "resolved_by": f"task_type={task_type}"}
        fallback = _resolve_fallback(task_type, agent)
        _LOG.warning("CB open for %s, falling back to %s", rule["model"], fallback["model"])
        return fallback

    default_task = AGENT_DEFAULT_TASK.get(agent, "general")
    if default_task in TASK_MODEL_MAP:
        rule = TASK_MODEL_MAP[default_task]
        return {**rule, "resolved_by": f"agent_default={default_task}"}

    return {"model": "go-flash", "thinking": None, "tier": "flash", "resolved_by": "absolute_default"}


def _resolve_fallback(task_type, agent):
    """Busca fallback en MODEL_FALLBACK_CHAIN cuando el primario no está disponible."""
    rule = TASK_MODEL_MAP.get(task_type, TASK_MODEL_MAP["general"])
    chain = MODEL_FALLBACK_CHAIN.get(rule["model"], [rule["model"]])
    for fb_model in chain:
        if fb_model != rule["model"] and _CIRCUIT_BREAKER.is_available(fb_model):
            fb_thinking = rule["thinking"] if fb_model == "go-pro" else None
            fb_tier = "pro" if fb_model == "go-pro" else "flash"
            return {"model": fb_model, "thinking": fb_thinking, "tier": fb_tier, "resolved_by": f"fallback_from_{rule['model']}"}
    return {"model": "go-flash", "thinking": None, "tier": "flash", "resolved_by": "last_resort_fallback"}


# ── Token Budget ────────────────────────────────────────────

def allocate(task_type: str, content_size: int, model: str = "flash") -> int:
    base = min(content_size, BUDGETS[model]["optimal"])
    heavy_tasks = {"synthesize", "strategy", "adr", "analyze"}
    if task_type in heavy_tasks:
        return min(content_size + 4096, BUDGETS[model]["max"])
    return max(BUDGETS[model]["min"], base)


# ── Output Config ───────────────────────────────────────────

def get_output_config(use_json: bool, thinking: str | None) -> dict:
    if use_json and thinking is None:
        return {"response_format": {"type": "json_object"}}
    return {}


# ── LangFuse Integration (optional) ─────────────────────────
# Para activar: pip install langfuse y agregar:
#   from langfuse.decorators import observe
#   @observe(name="dsol.call_api")
# antes de la definición de call_api()
# Configurar env: LANGFUSE_PUBLIC_KEY, LANGFUSE_SECRET_KEY, LANGFUSE_HOST=http://127.0.0.1:3000

# ── DeepSeek API Client ─────────────────────────────────────

def _get_api_key() -> str | None:
    return os.environ.get("DEEPSEEK_API_KEY") or None


def call_api(
    prompt: list[dict],
    model: str = "flash",
    thinking: str | None = None,
    use_json: bool = False,
    task_type: str = "general",
    max_retries: int = 2,
) -> dict:
    """Call DeepSeek API with retries. Returns {text, usage} or {error}."""
    import time
    api_key = _get_api_key()
    if not api_key:
        return {"error": "DEEPSEEK_API_KEY not set", "fallback": True}

    MODEL_MAP = {"flash": "deepseek-chat", "pro": "deepseek-reasoner"}
    model_name = MODEL_MAP.get(model, "deepseek-chat")
    prompt_tokens_est = sum(len(m["content"]) for m in prompt)

    body = {
        "model": model_name,
        "messages": prompt,
        "max_tokens": allocate(task_type, prompt_tokens_est, model),
        **configure_thinking(thinking),
        **get_output_config(use_json, thinking),
    }

    last_error = None
    for attempt in range(max_retries + 1):
        # DeepSeek requires the word 'json' in the prompt when response_format is json_object
        if use_json and thinking is None:
            prompt_content = body["messages"][-1]["content"]
            if "json" not in prompt_content.lower()[:200]:
                body["messages"][-1]["content"] += "\n\nRespond in JSON format."

        try:
            import requests
            resp = requests.post(
                DEEPSEEK_API_URL,
                headers={"Authorization": f"Bearer {api_key}", "Content-Type": "application/json"},
                json=body,
                timeout=120 if task_type != "extract" else 30,
            )
            resp.raise_for_status()
            data = resp.json()
            break
        except Exception as e:
            last_error = str(e)
            if attempt < max_retries:
                time.sleep(1 * (attempt + 1))
                continue
            return {"error": last_error, "fallback": True}

    choice = data.get("choices", [{}])[0].get("message", {})
    text = choice.get("content", "")
    usage_raw = data.get("usage", {})

    # Track tokens
    tracker = TokenTracker()
    tracker.track(
        prompt_tokens=usage_raw.get("prompt_tokens", 0),
        completion_tokens=usage_raw.get("completion_tokens", 0),
        cache_hit=usage_raw.get("prompt_cache_hit_tokens", 0),
        cache_miss=usage_raw.get("prompt_cache_miss_tokens", 0),
        reasoning=usage_raw.get("completion_tokens_details", {}).get("reasoning_tokens", 0),
        model=model,
        task=task_type,
    )

    return {
        "text": text,
        "usage": extract_cache_metrics(data),
    }


# ── Multi-Model Router: Entry Point ─────────────────────────

def chat(task_type: str, messages: list[dict], agent: str = "",
         model: str = None, thinking: str = None,
         temperature: float = 0.2, max_tokens: int = None) -> str:
    """High-level chat con ruteo automático multi-modelo via OpenCode Go.

    Args:
        task_type: Tipo de tarea (lint, research, strategy, etc.)
        messages: Mensajes estilo OpenAI [{"role":..., "content":...}]
        agent: Nombre del agente (para tracking y defaults)
        model: Override explícito de modelo (go-flash, go-pro, go-kimi-latest)
        thinking: Override de thinking level
        temperature: Temperatura para la generación
        max_tokens: Límite de tokens de respuesta

    Returns:
        str: Contenido de la respuesta, o "# LLM Error: ..." en caso de error
    """
    resolved = resolve_model(
        task_type=task_type,
        agent=agent,
        model_override=model,
    )
    thinking_level = thinking if thinking is not None else resolved["thinking"]
    model_key = resolved["model"]

    system = next((m["content"] for m in messages if m["role"] == "system"), "")
    user = next((m["content"] for m in messages if m["role"] == "user"), "")
    prompt_parts = [p for p in [system, user] if p]
    prompt = "\n\n".join(prompt_parts) if len(prompt_parts) > 1 else (prompt_parts[0] if prompt_parts else "")

    from lib.llm import agent_llm_call
    result = agent_llm_call(
        agent=agent,
        prompt=prompt,
        model_override=model_key,
        task_type=task_type,
        temperature=temperature,
    )

    if result.startswith("# LLM Error"):
        _CIRCUIT_BREAKER.record_failure(model_key)
    else:
        _CIRCUIT_BREAKER.record_success(model_key)

    return result


def call_structured(
    task: str,
    content: str,
    vault_data: str = "",
    model: str = "flash",
    use_json: bool = True,
    max_chars: int = 12000,
) -> dict | str:
    """Build prompt, call API, return parsed result."""
    if len(content) > max_chars:
        print(f"  ⚠️ DSOL: content truncated from {len(content)} to {max_chars} chars")
    prompt = build_prompt(task, vault_data, content[:max_chars])
    result = call_api(prompt, model=model, thinking=None, use_json=use_json, task_type=task)

    if "error" in result:
        return result

    text = result["text"]
    if use_json:
        try:
            return json.loads(text)
        except json.JSONDecodeError:
            return {"error": "JSON parse failed", "text": text, "fallback": True}

    return text


# ── Cache Metrics ───────────────────────────────────────────

def extract_cache_metrics(response: dict) -> dict:
    usage = response.get("usage", {})
    hit = usage.get("prompt_cache_hit_tokens", 0)
    miss = usage.get("prompt_cache_miss_tokens", 0)
    total = hit + miss
    prompt_total = usage.get("prompt_tokens", total)
    reasoning = usage.get("completion_tokens_details", {}).get("reasoning_tokens", 0)
    completion = usage.get("completion_tokens", 0)

    flash_rates = {"input": 0.00014, "cache_read": 0.000028, "output": 0.00028}
    cost = (miss * flash_rates["input"] + hit * flash_rates["cache_read"]
            + completion * flash_rates["output"])

    return {
        "cache_hit_rate": round(hit / total * 100, 1) if total > 0 else 0,
        "prompt_tokens": prompt_total,
        "cache_hit_tokens": hit,
        "cache_miss_tokens": miss,
        "completion_tokens": completion,
        "reasoning_tokens": reasoning,
        "estimated_cost_usd": round(cost, 6),
    }


# ── Token Tracker ───────────────────────────────────────────

class TokenTracker:
    """Persistent token usage tracker with batch writes.
    
    Accumulates entries in memory and flushes to disk every FLUSH_INTERVAL calls
    to avoid excessive I/O on the hot path.
    """

    FLUSH_INTERVAL = 10

    def __init__(self):
        self.path = TOKEN_CACHE
        self.path.parent.mkdir(parents=True, exist_ok=True)
        self.data = self._load()
        self._pending = 0

    def _load(self) -> dict:
        if self.path.exists():
            try:
                return json.loads(self.path.read_text(encoding="utf-8"))
            except Exception as e:
                _LOG.warning("TokenTracker: error loading cache: %s", e)
        return {"version": 2, "sessions": [], "totals": {}, "daily": {}}

    def _save(self):
        self.path.write_text(json.dumps(self.data, ensure_ascii=False, indent=2), encoding="utf-8")

    def flush(self):
        if self._pending > 0:
            self._save()
            self._pending = 0

    def track(self, prompt_tokens=0, completion_tokens=0, cache_hit=0, cache_miss=0,
              reasoning=0, model="flash", task="general", agent=""):
        today = date.today().isoformat()
        now = datetime.now().isoformat()
        cost = self._calc_cost(prompt_tokens, completion_tokens, cache_hit, cache_miss, model)

        entry = {
            "timestamp": now,
            "model": model,
            "agent": agent,
            "task": task,
            "prompt_tokens": prompt_tokens,
            "completion_tokens": completion_tokens,
            "cache_hit_tokens": cache_hit,
            "cache_miss_tokens": cache_miss,
            "reasoning_tokens": reasoning,
            "cost_usd": round(cost, 6),
        }
        self.data["sessions"].append(entry)

        # Update totals
        t = self.data["totals"]
        t["prompt_tokens"] = t.get("prompt_tokens", 0) + prompt_tokens
        t["completion_tokens"] = t.get("completion_tokens", 0) + completion_tokens
        t["cache_hit_tokens"] = t.get("cache_hit_tokens", 0) + cache_hit
        t["cache_miss_tokens"] = t.get("cache_miss_tokens", 0) + cache_miss
        t["reasoning_tokens"] = t.get("reasoning_tokens", 0) + reasoning
        t["cost_usd"] = round(t.get("cost_usd", 0) + cost, 6)
        t["total_calls"] = t.get("total_calls", 0) + 1

        # Update daily
        if today not in self.data["daily"]:
            self.data["daily"][today] = {"calls": 0, "prompt_tokens": 0, "cost_usd": 0}
        d = self.data["daily"][today]
        d["calls"] += 1
        d["prompt_tokens"] += prompt_tokens
        d["cost_usd"] = round(d.get("cost_usd", 0) + cost, 6)

        self._pending += 1
        if self._pending >= self.FLUSH_INTERVAL:
            self._save()
            self._pending = 0

    def _calc_cost(self, prompt_tokens, completion_tokens, cache_hit, cache_miss, model):
        rates = {
            "flash": {"input": 0.00014, "cache_read": 0.000028, "output": 0.00028},
            "pro": {"input": 0.00174, "cache_read": 0.000145, "output": 0.00348},
            "deepseek-v4-flash": {"input": 0.00014, "cache_read": 0.000028, "output": 0.00028},
            "deepseek-v4-pro": {"input": 0.000435, "cache_read": 0.00003625, "output": 0.00087},
            "qwen3.5-plus": {"input": 0.00040, "cache_read": 0.00008, "output": 0.00240},
            "qwen3.6-plus": {"input": 0.000325, "cache_read": 0.000406, "output": 0.00195},
            "glm-5": {"input": 0.00100, "cache_read": 0.00020, "output": 0.00320},
            "glm-5.1": {"input": 0.00140, "cache_read": 0.00026, "output": 0.00440},
            "kimi-k2.5": {"input": 0.00060, "cache_read": 0.00010, "output": 0.00300},
            "kimi-k2.6": {"input": 0.00095, "cache_read": 0.00016, "output": 0.00400},
            "mimo-v2-pro": {"input": 0.00100, "cache_read": 0.00020, "output": 0.00300},
            "gemini-3.5-flash": {"input": 0.00150, "cache_read": 0.00015, "output": 0.00900},
            # OCGo model key aliases (same as deepseek direct pricing via OCGo)
            "go-flash": {"input": 0.00014, "cache_read": 0.000028, "output": 0.00028},
            "go-pro": {"input": 0.00174, "cache_read": 0.000145, "output": 0.00348},
            "go-kimi-latest": {"input": 0.00095, "cache_read": 0.00016, "output": 0.00400},
        }
        r = rates.get(model, rates.get("deepseek-v4-flash", rates["flash"]))
        return (cache_miss * r["input"] + cache_hit * r["cache_read"]
                + completion_tokens * r["output"])

    def get_stats(self) -> dict:
        per_agent = {}
        for s in self.data.get("sessions", []):
            agent = s.get("agent", "unknown")
            if agent not in per_agent:
                per_agent[agent] = {"calls": 0, "cost_usd": 0, "prompt_tokens": 0, "completion_tokens": 0}
            per_agent[agent]["calls"] += 1
            per_agent[agent]["cost_usd"] += s.get("cost_usd", 0)
            per_agent[agent]["prompt_tokens"] += s.get("prompt_tokens", 0)
            per_agent[agent]["completion_tokens"] += s.get("completion_tokens", 0)
        totals = self.data.get("totals", {})
        daily = self.data.get("daily", {})
        return {
            "total_calls": totals.get("total_calls", 0),
            "total_prompt_tokens": totals.get("prompt_tokens", 0),
            "total_completion_tokens": totals.get("completion_tokens", 0),
            "total_cache_hit_tokens": totals.get("cache_hit_tokens", 0),
            "total_cache_miss_tokens": totals.get("cache_miss_tokens", 0),
            "total_reasoning_tokens": totals.get("reasoning_tokens", 0),
            "total_cost_usd": totals.get("cost_usd", 0),
            "daily_breakdown": dict(sorted(daily.items(), reverse=True)[:7]),
            "per_agent": per_agent,
        }

    def get_daily_report(self) -> str:
        stats = self.get_stats()
        lines = [
            "## Token Usage Report",
            f"- Total API calls: {stats['total_calls']}",
            f"- Total prompt tokens: {stats['total_prompt_tokens']:,}",
            f"- Total completion tokens: {stats['total_completion_tokens']:,}",
            f"- Cache hit tokens: {stats['total_cache_hit_tokens']:,}",
            f"- Cache miss tokens: {stats['total_cache_miss_tokens']:,}",
            f"- Reasoning tokens: {stats['total_reasoning_tokens']:,}",
            f"- Total cost: ${stats['total_cost_usd']:.4f} USD",
            "",
            "### Daily Breakdown",
        ]
        for day, d in stats["daily_breakdown"].items():
            lines.append(f"- {day}: {d['calls']} calls, {d['prompt_tokens']:,} tokens, ${d['cost_usd']:.4f}")
        return "\n".join(lines)

    def get_model_breakdown(self) -> dict:
        by_model = {}
        for s in self.data.get("sessions", []):
            model = s.get("model", "unknown")
            if model not in by_model:
                by_model[model] = {
                    "calls": 0, "cost_usd": 0.0,
                    "prompt_tokens": 0, "completion_tokens": 0,
                    "cache_hit_tokens": 0, "reasoning_tokens": 0,
                    "agents": set(),
                }
            m = by_model[model]
            m["calls"] += 1
            m["cost_usd"] += s.get("cost_usd", 0)
            m["prompt_tokens"] += s.get("prompt_tokens", 0)
            m["completion_tokens"] += s.get("completion_tokens", 0)
            m["cache_hit_tokens"] += s.get("cache_hit_tokens", 0)
            m["reasoning_tokens"] += s.get("reasoning_tokens", 0)
            if s.get("agent"):
                m["agents"].add(s["agent"])
        result = {}
        for model, data in by_model.items():
            result[model] = dict(data)
            result[model]["agents"] = sorted(data["agents"])
            result[model]["cost_usd"] = round(data["cost_usd"], 6)
        return result

    def get_routing_report(self) -> str:
        model_bd = self.get_model_breakdown()
        stats = self.get_stats()
        cb_status = _CIRCUIT_BREAKER.get_status()
        lines = [
            "## Multi-Model Routing Report",
            f"- Total calls: {stats['total_calls']}",
            f"- Total cost: ${stats['total_cost_usd']:.4f}",
            "",
            "### Breakdown by Model",
        ]
        for model in ["go-flash", "go-pro", "go-kimi-latest"]:
            data = model_bd.get(model, {})
            if data:
                pct = round(data["calls"] / max(stats['total_calls'], 1) * 100, 1)
                lines.append(f"\n#### {model} ({pct}% of traffic)")
                lines.append(f"- Calls: {data['calls']} ({pct}%)")
                lines.append(f"- Cost: ${data['cost_usd']:.4f}")
                lines.append(f"- Prompt: {data['prompt_tokens']:,} | Completion: {data['completion_tokens']:,}")
                lines.append(f"- Cache hit: {data['cache_hit_tokens']:,} | Reasoning: {data['reasoning_tokens']:,}")
                lines.append(f"- Agents: {', '.join(data.get('agents', []))}")
            else:
                lines.append(f"\n#### {model} — no calls yet")
        lines.append("\n### Circuit Breaker")
        for model, s in cb_status.items():
            icon = "✅" if s["state"] == "closed" else "⚠️" if s["state"] == "half-open" else "🔴"
            lines.append(f"- {icon} {model}: {s['state']} ({s['failures']} failures)")
        return "\n".join(lines)


# ── Structured JSON Generation ───────────────────────────────

def generate_structured(prompt: str, json_schema: dict = None) -> dict:
    """Generate structured JSON output from DeepSeek.
    
    Args:
        prompt: The prompt to send
        json_schema: Optional JSON schema for validation
    
    Returns:
        Parsed JSON dict, or {"error": msg} on failure
    """
    api_key = _get_api_key()
    if not api_key:
        return {"error": "DEEPSEEK_API_KEY not configured"}
    
    from openai import OpenAI
    client = OpenAI(api_key=api_key, base_url=DEEPSEEK_API_URL)
    
    messages = [{"role": "user", "content": prompt}]
    kwargs = {
        "model": "deepseek-v4-flash",
        "messages": messages,
        "max_tokens": 4000,
    }
    
    try:
        kwargs["response_format"] = {"type": "json_object"}
        response = client.chat.completions.create(**kwargs)
        content = response.choices[0].message.content
        parsed = json.loads(content)
        return parsed
    except json.JSONDecodeError:
        return {"error": "Failed to parse JSON response", "raw": content}
    except Exception as e:
        return {"error": str(e)}


# ── CLI ─────────────────────────────────────────────────────

def status() -> str:
    tracker = TokenTracker()
    stats = tracker.get_stats()
    api_key = _get_api_key()
    cb_status = _CIRCUIT_BREAKER.get_status()
    model_bd = tracker.get_model_breakdown()
    lines = [
        "## DeepSeek Optimization Layer v2 — Multi-Model Router",
        f"- API Key (DeepSeek): {'✅' if api_key else '❌'}",
        f"- API Endpoint: {DEEPSEEK_API_URL}",
        f"- Default model: go-flash",
        f"- Models: go-flash, go-pro, go-kimi-latest (via OpenCode Go)",
        f"- Thinking modes: None, high, xmax",
        f"- Total calls tracked: {stats['total_calls']}",
        f"- Total cost: ${stats['total_cost_usd']:.4f} USD",
        "",
        "### Router: Task → Model Mapping",
    ]
    for task, rule in sorted(TASK_MODEL_MAP.items()):
        lines.append(f"- {task}: → {rule['model']} (thinking={rule['thinking']})")
    lines.append("")
    lines.append("### Budgets")
    for model, b in BUDGETS.items():
        lines.append(f"- {model}: min={b['min']}, optimal={b['optimal']}, max={b['max']}")
    lines.append("")
    lines.append("### Traffic Distribution (tracked)")
    for model in ["go-flash", "go-pro", "go-kimi-latest"]:
        data = model_bd.get(model, {})
        if data:
            pct = round(data["calls"] / max(stats['total_calls'], 1) * 100, 1)
            lines.append(f"- {model}: {data['calls']} calls ({pct}%), ${data['cost_usd']:.4f}")
    lines.append("")
    lines.append("### Circuit Breaker")
    if any(s["state"] != "closed" for s in cb_status.values()):
        for model, s in cb_status.items():
            icon = "✅" if s["state"] == "closed" else "⚠️" if s["state"] == "half-open" else "🔴"
            lines.append(f"- {icon} {model}: {s['state']} ({s['failures']} failures)")
    else:
        lines.append("- All models: ✅ closed")
    lines.append("")
    lines.append("### Thinking Config")
    for level, cfg in THINKING_CONFIG.items():
        lines.append(f"- {level}: {cfg['description']}")
    return "\n".join(lines)


def reset_tracker() -> str:
    tracker = TokenTracker()
    tracker.data = {"version": 2, "sessions": [], "totals": {}, "daily": {}}
    tracker._save()
    return "Token usage data reset."
