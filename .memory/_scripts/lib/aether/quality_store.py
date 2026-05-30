"""QualityStore — persistent quality score tracking with thread safety.

Almacena scores de calidad por modelo+task_type para quality-aware routing.
Persistencia en .memory/cache/quality_history.json con atomic writes.
"""

import json
import logging
import os
import threading
from datetime import UTC, datetime
from pathlib import Path

_LOG = logging.getLogger(__name__)

CACHE_DIR = Path(__file__).resolve().parent.parent.parent.parent.parent / ".memory" / "cache"
DEFAULT_PATH = CACHE_DIR / "quality_history.json"
_KAOS_TESTING = os.environ.get("KAOS_TESTING", "").lower() in ("1", "true")


class QualityStore:
    """Thread-safe quality score store with atomic persistence.

    Cada entrada de calidad contiene:
    - model: nombre del modelo
    - task_type: categoría de tarea
    - agent: nombre del agente (opcional)
    - scores: dict con scores por dimensión (helpfulness, correctness, ...)
    - weighted_score: float (0-10)
    - verdict: "pass" | "warn" | "fail"
    - timestamp: ISO datetime
    """

    def __init__(self, path: Path | None = None):
        self.path = path or DEFAULT_PATH
        self.path.parent.mkdir(parents=True, exist_ok=True)
        self._lock = threading.Lock()
        self._data = self._load()
        _LOG.info("QualityStore initialized at %s (entries=%d)", self.path, len(self._data.get("entries", [])))

    # ── Persistencia ─────────────────────────────────────────

    def _load(self) -> dict:
        if _KAOS_TESTING:
            return {"version": 2, "entries": []}
        if self.path.exists():
            try:
                return json.loads(self.path.read_text(encoding="utf-8"))
            except Exception as e:
                _LOG.warning("QualityStore: failed to load: %s", e)
        return {"version": 2, "entries": []}

    def _save(self):
        if _KAOS_TESTING:
            return
        try:
            tmp = self.path.with_suffix(".tmp")
            tmp.write_text(
                json.dumps(self._data, ensure_ascii=False, indent=2),
                encoding="utf-8",
            )
            tmp.replace(self.path)
        except Exception as e:
            _LOG.warning("QualityStore: failed to save: %s", e)

    # ── Recording ─────────────────────────────────────────────

    def record(
        self,
        model: str,
        task_type: str,
        agent: str = "",
        scores: dict | None = None,
        weighted_score: float = 0.0,
        verdict: str = "pass",
        prompt_size: int = 0,
    ):
        """Registra un resultado de evaluación de calidad.

        Args:
            model: Modelo usado
            task_type: Tipo de tarea
            agent: Agente (opcional)
            scores: Dict de scores por dimensión
            weighted_score: Score ponderado (0-10)
            verdict: pass | warn | fail
            prompt_size: Tamaño del prompt en tokens
        """
        entry = {
            "timestamp": datetime.now(UTC).isoformat(),
            "model": model,
            "task_type": task_type,
            "agent": agent or "",
            "scores": scores or {},
            "weighted_score": round(weighted_score, 2),
            "verdict": verdict,
            "prompt_size": prompt_size,
        }
        with self._lock:
            self._data.setdefault("entries", []).append(entry)
            # Mantener máx 10K entries para no explotar el archivo
            if len(self._data["entries"]) > 10_000:
                self._data["entries"] = self._data["entries"][-5_000:]
            self._save()

    # ── Querying ──────────────────────────────────────────────

    def get_task_scores(self, task_type: str) -> dict[str, dict]:
        """Obtiene scores agregados por modelo para un task_type.

        Returns:
            dict[model, {"samples": int, "avg_score": float,
                         "pass_rate": float, "total_cost": float}]
        """
        with self._lock:
            entries = self._data.get("entries", [])

        model_data = {}
        for e in entries:
            if e.get("task_type") != task_type:
                continue
            model = e.get("model", "unknown")
            if model not in model_data:
                model_data[model] = {"scores": [], "pass_count": 0, "total": 0}
            model_data[model]["scores"].append(e.get("weighted_score", 0))
            model_data[model]["total"] += 1
            if e.get("verdict") == "pass":
                model_data[model]["pass_count"] += 1

        result = {}
        for model, data in model_data.items():
            samples = data["total"]
            if samples == 0:
                continue
            result[model] = {
                "samples": samples,
                "avg_score": round(sum(data["scores"]) / samples, 2),
                "pass_rate": round(data["pass_count"] / samples, 3),
                "total_calls": samples,
            }
        return result

    def get_best_model_for_task(self, task_type: str, min_samples: int = 3) -> tuple | None:
        """Obtiene el mejor modelo para un task_type según calidad histórica.

        Args:
            task_type: Tipo de tarea
            min_samples: Mínimo de muestras requeridas

        Returns:
            (model_name, avg_score) o None si no hay datos suficientes
        """
        scores = self.get_task_scores(task_type)
        best_model = None
        best_score = -1.0
        for model, data in scores.items():
            if data["samples"] >= min_samples and data["avg_score"] > best_score:
                best_model = model
                best_score = data["avg_score"]
        if best_model:
            return (best_model, best_score)
        return None

    def get_summary(self) -> dict:
        """Resumen global de calidad.

        Returns:
            dict con total_entries, per_task_type, per_model, global_avg
        """
        with self._lock:
            entries = self._data.get("entries", [])

        if not entries:
            return {
                "total_entries": 0,
                "per_task_type": {},
                "per_model": {},
                "global_avg": 0.0,
                "total_calls": 0,
            }

        # Agregar por task_type
        by_task = {}
        by_model = {}
        total_score = 0.0

        for e in entries:
            tt = e.get("task_type", "unknown")
            model = e.get("model", "unknown")
            ws = e.get("weighted_score", 0)

            if tt not in by_task:
                by_task[tt] = {"samples": 0, "total_score": 0.0, "pass_count": 0}
            by_task[tt]["samples"] += 1
            by_task[tt]["total_score"] += ws
            if e.get("verdict") == "pass":
                by_task[tt]["pass_count"] += 1

            if model not in by_model:
                by_model[model] = {"samples": 0, "total_score": 0.0}
            by_model[model]["samples"] += 1
            by_model[model]["total_score"] += ws

            total_score += ws

        # Normalizar
        task_summary = {}
        for tt, data in sorted(by_task.items()):
            task_summary[tt] = {
                "samples": data["samples"],
                "avg_score": round(data["total_score"] / data["samples"], 2),
                "pass_rate": round(data["pass_count"] / data["samples"], 3),
            }

        model_summary = {}
        for model, data in sorted(by_model.items()):
            model_summary[model] = {
                "samples": data["samples"],
                "avg_score": round(data["total_score"] / data["samples"], 2),
            }

        return {
            "total_entries": len(entries),
            "per_task_type": task_summary,
            "per_model": model_summary,
            "global_avg": round(total_score / len(entries), 2),
            "total_calls": len(entries),
        }

    def get_model_score(self, model: str, task_type: str = "", min_samples: int = 3) -> float:
        """Obtiene score promedio de calidad para un modelo (0-10).

        Args:
            model: Nombre del modelo a consultar.
            task_type: Filtrar por task_type (opcional).
            min_samples: Mínimo de muestras requeridas para considerar el score.

        Returns:
            float: Score promedio (0-10), o 10.0 si no hay datos suficientes (default trust).
        """
        with self._lock:
            entries = self._data.get("entries", [])

        relevant = [
            e for e in entries
            if e.get("model") == model
            and (not task_type or e.get("task_type") == task_type)
        ]

        if len(relevant) < min_samples:
            return 10.0  # default trust — sin datos, asumir calidad

        avg = sum(e.get("weighted_score", 0) for e in relevant) / len(relevant)
        return round(avg, 2)

    def get_recent_entries(self, n: int = 20) -> list:
        """Devuelve las últimas n entradas."""
        with self._lock:
            return list(self._data.get("entries", []))[-n:]

    # ── Maintenance ───────────────────────────────────────────

    def reset(self):
        """Limpia todos los datos de calidad."""
        with self._lock:
            self._data = {"version": 2, "entries": []}
            self._save()
        _LOG.info("QualityStore: reset completed")
