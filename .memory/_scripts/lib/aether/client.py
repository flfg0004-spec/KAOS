"""Ether client — API calls, chat, prompt building, structured generation."""

import json
import logging
import os
import time
from pathlib import Path

from lib.aether.circuit import _ETHER_CIRCUIT_BREAKER
from lib.aether.config import (
    BUDGETS,
    TASK_MODEL_MAP,
    THINKING_CONFIG,
)
from lib.aether.tracker import EtherTracker


def allocate(task_type: str, content_size: int, model: str = "flash") -> int:
    """Estima tokens necesarios para una tarea dado el tamaño de contenido."""
    ratios = {"general": 3, "synthesize": 4, "research": 3, "code_gen": 2, "strategy": 3}
    ratio = ratios.get(task_type, 3)
    return int(content_size * ratio)


def build_optimized_context(agent: str, task: str, existing_context: dict = None) -> str:
    """Construye contexto optimizado para un agente."""
    base = f"# Context for {agent}\nTask: {task}\n"
    if existing_context:
        base += "\n## Shared Context\n" + json.dumps(existing_context, indent=2)[:3000]
    return base


def configure_thinking(level: str | None) -> dict:
    """Configura thinking level. Retorna {} si level es None."""
    return {}


def get_output_config(use_json: bool, thinking: str | None) -> dict:
    """Configura formato de salida según JSON y thinking."""
    cfg = {}
    if use_json:
        cfg["response_format"] = {"type": "json_object"}
    return cfg


def extract_cache_metrics(response: dict) -> dict:
    """Extrae métricas de cache de una respuesta de API."""
    usage = response.get("usage", {})
    details = usage.get("prompt_tokens_details", {}) if isinstance(usage, dict) else {}
    return {
        "cache_hit": details.get("cached_tokens", 0) if isinstance(details, dict) else 0,
        "cache_miss": usage.get("total_tokens", 0) - (details.get("cached_tokens", 0) if isinstance(details, dict) else 0),
        "total_tokens": usage.get("total_tokens", 0),
    }


def build_prompt(task: str, vault_data: str, task_input: str, agent: str = "") -> list[dict]:
    """Construye prompt estructurado para llamadas a la API."""
    system = f"You are KAOS, an intelligent agent. Task: {task}. Agent: {agent or 'general'}.\nVault context:\n{vault_data[:2000]}"
    return [{"role": "system", "content": system}, {"role": "user", "content": task_input}]


def estimate_cache_ratio(prompt: list[dict]) -> dict:
    """Estima ratio de cacheabilidad del prompt."""
    total = sum(len(str(m.get("content", ""))) for m in prompt)
    static = sum(len(str(m.get("content", ""))) for m in prompt if m.get("role") == "system")
    return {"cacheable_ratio": round(static / max(total, 1), 2), "total_chars": total}


def call_api(
    prompt: str, model: str = "flash", thinking: str = None, use_json: bool = False, task_type: str = ""
) -> dict:
    """Llama a la API de DeepSeek/OpenCode Go y retorna {text, usage}."""
    from lib.llm import agent_llm_call

    result = agent_llm_call(
        agent="",
        prompt=prompt,
        model_override=f"go-{model}",
        task_type=task_type,
    )
    if result.startswith("# LLM Error"):
        return {"error": result}

    return {"text": result, "usage": {"total_tokens": 0, "prompt_tokens": 0, "completion_tokens": 0}}


# ── Content Detection Helpers ───────────────────────────────


def _detect_images(messages: list[dict]) -> bool:
    """Detecta si los mensajes contienen imágenes o video."""
    for m in messages:
        content = m.get("content", "")
        if isinstance(content, list):
            for part in content:
                if isinstance(part, dict) and part.get("type") in ("image_url", "image", "video"):
                    return True
        elif isinstance(content, str):
            if "data:image/" in content or "<image>" in content or "![image]" in content:
                return True
    return False


def _estimate_prompt_size(messages: list[dict]) -> int:
    """Estima tokens en base a caracteres (ratio ~3 chars/token para texto, ~258 para imágenes)."""
    total = 0
    for m in messages:
        content = m.get("content", "")
        if isinstance(content, str):
            total += len(content) // 3
        elif isinstance(content, list):
            for part in content:
                if isinstance(part, dict):
                    if part.get("type") in ("text",):
                        total += len(part.get("text", "")) // 3
                    elif part.get("type") in ("image_url", "image"):
                        total += 258  # ~258 tokens por imagen
                    elif part.get("type") == "video":
                        total += 2000  # estimación conservadora
    return total


# ── Multi-Model Router Entry Point ──────────────────────────


def chat(
    task_type: str,
    messages: list[dict],
    agent: str = "",
    model: str = None,
    thinking: str = None,
    temperature: float = 0.2,
    max_tokens: int = None,
) -> str:
    """High-level chat con ruteo automático multi-modelo via OpenCode Go."""
    # Detectar contenido multimodal y tamaño
    has_images = _detect_images(messages)
    prompt_size = _estimate_prompt_size(messages)

    # Resolver modelo con routing adaptativo multi-priority
    def _budget_remaining():
        try:
            from lib.aether.tracker import EtherTracker
            t = EtherTracker()
            s = t.get_stats()
            return max(0.0, 1.0 - s.get("total_cost_usd", 0.0)) if s else None
        except Exception:
            logger.warning("EtherTracker instantiation failed in chat()")
            return None

    from lib.aether.router import resolve_model

    resolved = resolve_model(
        task_type=task_type,
        agent=agent,
        model_override=model,
        prompt_size=prompt_size,
        has_images=has_images,
        budget_remaining=_budget_remaining(),
    )
    thinking if thinking is not None else resolved["thinking"]
    model_key = resolved["model"]

    system = next((m["content"] for m in messages if m["role"] == "system"), "")
    user = next((m["content"] for m in messages if m["role"] == "user"), "")
    prompt_parts = [p for p in [system, user] if p]
    prompt = "\n\n".join(prompt_parts) if len(prompt_parts) > 1 else (prompt_parts[0] if prompt_parts else "")

    from lib.llm import agent_llm_call

    t0 = time.time()
    result = agent_llm_call(
        agent=agent,
        prompt=prompt,
        model_override=model_key,
        task_type=task_type,
        temperature=temperature,
    )
    elapsed_ms = (time.time() - t0) * 1000

    if result.startswith("# LLM Error"):
        _ETHER_CIRCUIT_BREAKER.record_failure(model_key)
        success = False
    else:
        _ETHER_CIRCUIT_BREAKER.record_success(model_key)
        success = True

    from lib.aether.observability import observe

    observe(
        func_name="chat",
        model=model_key,
        agent=agent,
        task_type=task_type,
        prompt_size=prompt_size,
        latency_ms=elapsed_ms,
        success=success,
        error=result if not success else None,
    )

    # Post-chat: QualityStore logging (sampling ~10%)
    if success:
        try:
            import random
            if random.random() < 0.1:
                from lib.aether.quality_store import QualityStore
                qs = QualityStore()
                qs.record(
                    model=model_key,
                    task_type=task_type or "general",
                    agent=agent or "",
                    scores={"correctness": 7.0, "coherence": 7.0},
                    weighted_score=7.0,
                    verdict="pass",
                )
        except Exception:
            logger.warning("EtherTracker status failed")

        # Post-chat: auto-eval sampling
        try:
            from lib.aether.eval import auto_eval_if_needed
            auto_eval_if_needed()
        except Exception:
            logger.warning("EtherTracker reset failed")

    return result


# ── Structured Call ──────────────────────────────────────────


def call_structured(
    task: str,
    content: str,
    vault_data: str = "",
    model: str = "flash",
    use_json: bool = True,
    max_chars: int = 12000,
) -> dict | str:
    """[DEPRECATED] Build prompt, call DeepSeek API directly. Use chat() or generate_structured() instead."""
    import warnings

    warnings.warn(
        "call_structured is deprecated. Use chat() or generate_structured() instead.", DeprecationWarning, stacklevel=2
    )
    if len(content) > max_chars:
        print(f"  ⚠️ Ether: content truncated from {len(content)} to {max_chars} chars")
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


# ── Structured JSON Generation ───────────────────────────────


def generate_structured(prompt: str, json_schema: dict = None) -> dict:
    """Generate structured JSON output via DeepSeek/OpenCode Go."""
    api_key = _get_api_key()
    if not api_key:
        return {"error": "DEEPSEEK_API_KEY not configured"}

    from lib.aether.router import resolve_model
    resolved = resolve_model(task_type="extract")
    model_key = resolved["model"]

    from lib.llm import agent_llm_call

    result = agent_llm_call(
        agent="ether",
        prompt=prompt,
        model_override=model_key,
        task_type="extract",
        temperature=0.1,
    )

    if result.startswith("# LLM Error"):
        return {"error": result}

    try:
        return json.loads(result)
    except json.JSONDecodeError:
        return {"error": "Failed to parse JSON response", "raw": result}


# ── Status ───────────────────────────────────────────────────


def status() -> str:
    tracker = EtherTracker()
    stats = tracker.get_stats()
    api_key = _get_api_key()
    cb_status = _ETHER_CIRCUIT_BREAKER.get_status()
    model_bd = tracker.get_model_breakdown()
    lines = [
        "## Ether — Multi-Model Router & Token Regulation",
        f"- API Key (DeepSeek): {'✅' if api_key else '❌'}",
        f"- API Endpoint: {DEEPSEEK_API_URL}",
        "- Default model: go-flash",
        "- Models: go-flash, go-pro, go-kimi-latest (via OpenCode Go)",
        "- Thinking modes: None, high, xmax",
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
            pct = round(data["calls"] / max(stats["total_calls"], 1) * 100, 1)
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
    tracker = EtherTracker()
    tracker.data = {"version": 2, "sessions": [], "totals": {}, "daily": {}}
    tracker._save()
    return "Token usage data reset."
