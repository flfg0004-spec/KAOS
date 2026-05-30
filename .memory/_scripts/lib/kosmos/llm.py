"""kosmos/llm.py — LLM integration for KosmosV2 (KosmosV3 C1+C2+C3).

Proporciona:
- call_llm(): LLM calls via DSOL routing with cache (C1)
- call_llm_with_fallback(): LLM with automatic heuristic fallback (C2)
- evaluate_adr_quality(): Quality gate pre-validate (C3)

Sin dependencias externas forzosas.
"""

import json
import logging
import os
import re
import threading
from typing import Any, Callable, Dict, List, Optional

logger = logging.getLogger(__name__)

# ── Testing mode detection ──
_IS_TESTING = os.environ.get("KAOS_TESTING") == "1" or os.environ.get("LLM_DIRECT_ENABLED") == "false"

# ── LLM cache ──
_LLM_CACHE: Dict[str, str] = {}
_LLM_CACHE_LOCK = threading.Lock()

_DEFAULT_TIMEOUT = 30


def _get_resolved_model(node: str, state: dict = None) -> str:
    """Get model name for a node via DSOL routing."""
    try:
        from lib.kosmos.routing import resolve_routing
        route = resolve_routing(node, state)
        return route.get("model", "go-flash")
    except Exception:
        return "go-flash"


def call_llm(prompt: str, node: str, state: dict = None, timeout: int = _DEFAULT_TIMEOUT) -> Optional[str]:
    """Call LLM for a pipeline node. Returns None on failure (C1).

    Usa DSOL routing para determinar qué modelo usar.
    En modo testing, retorna None sin llamar al LLM.
    """
    if _IS_TESTING:
        return None

    cache_key = f"{node}:{hash(prompt)}"
    with _LLM_CACHE_LOCK:
        if cache_key in _LLM_CACHE:
            return _LLM_CACHE[cache_key]

    model = _get_resolved_model(node, state)
    system_context = (
        f"Eres el nodo '{node}' del pipeline arquitectónico KosmosV2. "
        f"Modelo asignado: {model}. "
        f"Responde en español con estructura markdown clara."
    )
    full_prompt = f"{system_context}\n\n---\n\n{prompt}"

    try:
        from lib.agent_executor import _llm_or_executor_call
        result = _llm_or_executor_call("kosmos", full_prompt)
        if result and len(result) > 20:
            with _LLM_CACHE_LOCK:
                _LLM_CACHE[cache_key] = result
            return result
    except Exception as exc:
        logger.warning("C1: LLM call failed for %s: %s", node, exc)

    return None


def call_llm_with_fallback(prompt: str, node: str, fallback_fn: Callable[[], Any],
                           state: dict = None, timeout: int = _DEFAULT_TIMEOUT) -> Any:
    """Call LLM with automatic heuristic fallback (C2).

    Args:
        prompt: Prompt to send to LLM.
        node: Pipeline node name (for routing).
        fallback_fn: Zero-argument function called if LLM fails.
        state: Pipeline state dict.
        timeout: LLM timeout in seconds.

    Returns:
        LLM response string, or fallback_fn() result.
    """
    result = call_llm(prompt, node, state, timeout)
    if result is not None:
        return result
    logger.info("C2: LLM unavailable — heuristic fallback for %s", node)
    return fallback_fn()


def llm_status() -> dict:
    """Get LLM integration status."""
    return {
        "testing_mode": _IS_TESTING,
        "cache_size": len(_LLM_CACHE),
        "default_timeout": _DEFAULT_TIMEOUT,
    }


# ── Helpers ──


def _extract_json(text: str) -> Optional[Dict[str, Any]]:
    """Extract a JSON object from an LLM response.

    Handles:
    - Raw JSON: ``{"score": 85, ...}``
    - Markdown-fenced JSON: `````json\n{"score": 85, ...}\n`````
    - Partial text with embedded JSON: ``Here is the score: {"score": 85}``

    Returns:
        Parsed dict or None if no valid JSON found.
    """
    # 1. Try to extract a ```json ... ``` block
    match = re.search(r'```(?:json)\s*([\s\S]*?)```', text)
    if match:
        candidate = match.group(1).strip()
        try:
            return json.loads(candidate)
        except json.JSONDecodeError:
            pass

    # 2. Try to extract any ``` ... ``` block
    match = re.search(r'```\s*([\s\S]*?)```', text)
    if match:
        candidate = match.group(1).strip()
        try:
            return json.loads(candidate)
        except json.JSONDecodeError:
            pass

    # 3. Try direct parse of entire text
    try:
        return json.loads(text.strip())
    except json.JSONDecodeError:
        pass

    # 4. Try to find the first balanced { ... } block
    brace_depth = 0
    start = -1
    for i, ch in enumerate(text):
        if ch == "{":
            if start == -1:
                start = i
            brace_depth += 1
        elif ch == "}":
            brace_depth -= 1
            if brace_depth == 0 and start >= 0:
                try:
                    return json.loads(text[start : i + 1])
                except json.JSONDecodeError:
                    start = -1

    return None


def _heuristic_gate(adr_text: str, min_score: float) -> Dict[str, Any]:
    """Heuristic pre-validate (fallback when LLM is unavailable).

    Scores the ADR based on structural checks:
      +15 → Frontmatter YAML completo (id, title, status)
      +15 → Sección de Contexto / Context
      +15 → Sección de Opciones / Options
      +15 → Sección de Decisión / Decision
      +15 → Sección de Consecuencias / Consequences
      +10 → Diagrama o bloque de código
      +10 → Referencias a ADRs existentes (ADR-NNN)
       +5 → Scores de calidad en el texto

    Returns:
        Dict with score, gaps, passed, source="heuristic".
    """
    score = 0.0
    gaps: List[str] = []

    # Frontmatter YAML
    if "id:" in adr_text and "title:" in adr_text and "status:" in adr_text:
        score += 15.0
    else:
        gaps.append("Frontmatter YAML incompleto (id, title, status)")

    # Context section
    if re.search(r'##\s*Context[o]?\s*', adr_text):
        score += 15.0
    else:
        gaps.append("Falta sección de Contexto")

    # Options section
    if re.search(r'##\s*Opcion[es]?\s*(Consideradas)?\s*', adr_text) or \
       re.search(r'##\s*Options?\s*(Considered)?\s*', adr_text):
        score += 15.0
    else:
        gaps.append("Falta sección de Opciones Consideradas")

    # Decision section
    if re.search(r'##\s*Decisi[oó]n\s*', adr_text):
        score += 15.0
    else:
        gaps.append("Falta sección de Decisión")

    # Consequences
    if re.search(r'##\s*Consecuencias\s*', adr_text) or \
       re.search(r'##\s*Consequences\s*', adr_text):
        score += 15.0
    else:
        gaps.append("Falta sección de Consecuencias")

    # Diagram or code block
    if "```" in adr_text or "graph " in adr_text or "flowchart" in adr_text:
        score += 10.0

    # ADR cross-references
    if re.search(r'ADR-\d+', adr_text):
        score += 10.0
    else:
        gaps.append("No hay referencias a ADRs existentes")

    # Quality scores
    if re.search(r'[Ss]core', adr_text):
        score += 5.0

    score = round(min(score, 100.0), 1)
    passed = score >= min_score

    return {
        "score": score,
        "gaps": gaps,
        "passed": passed,
        "source": "heuristic",
    }


# ── Public API ──


def evaluate_adr_quality(
    adr_text: str,
    state: Optional[Dict[str, Any]] = None,
    min_score: float = 70.0,
) -> Dict[str, Any]:
    """Quality gate pre-validate: evalúa ADR antes de guardar (KosmosV3 C3).

    Dos niveles:
      **Hard gate** (``should_save=False``): score < 50% de ``min_score``
        → el ADR NO se guarda, se genera un plan de mejora.
      **Soft gate** (``should_save=True``): score entre 50% y 100% de ``min_score``
        → el ADR se guarda con advertencia.
      **Pass** (``passed=True``): score >= ``min_score``
        → el ADR pasa limpio.

    Args:
        adr_text: ADR text to evaluate.
        state: Optional pipeline state (for future context-aware evaluations).
        min_score: Minimum quality score to pass (default 70.0).

    Returns:
        Dict with:
          - passed (bool): True if score >= min_score
          - score (float): 0-100 quality score
          - gaps (list[str]): Missing quality criteria
          - should_save (bool): True if score >= min_score * 0.5 (soft gate)
          - min_score (float): The threshold used
          - improvement_plan (list[str]): Top 3 actions to improve
          - source (str): "llm" or "heuristic"
    """
    # Guard: empty or too short ADR
    if not adr_text or len(adr_text) < 50:
        return {
            "score": 0.0,
            "gaps": ["ADR text too short or empty"],
            "passed": False,
            "should_save": False,
            "min_score": min_score,
            "improvement_plan": [
                "Generate a complete ADR with all required sections",
            ],
            "source": "heuristic",
        }

    # ── Attempt LLM evaluation with heuristic fallback (C1+C2) ──
    prompt = f"""# Quality Gate: Pre-validate ADR

Evalúa este ADR arquitectónico:

{adr_text[:3000]}

Criterios (0-100 cada uno):
1. Frontmatter YAML completo (id, title, status, date, tags)
2. Contexto con ≥3 problemas o drivers
3. Opciones consideradas ≥3
4. Decisión con justificación explícita
5. Consecuencias positivas Y negativas
6. Diagrama o referencia visual
7. Referencias a ADRs existentes

Responde SOLO con JSON:
{{"score": N, "gaps": ["gap1", ...], "passed": true/false}}"""

    def _heuristic_gate() -> dict:
        """Heuristic fallback for pre-validate quality gate."""
        hscore = 50.0
        hgaps = []
        if "id:" in adr_text and "title:" in adr_text and "status:" in adr_text:
            hscore += 15
        else:
            hgaps.append("Frontmatter YAML incompleto")
        if "## Context" in adr_text or "## Contexto" in adr_text:
            hscore += 15
        else:
            hgaps.append("Falta sección de Contexto")
        if "## Decisi" in adr_text:
            hscore += 15
        else:
            hgaps.append("Falta sección de Decisión")
        if "## Consecuencias" in adr_text or "## Consequences" in adr_text:
            hscore += 15
        else:
            hgaps.append("Falta sección de Consecuencias")
        if "```" in adr_text or "graph" in adr_text or "flowchart" in adr_text:
            hscore += 10
        return {"score": round(min(hscore, 100), 1), "gaps": hgaps, "passed": hscore >= min_score, "source": "heuristic"}

    llm_result = call_llm_with_fallback(prompt, "quality", _heuristic_gate, state=state)

    if isinstance(llm_result, dict):
        score = llm_result.get("score", 50.0)
        gaps = llm_result.get("gaps", [])
        passed = llm_result.get("passed", score >= min_score)
        source = llm_result.get("source", "heuristic")
    else:
        parsed = _extract_json(str(llm_result)) if llm_result else None
        if parsed and "score" in parsed:
            score = float(parsed["score"])
            gaps = parsed.get("gaps", [])
            passed = parsed.get("passed", score >= min_score)
            source = "llm"
        else:
            return _heuristic_gate()
    # Soft gate: allow save if score >= 50% of min_score
    should_save = passed or score >= min_score * 0.5

    return {
        "score": score,
        "gaps": gaps,
        "passed": passed,
        "should_save": should_save,
        "min_score": min_score,
        "improvement_plan": [f"Mejorar: {g}" for g in gaps[:3]],
        "source": source,
    }
