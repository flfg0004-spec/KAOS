"""
KAOS Verification Chain — Verificación cruzada entre agentes
"""
import json
import hashlib
from datetime import datetime, date
from pathlib import Path
import sys
sys.path.insert(0, str(Path(__file__).resolve().parent))
from score_engine import compute_composite, evaluate

BASE = Path(__file__).resolve().parent.parent
VERIFICATION_DIR = BASE / ".vault" / "quality" / "verifications"
SESSION_DIR = BASE / ".vault" / "quality" / "sessions"


def generate_claim_id(agent, topic):
    raw = f"{agent}-{date.today().isoformat()}-{topic}"
    return raw.lower().replace(" ", "-")


def verify_output(claim_id, agent_origin, agent_verifier, scores, profile="desarrollo", discrepancies=None):
    verification = {
        "verification_id": f"v-{date.today().strftime('%Y%m%d')}-{datetime.now().strftime('%H%M%S')}",
        "claim_id": claim_id,
        "agent_origin": agent_origin,
        "agent_verifier": agent_verifier,
        "timestamp": datetime.now().isoformat(),
        "profile": profile,
        "scores": scores,
        "evaluations": {k: evaluate(k, v, profile) for k, v in scores.items()},
        "discrepancies": discrepancies or [],
        "evidence_hash": hashlib.sha256(json.dumps(scores, sort_keys=True).encode()).hexdigest()[:16],
        "verifier_notes": "",
    }
    VERIFICATION_DIR.mkdir(parents=True, exist_ok=True)
    path = VERIFICATION_DIR / f"{verification['verification_id']}.json"
    with open(path, "w") as f:
        json.dump(verification, f, indent=2, ensure_ascii=False)
    return verification, path


def run_verification_chain(outputs, profile="desarrollo"):
    """
    Ejecuta la cadena triangular completa:
    Aletheia → Kosmos → Metis → Aletheia
    """
    chain_results = []
    pairs = [
        ("aletheia", "kosmos", ["veracidad", "coherencia"]),
        ("kosmos", "metis", ["completitud", "utilidad"]),
        ("metis", "aletheia", ["veracidad", "reproducibilidad"]),
    ]
    for origin, verifier, dims in pairs:
        if origin in outputs:
            scores = {d: outputs[origin].get(d, 50) for d in dims}
            claim_id = generate_claim_id(origin, "output")
            verification, path = verify_output(claim_id, origin, verifier, scores, profile)
            chain_results.append(verification)
    return chain_results


if __name__ == "__main__":
    profile = sys.argv[1] if len(sys.argv) > 1 else "desarrollo"
    dummy_outputs = {
        "aletheia": {"veracidad": 82, "coherencia": 76},
        "kosmos": {"completitud": 80, "utilidad": 78},
        "metis": {"veracidad": 85, "reproducibilidad": 72},
    }
    results = run_verification_chain(dummy_outputs, profile)
    print(json.dumps(results, indent=2, ensure_ascii=False))
