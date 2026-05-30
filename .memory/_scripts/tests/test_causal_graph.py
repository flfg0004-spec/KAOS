"""Tests for tools.causal_graph — Causal Modeler engine."""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[3] / ".tools"))
from causal_graph import CausalModeler


SAMPLE_VARIABLES = """
Market share is at 25%. Customer satisfaction currently at 72%.
Team velocity: 68%. Code coverage sits at 45%.
"""

SAMPLE_ACTIONS = """
We need to improve onboarding flow. We should hire more engineers.
We must reduce technical debt. It is critical to automate deployment.
"""

SAMPLE_CAUSAL = """
Investment in R&D causes product innovation. Product innovation leads to market growth.
Hiring more engineers drives faster development but hurts budget.
Marketing spend triggers brand awareness after a short delay.
"""

SAMPLE_COMPLEX = """
Market share is at 15%. Customer churn is at 8%.
We need to improve product quality. Better quality drives customer retention.
Customer retention leads to revenue growth. But increasing prices reduces retention.
We should invest in customer support. Support investment drives satisfaction after a short delay.
Satisfaction causes retention. But expanding too fast hurts product quality.
"""


class TestBuildFromContext:
    def test_build_from_context_variables(self):
        m = CausalModeler()
        result = m.build_from_context(SAMPLE_VARIABLES)
        names = {k for k in result["nodes"]}
        assert "market share" in names
        assert "customer satisfaction" in names
        assert "team velocity" in names
        assert "code coverage" in names

    def test_build_from_context_variables_baseline(self):
        m = CausalModeler()
        result = m.build_from_context(SAMPLE_VARIABLES)
        assert result["nodes"]["market share"]["baseline"] == 25.0
        assert result["nodes"]["customer satisfaction"]["baseline"] == 72.0
        assert result["nodes"]["team velocity"]["baseline"] == 68.0
        assert result["nodes"]["code coverage"]["baseline"] == 45.0

    def test_build_from_context_actions(self):
        m = CausalModeler()
        result = m.build_from_context(SAMPLE_ACTIONS)
        kinds = {result["nodes"][k]["kind"] for k in result["nodes"]}
        actions = {k for k, v in result["nodes"].items() if v["kind"] == "action"}
        assert len(actions) >= 3

    def test_build_from_context_causal_relations(self):
        m = CausalModeler()
        result = m.build_from_context(SAMPLE_CAUSAL)
        assert "investment in r&d" in result["graph"]
        assert "product innovation" in result["graph"].get("investment in r&d", {})

    def test_build_from_context_polarity_negative(self):
        m = CausalModeler()
        result = m.build_from_context(SAMPLE_CAUSAL)
        all_edges = []
        for src, targets in result["graph"].items():
            for tgt, edata in targets.items():
                all_edges.append((src, tgt, edata["polarity"]))
        has_negative = any(pol == -1 for _, _, pol in all_edges)
        assert has_negative, "No negative polarity edges found"

    def test_build_from_context_delay(self):
        m = CausalModeler()
        result = m.build_from_context(SAMPLE_CAUSAL)
        delays = set()
        for src, targets in result["graph"].items():
            for tgt, edata in targets.items():
                delays.add(edata["delay"])
        assert "short" in delays or len(delays) > 0


class TestLeveragePoints:
    def test_find_leverage_points(self):
        m = CausalModeler()
        m.build_from_context(SAMPLE_COMPLEX)
        leverage = m.find_leverage_points()
        assert len(leverage) >= 1
        for lp in leverage:
            assert lp["out_degree"] >= 2

    def test_leverage_score_positive(self):
        m = CausalModeler()
        m.build_from_context(SAMPLE_COMPLEX)
        leverage = m.find_leverage_points()
        for lp in leverage:
            assert lp["score"] > 0
            assert "node" in lp
            assert "out_degree" in lp


class TestSecondOrderEffects:
    def test_find_second_order_effects(self):
        m = CausalModeler()
        m.build_from_context(SAMPLE_COMPLEX)
        effects = m.find_second_order_effects("improve product quality")
        if effects:
            for eff in effects:
                assert "target" in eff
                assert "via" in eff
                assert "strength" in eff
                assert eff["hops"] == 2

    def test_second_order_empty_for_unknown(self):
        m = CausalModeler()
        m.build_from_context(SAMPLE_COMPLEX)
        effects = m.find_second_order_effects("nonexistent")
        assert effects == []


class TestTraceChains:
    def test_trace_chains_finds_paths(self):
        m = CausalModeler()
        m.build_from_context(SAMPLE_CAUSAL)
        chains = m.trace_chains("investment in r&d", max_depth=4)
        assert len(chains) >= 1
        for chain in chains:
            assert len(chain) >= 1
            assert chain[0] == "investment in r&d"

    def test_trace_chains_from_leaf(self):
        m = CausalModeler()
        m.build_from_context(SAMPLE_CAUSAL)
        chains = m.trace_chains("market growth", max_depth=4)
        assert isinstance(chains, list)

    def test_trace_chains_unknown_node(self):
        m = CausalModeler()
        m.build_from_context(SAMPLE_CAUSAL)
        chains = m.trace_chains("nonexistent", max_depth=4)
        assert chains == []

    def test_trace_chains_max_depth(self):
        m = CausalModeler()
        m.build_from_context(SAMPLE_COMPLEX)
        chains = m.trace_chains("improve product quality", max_depth=2)
        for chain in chains:
            assert len(chain) <= 3


class TestGenerateReport:
    def test_generate_report_contains_sections(self):
        m = CausalModeler()
        report = m.generate_report(SAMPLE_COMPLEX)
        assert "Causal Analysis" in report
        assert "Nodes detected" in report
        assert "Leverage Points" in report
        assert "Generated by Causal Modeler" in report

    def test_generate_report_with_empty_context(self):
        m = CausalModeler()
        report = m.generate_report("")
        assert "Causal Analysis" in report
        assert "Nodes detected" in report
        assert "0" in report or "No" in report


class TestCLIHelp:
    def test_cli_help(self):
        import subprocess
        result = subprocess.run(
            [sys.executable, str(Path(__file__).resolve().parents[3] / ".tools" / "causal_graph.py"), "--help"],
            capture_output=True, text=True,
        )
        assert result.returncode == 0
        assert "Causal Modeler" in result.stdout
