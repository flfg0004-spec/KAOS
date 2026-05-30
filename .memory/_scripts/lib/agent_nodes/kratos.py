import logging
import re
import time
from datetime import datetime
from typing import Any

logger = logging.getLogger(__name__)

from lib.agent_tools import (
    RAW_DIR,
    check_security,
    is_complete_code,
    llm_or_executor_call,
    load_context,
    notify_step,
    resolve_kratos_model,
    save_context,
    slugify,
)
from lib.config import KRATOS_PRUNE_ENABLED, KRATOS_PRUNE_THRESHOLD, KRATOS_SLEEP_ENABLED, LLM_DIRECT_ENABLED
from lib.feature_flags import is_enabled
from lib.kratos_decision import KratosDecision
from lib.kratos_telemetry import CircuitBreaker, record_invocation
from lib.lang_utils import detect_code_language as _detect_code_language




def kratos_node(state: dict[str, Any]) -> dict[str, Any]:
    if is_enabled("use_new_agent_executor"):
        return _kratos_node_v2(state)

    v1_result = _kratos_node_impl(state)

    # Shadow mode: execute v2 in parallel for comparison, but return v1 result
    if is_enabled("kratos_shadow_mode"):
        try:
            v2_result = _kratos_node_v2(state)
            _log_shadow_comparison(v1_result, v2_result)
        except Exception as e:
            logger.warning("Shadow mode v2 failed: %s", e)

    return v1_result


def _log_shadow_comparison(v1: dict, v2: dict) -> None:
    """Log comparison between v1 and v2 outputs for shadow mode analysis."""
    v1_dec = str(v1.get("kratos_decision", "?"))
    v2_dec = str(v2.get("kratos_decision", "?"))
    v1_qs = v1.get("kratos_composite", v1.get("quality_score", 0))
    v2_qs = v2.get("kratos_composite", 0)
    match = "✓" if v1_dec == v2_dec else "✗"
    logger.info(
        "[SHADOW] v1=%s(q=%.1f) vs v2=%s(q=%.1f) %s",
        v1_dec, v1_qs, v2_dec, v2_qs, match
    )


def _run_post_processing(content: str, state: dict[str, Any], prompt: str) -> dict[str, Any]:
    """Run governance check, viz orchestration, and sleep cycle after generation.
    
    Shared by both LLM-on and LLM-off paths to avoid duplication.
    """
    try:
        from lib.opa_bridge import check_agent
        governance = check_agent("kratos", content)
        gov_allowed = governance["allowed"]
        gov_denials = governance["denials"]
    except Exception as e:
        if is_enabled("opa_strict_mode"):
            gov_allowed = False
            gov_denials = [f"OPA check failed (strict mode): {e}"]
            logger.warning("OPA strict mode: denying due to check failure: %s", e)
        else:
            gov_allowed = True
            gov_denials = []
            logger.warning("OPA check failed (permissive mode): %s", e)

    try:
        from lib.viz_orchestrator import orchestrate as _viz
        _viz("kratos", {"code_flow": content})
    except Exception:
        pass

    if KRATOS_SLEEP_ENABLED:
        try:
            from lib.sleep_cycle import status as _sleep_status
            _sleep_status()
        except Exception:
            pass

    return {
        "governance_allowed": gov_allowed,
        "governance_denials": gov_denials,
    }


def _kratos_node_impl(state: dict[str, Any]) -> dict[str, Any]:
    _start_time = time.time()
    from lib.kratos_telemetry import CircuitBreaker
    _cb = CircuitBreaker(failure_threshold=3, recovery_timeout=300)
    _iteration = 0
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

    # ── Auto-pruning: keep DB under threshold ──
    if KRATOS_PRUNE_ENABLED:
        try:
            from lib.code_memory import prune as _ce_prune
            from lib.code_memory import status as _ce_status
            db_stat = _ce_status()
            total = db_stat.get("total_experiences", 0) if isinstance(db_stat, dict) else 0
            if total > KRATOS_PRUNE_THRESHOLD:
                pruned = _ce_prune(dry_run=False)
                if pruned.get("archived_now", 0) > 0 or pruned.get("deleted_now", 0) > 0:
                    import logging
                    _LOG = logging.getLogger(__name__)
                    _LOG.info("Kratos auto-pruned DB: %s", pruned)
        except Exception:
            pass

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
        try:
            raw = llm_or_executor_call("kratos", prompt, model_override=model_key)
        except Exception as e:
            logger.warning("Kratos LLM call failed: %s", e)
            return {
                **state,
                "kratos_output": "",
                "kratos_prompt": prompt,
                "kratos_decision": KratosDecision.NEEDS_CURATION,
                "governance_allowed": True,
                "governance_denials": [],
            }
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
                'Responde SOLO con JSON:\n'
                '{"has_errors": true|false, "issues": ["descripción del error lógico"], '
                '"severity": "critical|minor|none"}'
            )
            try:
                import json as _json

                from lib.llm import agent_llm_call
                if is_enabled("use_circuit_breaker"):
                    review = _cb(lambda: agent_llm_call("critic", review_prompt))()
                else:
                    review = agent_llm_call("critic", review_prompt)
                review_data = _json.loads(review.strip().strip("```json").strip("```").strip())
                if review_data.get("has_errors", False):
                    llm_issues = review_data.get("issues", [])
            except RuntimeError:
                logger.warning("Circuit breaker OPEN — skipping critic review")
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
                "Corrige el código. SOLO el código corregido, sin explicación."
            )
            raw = llm_or_executor_call("kratos", repair_prompt, model_override=model_key)
            iteration_log.append(f"🔄 Iteración {iteration}: reparado — {', '.join(all_issues[:2])}")

        output_path.write_text(raw, encoding="utf-8")
        ctx = load_context()
        ctx["agents"].append("kratos")
        ctx["context_summary"]["kratos"] = {"started_at": datetime.now().isoformat()}

        decision = KratosDecision.COMPLETE if is_complete_code(raw) else KratosDecision.NEEDS_CURATION
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

        # ── Post-processing: governance, viz, sleep ──
        post = _run_post_processing(raw, state, prompt)
        # ── Telemetry recording (feature-flagged) ──
        if is_enabled("use_kratos_telemetry"):
            record_invocation(
                decision=str(decision),
                quality_score=0.0,  # placeholder until quality integration
                language=detected_lang,
                flags_active={k: is_enabled(k) for k in ["use_kratos_v2", "use_real_coverage", "use_rust_gates", "use_ts_gates", "use_go_gates", "use_early_exit"]},
                duration_ms=(time.time() - _start_time) * 1000,
                iteration=_iteration,
            )

        return {
            **state, "kratos_output": raw, "kratos_prompt": prompt,
            "kratos_decision": decision,
            **post,
        }

    ctx["agents"].append("kratos")
    ctx["context_summary"]["kratos"] = {"started_at": datetime.now().isoformat()}
    ctx["cross_agent"]["kratos_decision"] = KratosDecision.NEEDS_CURATION
    save_context(ctx)

    # ── Post-processing: governance, viz, sleep ──
    post = _run_post_processing(prompt, state, prompt)
    return {
        **state,
        "kratos_output": f"Code prompt written to {output_path}",
        "kratos_prompt": prompt,
        "kratos_decision": KratosDecision.NEEDS_CURATION,
        **post,
    }


def _kratos_node_v2(state: dict[str, Any]) -> dict[str, Any]:
    _start_time = time.time()
    topic = state.get("topic", "")
    slug = slugify(topic)
    detected_lang = _detect_code_language(topic)

    from lib.quality_gate import evaluate_parallel
    quality_result = evaluate_parallel(topic, language=detected_lang)

    try:
        from lib.opa_bridge import check_agent
        governance = check_agent("kratos", topic)
        gov_allowed = governance.get("allowed", True)
        gov_denials = governance.get("denials", [])
    except Exception as e:
        if is_enabled("opa_strict_mode"):
            gov_allowed = False
            gov_denials = [f"OPA check failed (strict mode): {e}"]
            logger.warning("OPA strict mode: denying due to check failure: %s", e)
        else:
            gov_allowed = True
            gov_denials = []
            logger.warning("OPA check failed (permissive mode): %s", e)

    composite = quality_result.get("composite", 0.0)
    gates_passed = quality_result.get("passed", False)

    if not gov_allowed:
        decision = KratosDecision.REJECTED_BY_GOV
    elif not gates_passed and composite < 3.0:
        decision = KratosDecision.FAILED
    elif not gates_passed:
        decision = KratosDecision.NEEDS_CURATION
    else:
        decision = KratosDecision.COMPLETE

    output = {
        **state,
        "kratos_output": f"## Quality Assessment\n\n{quality_result.get('summary', '')}",
        "kratos_prompt": topic,
        "kratos_decision": decision,
        "kratos_composite": composite,
        "kratos_language": detected_lang,
        "kratos_gates": quality_result.get("gates", {}),
        "governance_allowed": gov_allowed,
        "governance_denials": gov_denials,
        "kratos_version": "v2",
    }

    if is_enabled("use_kratos_telemetry"):
        try:
            from lib.kratos_telemetry import record_invocation
            record_invocation(
                decision=str(decision),
                quality_score=composite,
                language=detected_lang,
                flags_active={k: is_enabled(k) for k in [
                    "use_kratos_telemetry", "use_parallel_gates",
                    "use_early_exit", "use_real_mypy", "use_circuit_breaker",
                ]},
                duration_ms=(time.time() - _start_time) * 1000,
            )
        except Exception:
            pass

    if is_enabled("use_kratos_telemetry"):
        try:
            from lib.kratos_self_heal import heal
            actions = heal()
            if actions:
                logger.info("Self-heal actions: %s", actions)
        except Exception:
            pass

    return output
