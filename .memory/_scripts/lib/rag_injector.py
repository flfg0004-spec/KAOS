"""RAG Injector — context enrichment from vector store for agent prompts."""
from lib.config import RAG_TOP_K
from lib.vectorstore import query as vector_query


def inject_context(topic: str, k: int = None) -> str:
    """Query vectorstore for semantically relevant chunks and format as context.

    Returns a markdown block to prepend to agent prompts, or empty string if
    no relevant context found or vectorstore unavailable.
    """
    k = max(1, k or RAG_TOP_K)
    try:
        results = vector_query(topic, top_k=k)
    except Exception:
        return ""

    if not results:
        return ""

    lines = ["\n---\n## Contexto Relevante (RAG)\n"]
    for r in results:
        path = r.get("path", "?")
        snippet = r.get("chunk_text", r.get("snippet", ""))[:400]
        lines.append(f"- [{path}]\n  {snippet}\n")
    lines.append("---\n")
    return "".join(lines)
