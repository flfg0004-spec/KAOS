import json
from datetime import datetime
from pathlib import Path
from typing import Any, Optional, Union

from crewai.memory.storage.backend import MemoryRecord
from crewai.memory.storage.lancedb_storage import LanceDBStorage
from lib.config import VAULT_ROOT

class KAOSStorageBackend(LanceDBStorage):
    """
    Custom StorageBackend for CrewAI within KAOS.
    Intercepts saves to emit asynchronous bridge signals in .memory/bridge/signals/
    and organizes memories locally in .memory/.crewai/memory.
    """
    def __init__(
        self,
        path: Optional[Union[str, Path]] = None,
        table_name: str = "memories",
        vector_dim: Optional[int] = None,
        compact_every: int = 100
    ) -> None:
        if path is None:
            # Organiza las memorias en .memory/.crewai/memory
            path = VAULT_ROOT / ".crewai" / "memory"
        
        path = Path(path)
        path.parent.mkdir(parents=True, exist_ok=True)
        super().__init__(path=path, table_name=table_name, vector_dim=vector_dim, compact_every=compact_every)
        self.bridge_dir = VAULT_ROOT / "bridge" / "signals"
        self.bridge_dir.mkdir(parents=True, exist_ok=True)

    def save(self, records: list[MemoryRecord]) -> None:
        super().save(records)
        self._emit_kaos_signals(records)

    async def asave(self, records: list[MemoryRecord]) -> None:
        await super().asave(records)
        self._emit_kaos_signals(records)

    def _emit_kaos_signals(self, records: list[MemoryRecord]) -> None:
        """
        Emite señales JSON a .memory/bridge/signals/ para procesamiento en background por KAOS.
        """
        for record in records:
            signal_data = {
                "id": record.id,
                "content": record.content,
                "scope": record.scope,
                "categories": record.categories,
                "metadata": record.metadata,
                "importance": record.importance,
                "created_at": record.created_at.isoformat() if isinstance(record.created_at, datetime) else str(record.created_at),
                "last_accessed": record.last_accessed.isoformat() if isinstance(record.last_accessed, datetime) else str(record.last_accessed),
                "source": record.source,
                "private": record.private,
                "origin_system": "crewai"
            }
            signal_file = self.bridge_dir / f"crewai_mem_{record.id}.json"
            try:
                signal_file.write_text(json.dumps(signal_data, indent=2, ensure_ascii=False), encoding="utf-8")
            except Exception:
                # Silencioso para evitar romper ejecuciones del agente
                pass
