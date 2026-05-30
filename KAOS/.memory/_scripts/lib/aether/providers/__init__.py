"""Providers module — Abstract base class and concrete implementations for LLM providers."""

from abc import ABC, abstractmethod


class BaseLLMProvider(ABC):
    """Abstract base class for all LLM providers in Aether.

    All providers must implement chat(), list_models(), and cost_of().
    """

    @abstractmethod
    def chat(self, messages: list, model: str, **kwargs) -> dict:
        ...

    @abstractmethod
    def list_models(self) -> list[str]:
        ...

    @abstractmethod
    def cost_of(self, model: str, prompt_tokens: int, completion_tokens: int, cache_hit: int = 0) -> float:
        ...
