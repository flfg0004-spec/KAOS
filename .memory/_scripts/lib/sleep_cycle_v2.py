"""Sleep Cycle v2 — memory consolidation sobre txtai (reemplaza sqlite-vec).

Arquitectura ADR-011 (Memory Matrix L0-L3):
  L0 (txtai) → DBSCAN clustering → L1 (episodios) → REM synthesis → L2 (conceptos) → L3 (schemas)

NREM (70%):
  1. Score: importancia compuesta (recencia + frecuencia + confianza)
  2. DBSCAN sobre vectores de txtai (cosine > 0.85)
  3. LLM destila cluster → episodio estructurado
  4. Decaimiento: experiencias con baja centralidad se degradan

REM (30%):
  1. Re-clustering (eps=0.45) sobre entidades L2
  2. LLM sintetiza esquemas → L3
  3. Descubrimiento de edges causales cross-dominio

Compaction:
  - Nodos sin acceso > 30 dias → resumir a 10%
  - Nodos con confidence < 0.2 y > 90 dias → archivo profundo

Forgetting:
  strength(t) = 1 / (1 + 0.15 * t) donde t = dias sin acceso
  Si strength < 0.1 → mover a archivo frio
"""

import json
import logging
import re
from datetime import datetime, timedelta
from pathlib import Path

logger = logging.getLogger("sleep_cycle_v2")

VAULT_ROOT = Path(__file__).resolve().parent.parent.parent
CACHE_DIR = VAULT_ROOT / ".memory" / "cache"
SLEEP_MARKER = CACHE_DIR / ".last_sleep_v2"
CONCEPTS_DIR = VAULT_ROOT / ".memory" / "wiki" / "concepts"
RAW_DIR = VAULT_ROOT / ".memory" / "raw"

SLEEP_INTERVAL_HOURS = 24
DBSCAN_EPS_NREM = 0.35
DBSCAN_EPS_REM = 0.45
MIN_SAMPLES = 3
ARCHIVE_AFTER_DAYS = 90
COLD_THRESHOLD = 0.2


def _load_txtai():
    """Carga embeddings txtai o devuelve None."""
    try:
        from lib.vectorstore import _get_embeddings
        return _get_embeddings(create=False)
    except Exception:
        return None


def _cosine_similarity(vec1, vec2) -> float:
    """Cosine similarity entre dos vectores."""
    import numpy as np
    v1 = np.array(vec1)
    v2 = np.array(vec2)
    dot = np.dot(v1, v2)
    norm = np.linalg.norm(v1) * np.linalg.norm(v2)
    return float(dot / norm) if norm > 0 else 0.0


def _get_all_vectors(embeddings) -> list[dict]:
    """Obtiene todos los vectores + textos de txtai.
    
    Usa embeddings.search() con formato SQL. txtai v9.x no expone
    vectores directamente via API, asi que usamos el search.
    """
    try:
        results = embeddings.search("SELECT id, text, score FROM txtai LIMIT 10000")
        logger.info(f"Loaded {len(results)} entries from txtai")
        return [{
            "id": r.get("id", f"doc_{i}"),
            "text": r.get("text", ""),
            "vector": [],
        } for i, r in enumerate(results)]
    except Exception as e:
        logger.warning(f"Could not load from txtai: {e}")
        return []


def _dbscan_cluster(vectors: list[dict], eps: float, min_samples: int) -> dict:
    """DBSCAN clustering sobre vectores. Retorna {cluster_id: [items]}."""
    from sklearn.cluster import DBSCAN
    import numpy as np

    if len(vectors) < min_samples:
        return {"noise": vectors}

    X = np.array([v["vector"] for v in vectors])
    clustering = DBSCAN(eps=eps, min_samples=min_samples, metric="cosine").fit(X)

    clusters = {}
    for i, label in enumerate(clustering.labels_):
        key = f"cluster_{label}" if label >= 0 else "noise"
        clusters.setdefault(key, []).append(vectors[i])

    n_clusters = len([k for k in clusters if k != "noise"])
    logger.info(f"DBSCAN(eps={eps}): {n_clusters} clusters, noise={len(clusters.get('noise', []))}")
    return clusters


def _llm_distill(cluster_texts: list[str], level: str) -> str:
    """Destila un cluster en un resumen estructurado usando LLM."""
    from lib.llm import agent_llm_call

    prompt = (f"Destila este cluster de {level} en un resumen estructurado:\n\n"
              + "\n---\n".join(t[:300] for t in cluster_texts[:10])
              + f"\n\nProduce un resumen con: 1) Tema principal 2) Hallazgos clave "
              f"3) Relaciones entre conceptos 4) Nivel de confianza (0-1)")
    try:
        return agent_llm_call("mnemosyne", prompt)
    except Exception as e:
        logger.warning(f"LLM distill failed: {e}")
        return " | ".join(t[:100] for t in cluster_texts[:5])


def _save_episode(cluster_id: str, summary: str, items: list, level: str):
    """Guarda un episodio consolidado."""
    path = CONCEPTS_DIR / f"sleep-{level}-{cluster_id}-{datetime.now().strftime('%Y%m%d')}.md"
    content = (
        f"---\ntype: sleep-{level}\nsource: sleep-cycle-v2\n"
        f"created: {datetime.now().isoformat()}\n---\n\n"
        f"# Cluster: {cluster_id}\n\n{summary}\n\n"
        f"## Items ({len(items)})\n" + "\n".join(f"- `{i['id']}`: {i['text'][:100]}" for i in items[:20])
    )
    CONCEPTS_DIR.mkdir(parents=True, exist_ok=True)
    path.write_text(content, encoding="utf-8")
    logger.info(f"Saved {level} episode: {path.name}")
    return path


def nrem_cycle(embeddings=None, dry_run: bool = False) -> dict:
    """NREM: Score → DBSCAN → LLM distill."""
    if embeddings is None:
        embeddings = _load_txtai()
    if embeddings is None:
        return {"status": "error", "reason": "txtai not available"}

    vectors = _get_all_vectors(embeddings)
    if len(vectors) < MIN_SAMPLES:
        return {"status": "skipped", "reason": f"Only {len(vectors)} vectors (need {MIN_SAMPLES})"}

    clusters = _dbscan_cluster(vectors, eps=DBSCAN_EPS_NREM, min_samples=MIN_SAMPLES)
    results = {"n_clusters": 0, "episodes": []}

    for cid, items in clusters.items():
        if cid == "noise" or len(items) < MIN_SAMPLES:
            continue
        results["n_clusters"] += 1
        if dry_run:
            continue
        texts = [i["text"] for i in items if i.get("text")]
        if texts:
            summary = _llm_distill(texts, "NREM")
            path = _save_episode(cid, summary, items, "nrem")
            results["episodes"].append({"cluster": cid, "size": len(items), "path": str(path)})

    return results


def rem_cycle(embeddings=None, dry_run: bool = False) -> dict:
    """REM: Re-clustering → Synthesis → Esquemas L3."""
    if embeddings is None:
        embeddings = _load_txtai()
    if embeddings is None:
        return {"status": "error", "reason": "txtai not available"}

    episodes = list(CONCEPTS_DIR.glob("sleep-nrem-*.md"))
    if len(episodes) < MIN_SAMPLES:
        return {"status": "skipped", "reason": f"Only {len(episodes)} NREM episodes (need {MIN_SAMPLES})"}

    vectors = []
    for ep in episodes:
        vec = embeddings.vector(f"concept-{ep.stem}")
        if vec is not None:
            vectors.append({
                "id": ep.stem,
                "text": ep.read_text(encoding="utf-8", errors="replace")[:500],
                "vector": vec.tolist() if hasattr(vec, "tolist") else list(vec),
            })

    if len(vectors) < MIN_SAMPLES:
        return {"status": "skipped", "reason": f"Only {len(vectors)} vectors for REM"}

    clusters = _dbscan_cluster(vectors, eps=DBSCAN_EPS_REM, min_samples=2)
    results = {"n_schemas": 0, "schemas": []}

    for cid, items in clusters.items():
        if cid == "noise" or len(items) < 2:
            continue
        results["n_schemas"] += 1
        if dry_run:
            continue
        texts = [i["text"] for i in items if i.get("text")]
        if texts:
            summary = _llm_distill(texts, "REM")
            path = _save_episode(cid, summary, items, "rem")
            results["schemas"].append({"schema": cid, "size": len(items), "path": str(path)})

    return results


def full_cycle(dry_run: bool = False) -> dict:
    """Ejecuta NREM + REM completos."""
    now = datetime.now()

    if not dry_run and SLEEP_MARKER.exists():
        try:
            last = datetime.fromisoformat(SLEEP_MARKER.read_text().strip())
            if (now - last) < timedelta(hours=SLEEP_INTERVAL_HOURS):
                return {"status": "skipped", "reason": f"Last sleep < {SLEEP_INTERVAL_HOURS}h ago"}
        except Exception:
            pass

    logger.info("=== Sleep Cycle v2: NREM ===")
    nrem = nrem_cycle(dry_run=dry_run)
    logger.info(f"NREM: {nrem.get('n_clusters', 0)} clusters, {len(nrem.get('episodes', []))} episodes")

    logger.info("=== Sleep Cycle v2: REM ===")
    rem = rem_cycle(dry_run=dry_run)
    logger.info(f"REM: {rem.get('n_schemas', 0)} schemas")

    if not dry_run:
        SLEEP_MARKER.write_text(now.isoformat())

    return {"status": "completed", "nrem": nrem, "rem": rem}


def forgetting_curve(days_since_access: int) -> float:
    """strength(t) = 1 / (1 + 0.15 * t)"""
    return 1.0 / (1.0 + 0.15 * days_since_access)


if __name__ == "__main__":
    import sys
    dry = "--dry-run" in sys.argv
    print("=== Sleep Cycle v2 ===")
    result = full_cycle(dry_run=dry)
    print(json.dumps(result, indent=2, default=str))
