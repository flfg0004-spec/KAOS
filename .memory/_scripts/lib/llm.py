"""Unified LLM Client — OpenCode Go + DeepSeek with fallback routing."""
from openai import OpenAI
from lib.config import DEEPSEEK_API_KEY, OPENCODE_GO_KEY, OPENCODE_GO_ENDPOINT, LLM_FALLBACK_ENABLED

DEEPSEEK_ENDPOINT = "https://api.deepseek.com/v1"

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
    "planner": "Eres Planner, orquestador de KAOS. Descompones tareas complejas en subtasks manejables con routing y prioridades.",
}

AGENT_MODELS = {
    "aletheia": "go-qwen",
    "kosmos": "go-pro",
    "metis": "go-glm",
    "kratos": "go-gemini-flash",
    "mnemosyne": "go-gemini-flash",
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
    return OpenAI(api_key=DEEPSEEK_API_KEY, base_url=DEEPSEEK_ENDPOINT)


def _llm_call_impl(prompt: str, system: str = "", model: str = "go-flash",
                   temperature: float = 0.2, max_tokens: int = 16384) -> tuple[str, dict]:
    """Returns (content, usage_dict) — usage captures token counts from API response."""
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
        if LLM_FALLBACK_ENABLED and cfg["provider"] != "opencode-go":
            fallback_client = get_client("opencode-go")
            fallback_model = MODELS.get("go-flash", MODELS["go-flash"])
            try:
                resp2 = fallback_client.chat.completions.create(
                    model=fallback_model["model"],
                    messages=messages,
                    temperature=temperature,
                    max_tokens=max_tokens,
                    timeout=120,
                )
                content = resp2.choices[0].message.content or ""
                return content, {"error": None, "model": fallback_model["model"], "provider": "opencode-go"}
            except Exception as e2:
                return f"# LLM Error: {e} (fallback: {e2})", {"error": str(e2)}
        return f"# LLM Error: {e}", {"error": str(e)}


def llm_call(prompt: str, system: str = "", model: str = "go-flash",
             temperature: float = 0.2, max_tokens: int = 16384) -> str:
    """Returns content only (backward compatible wrapper)."""
    content, _ = _llm_call_impl(prompt, system, model, temperature, max_tokens)
    return content


def agent_llm_call(agent: str, prompt: str, temperature: float = None, step_type: str = None, model_override: str = "") -> str:
    """Agent-aware LLM call with token tracking via TokenTracker.
    
    Args:
        agent: Agent name
        prompt: Prompt to send
        temperature: Override temperature. If None, uses agent default or step_type.
        step_type: For metis: "analysis", "generation", "review", or "routing"
        model_override: If set, use this model instead of AGENT_MODELS[agent]
    """
    model_key = model_override if model_override else AGENT_MODELS.get(agent, "go-flash")
    system = SYSTEM_PROMPTS.get(agent, "")
    if temperature is None and agent == "metis" and step_type:
        step_temps = METIS_TEMPERATURES
        temperature = step_temps.get(step_type, 0.2)
    if temperature is None:
        temperature = 0.2
    content, usage = _llm_call_impl(prompt=prompt, system=system, model=model_key, temperature=temperature)

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
            task=f"agent_{agent}",
        )
    except Exception:
        pass

    return content


def get_available_models() -> list[str]:
    return list(MODELS.keys())
