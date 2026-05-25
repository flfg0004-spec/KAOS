"""Seed sample data for the KAOS Dashboard."""
import json
import random
from datetime import datetime, timedelta
from pathlib import Path

random.seed(42)

timeseries = Path(__file__).resolve().parent.parent / ".vault" / "quality" / "timeseries"
timeseries.mkdir(parents=True, exist_ok=True)

now = datetime.utcnow()

# Seed verification scores
scores = {"scores": []}
for i in range(14):
    d = now - timedelta(days=13 - i)
    for agent in ["aletheia", "kosmos", "metis", "kratos", "mnemosyne"]:
        base = {"aletheia": 85, "kosmos": 82, "metis": 78, "kratos": 75, "mnemosyne": 80}
        s = base[agent] + random.uniform(-5, 5)
        scores["scores"].append({
            "agent": agent, "composite": round(s, 1),
            "veracidad": round(s + 2, 1), "coherencia": round(s - 1, 1),
            "completitud": round(s - 3, 1), "reproducibilidad": round(s + 1, 1),
            "utilidad": round(s - 2, 1),
            "timestamp": d.strftime("%Y-%m-%dT%H:%M:%S"),
            "topic": f"test-{i}", "pipeline_id": f"P-{d.strftime('%Y%m%d')}-{i:04d}",
        })

(timeseries / "verification-scores.json").write_text(json.dumps(scores, indent=2))
print(f"Seeded {len(scores['scores'])} verification scores")

# Seed pipeline durations
durations = {"entries": []}
for i in range(10):
    d = now - timedelta(hours=i * 6)
    durations["entries"].append({
        "timestamp": d.isoformat(), "duration_s": random.randint(180, 600),
        "profile": "desarrollo", "total_cost_usd": round(random.uniform(0.1, 0.5), 4),
        "total_calls": random.randint(3, 8),
    })
(timeseries / "pipeline-durations.json").write_text(json.dumps(durations, indent=2))
print(f"Seeded {len(durations['entries'])} pipeline durations")

# Seed token usage
cache_dir = Path(__file__).resolve().parent.parent / ".memory" / "cache"
cache_dir.mkdir(parents=True, exist_ok=True)
tokens = {
    "total_cost_usd": 4.23, "total_calls": 42,
    "total_prompt_tokens": 45000, "total_cache_hit": 3200,
    "total_cache_miss": 12800, "total_completion_tokens": 8500,
    "history": [],
}
(cache_dir / "token-usage.json").write_text(json.dumps(tokens, indent=2))
print("Seeded token usage data")

print("Done — dashboard data ready")
