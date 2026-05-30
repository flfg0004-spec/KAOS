"""TxtaiStrategyAdapter — implements VectorStoreAdapter for txtai backend."""
from lib.vector_adapter import VectorStoreAdapter
from lib import strategy_vectorstore
import logging

logger = logging.getLogger(__name__)


class TxtaiStrategyAdapter(VectorStoreAdapter):
    def search(self, text, top_k=5):
        return strategy_vectorstore.hybrid_search(text, top_k)

    def embed(self, doc_id, text):
        parts = doc_id.split("::")
        sid = parts[-1] if len(parts) > 1 else parts[0]
        return strategy_vectorstore.embed_strategy(sid, {"text": text}, {})

    def delete(self, doc_id):
        pass

    def status(self):
        return strategy_vectorstore.status()

    def health(self):
        return strategy_vectorstore.health()
