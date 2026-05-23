"""Tests for LLM output quality using DeepEval."""
import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

# Try to import DeepEval (optional dependency)
try:
    from deepeval import assert_test
    from deepeval.metrics import HallucinationMetric, AnswerRelevancyMetric, FaithfulnessMetric
    from deepeval.test_case import LLMTestCase
    HAS_DEEPEVAL = True
except ImportError:
    HAS_DEEPEVAL = False


def test_deepeval_importable():
    """Verifica que DeepEval está instalado."""
    assert HAS_DEEPEVAL, "DeepEval not installed. Run: pip install deepeval"


def test_hallucination_metric_exists():
    """Verifica que las métricas de DeepEval existen."""
    if not HAS_DEEPEVAL:
        return
    metric = HallucinationMetric(threshold=0.5)
    assert metric is not None
    assert metric.threshold == 0.5


def test_answer_relevancy_exists():
    """Verifica métrica de relevancia."""
    if not HAS_DEEPEVAL:
        return
    metric = AnswerRelevancyMetric(threshold=0.5)
    assert metric is not None


def test_faithfulness_exists():
    """Verifica métrica de fidelidad."""
    if not HAS_DEEPEVAL:
        return
    metric = FaithfulnessMetric(threshold=0.5)
    assert metric is not None


def test_llm_test_case():
    """Verifica creación de LLMTestCase."""
    if not HAS_DEEPEVAL:
        return
    test_case = LLMTestCase(
        input="What is DeepSeek v4 Flash?",
        actual_output="DeepSeek v4 Flash is a Mixture of Experts model with 284B parameters.",
        context=["DeepSeek v4 Flash uses MoE architecture with 284B total parameters."]
    )
    assert test_case.input == "What is DeepSeek v4 Flash?"
    assert "284B" in test_case.actual_output
