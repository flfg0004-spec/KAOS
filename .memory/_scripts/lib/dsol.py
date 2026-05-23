"""
DeepSeek Optimization Layer v2 — API client, token tracking, cache optimization.
Lee DEEPSEEK_API_KEY del entorno. Trackea tokens en .memory/cache/token-usage.json
"""
import json
import os
import re
from datetime import datetime, date
from pathlib import Path

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
    """Persistent token usage tracker. Stores in .memory/cache/token-usage.json"""

    def __init__(self):
        self.path = TOKEN_CACHE
        self.path.parent.mkdir(parents=True, exist_ok=True)
        self.data = self._load()

    def _load(self) -> dict:
        if self.path.exists():
            try:
                return json.loads(self.path.read_text(encoding="utf-8"))
            except Exception as e:
                print(f"  ⚠️ TokenTracker: error loading cache: {e}")
        return {"version": 2, "sessions": [], "totals": {}, "daily": {}}

    def _save(self):
        self.path.write_text(json.dumps(self.data, ensure_ascii=False, indent=2), encoding="utf-8")

    def track(self, prompt_tokens=0, completion_tokens=0, cache_hit=0, cache_miss=0,
              reasoning=0, model="flash", task="general"):
        today = date.today().isoformat()
        now = datetime.now().isoformat()
        cost = self._calc_cost(prompt_tokens, completion_tokens, cache_hit, cache_miss, model)

        entry = {
            "timestamp": now,
            "model": model,
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

        self._save()

    def _calc_cost(self, prompt_tokens, completion_tokens, cache_hit, cache_miss, model):
        rates = {"flash": {"input": 0.00014, "cache_read": 0.000028, "output": 0.00028},
                 "pro": {"input": 0.00174, "cache_read": 0.000145, "output": 0.00348}}
        r = rates.get(model, rates["flash"])
        return (cache_miss * r["input"] + cache_hit * r["cache_read"]
                + completion_tokens * r["output"])

    def get_stats(self) -> dict:
        return {
            "total_calls": self.data["totals"].get("total_calls", 0),
            "total_prompt_tokens": self.data["totals"].get("prompt_tokens", 0),
            "total_completion_tokens": self.data["totals"].get("completion_tokens", 0),
            "total_cache_hit_tokens": self.data["totals"].get("cache_hit_tokens", 0),
            "total_cache_miss_tokens": self.data["totals"].get("cache_miss_tokens", 0),
            "total_reasoning_tokens": self.data["totals"].get("reasoning_tokens", 0),
            "total_cost_usd": self.data["totals"].get("cost_usd", 0),
            "daily_breakdown": dict(sorted(self.data["daily"].items(), reverse=True)[:7]),
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
    lines = [
        "## DeepSeek Optimization Layer v2",
        f"- API Key: {'✅ configured' if api_key else '❌ not set'}",
        f"- API Endpoint: {DEEPSEEK_API_URL}",
        f"- Model: deepseek-v4-flash (default)",
        f"- Thinking modes: None, high, xmax",
        f"- Token budgets: Flash {BUDGETS['flash']}, Pro {BUDGETS['pro']}",
        f"- Cache optimization: prefix-aligned prompts",
        f"- Total calls tracked: {stats['total_calls']}",
        f"- Total cost: ${stats['total_cost_usd']:.4f} USD",
        "",
        "### Budgets",
    ]
    for model, b in BUDGETS.items():
        lines.append(f"- {model}: min={b['min']}, optimal={b['optimal']}, max={b['max']}")
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
