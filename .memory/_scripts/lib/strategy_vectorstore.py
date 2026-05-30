"""Vector store wrapper for strategic memory — txtai direct."""
import concurrent.futures
import json
import logging
import os
import sys
from pathlib import Path

import txtai

LIB_DIR = Path(__file__).resolve().parent
STRATEGY_DIR = LIB_DIR.parent.parent / "cache" / "txtai" / "strategy"
STRATEGY_PREFIX = "strategy::"
EMBEDDING_MODEL = os.getenv("EMBEDDING_MODEL", "BAAI/bge-small-en-v1.5")
logger = logging.getLogger(__name__)

_TIMEOUT = int(os.getenv("VECTOR_TIMEOUT", "30"))
_CIRCUIT_FAILURES = 0
_CIRCUIT_STATE = "closed"
_CIRCUIT_LAST_FAIL = 0.0
_CIRCUIT_THRESHOLD = int(os.getenv("CIRCUIT_THRESHOLD", "3"))
_CIRCUIT_RECOVERY = int(os.getenv("CIRCUIT_RECOVERY", "60"))

_EMBEDDINGS = None


def _circuit_call(fn, fallback=None):
    global _CIRCUIT_FAILURES, _CIRCUIT_STATE, _CIRCUIT_LAST_FAIL
    import time as _time
    now = _time.time()
    if _CIRCUIT_STATE == "open":
        if now - _CIRCUIT_LAST_FAIL > _CIRCUIT_RECOVERY:
            _CIRCUIT_STATE = "half-open"
        else:
            return fallback() if fallback else None
    try:
        result = fn()
        if _CIRCUIT_STATE == "half-open":
            _CIRCUIT_STATE = "closed"
        _CIRCUIT_FAILURES = 0
        return result
    except Exception as e:
        _CIRCUIT_FAILURES += 1
        _CIRCUIT_LAST_FAIL = now
        if _CIRCUIT_FAILURES >= _CIRCUIT_THRESHOLD:
            _CIRCUIT_STATE = "open"
            logger.warning("Circuit opened after %d failures", _CIRCUIT_FAILURES)
        logger.warning(
            "Circuit breaker failure %d/%d: %s",
            _CIRCUIT_FAILURES, _CIRCUIT_THRESHOLD, e,
        )
        return fallback() if fallback else None


def _run_with_timeout(fn, timeout=_TIMEOUT):
    with concurrent.futures.ThreadPoolExecutor(max_workers=1) as executor:
        future = executor.submit(fn)
        return future.result(timeout=timeout)


def _get_embeddings(create=True):
    global _EMBEDDINGS
    if _EMBEDDINGS is not None:
        return _EMBEDDINGS
    try:
        index_path = STRATEGY_DIR / "embeddings"
        if STRATEGY_DIR.exists() and index_path.exists():
            _EMBEDDINGS = txtai.Embeddings()
            _EMBEDDINGS.load(str(index_path))
        elif create:
            STRATEGY_DIR.mkdir(parents=True, exist_ok=True)
            _EMBEDDINGS = txtai.Embeddings(path=EMBEDDING_MODEL, content=True, hybrid=True)
        return _EMBEDDINGS
    except Exception as e:
        logger.warning("txtai unavailable: %s", e)
        return None


def embed_strategy(strategy_id, context, content):
    embeddings = _get_embeddings()
    if embeddings is None:
        return None
    text = json.dumps({"context": context, "content": content}, ensure_ascii=False)
    doc_id = f"{STRATEGY_PREFIX}{strategy_id}"

    def _do_embed():
        embeddings.upsert([(doc_id, text, None)])
        embeddings.save(str(STRATEGY_DIR / "embeddings"))
        return doc_id

    def _fallback():
        return None
    return _circuit_call(lambda: _run_with_timeout(_do_embed), fallback=_fallback)


def hybrid_search(query_text, top_k=5):
    embeddings = _get_embeddings(create=False)
    if embeddings is None:
        return []

    def _do_search():
        results = embeddings.search(query_text, limit=top_k * 3)
        strategy_results = []
        for r in results:
            doc_id = r.get("id", "")
            if isinstance(doc_id, str) and doc_id.startswith(STRATEGY_PREFIX):
                strategy_results.append({
                    **r,
                    "strategy_id": int(doc_id.replace(STRATEGY_PREFIX, "")),
                    "score": round(r.get("score", 0), 4),
                })
        return strategy_results[:top_k]

    def _fallback():
        return []
    return _circuit_call(lambda: _run_with_timeout(_do_search, timeout=15), fallback=_fallback)


def batch_embed_existing():
    embeddings = _get_embeddings()
    if embeddings is None:
        return {"embedded": 0, "total": 0, "error": "txtai unavailable"}
    sys.path.insert(0, str(LIB_DIR.parent))
    from strategy_memory import StrategicMemoryBank
    bank = StrategicMemoryBank()
    conn = bank._get_conn()
    rows = conn.execute(
        "SELECT id, context_json, content_json, plan_type FROM strategies"
    ).fetchall()
    count = 0
    for row in rows:
        try:
            ctx = json.loads(row["context_json"]) if row["context_json"] else {}
            content = json.loads(row["content_json"]) if row["content_json"] else {}
            text = json.dumps({"context": ctx, "content": content}, ensure_ascii=False)
            embeddings.upsert([(f"{STRATEGY_PREFIX}{row['id']}", text, None)])
            count += 1
        except Exception as e:
            logger.warning("Failed to embed strategy %s: %s", row["id"], e)
    embeddings.save(str(STRATEGY_DIR / "embeddings"))
    return {"embedded": count, "total": len(rows)}


def status():
    total = 0
    try:
        sys.path.insert(0, str(LIB_DIR.parent))
        from strategy_memory import StrategicMemoryBank
        bank = StrategicMemoryBank()
        total = bank.stats()["total_strategies"]
    except Exception as e:
        logger.warning("Failed to get strategy stats in status(): %s", e)
    embedded = 0
    embeddings = _get_embeddings(create=False)
    if embeddings:
        try:
            results = embeddings.search(f"SELECT id FROM txtai WHERE id LIKE '{STRATEGY_PREFIX}%'")
            embedded = len(results)
        except Exception as e:
            logger.warning("Failed to query embedded count in status(): %s", e)
    health_str = f"{embedded}/{total}" if total else "N/A"
    return {"total_in_db": total, "embedded": embedded, "health": health_str}


def health():
    """Health check for vectorstore. Returns dict with status."""
    result = {
        "status": "unknown",
        "mode": "vector" if _get_embeddings(create=False) else "exact",
        "last_check": __import__("datetime").datetime.now().isoformat(),
    }
    embeddings = _get_embeddings(create=False)
    if embeddings:
        try:
            result["status"] = "ok"
            t0 = __import__("time").time()
            embeddings.search("health check", limit=1)
            result["latency_ms"] = round((__import__("time").time() - t0) * 1000, 1)
        except Exception as e:
            result["status"] = "degraded"
            result["error"] = str(e)
    else:
        result["status"] = "offline"
    return result


if __name__ == "__main__":
    if len(sys.argv) > 1 and sys.argv[1] == "health":
        print(json.dumps(health(), indent=2, ensure_ascii=False))
    else:
        print(json.dumps(status(), indent=2, ensure_ascii=False))
