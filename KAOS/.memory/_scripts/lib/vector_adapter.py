"""Vector store adapter — abstract interface for vector storage backends."""
from abc import ABC, abstractmethod
from typing import Optional


class VectorStoreAdapter(ABC):
    @abstractmethod
    def search(self, text: str, top_k: int = 5) -> list[dict]:
        ...

    @abstractmethod
    def embed(self, doc_id: str, text: str) -> Optional[str]:
        ...

    @abstractmethod
    def delete(self, doc_id: str) -> None:
        ...

    @abstractmethod
    def status(self) -> dict:
        ...

    @abstractmethod
    def health(self) -> dict:
        ...
