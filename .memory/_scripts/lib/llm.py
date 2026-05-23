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
    "metis": "go-flash",
    "kratos": "deepseek-flash",
    "mnemosyne": "go-qwen",
    "critic": "go-flash",
    "planner": "go-flash",
}


def get_client(provider: str = "deepseek") -> OpenAI:
    if provider == "opencode-go":
        return OpenAI(api_key=OPENCODE_GO_KEY, base_url=OPENCODE_GO_ENDPOINT)
    return OpenAI(api_key=DEEPSEEK_API_KEY, base_url=DEEPSEEK_ENDPOINT)


def llm_call(prompt: str, system: str = "", model: str = "go-flash",
             temperature: float = 0.2, max_tokens: int = 16384) -> str:
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
        return resp.choices[0].message.content or ""
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
                return resp2.choices[0].message.content or ""
            except Exception as e2:
                return f"# LLM Error: {e} (fallback: {e2})"
        return f"# LLM Error: {e}"


def agent_llm_call(agent: str, prompt: str, temperature: float = 0.2) -> str:
    model_key = AGENT_MODELS.get(agent, "go-flash")
    system = SYSTEM_PROMPTS.get(agent, "")
    return llm_call(prompt=prompt, system=system, model=model_key, temperature=temperature)


def get_available_models() -> list[str]:
    return list(MODELS.keys())
