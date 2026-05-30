"""EtherTracker — persistent token usage tracker with thread safety."""

import json
import logging
import threading
from datetime import date, datetime
from pathlib import Path

from lib.aether.circuit import _ETHER_CIRCUIT_BREAKER
from lib.aether.config import COST_CAPS, COST_RATES

_LOG = logging.getLogger(__name__)

BASE = Path(__file__).resolve().parent.parent.parent.parent.parent
TOKEN_CACHE = BASE / ".memory" / "cache" / "token-usage.json"


class EtherTracker:
    """Persistent token usage tracker with batch writes and thread safety.

    Accumulates entries in memory and flushes to disk every FLUSH_INTERVAL calls.
    Uses threading.Lock and atomic writes (temp + rename) for I/O safety.
    """

    FLUSH_INTERVAL = 10

    def __init__(self):
        self.path = TOKEN_CACHE
        self.path.parent.mkdir(parents=True, exist_ok=True)
        self._lock = threading.Lock()
        self.data = self._load()
        self._pending = 0

    def _load(self) -> dict:
        if self.path.exists():
            try:
                return json.loads(self.path.read_text(encoding="utf-8"))
            except Exception as e:
                _LOG.warning("EtherTracker: error loading cache: %s", e)
        return {"version": 2, "sessions": [], "totals": {}, "daily": {}}

    def _save(self):
        with self._lock:
            tmp = self.path.with_suffix(".tmp")
            tmp.write_text(
                json.dumps(self.data, ensure_ascii=False, indent=2),
                encoding="utf-8",
            )
            tmp.replace(self.path)

    def flush(self):
        if self._pending > 0:
            self._save()
            self._pending = 0

    def track(
        self,
        prompt_tokens=0,
        completion_tokens=0,
        cache_hit=0,
        cache_miss=0,
        reasoning=0,
        model="flash",
        task="general",
        agent="",
        content_type="text",
        compression_ratio=None,
        latency_ms=0.0,
        has_images=False,
    ):
        today = date.today().isoformat()
        now = datetime.now().isoformat()
        cost = self._calc_cost(prompt_tokens, completion_tokens, cache_hit, cache_miss, model)

        entry = {
            "timestamp": now,
            "model": model,
            "agent": agent,
            "task": task,
            "prompt_tokens": prompt_tokens,
            "completion_tokens": completion_tokens,
            "cache_hit_tokens": cache_hit,
            "cache_miss_tokens": cache_miss,
            "reasoning_tokens": reasoning,
            "cost_usd": round(cost, 6),
            "content_type": content_type,
            "compression_ratio": compression_ratio,
            "latency_ms": round(latency_ms, 2),
            "has_images": has_images,
        }

        with self._lock:
            self.data.setdefault("sessions", []).append(entry)

            t = self.data["totals"]
            t["prompt_tokens"] = t.get("prompt_tokens", 0) + prompt_tokens
            t["completion_tokens"] = t.get("completion_tokens", 0) + completion_tokens
            t["cache_hit_tokens"] = t.get("cache_hit_tokens", 0) + cache_hit
            t["cache_miss_tokens"] = t.get("cache_miss_tokens", 0) + cache_miss
            t["reasoning_tokens"] = t.get("reasoning_tokens", 0) + reasoning
            t["cost_usd"] = round(t.get("cost_usd", 0) + cost, 6)
            t["total_calls"] = t.get("total_calls", 0) + 1

            if today not in self.data["daily"]:
                self.data["daily"][today] = {"calls": 0, "prompt_tokens": 0, "cost_usd": 0}
            d = self.data["daily"][today]
            d["calls"] += 1
            d["prompt_tokens"] += prompt_tokens
            d["cost_usd"] = round(d.get("cost_usd", 0) + cost, 6)

            self._pending += 1

        if self._pending >= self.FLUSH_INTERVAL:
            self._save()
            self._pending = 0

    def _calc_cost(self, prompt_tokens, completion_tokens, cache_hit, cache_miss, model):
        rates = COST_RATES
        r = rates.get(model, rates.get("go-flash", rates["flash"]))
        return cache_miss * r["input"] + cache_hit * r["cache_read"] + completion_tokens * r["output"]

    def get_stats(self) -> dict:
        per_agent = {}
        with self._lock:
            for s in self.data.get("sessions", []):
                agent = s.get("agent", "unknown")
                if agent not in per_agent:
                    per_agent[agent] = {
                        "calls": 0,
                        "cost_usd": 0,
                        "prompt_tokens": 0,
                        "completion_tokens": 0,
                    }
                per_agent[agent]["calls"] += 1
                per_agent[agent]["cost_usd"] += s.get("cost_usd", 0)
                per_agent[agent]["prompt_tokens"] += s.get("prompt_tokens", 0)
                per_agent[agent]["completion_tokens"] += s.get("completion_tokens", 0)
            totals = dict(self.data.get("totals", {}))
            daily = dict(self.data.get("daily", {}))
            total_latency_ms = sum(e.get("latency_ms", 0) for e in self.data.get("sessions", []))
            total_multimodal_calls = sum(1 for e in self.data.get("sessions", []) if e.get("has_images", False))
        return {
            "total_calls": totals.get("total_calls", 0),
            "total_prompt_tokens": totals.get("prompt_tokens", 0),
            "total_completion_tokens": totals.get("completion_tokens", 0),
            "total_cache_hit_tokens": totals.get("cache_hit_tokens", 0),
            "total_cache_miss_tokens": totals.get("cache_miss_tokens", 0),
            "total_reasoning_tokens": totals.get("reasoning_tokens", 0),
            "total_cost_usd": totals.get("cost_usd", 0),
            "total_latency_ms": round(total_latency_ms, 2),
            "total_multimodal_calls": total_multimodal_calls,
            "daily_breakdown": dict(sorted(daily.items(), reverse=True)[:7]),
            "per_agent": per_agent,
        }

    def get_daily_report(self) -> str:
        stats = self.get_stats()
        lines = [
            "## Token Usage Report",
            f"- Total API calls: {stats['total_calls']}",
            f"- Total prompt tokens: {stats['total_prompt_tokens']:,}",
            f"- Total completion tokens: {stats['total_completion_tokens']:,}",
            f"- Cache hit tokens: {stats['total_cache_hit_tokens']:,}",
            f"- Cache miss tokens: {stats['total_cache_miss_tokens']:,}",
            f"- Reasoning tokens: {stats['total_reasoning_tokens']:,}",
            f"- Total cost: ${stats['total_cost_usd']:.4f} USD",
            "",
            "### Daily Breakdown",
        ]
        for day, d in stats["daily_breakdown"].items():
            lines.append(f"- {day}: {d['calls']} calls, {d['prompt_tokens']:,} tokens, ${d['cost_usd']:.4f}")
        return "\n".join(lines)

    def get_model_breakdown(self) -> dict:
        by_model = {}
        with self._lock:
            for s in self.data.get("sessions", []):
                model = s.get("model", "unknown")
                if model not in by_model:
                    by_model[model] = {
                        "calls": 0,
                        "cost_usd": 0.0,
                        "prompt_tokens": 0,
                        "completion_tokens": 0,
                        "cache_hit_tokens": 0,
                        "reasoning_tokens": 0,
                        "agents": set(),
                    }
                m = by_model[model]
                m["calls"] += 1
                m["cost_usd"] += s.get("cost_usd", 0)
                m["prompt_tokens"] += s.get("prompt_tokens", 0)
                m["completion_tokens"] += s.get("completion_tokens", 0)
                m["cache_hit_tokens"] += s.get("cache_hit_tokens", 0)
                m["reasoning_tokens"] += s.get("reasoning_tokens", 0)
                if s.get("agent"):
                    m["agents"].add(s["agent"])
        result = {}
        for model, data in by_model.items():
            result[model] = dict(data)
            result[model]["agents"] = sorted(data["agents"])
            result[model]["cost_usd"] = round(data["cost_usd"], 6)
        return result

    def get_model_tier_breakdown(self) -> dict:
        tiers = {}
        for e in self.data.get("sessions", []):
            model = e.get("model", "unknown")
            tokens = e.get("completion_tokens", 0) + e.get("prompt_tokens", 0)
            if "mimo" in model:
                tier = "mimo"
            elif model in ("go-pro", "deepseek-pro"):
                tier = "pro"
            elif "kimi" in model:
                tier = "kimi"
            else:
                tier = "flash"
            if tier not in tiers:
                tiers[tier] = {"calls": 0, "tokens": 0, "cost": 0.0}
            tiers[tier]["calls"] += 1
            tiers[tier]["tokens"] += tokens
            tiers[tier]["cost"] += e.get("cost_usd", 0)
        return tiers

    def get_routing_report(self) -> str:
        model_bd = self.get_model_breakdown()
        stats = self.get_stats()
        cb_status = _ETHER_CIRCUIT_BREAKER.get_status()
        lines = [
            "## Multi-Model Routing Report",
            f"- Total calls: {stats['total_calls']}",
            f"- Total cost: ${stats['total_cost_usd']:.4f}",
            "",
            "### Breakdown by Model",
        ]
        for model in ["go-flash", "go-pro", "go-kimi-latest"]:
            data = model_bd.get(model, {})
            if data:
                pct = round(data["calls"] / max(stats["total_calls"], 1) * 100, 1)
                lines.append(f"\n#### {model} ({pct}% of traffic)")
                lines.append(f"- Calls: {data['calls']} ({pct}%)")
                lines.append(f"- Cost: ${data['cost_usd']:.4f}")
                lines.append(f"- Prompt: {data['prompt_tokens']:,} | Completion: {data['completion_tokens']:,}")
                lines.append(f"- Cache hit: {data['cache_hit_tokens']:,} | Reasoning: {data['reasoning_tokens']:,}")
                lines.append(f"- Agents: {', '.join(data.get('agents', []))}")
            else:
                lines.append(f"\n#### {model} — no calls yet")
        lines.append("\n### Circuit Breaker")
        for model, s in cb_status.items():
            icon = "✅" if s["state"] == "closed" else "⚠️" if s["state"] == "half-open" else "🔴"
            lines.append(f"- {icon} {model}: {s['state']} ({s['failures']} failures)")
        return "\n".join(lines)

    WEEKLY_BUDGET_WARN_THRESHOLD = 0.8  # 80%

    def check_budget(self) -> dict:
        """Verifica estado del budget semanal y emite alertas si es necesario.
        Usa los últimos 7 días de daily_breakdown para el cálculo semanal.
        Returns: {"status": str, "message": str, "alerts": list[str]}
        """
        stats = self.get_stats()
        # Calcular costo semanal de los últimos 7 días
        weekly_breakdown = dict(sorted(stats.get("daily_breakdown", {}).items(), reverse=True)[:7])
        weekly_cost = sum(d["cost_usd"] for d in weekly_breakdown.values())
        alerts = []

        for tier, cap in COST_CAPS.items():
            model_bd = self.get_model_breakdown()
            tier_cost = sum(
                data["cost_usd"]
                for model, data in model_bd.items()
                if model.startswith(f"go-{tier}") or (tier == "kimi" and "kimi" in model)
            )
            if tier_cost > cap["weekly_usd"] * WEEKLY_BUDGET_WARN_THRESHOLD:
                pct = round(tier_cost / cap["weekly_usd"] * 100, 1)
                alerts.append(f"⚠️ {tier}: ${tier_cost:.2f}/{cap['weekly_usd']} ({pct}%)")

            if tier_cost > cap["weekly_usd"]:
                alerts.append(f"🔴 {tier}: EXCEEDED ${tier_cost:.2f} > ${cap['weekly_usd']}")

        status = "ok" if not alerts else "warning" if not any("EXCEEDED" in a for a in alerts) else "exceeded"
        return {
            "status": status,
            "weekly_cost_usd": round(weekly_cost, 4),
            "alerts": alerts,
            "message": "; ".join(alerts) if alerts else "All budgets within limits",
        }

    def get_budget_report(self) -> dict:
        """Weekly budget usage per model tier."""
        stats = self.get_stats()
        weekly_breakdown = dict(sorted(stats.get("daily_breakdown", {}).items(), reverse=True)[:7])
        weekly = sum(d["cost_usd"] for d in weekly_breakdown.values())
        return {
            "weekly_cost_usd": round(weekly, 4),
            "flash_cap": COST_CAPS["flash"]["weekly_usd"],
            "pro_cap": COST_CAPS["pro"]["weekly_usd"],
            "kimi_cap": COST_CAPS["kimi"]["weekly_usd"],
            "flash_used_pct": round(weekly * 0.8 / COST_CAPS["flash"]["weekly_usd"] * 100, 1),
        }

    def get_recent_sessions(self, n: int = 10) -> list:
        """Devuelve las últimas n sesiones trackeadas."""
        with self._lock:
            return list(self.data.get("sessions", []))[-n:]

    def get_content_type_breakdown(self) -> dict:
        breakdown = {}
        for e in self.data.get("sessions", []):
            ct = e.get("content_type", "text")
            breakdown[ct] = breakdown.get(ct, 0) + 1
        return breakdown
