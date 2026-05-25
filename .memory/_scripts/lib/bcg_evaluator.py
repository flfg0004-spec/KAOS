"""BCG Evaluation Framework — 8-dimension rubric for strategic outputs.

Adapted from BCG's analyst evaluation rubric for LLM strategic outputs.
Includes OKR Quality Checklist (7 criteria) as sub-module.

Scale: 0-5 per dimension → weighted total → mapped to 0.0-1.0
Threshold: < 7.0/10 → review required
"""

import re
import json
from datetime import datetime

DIMENSIONS = [
    {
        "id": "structure",
        "name": "Structure",
        "weight": 0.15,
        "description": "Clear structure with well-defined sections",
        "rubric": {
            0: "No structure, stream of consciousness",
            1: "Minimal structure, missing key sections",
            2: "Some structure but sections are unclear",
            3: "Adequate structure with most sections present",
            4: "Good structure with clear, logical sections",
            5: "Excellent structure, professional formatting, intuitive flow",
        },
    },
    {
        "id": "ambiguity_handling",
        "name": "Ambiguity Handling",
        "weight": 0.10,
        "description": "Explicitly addresses ambiguities vs. ignoring them",
        "rubric": {
            0: "Ignores all ambiguities, assumes single interpretation",
            1: "Briefly mentions uncertainty but doesn't address it",
            2: "Acknowledges some ambiguities without resolution",
            3: "Identifies ambiguities and discusses trade-offs",
            4: "Systematically addresses ambiguities with scenarios",
            5: "Exceptional handling: multiple scenarios, sensitivity analysis",
        },
    },
    {
        "id": "narrowing",
        "name": "Narrowing / Prioritization",
        "weight": 0.10,
        "description": "Applies 80/20, focuses on what matters",
        "rubric": {
            0: "Flat attention to all points, no prioritization",
            1: "Minimal prioritization, mostly listing",
            2: "Some prioritization but unclear rationale",
            3: "Clear prioritization with rationale",
            4: "Strong prioritization with data-backed rationale",
            5: "Expert-level narrowing: clear what matters and why",
        },
    },
    {
        "id": "rigor",
        "name": "Rigor + Sanity Checks",
        "weight": 0.10,
        "description": "Correct data, methods, and arithmetic sanity",
        "rubric": {
            0: "Contains factual errors or impossible numbers",
            1: "Multiple questionable assertions without evidence",
            2: "Some claims unsupported, weak methodology",
            3: "Most claims supported, reasonable methodology",
            4: "Rigorous methodology with cross-validation",
            5: "Academic-grade rigor: multi-source, triangulated",
        },
    },
    {
        "id": "breaking_obviousness",
        "name": "Breaking Obviousness",
        "weight": 0.20,
        "description": "Contains counter-narratives, non-obvious insights",
        "rubric": {
            0: "Generic boilerplate, could apply to any situation",
            1: "Surface-level analysis, obvious conclusions",
            2: "Some specific insights but mostly generic",
            3: "Several non-obvious insights with reasoning",
            4: "Strong counter-narratives and novel perspectives",
            5: "Truly original analysis with surprising, validated insights",
        },
    },
    {
        "id": "synthesis",
        "name": "Synthesis for Leadership",
        "weight": 0.20,
        "description": "Concludes vs. just describes; executive-ready",
        "rubric": {
            0: "Pure data dump, no synthesis or conclusion",
            1: "Minimal synthesis, weak conclusion",
            2: "Some synthesis but lacks executive focus",
            3: "Clear synthesis with actionable conclusions",
            4: "Strong synthesis with prioritized recommendations",
            5: "Board-ready: clear narrative, data-backed, actionable",
        },
    },
    {
        "id": "independence",
        "name": "Independence (Anti-Sycophancy)",
        "weight": 0.10,
        "description": "Questions premises vs. accepting them uncritically",
        "rubric": {
            0: "Accepts all premises without question",
            1: "Rarely challenges assumptions",
            2: "Occasionally questions but doesn't push back",
            3: "Regularly questions assumptions with reasoning",
            4: "Strong independence: challenges, offers alternatives",
            5: "Exemplary: systematically stress-tests every premise",
        },
    },
    {
        "id": "achievement",
        "name": "Achievement",
        "weight": 0.05,
        "description": "Ends with action, not 'further research needed'",
        "rubric": {
            0: "Ends with 'further analysis recommended' or nothing",
            1: "Vague next steps without ownership",
            2: "Some concrete next steps but incomplete",
            3: "Clear next steps with owners and timelines",
            4: "Detailed action plan with dependencies and risks",
            5: "Execution-ready: owners, dates, resources, success criteria",
        },
    },
]

OKR_CRITERIA = [
    {"id": "measurability", "name": "Measurability", "weight": 0.20},
    {"id": "ambition", "name": "Ambition (stretch)", "weight": 0.15},
    {"id": "outcome_focus", "name": "Outcome Focus", "weight": 0.20},
    {"id": "alignment", "name": "Alignment", "weight": 0.15},
    {"id": "counter_metric", "name": "Counter-metric", "weight": 0.10},
    {"id": "verifiability", "name": "Verifiability", "weight": 0.10},
    {"id": "within_control", "name": "Within Control", "weight": 0.10},
]


def _count_sections(text: str) -> int:
    """Count markdown headings as a proxy for structure."""
    return len(re.findall(r"^#{1,3}\s+\w", text, re.MULTILINE))


def _has_numeric_targets(text: str) -> bool:
    """Check for numeric targets in the text."""
    return bool(re.search(r"\d+%|\d+x|\d+/\d+|[±+]\d+|reduce.*\d+|increase.*\d+", text.lower()))


def _estimate_structure(text: str) -> int:
    """Score structure 0-5 based on headings and organization."""
    sections = _count_sections(text)
    if sections >= 8:
        return 5
    if sections >= 6:
        return 4
    if sections >= 4:
        return 3
    if sections >= 2:
        return 2
    if sections >= 1:
        return 1
    return 0


def _estimate_ambiguity(text: str) -> int:
    """Score ambiguity handling 0-5."""
    ambiguity_words = ["incierto", "depende", "variable", "escenario", "trade-off",
                       "riesgo", "podría", "uncertain", "scenario", "depending"]
    count = sum(1 for w in ambiguity_words if w in text.lower())
    if count >= 6:
        return 4
    if count >= 4:
        return 3
    if count >= 2:
        return 2
    if count >= 1:
        return 1
    return 0


def _estimate_narrowing(text: str) -> int:
    """Score prioritization 0-5."""
    priority_words = ["prioridad", "critical", "importante", "urgente", "quick win",
                      "alta prioridad", "bajo esfuerzo", "alto impacto", "paret"]
    count = sum(1 for w in priority_words if w in text.lower())
    if count >= 5:
        return 4
    if count >= 3:
        return 3
    if count >= 2:
        return 2
    if count >= 1:
        return 1
    return 0


def _estimate_rigor(text: str) -> int:
    """Score rigor 0-5 based on evidence and data."""
    evidence_words = ["evidencia", "dato", "fuente", "estudio", "investigación",
                      "según", "de acuerdo con", "data", "source", "research",
                      "according", "study"]
    has_numbers = bool(re.search(r"\d+[.,]?\d*", text))
    count = sum(1 for w in evidence_words if w in text.lower())
    score = 0
    if has_numbers:
        score += 1
    if count >= 5:
        score += 3
    elif count >= 3:
        score += 2
    elif count >= 1:
        score += 1
    return min(score, 5)


def _estimate_obviousness(text: str) -> int:
    """Score breaking obviousness 0-5 — penalize generic text."""
    generic_patterns = [
        r"es importante", r"es necesario", r"se recomienda",
        r"further research", r"más investigación",
        r"depende del contexto", r"it depends",
    ]
    specific_patterns = [
        r"\d+%", r"específicamente", r"concretamente",
        r"por ejemplo", r"en particular", r"for example",
        r"specifically", r"in particular",
    ]
    generic_count = sum(1 for p in generic_patterns if re.search(p, text.lower()))
    specific_count = sum(1 for p in specific_patterns if re.search(p, text.lower()))
    score = specific_count - generic_count
    return max(0, min(5, score + 2))


def _estimate_synthesis(text: str) -> int:
    """Score synthesis for leadership 0-5."""
    has_conclusion = bool(re.search(r"(?:^#{1,3}\s*(?:conclusion|conclusión|resumen|summary|recommend|recomend))", text, re.MULTILINE | re.IGNORECASE))
    has_recommendations = bool(re.search(r"(?:recomendaci|recommend|próximo paso|next step|acción|action)", text.lower()))
    score = 0
    if has_conclusion:
        score += 2
    if has_recommendations:
        score += 2
    if _has_numeric_targets(text):
        score += 1
    return min(score, 5)


def _estimate_independence(text: str) -> int:
    """Score independence/anti-sycophancy 0-5."""
    challenge_words = ["sin embargo", "no obstante", "however", "no es claro",
                       "cuestionable", "debate", "alternativa", "alternative",
                       "counter", "contra", "desafío", "challenge"]
    count = sum(1 for w in challenge_words if w in text.lower())
    if count >= 6:
        return 5
    if count >= 4:
        return 4
    if count >= 3:
        return 3
    if count >= 2:
        return 2
    if count >= 1:
        return 1
    return 0


def _estimate_achievement(text: str) -> int:
    """Score achievement 0-5 — actionability."""
    action_words = ["implementar", "implement", "ejecutar", "execute",
                    "asignar", "assign", "fecha", "deadline", "responsible",
                    "responsable", "hito", "milestone", "semana", "week",
                    "mes", "month", "q1", "q2", "q3", "q4"]
    count = sum(1 for w in action_words if w in text.lower())
    if count >= 6:
        return 5
    if count >= 4:
        return 4
    if count >= 3:
        return 3
    if count >= 2:
        return 2
    if count >= 1:
        return 1
    return 0


def evaluate_strategy(text: str) -> dict:
    """Full BCG evaluation of a strategic text output.

    Args:
        text: Strategic output text to evaluate

    Returns:
        dict with per-dimension scores, weighted total, pass/fail
    """
    estimators = {
        "structure": _estimate_structure,
        "ambiguity_handling": _estimate_ambiguity,
        "narrowing": _estimate_narrowing,
        "rigor": _estimate_rigor,
        "breaking_obviousness": _estimate_obviousness,
        "synthesis": _estimate_synthesis,
        "independence": _estimate_independence,
        "achievement": _estimate_achievement,
    }

    dim_scores = {}
    for dim in DIMENSIONS:
        estimator = estimators.get(dim["id"])
        score = estimator(text) if estimator else 0
        dim_scores[dim["id"]] = {
            "score": score,
            "max": 5,
            "weight": dim["weight"],
            "weighted": round(score / 5 * dim["weight"] * 100, 1),
            "label": dim["rubric"].get(score, dim["rubric"][0]),
        }

    total_pct = sum(d["weighted"] for d in dim_scores.values())
    total_10 = round(total_pct / 10, 1)

    return {
        "framework": "BCG 8-Dimension Rubric",
        "total_score_10": total_10,
        "total_score_100": round(total_pct, 1),
        "total_score_01": round(total_pct / 100, 2),
        "passed": total_10 >= 7.0,
        "dimensions": dim_scores,
        "dimension_order": [d["id"] for d in DIMENSIONS],
        "generated_at": datetime.now().isoformat(),
    }


def evaluate_okrs(okrs: list[dict]) -> dict:
    """OKR Quality Checklist — 7 criteria.

    Args:
        okrs: List of OKR dicts with "objective" and "key_results"

    Returns:
        dict with per-criteria scores, weighted total, pass/fail
    """
    if not okrs:
        return {
            "framework": "OKR Quality Checklist",
            "total_okrs": 0,
            "score_100": 0,
            "passed": False,
            "checks": [],
            "generated_at": datetime.now().isoformat(),
        }

    checks = []
    for i, okr in enumerate(okrs):
        objective = okr.get("objective", "")
        krs = okr.get("key_results", [])

        kr_text = " ".join(krs) if isinstance(krs, list) else str(krs)
        full_text = objective + " " + kr_text

        check = {
            "okr_index": i,
            "objective": objective[:60],
            "scores": {
                "measurability": 1 if _has_numeric_targets(full_text) else 0,
                "ambition": 1 if any(w in full_text.lower() for w in ["reducir", "aumentar", "mejorar", "increment", "reduc", "increase", "improve"]) else 0,
                "outcome_focus": 1 if not any(w in full_text.lower() for w in ["tarea", "task", "activity", "reunión", "meeting"]) else 0,
                "alignment": 1 if len(objective) > 20 else 0,
                "counter_metric": 1 if any(w in full_text.lower() for w in ["sin afectar", "without affecting", "manteniendo", "while maintaining", "trade-off"]) else 0,
                "verifiability": 1 if len(krs) > 0 else 0,
                "within_control": 1 if not any(w in full_text.lower() for w in ["depende de", "depends on", "if they", "si ellos"]) else 0,
            },
        }
        check["total"] = round(sum(check["scores"].values()) / len(OKR_CRITERIA) * 100, 1)
        checks.append(check)

    avg_score = round(sum(c["total"] for c in checks) / len(checks), 1) if checks else 0

    return {
        "framework": "OKR Quality Checklist",
        "total_okrs": len(okrs),
        "score_100": avg_score,
        "passed": avg_score >= 70.0,
        "checks": checks,
        "generated_at": datetime.now().isoformat(),
    }


def evaluate_strategy_llm(text: str, use_llm: bool = False) -> dict:
    """Evaluate strategy using LLM for deeper analysis (optional).

    Falls back to heuristic if use_llm=False or LLM unavailable.
    """
    if not use_llm:
        return evaluate_strategy(text)

    try:
        from lib.llm import agent_llm_call
        dims_json = json.dumps([
            {"id": d["id"], "name": d["name"], "weight": d["weight"], "rubric": d["rubric"]}
            for d in DIMENSIONS
        ])
        prompt = (
            f"Evalúa este output estratégico usando la rúbrica BCG de 8 dimensiones.\n\n"
            f"## Output a evaluar\n{text[:3000]}\n\n"
            f"## Rúbrica\n{dims_json}\n\n"
            f"Responde SOLO con JSON:\n"
            f'{{"scores": {{"structure": 0, "ambiguity_handling": 0, ...}}, '
            f'"rationale": "..."}}\n'
            f"Escala 0-5 para cada dimensión."
        )
        raw = agent_llm_call("critic", prompt, step_type="review")
        parsed = json.loads(raw.strip().strip("```json").strip("```").strip())

        dim_scores = {}
        for dim in DIMENSIONS:
            s = parsed.get("scores", {}).get(dim["id"], 0)
            dim_scores[dim["id"]] = {
                "score": min(5, max(0, int(s))),
                "max": 5,
                "weight": dim["weight"],
                "weighted": round(min(5, max(0, int(s))) / 5 * dim["weight"] * 100, 1),
                "label": dim["rubric"].get(int(s), dim["rubric"][0]),
            }

        total_pct = sum(d["weighted"] for d in dim_scores.values())
        total_10 = round(total_pct / 10, 1)

        return {
            "framework": "BCG 8-Dimension Rubric (LLM-as-Judge)",
            "total_score_10": total_10,
            "total_score_100": round(total_pct, 1),
            "total_score_01": round(total_pct / 100, 2),
            "passed": total_10 >= 7.0,
            "dimensions": dim_scores,
            "dimension_order": [d["id"] for d in DIMENSIONS],
            "rationale": parsed.get("rationale", ""),
            "generated_at": datetime.now().isoformat(),
        }
    except Exception:
        return evaluate_strategy(text)
