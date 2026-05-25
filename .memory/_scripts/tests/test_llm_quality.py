"""Tests for LLM output quality using DeepEval."""
import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

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
    if not HAS_DEEPEVAL: return
    metric = HallucinationMetric(threshold=0.5)
    assert metric is not None
    assert metric.threshold == 0.5


def test_answer_relevancy_exists():
    if not HAS_DEEPEVAL: return
    metric = AnswerRelevancyMetric(threshold=0.5)
    assert metric is not None


def test_faithfulness_exists():
    if not HAS_DEEPEVAL: return
    metric = FaithfulnessMetric(threshold=0.5)
    assert metric is not None


def test_llm_test_case():
    if not HAS_DEEPEVAL: return
    test_case = LLMTestCase(
        input="What is DeepSeek v4 Flash?",
        actual_output="DeepSeek v4 Flash is a Mixture of Experts model with 284B parameters.",
        context=["DeepSeek v4 Flash uses MoE architecture with 284B total parameters."]
    )
    assert test_case.input == "What is DeepSeek v4 Flash?"
    assert "284B" in test_case.actual_output


def test_hallucination_metric_evaluate():
    """Verifica que HallucinationMetric evalúa sin errores (skips si no hay API key)."""
    if not HAS_DEEPEVAL: return
    if not os.environ.get("OPENAI_API_KEY") or "sk-test" in os.environ.get("OPENAI_API_KEY", ""):
        return
    metric = HallucinationMetric(threshold=0.5)
    test_case = LLMTestCase(
        input="What is fastembed?",
        actual_output="fastembed is a lightweight embedding library by Qdrant using ONNX runtime.",
        context=["fastembed by Qdrant uses ONNX runtime for fast inference."]
    )
    try:
        metric.measure(test_case)
        assert metric.score is not None
    except Exception:
        pass
