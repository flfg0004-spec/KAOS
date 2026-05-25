"""Memory Bridge — sincronizacion asimetrica entre KAOS L0-L3 y DeerFlow.

Decision ADR-012 (P3):
  KAOS es source of truth con memoria jerarquica L0-L3 (Hebbian + Sleep Cycle).
  DeerFlow tiene 100 facts planos sin embeddings ni busqueda semantica.
  La sincronizacion es ASIMETRICA y UNIDIRECCIONAL (KAOS → DeerFlow).

Flujo:
  1. Push (cada hora): KAOS selecciona top-100 facts de L1 (episodios relevantes)
     y los envia comprimidos a DeerFlow via DeerFlowClient.memory_set()
  2. Pull (on-demand al finalizar tarea): DeerFlow escribe facts nuevos durante
     conversaciones. KAOS lee via DeerFlowClient.memory_get_all(), los ingesta
     en L0 como chunks raw. Sleep Cycle de Mnemosyne los consolida a L1→L2.

  No hay sincronia bidireccional completa porque DeerFlow no soporta embeddings
  ni busqueda semantica. La conversion perderia fidelidad.
"""

import json
import logging
from datetime import datetime, timedelta
from pathlib import Path

logger = logging.getLogger("memory_bridge")

BRIDGE_DIR = Path(__file__).resolve().parent.parent.parent / "bridge"
MEMORY_CACHE = BRIDGE_DIR / "context" / "memory-bridge-cache.json"
RAW_DIR = Path(__file__).resolve().parent.parent.parent / "raw"

SYNC_INTERVAL_HOURS = 1
MAX_FACTS_PUSH = 100
DEERFLOW_AVAILABLE = False


class MemoryBridge:
    def __init__(self):
        self.last_sync = None
        self._check_deerflow()

    def _check_deerflow(self):
        global DEERFLOW_AVAILABLE
        for modname in ("deerflow.client", "lib.deerflow_client"):
            try:
                __import__(modname, fromlist=["DeerFlowClient"])
                DEERFLOW_AVAILABLE = True
                return
            except ImportError:
                continue
        DEERFLOW_AVAILABLE = False

    def _load_cache(self) -> dict:
        if MEMORY_CACHE.exists():
            try:
                return json.loads(MEMORY_CACHE.read_text(encoding="utf-8"))
            except Exception:
                pass
        return {"last_sync": None, "facts_pushed": 0, "facts_pulled": 0}

    def _save_cache(self, data: dict):
        MEMORY_CACHE.parent.mkdir(parents=True, exist_ok=True)
        MEMORY_CACHE.write_text(json.dumps(data, indent=2))

    def _get_top_facts(self, max_facts: int = MAX_FACTS_PUSH) -> list[dict]:
        facts = []
        try:
            from lib.code_memory import search
            experiences = search("", top_k=max_facts)
            for exp in experiences:
                facts.append({
                    "id": exp.get("id", 0),
                    "error": exp.get("error", "")[:200],
                    "language": exp.get("language", "unknown"),
                    "confidence": exp.get("confidence", 0.5),
                    "retrievals": exp.get("retrieval_count", 0),
                })
        except Exception as e:
            logger.warning(f"Could not read CodeExperience: {e}")

        wiki_concepts = list((Path(__file__).resolve().parent.parent.parent / "wiki" / "concepts").glob("*.md"))
        for concept_file in wiki_concepts[:max_facts]:
            facts.append({
                "id": f"concept-{concept_file.stem}",
                "content": concept_file.read_text(encoding="utf-8", errors="replace")[:200],
                "source": "wiki/concepts",
            })

        return facts[:max_facts]

    def push_to_deerflow(self) -> dict:
        now = datetime.now()
        cache = self._load_cache()

        if cache.get("last_sync"):
            last = datetime.fromisoformat(cache["last_sync"])
            if (now - last) < timedelta(hours=SYNC_INTERVAL_HOURS):
                return {"status": "skipped", "reason": f"Last sync < {SYNC_INTERVAL_HOURS}h ago"}

        if not DEERFLOW_AVAILABLE:
            facts = self._get_top_facts()
            cache["last_sync"] = now.isoformat()
            cache["facts_pushed"] = len(facts)
            cache["facts"] = [f["id"] for f in facts]
            self._save_cache(cache)
            logger.info(f"[MOCK] Would push {len(facts)} facts to DeerFlow")
            return {"status": "mock", "facts_pushed": len(facts)}

        try:
            try:
                from deerflow.client import DeerFlowClient as DFC
            except ImportError:
                from lib.deerflow_client import DeerFlowClient as DFC
            client = DFC()
            facts = self._get_top_facts()

            for i, fact in enumerate(facts):
                client.memory_set(f"kaos-fact-{i}", json.dumps(fact))

            cache["last_sync"] = now.isoformat()
            cache["facts_pushed"] = len(facts)
            self._save_cache(cache)
            logger.info(f"Pushed {len(facts)} facts to DeerFlow")
            return {"status": "ok", "facts_pushed": len(facts)}

        except Exception as e:
            logger.error(f"Push to DeerFlow failed: {e}")
            return {"status": "error", "error": str(e)}

    def pull_from_deerflow(self) -> dict:
        if not DEERFLOW_AVAILABLE:
            cache = self._load_cache()
            logger.info("[MOCK] Would pull facts from DeerFlow")
            return {"status": "mock", "facts_pulled": 0}

        try:
            try:
                from deerflow.client import DeerFlowClient as DFC
            except ImportError:
                from lib.deerflow_client import DeerFlowClient as DFC
            client = DFC()
            facts_raw = client.memory_get_all()
            facts = json.loads(facts_raw) if isinstance(facts_raw, str) else facts_raw

            count = 0
            for key, value in facts.items():
                if key.startswith("kaos-fact-"):
                    continue
                slug = f"deerflow-fact-{datetime.now().strftime('%Y%m%d-%H%M%S')}-{count}"
                path = RAW_DIR / f"{slug}.md"
                fact_content = json.dumps(value, indent=2) if not isinstance(value, str) else value
                path.write_text(
                    f"---\ntype: deerflow-fact\nsource: deerflow-memory\n"
                    f"ingested_at: {datetime.now().isoformat()}\n---\n\n{fact_content}",
                    encoding="utf-8",
                )
                count += 1

            cache = self._load_cache()
            cache["facts_pulled"] = cache.get("facts_pulled", 0) + count
            self._save_cache(cache)
            logger.info(f"Pulled {count} facts from DeerFlow → raw/")
            return {"status": "ok", "facts_pulled": count}

        except Exception as e:
            logger.error(f"Pull from DeerFlow failed: {e}")
            return {"status": "error", "error": str(e)}

    def status(self) -> dict:
        cache = self._load_cache()
        return {
            "deerflow_available": DEERFLOW_AVAILABLE,
            "last_sync": cache.get("last_sync"),
            "facts_pushed": cache.get("facts_pushed", 0),
            "facts_pulled": cache.get("facts_pulled", 0),
            "sync_interval_hours": SYNC_INTERVAL_HOURS,
        }


bridge = MemoryBridge()
