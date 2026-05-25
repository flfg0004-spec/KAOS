"""Gap Query API — Phase 0 pre-research service for Aletheia.

Provides a query_gaps(topic) interface that Aletheia calls before research:
  - existing_concepts: semantic search for notes related to topic
  - gaps_detected: structural gaps around topic
  - orphan_pages: unreferenced notes related to topic
  - decayed_topics: lifecycle decay in related notes
  - confidence_gaps: investigations with incomplete frontmatter
"""

import re
from pathlib import Path
from datetime import datetime

from lib.gaps import GapDetector
from lib.memory_lifecycle import evaluate as lifecycle_evaluate, _get_md_files as get_wiki_files
from lib.config import VAULT_ROOT

BASE = (Path(__file__).resolve().parent.parent.parent)


def _semantic_search(query: str, top_k: int = 10) -> list[dict]:
    """Basic token-overlap semantic search over wiki files."""
    query_tokens = set(re.findall(r"\w{4,}", query.lower()))
    if not query_tokens:
        return []

    results = []
    for f in (BASE / "wiki").rglob("*.md"):
        content = f.read_text(encoding="utf-8", errors="replace")[:3000]
        file_tokens = set(re.findall(r"\w{4,}", content.lower()))
        overlap = len(query_tokens & file_tokens)
        if overlap > 0:
            results.append({
                "name": f.stem,
                "path": str(f.relative_to(BASE)),
                "overlap": overlap,
                "score": round(overlap / len(query_tokens), 3),
            })

    results.sort(key=lambda x: -x["score"])
    return results[:top_k]


def _confidence_gaps() -> list[dict]:
    """Find investigations with low or missing confidence matrix."""
    gaps = []
    raw_dir = BASE / "raw"
    if not raw_dir.exists():
        return gaps
    for f in raw_dir.glob("*.md"):
        content = f.read_text(encoding="utf-8", errors="replace")
        has_matrix = "## Matriz de Confianza" in content or "Confianza" in content
        if not has_matrix:
            gaps.append({"file": f.stem, "path": str(f.relative_to(BASE)), "issue": "missing_confidence_matrix"})
    return gaps


def _decayed_topics(min_confidence: float = 0.5) -> list[dict]:
    """Notes with lifecycle confidence below threshold."""
    decayed = []
    for f in get_wiki_files():
        try:
            ev = lifecycle_evaluate(f)
            if ev.get("confidence", 1.0) < min_confidence:
                decayed.append(ev)
        except Exception:
            pass
    return sorted(decayed, key=lambda x: x.get("confidence", 1.0))[:20]


def query_gaps(topic: str) -> dict:
    """Full gap query — the primary API called by Aletheia before research.

    Args:
        topic: Research topic string (e.g. "quantum computing", "estoicismo")

    Returns:
        dict with existing_concepts, gaps_detected, orphan_pages,
        decayed_topics, confidence_gaps
    """
    detector = GapDetector()
    all_gaps = detector.suggest_gaps(min_confidence=0.15) if detector.graph else []

    existing = _semantic_search(topic)
    topic_lower = topic.lower()
    related_gaps = [
        g for g in all_gaps
        if topic_lower in str(g.get("missing", g.get("node", g.get("members", "")))).lower()
           or topic_lower in g.get("reason", "").lower()
    ]

    orphans = []
    if detector.page_map:
        for name, data in detector.page_map.items():
            if name in {"index", "log"}:
                continue
            if not data.get("backlinks"):
                name_lower = name.lower()
                if topic_lower in name_lower or any(w in name_lower for w in topic_lower.split()):
                    orphans.append({"name": name, "path": data.get("path", "")})

    decayed = _decayed_topics()
    topic_decayed = [
        d for d in decayed
        if topic_lower in d.get("path", "").lower()
    ]

    confidence_gaps = _confidence_gaps()
    topic_confidence = [
        c for c in confidence_gaps
        if topic_lower in c.get("file", "").lower()
    ]

    return {
        "topic": topic,
        "existing_concepts": existing,
        "gaps_detected": related_gaps[:10],
        "orphan_pages": orphans[:10],
        "decayed_topics": topic_decayed[:10],
        "confidence_gaps": topic_confidence[:10] if topic_confidence else confidence_gaps[:5],
        "total_existing": len(existing),
        "total_gaps": len(all_gaps),
        "generated_at": datetime.now().isoformat(),
    }
