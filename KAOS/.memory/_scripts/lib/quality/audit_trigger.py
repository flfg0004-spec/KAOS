import logging
import subprocess
from datetime import datetime
from pathlib import Path

from lib.file_lock import locked_write

_LOG = logging.getLogger(__name__)

AUDIT_DIR = Path(__file__).resolve().parent.parent.parent / ".vault" / "quality" / "hooks"

AETHER_DIR = Path(__file__).resolve().parent.parent / "aether"

AETHER_YAML = Path(__file__).resolve().parent.parent.parent / "aether.yaml"


def get_changed_aether_files():
    try:
        result = subprocess.run(
            ["git", "diff", "--name-only", "HEAD"],
            capture_output=True, text=True, check=False, timeout=30,
            cwd=AETHER_DIR.parent.parent.parent,
        )
        if result.returncode != 0:
            return []
        files = []
        for line in result.stdout.strip().splitlines():
            line = line.strip()
            if not line:
                continue
            abs_path = (AETHER_DIR.parent.parent.parent / line).resolve()
            if "lib/aether/" in str(abs_path) and abs_path.suffix == ".py":
                files.append(str(abs_path))
        return files
    except Exception:
        return []


def check_imports(file_paths):
    results = []
    for fp in file_paths:
        try:
            with open(fp, encoding="utf-8") as f:
                source = f.read()
            compile(source, fp, "exec")
            results.append({"file": fp, "status": "ok", "error": None})
        except SyntaxError as e:
            results.append({"file": fp, "status": "error", "error": str(e)})
        except Exception as e:
            results.append({"file": fp, "status": "error", "error": str(e)})
    return results


def check_feature_flags():
    results = []
    try:
        import yaml
        with open(AETHER_YAML) as f:
            data = yaml.safe_load(f)

        flags = data.get("feature_flags", {})
        if not flags:
            return [{"flag": "_none_", "in_config": False, "in_refresh": False}]

        from lib.aether import config as cfg

        refresh_names = {
            "ETHER_MIMO_ENABLED", "ETHER_MIMO_DIRECT_ENABLED",
            "ETHER_KIMI_ENABLED", "ETHER_CONTEXT_ROUTING",
            "ETHER_MULTIMODAL_ENABLED", "ETHER_BUDGET_ENFORCEMENT",
            "ETHER_LANGFUSE_ENABLED", "ETHER_DEEPEVAL_ENABLED",
            "QUALITY_ROUTING_ENABLED", "ETHER_EVAL_SAMPLE_SIZE",
            "ETHER_ROUTER9_ENABLED",
        }

        const_to_flag = {
            "ETHER_MIMO_ENABLED": "ether_mimo_enabled",
            "ETHER_MIMO_DIRECT_ENABLED": "ether_mimo_direct_enabled",
            "ETHER_KIMI_ENABLED": "ether_kimi_enabled",
            "ETHER_CONTEXT_ROUTING": "ether_context_routing",
            "ETHER_MULTIMODAL_ENABLED": "ether_multimodal_enabled",
            "ETHER_BUDGET_ENFORCEMENT": "ether_budget_enforcement",
            "ETHER_LANGFUSE_ENABLED": "ether_langfuse_enabled",
            "ETHER_DEEPEVAL_ENABLED": "ether_deepeval_enabled",
            "QUALITY_ROUTING_ENABLED": "quality_routing_enabled",
            "ETHER_EVAL_SAMPLE_SIZE": "ether_eval_sample_size",
            "ETHER_ROUTER9_ENABLED": "ether_router9_enabled",
        }

        for flag_name, flag_value in flags.items():
            in_config = hasattr(cfg, flag_name.upper())
            in_refresh = flag_name.upper() in refresh_names
            results.append({
                "flag": flag_name,
                "in_config": in_config,
                "in_refresh": in_refresh,
            })
    except Exception as e:
        results.append({"flag": "_error_", "in_config": False, "in_refresh": False, "error": str(e)})
    return results


def check_config_consistency():
    results = []
    try:
        import yaml
        with open(AETHER_YAML) as f:
            data = yaml.safe_load(f)

        cost_rates = data.get("cost_rates", {})
        cost_models = set(cost_rates.keys())

        fallback_chains = data.get("fallback_chains", {})
        fb_models = set()
        for chain_models in fallback_chains.values():
            fb_models.update(chain_models)

        missing_in_cost = fb_models - cost_models
        if missing_in_cost:
            results.append({
                "check": "fallback_chains_models_in_cost_rates",
                "status": "warning",
                "detail": f"Models in fallback_chains missing from cost_rates: {sorted(missing_in_cost)}",
            })
        else:
            results.append({
                "check": "fallback_chains_models_in_cost_rates",
                "status": "ok",
                "detail": "All fallback chain models have cost rate entries",
            })

        task_model_map = data.get("task_model_map", {})
        tmm_models = set()
        for rules in task_model_map.values():
            if isinstance(rules, dict):
                rules = [rules]
            for r in rules:
                if isinstance(r, dict) and "model" in r:
                    tmm_models.add(r["model"])

        missing_in_cost = tmm_models - cost_models
        if missing_in_cost:
            results.append({
                "check": "task_model_map_models_in_cost_rates",
                "status": "warning",
                "detail": f"Models in task_model_map missing from cost_rates: {sorted(missing_in_cost)}",
            })
        else:
            results.append({
                "check": "task_model_map_models_in_cost_rates",
                "status": "ok",
                "detail": "All task_model_map models have cost rate entries",
            })

        if not results:
            results.append({
                "check": "config_consistency",
                "status": "ok",
                "detail": "No inconsistencies found",
            })
    except Exception as e:
        results.append({
            "check": "config_consistency",
            "status": "error",
            "detail": str(e),
        })
    return results


def run_audit():
    AUDIT_DIR.mkdir(parents=True, exist_ok=True)
    changed = get_changed_aether_files()

    imports_result = check_imports(changed) if changed else []
    feature_flags_result = check_feature_flags()
    config_consistency_result = check_config_consistency()

    errors = 0
    warnings = 0
    for r in imports_result:
        if r.get("status") == "error":
            errors += 1
    for r in feature_flags_result:
        if not r.get("in_config"):
            warnings += 1
    for r in config_consistency_result:
        if r.get("status") == "error":
            errors += 1
        elif r.get("status") == "warning":
            warnings += 1

    result = {
        "timestamp": datetime.now().strftime("%Y%m%d_%H%M%S"),
        "files_changed": changed,
        "imports": imports_result,
        "feature_flags": feature_flags_result,
        "config_consistency": config_consistency_result,
        "summary": {
            "total_checks": len(imports_result) + len(feature_flags_result) + len(config_consistency_result),
            "errors": errors,
            "warnings": warnings,
        },
    }

    out_path = AUDIT_DIR / f"audit_{result['timestamp']}.json"
    locked_write(out_path, result)
    _LOG.info("Audit saved to %s", out_path)
    return result
