from lib.agent_tools import load_context
from lib.feature_flags import is_enabled


def bcg_evaluator_node(state: dict) -> dict:
    if is_enabled("use_new_agent_executor"):
        return _bcg_evaluator_node_v2(state)
    return _bcg_evaluator_node_impl(state)


def _bcg_evaluator_node_impl(state: dict) -> dict:
    metis_output = state.get("metis_output", "") or ""
    if not metis_output:
        return {**state, "bcg_score": 0, "bcg_passed": False, "bcg_details": {}}

    try:
        from lib.bcg_evaluator import evaluate_okrs, evaluate_strategy
        bcg = evaluate_strategy(metis_output)

        okr_result = {}
        try:
            ctx = load_context()
            metis_data = ctx.get("cross_agent", {}).get("metis_to_kratos", {})
            if not isinstance(metis_data, dict):
                metis_data = {}
            okrs = metis_data.get("okrs", [])
            if okrs:
                okr_result = evaluate_okrs(okrs)
        except Exception:
            okr_result = {}

        try:
            from lib.strategy_analytics import track_bcg as _track
            _track({**state, "bcg_score": bcg.get("total_score_10", 0),
                     "bcg_passed": bcg.get("passed", False),
                     "bcg_details": bcg,
                     "okr_quality": okr_result})
        except Exception:
            pass

        try:
            ctx = load_context()
            metis_feedback = ctx.get("cross_agent", {}).get("metis_to_aletheia", {})
            gaps = metis_feedback.get("gaps_identified", [])
        except Exception:
            gaps = []

        return {
            **state,
            "bcg_score": bcg.get("total_score_10", 0),
            "bcg_passed": bcg.get("passed", False),
            "bcg_details": bcg,
            "okr_quality": okr_result,
            "aletheia_pending_gaps": gaps,
        }
    except Exception as e:
        return {**state, "bcg_score": 0, "bcg_passed": False, "bcg_details": {"error": str(e)}}


def _bcg_evaluator_node_v2(state: dict) -> dict:
    return _bcg_evaluator_node_impl(state)
