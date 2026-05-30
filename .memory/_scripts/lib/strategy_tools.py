"""Strategy execution tools — Initiative scoper, KR assignment, task mapping.

Decomposes OKRs into executable initiatives with dependencies,
effort estimates, and critical path mapping for Kratos.
"""

from datetime import datetime


def scope_initiatives(okrs: list[dict], topic: str = "") -> list[dict]:
    """Decompose OKRs into scoped initiatives with dependencies.

    Each initiative maps to a specific KR and includes:
      - description and rationale
      - dependencies on other initiatives
      - estimated effort (person-weeks)
      - critical path flag
      - suggested assignee agent

    Args:
        okrs: List of OKR dicts with "objective" and "key_results"
        topic: Optional topic for context

    Returns:
        List of initiative dicts
    """
    if not okrs:
        return []

    initiatives = []
    initiative_id = 0
    deps = []

    for oi, okr in enumerate(okrs):
        objective = okr.get("objective", "")
        krs = okr.get("key_results", [])
        if isinstance(krs, str):
            krs = [krs]

        for ki, kr in enumerate(krs):
            kr_text = kr if isinstance(kr, str) else kr.get("kr", "")
            initiative_id += 1
            ini = {
                "id": f"INI-{oi+1}-{ki+1}",
                "kr_index": ki,
                "okr_index": oi,
                "objective": objective[:80],
                "key_result": kr_text[:120],
                "description": f"Implement initiative for KR: {kr_text[:100]}",
                "effort_weeks": _estimate_effort(kr_text),
                "dependencies": [],  # filled below
                "critical_path": False,
                "suggested_agent": "kratos",
                "success_criteria": [f"KR {ki+1} del OKR {oi+1}: {kr_text[:80]}"],
                "status": "pending",
            }
            initiatives.append(ini)

            # Build dependency graph: KRs within same objective depend on each other
            if ki > 0:
                prev_id = f"INI-{oi+1}-{ki}"
                ini["dependencies"].append(prev_id)

    # Determine critical path: longest chain of dependencies
    _mark_critical_path(initiatives)

    return initiatives


def assign_krs(okrs: list[dict], initiatives: list[dict]) -> dict:
    """Map KRs to responsible agents based on content analysis.

    Returns:
        dict mapping initiative_id → agent_name
    """
    assignment = {}
    for ini in initiatives:
        kr_text = ini.get("key_result", "").lower()
        # Heuristic: detect agent from content
        if any(w in kr_text for w in ["implementar", "codigo", "api", "desarroll", "code", "implement", "api"]):
            assignment[ini["id"]] = "kratos"
        elif any(w in kr_text for w in ["arquitectura", "diseño", "design", "architecture", "adr"]):
            assignment[ini["id"]] = "kosmos"
        elif any(w in kr_text for w in ["investigar", "research", "analizar", "analyz"]):
            assignment[ini["id"]] = "aletheia"
        else:
            assignment[ini["id"]] = "kratos"  # default to execution
    return assignment


def build_execution_plan(okrs: list[dict], initiatives: list[dict], assignment: dict) -> dict:
    """Build a complete execution plan from OKRs, initiatives, and KR assignment.

    Returns:
        dict with plan structure, phases, and agent tasks
    """
    if not initiatives:
        return {"plan": [], "total_initiatives": 0}

    phases = []
    for ini in initiatives:
        agent = assignment.get(ini["id"], "kratos")
        phases.append({
            "id": ini["id"],
            "kr": ini["key_result"],
            "agent": agent,
            "dependencies": ini.get("dependencies", []),
            "effort_weeks": ini.get("effort_weeks", 2),
            "critical_path": ini.get("critical_path", False),
            "success_criteria": ini.get("success_criteria", []),
        })

    return {
        "plan": phases,
        "total_initiatives": len(phases),
        "critical_path_length": sum(1 for p in phases if p["critical_path"]),
        "estimated_total_weeks": _estimate_total_duration(phases),
        "generated_at": datetime.now().isoformat(),
    }


def _estimate_effort(kr_text: str) -> int:
    """Estimate person-weeks from KR text content."""
    kr_lower = kr_text.lower()
    if any(w in kr_lower for w in ["complejo", "migrar", "rediseñar", "reescribir", "complex", "migrate", "redesign"]):
        return 4
    if any(w in kr_lower for w in ["medio", "nuevo", "integrar", "new", "integrate"]):
        return 3
    if any(w in kr_lower for w in ["simple", "menor", "ajuste", "minor", "tweak"]):
        return 1
    return 2


def _mark_critical_path(initiatives: list[dict]) -> None:
    """Mark the critical path: initiatives with longest dependency chain."""
    if not initiatives:
        return
    # Simple heuristic: initiatives in the longest dep chain
    depth = {}
    for ini in initiatives:
        deps = ini.get("dependencies", [])
        if not deps:
            depth[ini["id"]] = 1
        else:
            depth[ini["id"]] = max(depth.get(d, 0) for d in deps) + 1

    max_depth = max(depth.values()) if depth else 1
    for ini in initiatives:
        if depth.get(ini["id"], 0) == max_depth:
            ini["critical_path"] = True


def _estimate_total_duration(phases: list[dict]) -> int:
    """Estimate total weeks considering parallel vs sequential execution."""
    if not phases:
        return 0
    # Critical path duration + parallel buffer
    cp_weeks = sum(p["effort_weeks"] for p in phases if p.get("critical_path"))
    buffer = max(1, cp_weeks // 4)
    return cp_weeks + buffer
