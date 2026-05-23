"""
KAOS Synapse Engine — Cross-linking semántico automático entre conceptos.
Usa embeddings (local o txtai) para detectar relaciones y crear [[wikilinks]] bidireccionales.
"""

import json
import re
from pathlib import Path

BASE = Path(__file__).resolve().parent.parent.parent  # .memory/
KAOS_ROOT = BASE.parent  # KAOS project root
CONCEPTS_DIR = KAOS_ROOT / ".memory" / "wiki" / "concepts"
RAW_DIR = KAOS_ROOT / ".memory" / "raw"
EMBEDDINGS_CACHE = KAOS_ROOT / ".memory" / "cache" / "embeddings.json"
SYNAPSE_INDEX = KAOS_ROOT / ".memory" / "cache" / "synapse-index.json"


def _load_embeddings() -> dict:
    """Load embeddings — delegates to vectorstore for concept entries."""
    try:
        from lib import vectorstore as vs
        entries = vs.get_all_entries()
        return {"version": 1, "entries": entries}
    except Exception:
        # Fallback to JSON file
        if EMBEDDINGS_CACHE.exists():
            try:
                return json.loads(EMBEDDINGS_CACHE.read_text(encoding="utf-8"))
            except Exception as e:
                print(f"  ⚠️ synapse: cache load error: {e}")
    return {"version": 1, "entries": []}


def _find_similar(concept_name: str, top_k: int = 3) -> list[dict]:
    """Find semantically similar concepts via cosine similarity on embeddings, with BM25 fallback."""
    index = _load_embeddings()
    if not index.get("entries"):
        return _bm25_search(concept_name, top_k)

    try:
        return _find_similar_cosine(concept_name, top_k)
    except Exception as e:
        print(f"  ⚠️ synapse: cosine similarity failed, using BM25: {e}")

    return _bm25_search(concept_name, top_k)


def _find_similar_cosine(concept_name: str, top_k: int = 3) -> list[dict]:
    """Find similar concepts using sqlite-vec vector search."""
    slug = concept_name.replace(" ", "-")
    concept_file = CONCEPTS_DIR / f"{slug}.md"
    if not concept_file.exists():
        return _bm25_search(concept_name, top_k)

    rel_path = f"wiki/concepts/{concept_file.name}"
    try:
        from lib import vectorstore as vs
        results = vs.query_vectors(rel_path, top_k=top_k)
        if results:
            return results
    except Exception as e:
        print(f"  ⚠️ synapse: vector search failed: {e}")

    return _bm25_search(concept_name, top_k)


def _bm25_search(query: str, top_k: int = 3) -> list[dict]:
    """BM25 keyword overlap search when vector embeddings aren't available."""
    query_tokens = set(query.lower().split())
    if not query_tokens:
        return []

    scores = []
    for concept_file in CONCEPTS_DIR.glob("*.md"):
        content = concept_file.read_text(encoding="utf-8")
        tokens = set(content.lower().split())
        overlap = len(query_tokens & tokens)
        if overlap > 0:
            scores.append({
                "path": f"wiki/concepts/{concept_file.name}",
                "slug": concept_file.stem,
                "score": overlap / len(query_tokens),
                "snippet": content[:200],
            })

    scores.sort(key=lambda x: x["score"], reverse=True)
    return scores[:top_k]


def _inject_wikilink(content: str, target_slug: str) -> tuple[str, bool]:
    """Inject [[wikilink]] into content if not already present."""
    link = f"[[{target_slug}]]"
    if link in content:
        return content, False

    # Add to a "## Referencias Cruzadas" section
    if "## Referencias Cruzadas" not in content:
        content += f"\n\n## Referencias Cruzadas\n"
    content += f"- Relacionado: {link}\n"
    return content, True


def cross_link(concept_slug: str) -> str:
    """
    Cross-link a concept with semantically similar existing concepts.
    1. Find similar concepts
    2. Inject [[wikilinks]] bidirectionally
    """
    concept_path = CONCEPTS_DIR / f"{concept_slug}.md"
    if not concept_path.exists():
        return f"Synapse: concept '{concept_slug}' not found"

    concept_name = concept_slug.replace("-", " ")
    similar = _find_similar(concept_name, top_k=3)

    if not similar:
        return f"Synapse: no similar concepts found for '{concept_slug}'"

    # Inject links into the new concept
    content = concept_path.read_text(encoding="utf-8")
    modified = False
    for match in similar:
        target_slug = match["slug"]
        if target_slug == concept_slug:
            continue
        content, changed = _inject_wikilink(content, target_slug)
        if changed:
            modified = True

    if modified:
        concept_path.write_text(content, encoding="utf-8")

    # Inject backlinks into existing concepts
    backlinks_added = 0
    for match in similar:
        target_slug = match["slug"]
        if target_slug == concept_slug:
            continue
        target_path = CONCEPTS_DIR / f"{target_slug}.md"
        if target_path.exists():
            target_content = target_path.read_text(encoding="utf-8")
            target_content, changed = _inject_wikilink(target_content, concept_slug)
            if changed:
                target_path.write_text(target_content, encoding="utf-8")
                backlinks_added += 1

    summary = (f"Synapse: '{concept_slug}' linked to {len(similar)} concepts"
               f" ({backlinks_added} backlinks added)")
    return summary


def cross_link_all() -> str:
    """Cross-link ALL concepts in the vault."""
    concepts = list(CONCEPTS_DIR.glob("*.md"))
    total_links = 0
    results = []
    for concept_file in concepts:
        slug = concept_file.stem
        try:
            result = cross_link(slug)
            if "linked" in result:
                total_links += 1
                results.append(result)
        except Exception as e:
            results.append(f"  ⚠️ {slug}: {e}")

    summary = f"Synapse: cross-linked {total_links}/{len(concepts)} concepts"
    return summary + "\n" + "\n".join(results[-5:])


def index_all() -> str:
    """Rebuild the full synapse index from all concepts."""
    concepts = list(CONCEPTS_DIR.glob("*.md"))
    entries = []
    for cf in concepts:
        content = cf.read_text(encoding="utf-8")
        chunks = []
        for section in content.split("\n## "):
            if section.strip():
                chunks.append(section[:512])
        entries.append({
            "path": f"wiki/concepts/{cf.name}",
            "chunks": chunks,
        })

    index = {"version": 1, "entries": entries}
    SYNAPSE_INDEX.parent.mkdir(parents=True, exist_ok=True)
    SYNAPSE_INDEX.write_text(json.dumps(index, ensure_ascii=False), encoding="utf-8")

    return f"Synapse: indexed {len(entries)} concepts to {SYNAPSE_INDEX.name}"


def _try_vector_status() -> str:
    try:
        from lib import vectorstore as vs
        return vs.status()
    except Exception:
        return "unavailable"


def status() -> str:
    """Show synapse engine status."""
    concepts = list(CONCEPTS_DIR.glob("*.md"))
    total_wikilinks = 0
    for cf in concepts:
        content = cf.read_text(encoding="utf-8")
        total_wikilinks += len(re.findall(r"\[\[([^\]]+)\]\]", content))

    return (f"Synapse Engine Status:\n"
            f"- Concepts indexed: {len(concepts)}\n"
            f"- Total [[wikilinks]]: {total_wikilinks}\n"
            f"- Vector store: active ({_try_vector_status()})")
