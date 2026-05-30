ROUTER9_BASE_URL = "http://localhost:20128/v1"
DEFAULT_MODEL = "router9-default"

ROUTER9_MODELS = {
    "router9-minimax": {
        "input": 0.0000002,
        "output": 0.0000002,
        "cache_read": 0.00000004,
        "description": "MiniMax M2.7 via 9Router — cheapest, $0.2/1M",
    },
    "router9-glm": {
        "input": 0.0000006,
        "output": 0.0000006,
        "cache_read": 0.00000012,
        "description": "GLM-5.1 via 9Router — cheap backup, $0.6/1M",
    },
    "router9-default": {
        "input": 0.000001,
        "output": 0.000002,
        "cache_read": 0.0000002,
        "description": "9Router default — falls through to configured fallback chain",
    },
}

import os

import requests
from openai import OpenAI

from . import BaseLLMProvider


class Router9Client(BaseLLMProvider):
    """OpenAI-compatible client for 9Router proxy.

    Connects to localhost:20128/v1 and routes through 9Router's
    40+ provider network with auto-fallback.
    """

    def __init__(self, base_url: str = None):
        self.base_url = base_url or ROUTER9_BASE_URL
        self._client = OpenAI(api_key=os.environ.get("ROUTER9_API_KEY", "9router"), base_url=self.base_url)

    def chat(self, messages: list, model: str = None, temperature: float = 0.2, max_tokens: int = None) -> dict:
        """OpenAI-compatible chat completion via 9Router."""
        if model is None:
            model = DEFAULT_MODEL
        kwargs = {"model": model, "messages": messages, "temperature": temperature}
        if max_tokens:
            kwargs["max_tokens"] = max_tokens
        try:
            resp = self._client.chat.completions.create(**kwargs)
            return {
                "text": resp.choices[0].message.content or "",
                "usage": {
                    "prompt_tokens": resp.usage.prompt_tokens if resp.usage else 0,
                    "completion_tokens": resp.usage.completion_tokens if resp.usage else 0,
                    "total_tokens": resp.usage.total_tokens if resp.usage else 0,
                },
                "model": resp.model,
            }
        except Exception as e:
            return {"error": str(e), "text": ""}

    def cost_of(self, model: str, prompt_tokens: int, completion_tokens: int, cache_hit: int = 0) -> float:
        """Calculate cost for given model and token usage using ROUTER9_MODELS pricing.

        Args:
            model: Model name (e.g. 'router9-minimax').
            prompt_tokens: Number of input tokens.
            completion_tokens: Number of output tokens.
            cache_hit: Number of tokens served from cache.

        Returns:
            Cost in USD.
        """
        rates = ROUTER9_MODELS.get(model, ROUTER9_MODELS.get(DEFAULT_MODEL, {}))
        input_cost = prompt_tokens * rates.get("input", 0)
        output_cost = completion_tokens * rates.get("output", 0)
        cache_savings = cache_hit * rates.get("cache_read", 0)
        return round(input_cost + output_cost - cache_savings, 10)

    def list_models(self) -> list:
        """List available models from 9Router endpoint."""
        try:
            resp = requests.get(f"{self.base_url}/models", timeout=5)
            if resp.status_code == 200:
                return resp.json().get("data", [])
            return []
        except Exception:
            return []


def chat_via_router9(messages: list, model: str = None, **kwargs) -> str:
    """Quick chat via 9Router. Returns text or empty string on error."""
    client = Router9Client()
    result = client.chat(messages, model=model, **kwargs)
    if "error" in result:
        return ""
    return result.get("text", "")


def get_fallback_chain_entry() -> dict:
    """Returns fallback chain entry for 9Router models.

    This can be merged into MODEL_FALLBACK_CHAIN to add
    9Router as an ultra-cheap last-resort fallback.
    """
    return {
        "router9-default": ["router9-default", "router9-minimax", "router9-glm"],
        "router9-minimax": ["router9-minimax", "router9-glm"],
        "router9-glm": ["router9-glm"],
    }
