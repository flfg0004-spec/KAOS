"""Unified LLM Client — dual-provider with smart fallback.

Strategy: Optimize DeepSeek + OpenCode Go through cost tracking,
exponential backoff retry, circuit breaker, and cache warming.
"""

import hashlib
import logging
import threading
import time
from collections import OrderedDict
from collections.abc import Generator
from concurrent.futures import ThreadPoolExecutor, as_completed

import httpx
from openai import OpenAI

from lib.cache_warmer import get as _warm_get
from lib.cache_warmer import put as _warm_put
from lib.cache_warmer import save as _warm_save
from lib.config import (
    DEEPSEEK_API_KEY,
    LLM_FALLBACK_ENABLED,
    OPENCODE_GO_ENDPOINT,
    OPENCODE_GO_KEY,
    XIAOMI_API_ENDPOINT,
    XIAOMI_API_KEY,
)
from lib.cost_optimizer import (
    backoff_delay,
    provider_available,
    record_cache_hit,
    record_cache_miss,
    record_provider_result,
    track_call,
)

_LOG = logging.getLogger(__name__)

_LLM_CACHE: OrderedDict[str, tuple[str, dict]] = OrderedDict()
_LLM_CACHE_MAXSIZE = 100
_LLM_CACHE_LOCK: threading.Lock = threading.Lock()


def _cache_key(system: str, prompt: str, model: str, temperature: float) -> str:
    raw = f"{system}|{prompt}|{model}|{temperature}"
    return hashlib.md5(raw.encode()).hexdigest()


def _cached_call(system: str, prompt: str, model: str, temperature: float, max_tokens: int) -> tuple[str, dict]:
    key = _cache_key(system, prompt, model, temperature)

    with _LLM_CACHE_LOCK:
        # Check memory cache first
        if key in _LLM_CACHE:
            _LLM_CACHE.move_to_end(key)
            record_cache_hit()
            _LOG.debug("LLM cache hit (memory) for model=%s", model)
            return _LLM_CACHE[key]

        # Check persistent cache
        warm_entry = _warm_get(key)
        if warm_entry:
            _LLM_CACHE[key] = warm_entry
            record_cache_hit()
            _LOG.debug("LLM cache hit (disk) for model=%s", model)
            return warm_entry

    record_cache_miss()
    content, usage = _llm_call_impl(prompt, system, model, temperature, max_tokens)
    with _LLM_CACHE_LOCK:
        if not usage.get("error"):
            _LLM_CACHE[key] = (content, usage)
            _LLM_CACHE.move_to_end(key)
            _warm_put(key, content, usage)
            _warm_save()
            if len(_LLM_CACHE) > _LLM_CACHE_MAXSIZE:
                _LLM_CACHE.popitem(last=False)
    return content, usage


DEEPSEEK_ENDPOINT = "https://api.deepseek.com/v1"
OPENROUTER_ENDPOINT = "https://openrouter.ai/api/v1"
XIAOMI_ENDPOINT = "https://api.momoai.com/v1"

PROVIDER_CHAIN = [
    {"name": "opencode-go", "priority": 1, "timeout": 30},
    {"name": "deepseek", "priority": 2, "timeout": 30},
    {"name": "xiaomi", "priority": 3, "timeout": 30},
]

MODELS = {
    "deepseek-flash": {"provider": "deepseek", "model": "deepseek-v4-flash"},
    "deepseek-pro": {"provider": "deepseek", "model": "deepseek-v4-pro"},
    "go-flash": {"provider": "opencode-go", "model": "deepseek-v4-flash"},
    "go-pro": {"provider": "opencode-go", "model": "deepseek-v4-pro"},
    "go-qwen": {"provider": "opencode-go", "model": "qwen3.5-plus"},
    "go-qwen-latest": {"provider": "opencode-go", "model": "qwen3.6-plus"},
    "go-glm": {"provider": "opencode-go", "model": "glm-5"},
    "go-glm-latest": {"provider": "opencode-go", "model": "glm-5.1"},
    "go-kimi": {"provider": "opencode-go", "model": "kimi-k2.5"},
    "go-kimi-latest": {"provider": "opencode-go", "model": "kimi-k2.6"},
    "go-mimo": {"provider": "opencode-go", "model": "mimo-v2-pro"},
    # Direct providers
    "mimo-direct": {"provider": "xiaomi", "model": "mimo-v2.5-pro"},
    # DeepSeek direct (failover rápido)
    "deepseek-direct-flash": {"provider": "deepseek", "model": "deepseek-v4-flash"},
    "deepseek-direct-pro": {"provider": "deepseek", "model": "deepseek-v4-pro"},
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
    "critic": "go-pro",
    "planner": "go-flash",
}

ALETHEIA_PROFILE_MODELS = {
    "flash": "go-flash",
    "standard": "go-pro",
    "deep": "go-kimi-latest",
    "massive": "go-pro",
    "estrategico": "go-kimi-latest",
}

METIS_TEMPERATURES = {
    "analysis": 0.2,  # FODA, diagnóstico, estructuración
    "generation": 0.4,  # OKRs, roadmaps, iniciativas
    "review": 0.2,  # Revisión, crítica, refinamiento
    "routing": 0.1,  # Decisión de siguiente paso
}

DEFAULT_STEP_TEMPERATURES = {
    "metis": METIS_TEMPERATURES,
}


class XiaomiApiKeyAuth(httpx.Auth):
    """Custom auth: MiMo expects 'api-key' header, not 'Authorization: Bearer'."""

    requires_request_body = False

    def __init__(self, api_key: str):
        self.api_key = api_key

    def auth_flow(self, request: httpx.Request) -> Generator[httpx.Request, httpx.Response, None]:
        request.headers.pop("Authorization", None)
        request.headers["api-key"] = self.api_key
        request.headers["User-Agent"] = "claude-code/1.0"
        yield request


def get_xiaomi_client() -> OpenAI:
    """OpenAI-compatible client for Xiaomi MiMo with custom api-key auth."""
    custom_http_client = httpx.Client(
        base_url=XIAOMI_API_ENDPOINT,
        auth=XiaomiApiKeyAuth(XIAOMI_API_KEY),
        timeout=httpx.Timeout(30.0, connect=10.0),
    )
    return OpenAI(
        api_key="",
        base_url=XIAOMI_API_ENDPOINT,
        http_client=custom_http_client,
    )


def get_client(provider: str = "deepseek") -> OpenAI:
    if provider == "opencode-go":
        return OpenAI(api_key=OPENCODE_GO_KEY, base_url=OPENCODE_GO_ENDPOINT)
    if provider == "xiaomi":
        return get_xiaomi_client()
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
        "cached_tokens": (
            resp.usage.prompt_tokens_details.cached_tokens if resp.usage and resp.usage.prompt_tokens_details else 0
        ),
        "reasoning_tokens": (
            resp.usage.completion_tokens_details.reasoning_tokens
            if resp.usage and resp.usage.completion_tokens_details
            else 0
        ),
        "model": resp.model,
        "provider": provider_name,
    }


def _try_provider(
    provider_name: str, messages: list[dict], temperature: float, max_tokens: int, attempt: int = 0
) -> tuple[str, dict] | None:
    if not provider_available(provider_name):
        _LOG.debug("Provider %s blocked by circuit breaker", provider_name)
        return None
    if attempt > 0:
        delay = backoff_delay(attempt)
        _LOG.info("Retry %d for %s in %.1fs", attempt, provider_name, delay)
        time.sleep(delay)
    client = get_client(provider_name)
    if client is None:
        return None
    try:
        resp = client.chat.completions.create(
            model=_resolve_model(provider_name),
            messages=messages,
            temperature=temperature,
            max_tokens=max_tokens,
            timeout=30,
        )
        content = resp.choices[0].message.content or ""
        usage = _extract_usage(resp, provider_name)
        record_provider_result(provider_name, True)
        track_call(
            provider_name,
            resp.model or _resolve_model(provider_name),
            usage.get("prompt_tokens", 0),
            usage.get("completion_tokens", 0),
        )
        return content, usage
    except Exception as e:
        record_provider_result(provider_name, False)
        raise e


MAX_RETRIES = 3


def _llm_call_impl(
    prompt: str, system: str = "", model: str = "go-flash", temperature: float = 0.2, max_tokens: int = 16384
) -> tuple[str, dict]:
    """Returns (content, usage_dict) — retry with exponential backoff, then fallback."""
    cfg = MODELS.get(model, MODELS["go-flash"])
    messages = _build_messages(system, prompt)
    primary_provider = cfg["provider"]

    providers_to_try = [primary_provider]
    if LLM_FALLBACK_ENABLED:
        for p in PROVIDER_CHAIN:
            if p["name"] not in providers_to_try:
                providers_to_try.append(p["name"])

    # Retry primary with exponential backoff
    last_error = ""
    for attempt in range(MAX_RETRIES):
        try:
            content, usage = _try_provider(primary_provider, messages, temperature, max_tokens, attempt)
            return content, usage
        except Exception as e:
            last_error = str(e)[:80]
            _LOG.warning("Primary %s attempt %d/%d failed: %s", primary_provider, attempt + 1, MAX_RETRIES, last_error)

    # Parallel fallback: launch all remaining providers, take first success
    fallbacks = [p for p in providers_to_try if p != primary_provider]
    if not fallbacks:
        return f"# LLM Error: {last_error}", {"error": last_error}

    with ThreadPoolExecutor(max_workers=len(fallbacks)) as executor:
        futures = {executor.submit(_try_provider, p, messages, temperature, max_tokens): p for p in fallbacks}
        for future in as_completed(futures):
            provider = futures[future]
            try:
                content, usage = future.result()
                _LOG.info("LLM fallback to %s succeeded", provider)
                return content, usage
            except Exception as e:
                _LOG.warning("LLM fallback %s failed: %s", provider, str(e)[:80])
                continue

    return f"# LLM Error: {last_error}", {"error": last_error}


def _resolve_model(provider: str) -> str:
    mapping = {
        "opencode-go": "qwen3.5-plus",
        "deepseek": "deepseek-chat",
        "xiaomi": "mimo-v2.5-pro",
    }
    return mapping.get(provider, "qwen3.5-plus")


def llm_call(
    prompt: str, system: str = "", model: str = "go-flash", temperature: float = 0.2, max_tokens: int = 16384
) -> str:
    """Returns content only (backward compatible wrapper)."""
    content, _ = _cached_call(system, prompt, model, temperature, max_tokens)
    return content


def agent_llm_call(
    agent: str,
    prompt: str,
    temperature: float = None,
    step_type: str = None,
    model_override: str = "",
    task_type: str = None,
) -> str:
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
        try:
            from lib.aether.router import resolve_model
        except ImportError:
            resolve_model = lambda **kw: {"model": model_override or AGENT_MODELS.get(agent, "go-flash")}

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
    content, usage = _cached_call(
        system=system, prompt=prompt, model=model_key, temperature=temperature, max_tokens=16384
    )

    try:
        from lib.aether.tracker import EtherTracker as TokenTracker

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
    except ImportError:
        pass

    return content


def get_available_models() -> list[str]:
    return list(MODELS.keys())
