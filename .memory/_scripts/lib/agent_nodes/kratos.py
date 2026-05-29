import re
from datetime import datetime

from lib.config import LLM_DIRECT_ENABLED
from lib.agent_tools import (
    slugify, load_context, save_context,
    llm_or_executor_call, notify_step,
    is_complete_code, check_security, resolve_kratos_model,
    RAW_DIR,
)
from lib.feature_flags import is_enabled
from lib.lang_utils import detect_code_language as _detect_code_language


def kratos_node(state: dict) -> dict:
    if is_enabled("use_new_agent_executor"):
        return _kratos_node_v2(state)
    return _kratos_node_impl(state)


def _kratos_node_impl(state: dict) -> dict:
    topic = state.get("topic", "")
    slug = slugify(topic)

    ctx = load_context()
    cross_agent = ctx.get("cross_agent", {})
    if not isinstance(cross_agent, dict):
        cross_agent = {}
    strategy = cross_agent.get("metis_to_kratos", {})
    if not isinstance(strategy, dict):
        strategy = {}
    code_context = cross_agent.get("aletheia_to_kratos", {})
    if not isinstance(code_context, dict):
        code_context = {}

    strategy_summary = strategy.get("strategy_summary", topic)
    okrs = strategy.get("okrs", [])
    initiatives = strategy.get("initiatives", [])
    execution_plan = strategy.get("execution_plan", {})
    kr_assignment = strategy.get("kr_assignment", {})
    model_key = resolve_kratos_model(state)

    experiences_section = ""
    detected_lang = _detect_code_language(topic)
    try:
        from lib.code_memory import search as ce_search
        experiences = ce_search(query=topic, top_k=10, code_snippet="", language=detected_lang)
        if experiences:
            exp_lines = []
            for e in experiences:
                exp_lines.append(
                    f"- [{e['language']}] `{e['error'][:80]}` "
                    f"(conf:{e['confidence']:.2f}, score:{e.get('rrf_score', e['score']):.2f})"
                )
            experiences_section = (
                "## Experiencias Relevantes de CodeExperience\n"
                + "Tienes 1M de contexto — se incluyen todas las experiencias relevantes:\n"
                + "\n".join(exp_lines)
                + "\n\n*Estos patrones de error deben evitarse durante la implementación.*\n"
            )
    except Exception:
        experiences_section = ""

    initiatives_section = ""
    if initiatives:
        init_lines = []
        for ini in initiatives:
            deps = ", ".join(ini.get("dependencies", [])) or "ninguna"
            cp = " [CRITICAL PATH]" if ini.get("critical_path") else ""
            init_lines.append(
                f"- **{ini['id']}**: {ini['key_result'][:80]}{cp}\n"
                f"  - Dependencias: {deps}\n"
                f"  - Esfuerzo estimado: {ini.get('effort_weeks', '?')} semanas\n"
                f"  - Criterio de éxito: {ini.get('success_criteria', [''])[0][:80]}"
            )
        initiatives_section = "\n".join(init_lines)

    okrs_section = ""
    if okrs:
        okr_lines = []
        for oi, okr in enumerate(okrs):
            krs = okr.get("key_results", [])
            kr_text = "\n".join(f"    - KR: {k}" for k in krs[:3])
            okr_lines.append(f"- OKR {oi+1}: {okr.get('objective', '')[:80]}\n{kr_text}")
        okrs_section = "\n".join(okr_lines)

    prompt = (
        f"# Pipeline: Implementación — PRGII (1M Contexto)\n\n"
        f"## Tarea\n{topic}\n\n"
        f"## OKRs Estratégicos (de Metis)\n{okrs_section}\n\n"
        f"## Contexto Estratégico\n{strategy_summary}\n\n"
        f"## Initiatives Asignadas\n{initiatives_section}\n\n"
        f"{experiences_section}"
        f"## Contexto de Investigación (de Aletheia)\n"
        f"{str(code_context)[:1500] if code_context else 'Sin contexto de código específico.'}\n\n"
        f"## Metodología PRGII\n\n"
        f"### 1. PLAN\n- Descompón la tarea en subtareas de implementación\n"
        f"- Identifica archivos a crear/modificar\n- Evalúa dependencias y riesgos técnicos\n\n"
        f"### 2. RETRIEVE (automático)\n"
        f"- Revisa experiencias previas de errores similares (arriba)\n- Aplica lecciones aprendidas\n\n"
        f"### 3. GENERATE\n"
        f"- Implementa siguiendo clean code y mejores prácticas\n- Usa type hints y documentación inline\n"
        f"- Maneja edge cases: null, vacío, límites, errores\n- Sigue SOLID y DRY\n\n"
        f"### 4. TEST\n- Escribe tests unitarios (pytest)\n- Incluye: casos normales, boundary, y error\n\n"
        f"### 5. DOCUMENT\n- Documenta funciones/clases con docstrings\n- Especifica parámetros, retorno, excepciones\n\n"
        f"## Formato de Salida\n"
        f"- Código en bloques ```lenguaje\n- Tests en bloque separado ```python\n"
        f"- Explicación de decisiones técnicas fuera de bloques\n- Resumen de archivos modificados/creados al final\n"
    )

    output_path = RAW_DIR / f"{slug}-code.md"
    output_path.write_text(prompt, encoding="utf-8")

    if LLM_DIRECT_ENABLED:
        notify_step(state, "Kratos Implementation", "in_progress")
        raw = llm_or_executor_call("kratos", prompt, model_override=model_key)
        max_iterations = 3
        iteration = 0
        iteration_log = []

        while iteration < max_iterations:
            iteration += 1
            notify_step(state, f"Kratos Quality Check ({iteration}/{max_iterations})", "in_progress")
            code_blocks = re.findall(r"```(\w+)\n(.*?)```", raw, re.DOTALL)
            tool_issues = []

            for lang, code in code_blocks:
                if lang in ("python", "py"):
                    from lib.quality_gate import gate_lint, gate_types
                    lint_result = gate_lint(code, "python")
                    if lint_result["score"] < 5:
                        tool_issues.append(f"lint ({lint_result['detail']})")
                    types_result = gate_types(code, "python")
                    if not types_result["passed"]:
                        tool_issues.append(f"types ({types_result['detail']})")
                    security_result = check_security(code)
                    if security_result:
                        tool_issues.extend(security_result)

            llm_issues = []
            review_prompt = (
                f"Revisa este código en busca de errores lógicos, edge cases o problemas de diseño.\n\n"
                f"## Código\n{raw[:4000]}\n\n"
                f"## Issues de Herramientas\n" + ("\n".join(f"- {i}" for i in tool_issues[:5]) if tool_issues else "Ninguno") + "\n\n"
                f'Responde SOLO con JSON:\n'
                f'{{"has_errors": true|false, "issues": ["descripción del error lógico"], '
                f'"severity": "critical|minor|none"}}'
            )
            try:
                from lib.llm import agent_llm_call
                import json as _json
                review = agent_llm_call("critic", review_prompt)
                review_data = _json.loads(review.strip().strip("```json").strip("```").strip())
                if review_data.get("has_errors", False):
                    llm_issues = review_data.get("issues", [])
            except Exception:
                pass

            all_issues = tool_issues + llm_issues
            if not all_issues:
                iteration_log.append(f"✅ Iteración {iteration}: sin errores")
                break

            notify_step(state, f"Kratos Repair ({iteration}/{max_iterations})", "in_progress")
            repair_prompt = (
                f"## Tarea Original\n{topic}\n\n"
                f"## Código Actual (con errores)\n```\n{raw[:4000]}\n```\n\n"
                f"## Errores Detectados\n" + "\n".join(f"- {i}" for i in all_issues[:5]) + "\n\n"
                f"Corrige el código. SOLO el código corregido, sin explicación."
            )
            raw = llm_or_executor_call("kratos", repair_prompt, model_override=model_key)
            iteration_log.append(f"🔄 Iteración {iteration}: reparado — {', '.join(all_issues[:2])}")

        output_path.write_text(raw, encoding="utf-8")
        ctx = load_context()
        ctx["agents"].append("kratos")
        ctx["context_summary"]["kratos"] = {"started_at": datetime.now().isoformat()}

        decision = "complete" if is_complete_code(raw) else "needs_curation"
        ctx["cross_agent"]["kratos_decision"] = decision
        ctx["cross_agent"]["kratos_iterations"] = iteration_log
        save_context(ctx)
        notify_step(state, "Kratos Implementation", "completed")

        try:
            has_errors = "error" in raw.lower() or "traceback" in raw.lower()
            from lib.kratos_hook import capture_agent_output
            if has_errors:
                capture_agent_output(raw)
            else:
                from lib.code_memory import capture_from_bash
                capture_from_bash(exit_code=0, stderr="", cmd=f"kratos_generate: {topic[:200]}", cwd=detected_lang)
        except Exception:
            pass

        try:
            from lib.opa_bridge import check_agent
            governance = check_agent("kratos", raw)
            gov_allowed = governance["allowed"]
            gov_denials = governance["denials"]
        except Exception:
            gov_allowed = True
            gov_denials = []

        try:
            from lib.viz_orchestrator import orchestrate as _viz
            _viz("kratos", {"code_flow": raw})
        except Exception:
            pass

        return {
            **state, "kratos_output": raw, "kratos_prompt": prompt,
            "kratos_decision": decision,
            "governance_allowed": gov_allowed,
            "governance_denials": gov_denials,
        }

    ctx["agents"].append("kratos")
    ctx["context_summary"]["kratos"] = {"started_at": datetime.now().isoformat()}
    ctx["cross_agent"]["kratos_decision"] = "needs_curation"
    save_context(ctx)

    try:
        from lib.opa_bridge import check_agent
        governance = check_agent("kratos", prompt)
        gov_allowed = governance["allowed"]
        gov_denials = governance["denials"]
    except Exception:
        gov_allowed = True
        gov_denials = []

    try:
        from lib.viz_orchestrator import orchestrate as _viz
        _viz("kratos", {"code_flow": prompt})
    except Exception:
        pass

    return {
        **state,
        "kratos_output": f"Code prompt written to {output_path}",
        "kratos_prompt": prompt,
        "kratos_decision": "needs_curation",
        "governance_allowed": gov_allowed,
        "governance_denials": gov_denials,
    }


def _kratos_node_v2(state: dict) -> dict:
    return _kratos_node_impl(state)
