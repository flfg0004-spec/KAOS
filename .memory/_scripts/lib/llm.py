"""Unified LLM Client — multi-provider with fallback chain."""
import hashlib
import logging
from collections import OrderedDict
from concurrent.futures import ThreadPoolExecutor, as_completed
from openai import OpenAI
from lib.config import DEEPSEEK_API_KEY, OPENCODE_GO_KEY, OPENCODE_GO_ENDPOINT, LLM_FALLBACK_ENABLED

_LOG = logging.getLogger(__name__)

_LLM_CACHE: OrderedDict[str, tuple[str, dict]] = OrderedDict()
_LLM_CACHE_MAXSIZE = 100

def _cache_key(system: str, prompt: str, model: str, temperature: float) -> str:
    raw = f"{system}|{prompt}|{model}|{temperature}"
    return hashlib.md5(raw.encode()).hexdigest()

def _cached_call(system: str, prompt: str, model: str, temperature: float, max_tokens: int) -> tuple[str, dict]:
    key = _cache_key(system, prompt, model, temperature)
    if key in _LLM_CACHE:
        _LLM_CACHE.move_to_end(key)
        _LOG.debug("LLM cache hit for model=%s", model)
        return _LLM_CACHE[key]
    content, usage = _llm_call_impl(prompt, system, model, temperature, max_tokens)
    if not usage.get("error"):
        _LLM_CACHE[key] = (content, usage)
        _LLM_CACHE.move_to_end(key)
        if len(_LLM_CACHE) > _LLM_CACHE_MAXSIZE:
            _LLM_CACHE.popitem(last=False)
    return content, usage

DEEPSEEK_ENDPOINT = "https://api.deepseek.com/v1"
OPENROUTER_ENDPOINT = "https://openrouter.ai/api/v1"

PROVIDER_CHAIN = [
    {"name": "opencode-go", "priority": 1, "timeout": 30},
    {"name": "deepseek", "priority": 2, "timeout": 30},
    {"name": "openrouter", "priority": 3, "timeout": 30},
]

MODELS = {
    "deepseek-flash": {"provider": "deepseek", "model": "deepseek-v4-flash"},
    "deepseek-pro":   {"provider": "deepseek", "model": "deepseek-v4-pro"},
    "go-flash":       {"provider": "opencode-go", "model": "deepseek-v4-flash"},
    "go-pro":         {"provider": "opencode-go", "model": "deepseek-v4-pro"},
    "go-qwen":        {"provider": "opencode-go", "model": "qwen3.5-plus"},
    "go-qwen-latest": {"provider": "opencode-go", "model": "qwen3.6-plus"},
    "go-glm":         {"provider": "opencode-go", "model": "glm-5"},
    "go-glm-latest":  {"provider": "opencode-go", "model": "glm-5.1"},
    "go-kimi":        {"provider": "opencode-go", "model": "kimi-k2.5"},
    "go-kimi-latest": {"provider": "opencode-go", "model": "kimi-k2.6"},
    "go-mimo":        {"provider": "opencode-go", "model": "mimo-v2-pro"},
    "go-gemini-flash": {"provider": "opencode-go", "model": "gemini-3.5-flash"},
}

SYSTEM_PROMPTS = {
    "aletheia": "Eres Aletheia, agente de investigación de KAOS. Produces informes detallados con fuentes, evidencia y análisis estructurado en markdown.",
    "kosmos": "Eres Kosmos, arquitecto de software de KAOS. Produces ADRs, diagramas C4 y recomendaciones arquitectónicas detalladas.",
    "metis": "Eres Metis, estratega de KAOS. Sintetizas investigación y análisis en planes estratégicos con OKRs, roadmap y riesgos.",
    "kratos": "Eres Kratos, ingeniero de KAOS. Implementas código, escribes tests y documentas cambios siguiendo las mejores prácticas.",
    "mnemosyne": "Eres Mnemosyne, curadora de conocimiento de KAOS. Revisas calidad, actualizas wikilinks y mantienes el índice de conocimiento.",
    "critic": "Eres Critic, evaluador de calidad de KAOS. Evalúas salidas de agents por estructura, contenido y valor.",
    "bcg": "Eres BCG Evaluator, especialista en evaluación de outputs estratégicos. Usas la rúbrica de 8 dimensiones de BCG: estructura, manejo de ambigüedad, priorización, rigor, originalidad, síntesis ejecutiva, independencia y accionabilidad. Escala 0-5.",
    "planner": "Eres Planner, orquestador de KAOS. Descompones tareas complejas en subtasks manejables con routing y prioridades.",
}

AGENT_MODELS = {
    "aletheia": "go-pro",
    "kosmos": "go-flash",
    "metis": "go-kimi-latest",
    "kratos": "go-flash",
    "mnemosyne": "go-flash",
    "critic": "go-flash",
    "planner": "go-flash",
}

METIS_TEMPERATURES = {
    "analysis": 0.2,      # FODA, diagnóstico, estructuración
    "generation": 0.4,    # OKRs, roadmaps, iniciativas
    "review": 0.2,        # Revisión, crítica, refinamiento
    "routing": 0.1,       # Decisión de siguiente paso
}

DEFAULT_STEP_TEMPERATURES = {
    "metis": METIS_TEMPERATURES,
}


def get_client(provider: str = "deepseek") -> OpenAI:
    if provider == "opencode-go":
        return OpenAI(api_key=OPENCODE_GO_KEY, base_url=OPENCODE_GO_ENDPOINT)
    if provider == "openrouter":
        key = __import__("os").environ.get("OPENROUTER_API_KEY", "")
        return OpenAI(api_key=key, base_url=OPENROUTER_ENDPOINT) if key else None
    return OpenAI(api_key=DEEPSEEK_API_KEY, base_url=DEEPSEEK_ENDPOINT)


def _build_messages(system: str, prompt: str) -> list[dict]:
    msgs = []
    if system:
        msgs.append({"role": "system", "content": system})
    msgs.append({"role": "user", "content": prompt})
    return msgs


def _extract_usage(resp, provider_name: str) -> dict:
    return {
        "prompt_tokens": resp.usage.prompt_tokens if resp.usage else 0,
        "completion_tokens": resp.usage.completion_tokens if resp.usage else 0,
        "total_tokens": resp.usage.total_tokens if resp.usage else 0,
        "cached_tokens": (resp.usage.prompt_tokens_details.cached_tokens
                          if resp.usage and resp.usage.prompt_tokens_details else 0),
        "reasoning_tokens": (resp.usage.completion_tokens_details.reasoning_tokens
                             if resp.usage and resp.usage.completion_tokens_details else 0),
        "model": resp.model,
        "provider": provider_name,
    }


def _try_provider(provider_name: str, messages: list[dict],
                  temperature: float, max_tokens: int) -> tuple[str, dict] | None:
    client = get_client(provider_name)
    if client is None:
        return None
    resp = client.chat.completions.create(
        model=_resolve_model(provider_name),
        messages=messages,
        temperature=temperature,
        max_tokens=max_tokens,
        timeout=30,
    )
    content = resp.choices[0].message.content or ""
    usage = _extract_usage(resp, provider_name)
    return content, usage


def _llm_call_impl(prompt: str, system: str = "", model: str = "go-flash",
                   temperature: float = 0.2, max_tokens: int = 16384) -> tuple[str, dict]:
    """Returns (content, usage_dict) — parallel fallback chain on failure."""
    cfg = MODELS.get(model, MODELS["go-flash"])
    messages = _build_messages(system, prompt)
    primary_provider = cfg["provider"]

    providers_to_try = [primary_provider]
    if LLM_FALLBACK_ENABLED:
        for p in PROVIDER_CHAIN:
            if p["name"] not in providers_to_try:
                providers_to_try.append(p["name"])

    # Try primary first with short timeout
    try:
        content, usage = _try_provider(primary_provider, messages, temperature, max_tokens)
        return content, usage
    except Exception as e:
        _LOG.warning("Primary LLM provider %s failed: %s", primary_provider, str(e)[:80])

    # Parallel fallback: launch all remaining providers, take first success
    fallbacks = [p for p in providers_to_try if p != primary_provider]
    if not fallbacks:
        return "# LLM Error: no fallback providers", {"error": "no fallbacks"}

    with ThreadPoolExecutor(max_workers=len(fallbacks)) as executor:
        futures = {
            executor.submit(_try_provider, p, messages, temperature, max_tokens): p
            for p in fallbacks
        }
        for future in as_completed(futures):
            provider = futures[future]
            try:
                content, usage = future.result()
                _LOG.info("LLM fallback to %s succeeded", provider)
                return content, usage
            except Exception as e:
                _LOG.warning("LLM fallback %s failed: %s", provider, str(e)[:80])
                continue

    return "# LLM Error: all providers failed", {"error": "all providers failed"}


def _resolve_model(provider: str) -> str:
    mapping = {
        "opencode-go": "qwen3.5-plus",
        "deepseek": "deepseek-chat",
        "openrouter": "openai/gpt-4o-mini",
    }
    return mapping.get(provider, "qwen3.5-plus")


def llm_call(prompt: str, system: str = "", model: str = "go-flash",
             temperature: float = 0.2, max_tokens: int = 16384) -> str:
    """Returns content only (backward compatible wrapper)."""
    content, _ = _cached_call(system, prompt, model, temperature, max_tokens)
    return content


def agent_llm_call(agent: str, prompt: str, temperature: float = None, step_type: str = None, model_override: str = "", task_type: str = None) -> str:
    """Agent-aware LLM call with token tracking via TokenTracker.
    
    Args:
        agent: Agent name
        prompt: Prompt to send
        temperature: Override temperature. If None, uses agent default or step_type.
        step_type: For metis: "analysis", "generation", "review", or "routing"
        model_override: If set, use this model instead of AGENT_MODELS[agent]
        task_type: If set, router resolves model via DSOL (overrides AGENT_MODELS)
    """
    if task_type:
        from lib.dsol import resolve_model
        resolved = resolve_model(task_type=task_type, agent=agent, model_override=model_override or None)
        model_key = resolved["model"]
    else:
        model_key = model_override if model_override else AGENT_MODELS.get(agent, "go-flash")
    system = SYSTEM_PROMPTS.get(agent, "")
    if temperature is None and agent == "metis" and step_type:
        step_temps = METIS_TEMPERATURES
        temperature = step_temps.get(step_type, 0.2)
    if temperature is None:
        temperature = 0.2
    content, usage = _cached_call(system=system, prompt=prompt, model=model_key, temperature=temperature, max_tokens=16384)

    try:
        from lib.dsol import TokenTracker
        tt = TokenTracker()
        tt.track(
            agent=agent,
            prompt_tokens=usage.get("prompt_tokens", 0),
            completion_tokens=usage.get("completion_tokens", 0),
            cache_hit=usage.get("cached_tokens", 0),
            reasoning=usage.get("reasoning_tokens", 0),
            model=usage.get("model", model_key),
            task=task_type or f"agent_{agent}",
        )
    except Exception:
        pass

    return content


def get_available_models() -> list[str]:
    return list(MODELS.keys())
