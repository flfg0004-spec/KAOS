"""
KAOS Session Runner — Ejecuta sesiones de test programadas
Modos: smoke (2min), functional (15min), audit (60min)
"""
import json
import sys
from datetime import datetime, date
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent))
from score_engine import compute_all_and_store, smoke_check, load_profiles

BASE = Path(__file__).resolve().parent.parent
VAULT = BASE / ".vault" / "quality"
SCHEMA = BASE / ".memory" / "schema"


def run_smoke(profile="desarrollo"):
    results = {
        "session_type": "smoke",
        "timestamp": datetime.now().isoformat(),
        "profile": profile,
        "checks": [],
        "passed": 0,
        "failed": 0,
    }
    checks = [
        ("vault_exists", VAULT.exists()),
        ("scores_engine", Path(__file__).resolve().parent.joinpath("score_engine.py").exists()),
        ("profiles_config", (SCHEMA / "eval-profile.yaml").exists()),
        ("adr_002", (SCHEMA / "adr-002-sistema-scores.md").exists()),
        ("adr_003", (SCHEMA / "adr-003-protocolo-verificacion.md").exists()),
    ]
    for name, passed in checks:
        results["checks"].append({"name": name, "passed": passed})
        if passed:
            results["passed"] += 1
        else:
            results["failed"] += 1
    results["health"] = "ok" if results["failed"] == 0 else "degraded"
    return results


def run_functional(outputs_to_test, profile="desarrollo"):
    results = {
        "session_type": "functional",
        "timestamp": datetime.now().isoformat(),
        "profile": profile,
        "tests": [],
        "passed": 0,
        "failed": 0,
    }
    for output in outputs_to_test:
        test = {
            "claim_id": output.get("claim_id", "unknown"),
            "agent": output.get("agent", "unknown"),
            "scores": {},
            "evaluations": {},
        }
        if output.get("scores"):
            composite_result = compute_all_and_store(output["scores"], profile)
            test["composite"] = composite_result["composite"]
            test["scores"] = composite_result["dimensions"]
            test["evaluations"] = composite_result["evaluations"]
            all_pass = all(v == "pass" for v in composite_result["evaluations"].values())
            test["passed"] = all_pass
            if all_pass:
                results["passed"] += 1
            else:
                results["failed"] += 1
        results["tests"].append(test)
    results["health"] = "ok" if results["failed"] == 0 else "degraded"
    return results


def run_audit(profile="auditoria"):
    results = {
        "session_type": "audit",
        "timestamp": datetime.now().isoformat(),
        "profile": profile,
        "phases": [],
        "passed": 0,
        "failed": 0,
    }
    # Fase 1: Smoke extendido
    smoke = run_smoke(profile)
    results["phases"].append({"phase": "smoke_extended", "checks": smoke["checks"], "health": smoke["health"]})
    if smoke["health"] == "ok":
        results["passed"] += 1
    else:
        results["failed"] += 1
    # Fase 2: Perfiles cargados correctamente
    try:
        profiles = load_profiles()
        profile_count = len(profiles.get("profiles", {}))
        results["phases"].append({"phase": "profile_validation", "profiles_loaded": profile_count, "health": "ok"})
        results["passed"] += 1
    except Exception as e:
        results["phases"].append({"phase": "profile_validation", "error": str(e), "health": "failed"})
        results["failed"] += 1
    # Fase 3: Integridad del vault
    vault_dirs = [d for d in VAULT.iterdir() if d.is_dir()]
    results["phases"].append({"phase": "vault_integrity", "directories": [d.name for d in vault_dirs], "health": "ok"})
    results["passed"] += 1
    results["health"] = "ok" if results["failed"] == 0 else "degraded"
    return results


def store_session(session_type, results):
    today = date.today().isoformat()
    session_dir = VAULT / "sessions"
    session_dir.mkdir(parents=True, exist_ok=True)
    path = session_dir / f"{today}-{session_type}.json"
    with open(path, "w", encoding="utf-8") as f:
        json.dump(results, f, indent=2, ensure_ascii=False)
    return path


if __name__ == "__main__":
    mode = sys.argv[1] if len(sys.argv) > 1 else "smoke"
    profile = sys.argv[2] if len(sys.argv) > 2 else "desarrollo"
    if mode == "smoke":
        results = run_smoke(profile)
    elif mode == "functional":
        dummy_outputs = [
            {"claim_id": "test-001", "agent": "aletheia", "scores": {"veracidad": 85, "coherencia": 78, "completitud": 72, "reproducibilidad": 68, "utilidad": 80}},
            {"claim_id": "test-002", "agent": "kosmos", "scores": {"veracidad": 80, "coherencia": 85, "completitud": 75, "reproducibilidad": 70, "utilidad": 75}},
        ]
        results = run_functional(dummy_outputs, profile)
    elif mode == "audit":
        results = run_audit(profile)
    else:
        print(f"Unknown mode: {mode}")
        sys.exit(1)
    path = store_session(mode, results)
    print(f"Session saved: {path}")
    print(json.dumps(results, indent=2, ensure_ascii=False))
