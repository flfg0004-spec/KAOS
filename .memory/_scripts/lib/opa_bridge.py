"""OPA Policy Bridge — evaluates architecture governance policies."""

import json
import logging
import re
import time
from pathlib import Path

logger = logging.getLogger("opa_bridge")

POLICY_DIR = Path(__file__).resolve().parent.parent.parent.parent / "policy"

POLICY_PACKAGES: dict[str, str] = {
    "architecture": "kaos.architecture",
    "agents": "kaos.agents",
    "synthesis": "kaos.synthesis",
}

# Prometheus metrics
try:
    from prometheus_client import Counter, Histogram

    OPA_EVAL_COUNT = Counter("opa_evaluations_total", "Total OPA evaluations", ["policy_type", "allowed"])
    OPA_LATENCY = Histogram(
        "opa_evaluation_seconds",
        "OPA evaluation latency",
        buckets=[0.001, 0.005, 0.01, 0.025, 0.05, 0.1, 0.25, 0.5, 1.0],
    )
except ImportError:
    OPA_EVAL_COUNT = None
    OPA_LATENCY = None


def _track_metrics(policy_type: str):
    def decorator(func):
        def wrapper(*args, **kwargs):
            start = time.time()
            result = func(*args, **kwargs)
            duration = time.time() - start
            if OPA_EVAL_COUNT:
                OPA_EVAL_COUNT.labels(policy_type=policy_type, allowed=str(result.get("allowed", False))).inc()
            if OPA_LATENCY:
                OPA_LATENCY.observe(duration)
            return result

        return wrapper

    return decorator


try:
    from lib.config import OPA_EVAL_MODE
except Exception:
    OPA_EVAL_MODE = "auto"

_HAS_OPA = False
if OPA_EVAL_MODE == "native":
    _HAS_OPA = False
elif OPA_EVAL_MODE == "opa":
    _HAS_OPA = True
else:
    try:
        import subprocess

        result = subprocess.run(["opa", "version"], capture_output=True, text=True, timeout=5)
        _HAS_OPA = result.returncode == 0
    except Exception:
        pass


@_track_metrics("architecture")
def _evaluate_architecture_policies(input_data: dict) -> list:
    denials = []
    adr = input_data.get("kosmos_adr", {})
    code = input_data.get("kratos_code", "")
    required = adr.get("required_pattern", "")
    if required and required not in code:
        denials.append({"msg": f"Code violates ADR '{adr.get('title', '')}': missing required pattern '{required}'"})
    approved = {
        "microservices",
        "modular-monolith",
        "event-driven",
        "layered",
        "hexagonal",
        "cqrs",
        "clean-architecture",
    }
    pattern = input_data.get("architecture_pattern", "")
    if pattern and pattern not in approved:
        denials.append({"msg": f"Architecture pattern '{pattern}' is not in approved list"})
    dep = input_data.get("dependency", {})
    if dep.get("source") and dep.get("source") == dep.get("target"):
        denials.append({"msg": f"Self-dependency detected: '{dep['source']}' depends on itself"})
    adr_input = input_data.get("adr", {})
    required_fields = {"title", "context", "decision", "consequences", "status"}
    if adr_input:
        missing = required_fields - set(adr_input.keys())
        if missing:
            denials.append({"msg": f"ADR is missing required fields: {', '.join(sorted(missing))}"})
    concept = input_data.get("concept", {})
    if concept.get("min_confidence", 0) > 0 and concept.get("confidence", 0) < concept["min_confidence"]:
        denials.append(
            {
                "msg": f"Concept '{concept.get('name', '')}' confidence ({concept.get('confidence', 0)}) below threshold ({concept['min_confidence']})"
            }
        )
    bridge = input_data.get("cross_agent_bridge", {})
    if bridge.get("expected") and bridge.get("value", "") == "":
        denials.append({"msg": f"Cross-agent bridge '{bridge.get('name', '')}' is empty but expected to be populated"})
    return denials


@_track_metrics("agents")
def _evaluate_agent_policies(input_data: dict) -> list:
    denials = []
    agent = input_data.get("agent", "")
    output = input_data.get("output", "")

    # ── Per-agent content policies ──
    if agent == "aletheia" and "[[" not in output:
        denials.append({"msg": "Aletheia research output must contain wikilinks to sources"})
    if agent == "kosmos" and "ADR" not in output and "# " not in output:
        denials.append({"msg": "Kosmos architecture analysis must reference ADR and have structure"})
    if agent == "metis" and "OKR" not in output and "objective" not in output.lower():
        denials.append({"msg": "Metis strategy output must contain OKRs or objectives"})
    if agent == "mnemosyne" and "[[" not in output:
        denials.append({"msg": "Mnemosyne curation must contain wikilinks to concepts"})

    # ── Universal quality policies ──
    if len(output) < 50:
        denials.append({"msg": f"Agent '{agent}' output too short ({len(output)} chars, minimum 50)"})

    # ── Code-specific security policies (kratos) ──
    if agent == "kratos":
        if "```" not in output:
            denials.append({"msg": "Kratos code output must contain code blocks"})
        # Security anti-patterns
        dangerous_patterns = [
            (r"eval\s*\(", "eval() usage is prohibited"),
            (r"exec\s*\(", "exec() usage is prohibited"),
            (r"__import__\s*\(", "dynamic import via __import__ is prohibited"),
            (r"pickle\.loads?\s*\(", "unsafe deserialization via pickle is prohibited"),
            (r"(?i)password\s*=\s*['\"]", "hardcoded password detected"),
            (r"(?i)(api[_-]?key|secret|token)\s*=\s*['\"]", "hardcoded credential detected"),
        ]
        for pattern, msg in dangerous_patterns:
            if re.search(pattern, output):
                denials.append({"msg": f"Security policy violation: {msg}"})

        # Code quality policies
        code_blocks = re.findall(r"```\w+\n(.*?)```", output, re.DOTALL)
        for block in code_blocks:
            if "def " not in block and "class " not in block and "fn " not in block and "func " not in block:
                denials.append({"msg": "Code block must contain a function or class definition"})

    return denials


def evaluate(policy_type: str, input_data: dict) -> dict:
    if _HAS_OPA:
        try:
            pkg = POLICY_PACKAGES.get(policy_type, f"kaos.{policy_type}")
            policy_file = POLICY_DIR / f"{policy_type}.rego"
            if not policy_file.exists():
                logger.warning("Policy file not found: %s", policy_file)
                return {"allowed": True, "denials": [], "policy_source": "no_policy"}
            result = subprocess.run(
                ["opa", "eval", f"--data={policy_file}", f"--input={json.dumps(input_data)}", f"data.{pkg}.deny"],
                capture_output=True,
                text=True,
                timeout=10,
            )
            if result.returncode == 0:
                denials = json.loads(result.stdout).get("result", [])
                return {"allowed": len(denials) == 0, "denials": denials, "policy_source": "opa"}
        except Exception as e:
            logger.warning(f"OPA evaluation failed: {e}, using native fallback")
    denials = _evaluate_native(policy_type, input_data)
    return {"allowed": len(denials) == 0, "denials": denials, "policy_source": "native"}


def _evaluate_native(policy_type: str, input_data: dict) -> list:
    if policy_type == "architecture":
        return _evaluate_architecture_policies(input_data)
    elif policy_type == "agents":
        return _evaluate_agent_policies(input_data)
    elif policy_type == "synthesis":
        return _evaluate_synthesis_policies(input_data)
    return []


@_track_metrics("synthesis")
def _evaluate_synthesis_policies(input_data: dict) -> list:
    denials = []
    synthesis = input_data.get("synthesis", {})
    level = synthesis.get("level", "")
    score = synthesis.get("score", 100)
    diff_ratio = synthesis.get("diff_ratio", 0)

    if level == "CANONICAL":
        denials.append({"msg": "CANONICAL documents cannot be auto-synthesized"})
    if score < 10:
        denials.append({"msg": f"Score {score} below minimum threshold for synthesis"})
    max_diff = synthesis.get("max_diff_ratio", 0.5)
    if diff_ratio > max_diff:
        denials.append({"msg": f"Diff ratio {diff_ratio:.2f} exceeds maximum {max_diff:.2f}"})
    return denials


def check_architecture(adr: dict = None, code: str = "", pattern: str = "") -> dict:
    return evaluate(
        "architecture",
        {"kosmos_adr": adr or {}, "kratos_code": code, "architecture_pattern": pattern, "adr": adr or {}},
    )


def check_agent(agent: str, output: str) -> dict:
    return evaluate("agents", {"agent": agent, "output": output})


def check_synthesis(synthesis_data: dict) -> dict:
    return evaluate("synthesis", {"synthesis": synthesis_data})


def status() -> dict:
    return {
        "opa_available": _HAS_OPA,
        "mode": OPA_EVAL_MODE,
        "policy_files": [str(p) for p in POLICY_DIR.glob("*.rego")] if POLICY_DIR.exists() else [],
    }
