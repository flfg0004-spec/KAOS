"""AetherConfig — loads Aether configuration from aether.yaml with env var overrides."""

import logging
import os
import signal
from pathlib import Path

AETHER_YAML = Path(__file__).resolve().parent.parent.parent / "aether.yaml"
_LOG = logging.getLogger(__name__)


class AetherConfig:
    """Single source of truth for all Aether routing configuration.

    Loads from aether.yaml. Env vars override feature flag values.
    Provides dict/list access matching the original config.py constants.
    """

    def __init__(self, path: str | Path = None):
        import yaml
        path = path or AETHER_YAML
        with open(path) as f:
            self._data = yaml.safe_load(f)
        self._apply_env_overrides()

    def _apply_env_overrides(self):
        flags = self._data.get("feature_flags", {})
        env_map = {
            "ETHER_MIMO_ENABLED": "ether_mimo_enabled",
            "ETHER_MIMO_DIRECT_ENABLED": "ether_mimo_direct_enabled",
            "ETHER_KIMI_ENABLED": "ether_kimi_enabled",
            "ETHER_CONTEXT_ROUTING": "ether_context_routing",
            "ETHER_MULTIMODAL_ENABLED": "ether_multimodal_enabled",
            "ETHER_BUDGET_ENFORCEMENT": "ether_budget_enforcement",
            "ETHER_LANGFUSE_ENABLED": "ether_langfuse_enabled",
            "ETHER_DEEPEVAL_ENABLED": "ether_deepeval_enabled",
            "ETHER_QUALITY_ROUTING": "quality_routing_enabled",
            "ETHER_ROUTER9_ENABLED": "ether_router9_enabled",
        }
        for env_key, flag_key in env_map.items():
            val = os.environ.get(env_key)
            if val is not None:
                flags[flag_key] = val.lower() in ("1", "true")

        sample = os.environ.get("ETHER_EVAL_SAMPLE_SIZE")
        if sample is not None:
            try:
                flags["ether_eval_sample_size"] = int(sample)
            except ValueError:
                pass

    # ── Accessors matching config.py constants ────────────────

    @property
    def TASK_MODEL_MAP(self) -> dict:
        raw = dict(self._data.get("task_model_map", {}))
        result = {}
        for task, rules in raw.items():
            if isinstance(rules, dict):
                rules = [rules]
            result[task] = rules
        return result

    @property
    def AGENT_DEFAULT_TASK(self) -> dict:
        return dict(self._data.get("agent_default_task", {}))

    @property
    def AGENT_TASK_MODEL(self) -> dict:
        return dict(self._data.get("agent_task_model", {}))

    @property
    def MODEL_TIERS(self) -> dict:
        return dict(self._data.get("model_tiers", {}))

    @property
    def MODEL_FALLBACK_CHAIN(self) -> dict:
        return dict(self._data.get("fallback_chains", {}))

    @property
    def COST_RATES(self) -> dict:
        return dict(self._data.get("cost_rates", {}))

    @property
    def COST_CAPS(self) -> dict:
        return dict(self._data.get("cost_caps", {}))

    @property
    def BUDGETS(self) -> dict:
        b = dict(self._data.get("budgets", {}))
        kb = b.pop("kimi_long", None)
        self._kimi_budgets = {"kimi": kb} if kb else {}
        return b

    @property
    def KIMI_BUDGETS(self) -> dict:
        return dict(self._kimi_budgets)

    @property
    def THINKING_CONFIG(self) -> dict:
        raw = self._data.get("thinking_config", {})
        result = {}
        for k, v in raw.items():
            key = None if k == "null" else k
            result[key] = v
        return result

    @property
    def FEATURE_FLAGS(self) -> dict:
        return dict(self._data.get("feature_flags", {}))

    def get_flag(self, name: str, default=None):
        return self._data.get("feature_flags", {}).get(name, default)

    def to_dict(self) -> dict:
        return {
            "version": self._data.get("version"),
            "task_model_map": self.TASK_MODEL_MAP,
            "agent_default_task": self.AGENT_DEFAULT_TASK,
            "model_tiers": self.MODEL_TIERS,
            "cost_rates": self.COST_RATES,
            "cost_caps": self.COST_CAPS,
            "fallback_chains": self.MODEL_FALLBACK_CHAIN,
            "budgets": self.BUDGETS,
            "thinking_config": self.THINKING_CONFIG,
            "feature_flags": self.FEATURE_FLAGS,
        }

    def validate(self) -> list[str]:
        errors = []
        models = set(self.COST_RATES.keys())
        for task, rules in self.TASK_MODEL_MAP.items():
            if isinstance(rules, list):
                for rule in rules:
                    m = rule.get("model") if isinstance(rule, dict) else getattr(rule, "model", None)
                    if m and m not in models:
                        errors.append(f"task '{task}': model '{m}' not found in cost_rates")
                    t = rule.get("tier") if isinstance(rule, dict) else getattr(rule, "tier", None)
                    if t and t not in self.MODEL_TIERS:
                        errors.append(f"task '{task}': tier '{t}' not found in model_tiers")
            elif isinstance(rules, dict):
                m = rules.get("model")
                if m and m not in models:
                    errors.append(f"task '{task}': model '{m}' not found in cost_rates")
                t = rules.get("tier")
                if t and t not in self.MODEL_TIERS:
                    errors.append(f"task '{task}': tier '{t}' not found in model_tiers")
        for chain_name, chain in self.MODEL_FALLBACK_CHAIN.items():
            for m in chain:
                if m not in models:
                    errors.append(f"fallback chain '{chain_name}': model '{m}' not in cost_rates")
        return errors


_config_instance = None


def get_config(path: str | Path = None) -> AetherConfig:
    global _config_instance
    if _config_instance is None:
        _config_instance = AetherConfig(path)
    return _config_instance


def reload_config(path: str | Path = None):
    global _config_instance
    _config_instance = AetherConfig(path)
    _config_instance.validate()
    _LOG.info("Config reloaded from %s", path or AETHER_YAML)
    # Propagate new values to config.py module-level constants
    import lib.aether.config as _cfg_module
    _cfg_module._cfg = _config_instance
    _cfg_module.refresh_constants()


def _handle_sighup(signum, frame):
    _LOG.info("SIGHUP received — reloading config")
    reload_config()


try:
    signal.signal(signal.SIGHUP, _handle_sighup)
except (AttributeError, ValueError):
    pass
