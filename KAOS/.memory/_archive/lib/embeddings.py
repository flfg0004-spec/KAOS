"""Vector embeddings for semantic vault search — delegates to sqlite-vec."""

from . import vectorstore

def chunk_text(text: str) -> list[str]:
    return vectorstore.chunk_text(text)


def build_index(full: bool = False) -> str:
    return vectorstore.build_index(full=full)


def query(text: str, top_k: int = 5) -> list[dict]:
    return vectorstore.query(text, top_k=top_k)


def update(path: str) -> str:
    return vectorstore.update(path)


def update_many(paths: list[str]) -> str:
    return vectorstore.update_many(paths)


def status() -> str:
    return vectorstore.status()
