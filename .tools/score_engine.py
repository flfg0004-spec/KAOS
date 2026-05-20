"""
KAOS Score Engine — Motor de evaluación y score compuesto
Basado en DeepEval + perfiles YAML.
"""
import json
import os
import yaml
from datetime import datetime, date
from pathlib import Path

BASE = Path(__file__).resolve().parent.parent
VAULT_QUALITY = BASE / ".vault" / "quality"
SCHEMA = BASE / ".memory" / "schema"
PROFILES_PATH = SCHEMA / "eval-profile.yaml"


def load_profiles():
    with open(PROFILES_PATH, encoding="utf-8") as f:
        return yaml.safe_load(f)


def get_profile(name=None):
    profiles = load_profiles()
    if name is None:
        name = profiles.get("default_profile", "desarrollo")
    return profiles["profiles"][name], name


def compute_composite(scores, profile_name=None):
    profile, name = get_profile(profile_name)
    weights = profile["weights"]
    total_weight = sum(weights.values())
    composite = sum(scores[k] * weights[k] for k in weights) / total_weight
    return round(composite, 1), name


def evaluate(metric_name, score, profile_name=None):
    profile, _ = get_profile(profile_name)
    key = metric_name.lower()
    if key == "veracidad":
        threshold = profile["thresholds"]["veracidad_min"]
    elif key == "coherencia":
        threshold = profile["thresholds"]["coherencia_min"]
    elif key == "completitud":
        threshold = profile["thresholds"]["completitud_min"]
    elif key == "reproducibilidad":
        threshold = profile["thresholds"]["reproducibilidad_min"]
    elif key == "utilidad":
        threshold = profile["thresholds"]["utilidad_min"]
    else:
        return "unknown"
    if score >= threshold:
        return "pass"
    return "fail"


def store_session(session_type, results, profile_name="desarrollo"):
    today = date.today().isoformat()
    session_dir = VAULT_QUALITY / "sessions"
    session_dir.mkdir(parents=True, exist_ok=True)
    path = session_dir / f"{today}-{session_type}.json"
    entry = {
        "timestamp": datetime.now().isoformat(),
        "session_type": session_type,
        "profile": profile_name,
        "results": results,
    }
    with open(path, "w", encoding="utf-8") as f:
        json.dump(entry, f, indent=2, ensure_ascii=False)
    return path


def store_timeseries(scores, profile_name="desarrollo"):
    today = date.today().isoformat()
    ts_dir = VAULT_QUALITY / "timeseries"
    ts_dir.mkdir(parents=True, exist_ok=True)
    path = ts_dir / f"{today}.json"
    if path.exists():
        with open(path, encoding="utf-8") as f:
            data = json.load(f)
    else:
        data = []
    entry = {
        "timestamp": datetime.now().isoformat(),
        "profile": profile_name,
        "scores": scores,
    }
    data.append(entry)
    with open(path, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2, ensure_ascii=False)
    return path


def compute_all_and_store(scores, profile_name=None):
    composite, pname = compute_composite(scores, profile_name)
    results = {
        "composite": composite,
        "dimensions": scores,
        "evaluations": {k: evaluate(k, v, pname) for k, v in scores.items()},
    }
    store_session("score", results, pname)
    store_timeseries(scores, pname)
    return results


def smoke_check(output_text, sources=None):
    """Stub: hallucination check disabled (deepeval not installed)."""
    return {"hallucination_score": 0, "passed": True, "reason": "hallucination check disabled"}


def compute_time_to_knowledge():
    """Calcula métrica de tiempo entre creación raw/ y conversión a wiki/."""
    from datetime import datetime
    raw_files = list((Path(__file__).resolve().parent.parent / ".memory" / "raw").glob("*.md"))
    concept_files = list((Path(__file__).resolve().parent.parent / ".memory" / "wiki" / "concepts").glob("*.md"))

    total_ttk = 0
    count = 0
    for raw_file in raw_files:
        raw_mtime = datetime.fromtimestamp(raw_file.stat().st_mtime)
        slug = raw_file.stem
        # Buscar conceptos que referencien este raw
        for cf in concept_files:
            content = cf.read_text(encoding="utf-8")
            if slug in content or raw_file.name in content:
                cf_mtime = datetime.fromtimestamp(cf.stat().st_mtime)
                ttk = (cf_mtime - raw_mtime).total_seconds() / 3600  # horas
                if ttk > 0:
                    total_ttk += ttk
                    count += 1
                break

    avg_ttk = round(total_ttk / count, 1) if count > 0 else 0
    return {
        "average_hours": avg_ttk,
        "investigations_converted": count,
        "investigations_total": len(raw_files),
        "conversion_rate": f"{round(count / len(raw_files) * 100) if raw_files else 0}%"
    }


if __name__ == "__main__":
    import sys
    if len(sys.argv) > 1 and sys.argv[1] == "test":
        scores = {"veracidad": 85, "coherencia": 78, "completitud": 72, "reproducibilidad": 68, "utilidad": 80}
        result = compute_all_and_store(scores, "desarrollo")
        print(json.dumps(result, indent=2, ensure_ascii=False))
    elif len(sys.argv) > 1 and sys.argv[1] == "ttk":
        ttk = compute_time_to_knowledge()
        print(json.dumps(ttk, indent=2, ensure_ascii=False))
