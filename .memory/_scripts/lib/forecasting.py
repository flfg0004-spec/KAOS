"""Score Forecasting — predicts quality score trends using sklearn or moving average."""

import json
import logging
from datetime import datetime, timedelta
from pathlib import Path

logger = logging.getLogger("forecasting")

TIMESERIES_DIR = Path(__file__).resolve().parent.parent.parent / ".vault" / "quality" / "timeseries"
VERIFICATION_FILE = TIMESERIES_DIR / "verification-scores.json"
MIN_DATA_POINTS = 5

_HAS_SKLEARN = False
try:
    import numpy as np
    from sklearn.linear_model import LinearRegression

    _HAS_SKLEARN = True
except ImportError:
    pass


def _load_scores(days: int = 90) -> list:
    if not VERIFICATION_FILE.exists():
        return []
    try:
        data = json.loads(VERIFICATION_FILE.read_text(encoding="utf-8"))
        cutoff = (datetime.now() - timedelta(days=days)).isoformat()
        return [s for s in data.get("scores", []) if s.get("timestamp", "") >= cutoff]
    except Exception as e:
        logger.warning(f"Failed to load scores: {e}")
        return []


def moving_average(scores: list, window: int = 5) -> list:
    if len(scores) < window:
        return scores
    result = []
    for i in range(len(scores)):
        if i < window - 1:
            result.append(scores[i])
        else:
            result.append(round(sum(scores[i - window + 1 : i + 1]) / window, 1))
    return result


def forecast_by_agent(days: int = 90, forecast_horizon: int = 14) -> dict:
    scores = _load_scores(days)
    if len(scores) < MIN_DATA_POINTS:
        return {"status": "insufficient_data", "data_points": len(scores), "required": MIN_DATA_POINTS}
    agents = {}
    for s in scores:
        agent = s.get("agent", "unknown")
        composite = s.get("composite", 0)
        ts = s.get("timestamp", "")
        if agent not in agents:
            agents[agent] = []
        agents[agent].append({"composite": composite, "timestamp": ts})
    results = {}
    for agent, points in agents.items():
        points.sort(key=lambda x: x["timestamp"])
        values = [p["composite"] for p in points]
        if len(values) < MIN_DATA_POINTS:
            results[agent] = {"status": "insufficient_data", "data_points": len(values)}
            continue
        current = values[-1] if values else 0
        avg = sum(values) / len(values)
        if _HAS_SKLEARN:
            try:
                X = np.arange(len(values)).reshape(-1, 1)
                y = np.array(values)
                model = LinearRegression()
                model.fit(X, y)
                future_X = np.arange(len(values), len(values) + forecast_horizon).reshape(-1, 1)
                predictions = model.predict(future_X)
                predicted = max(0, min(100, predictions[-1]))
                trend = "improving" if model.coef_[0] > 0.1 else "declining" if model.coef_[0] < -0.1 else "stable"
            except Exception:
                predicted = current
                trend = "stable"
        else:
            ma = moving_average(values, window=min(5, len(values)))
            predicted = ma[-1] if ma else current
            trend = "stable"
        results[agent] = {
            "current": round(current, 1),
            "average": round(avg, 1),
            "predicted_14d": round(predicted, 1),
            "trend": trend,
            "data_points": len(values),
            "last_updated": points[-1]["timestamp"] if points else "",
        }
    return {"status": "success", "agents": results, "forecast_horizon_days": forecast_horizon}


def summary(days: int = 90) -> dict:
    scores = _load_scores(days)
    if not scores:
        return {"status": "no_data", "message": "No quality scores found"}
    composites = [s.get("composite", 0) for s in scores]
    return {
        "status": "success",
        "current_score": round(composites[-1], 1),
        "average_score": round(sum(composites) / len(composites), 1),
        "min_score": round(min(composites), 1),
        "max_score": round(max(composites), 1),
        "data_points": len(composites),
        "agent_count": len(set(s.get("agent", "") for s in scores)),
        "time_period_days": days,
        "real_metrics": any(s.get("real_metrics", False) for s in scores),
    }


def status() -> dict:
    scores = _load_scores(90)
    return {
        "available": len(scores) >= MIN_DATA_POINTS,
        "data_points": len(scores),
        "min_required": MIN_DATA_POINTS,
        "sklearn_available": _HAS_SKLEARN,
        "agents_tracked": len(set(s.get("agent", "") for s in scores)),
    }
