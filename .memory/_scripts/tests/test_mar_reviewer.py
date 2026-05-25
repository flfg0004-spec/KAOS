"""Tests for Multi-Agent Review (MAR) — syntax, logic, security reviewers."""

import os, sys
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))
os.environ["KAOS_TESTING"] = "1"


SAMPLE_GOOD_CODE = """```python
def add(a: int, b: int) -> int:
    '''Add two numbers.'''
    return a + b

def test_add():
    assert add(1, 2) == 3
    assert add(-1, 1) == 0
```"""

SAMPLE_BAD_CODE = """```python
def process(data):
    result = {}
    try:
        result = eval(data)
    except:
        pass
    api_key = "sk-1234567890abcdef"
    return result
```"""


def test_syntax_reviewer():
    from lib.mar_reviewer import SyntaxReviewer, _extract_code_blocks
    blocks = _extract_code_blocks(SAMPLE_GOOD_CODE)
    reviewer = SyntaxReviewer()
    result = reviewer.review(blocks)
    assert result["reviewer"] == "syntax"
    assert 0 <= result["score"] <= 10


def test_logic_reviewer():
    from lib.mar_reviewer import LogicReviewer, _extract_code_blocks
    blocks = _extract_code_blocks(SAMPLE_BAD_CODE)
    reviewer = LogicReviewer()
    result = reviewer.review(blocks)
    assert result["reviewer"] == "logic"
    assert result["issue_count"] > 0


def test_security_reviewer():
    from lib.mar_reviewer import SecurityReviewer, _extract_code_blocks
    blocks = _extract_code_blocks(SAMPLE_BAD_CODE)
    reviewer = SecurityReviewer()
    result = reviewer.review(blocks)
    assert result["reviewer"] == "security"
    assert result["score"] < 10  # Should find issues


def test_security_detects_eval():
    from lib.mar_reviewer import SecurityReviewer, _extract_code_blocks
    blocks = _extract_code_blocks(SAMPLE_BAD_CODE)
    reviewer = SecurityReviewer()
    result = reviewer.review(blocks)
    categories = [i["category"] for i in result["issues"]]
    assert "eval_usage" in categories


def test_security_detects_hardcoded_secrets():
    from lib.mar_reviewer import SecurityReviewer, _extract_code_blocks
    blocks = _extract_code_blocks(SAMPLE_BAD_CODE)
    reviewer = SecurityReviewer()
    result = reviewer.review(blocks)
    categories = [i["category"] for i in result["issues"]]
    assert "hardcoded_secret" in categories


def test_meta_reviewer_consolidates():
    from lib.mar_reviewer import MetaReviewer
    meta = MetaReviewer()
    reviews = [
        {"reviewer": "syntax", "score": 8.0, "issues": [{"severity": "minor", "category": "style", "message": "x"}]},
        {"reviewer": "logic", "score": 6.0, "issues": [{"severity": "major", "category": "bug", "message": "y"}]},
    ]
    result = meta.consolidate(reviews)
    assert result["composite_score"] == 7.0
    assert result["reviewer_scores"]["syntax"] == 8.0
    assert "critical" in result["issues"]
    assert "major" in result["issues"]


def test_review_code_full():
    from lib.mar_reviewer import review_code
    result = review_code(SAMPLE_GOOD_CODE)
    assert "composite_score" in result
    assert "reviewer_scores" in result
    assert "syntax" in result["reviewer_scores"]
    assert "logic" in result["reviewer_scores"]
    assert "security" in result["reviewer_scores"]


def test_review_code_no_blocks():
    from lib.mar_reviewer import review_code
    result = review_code("just text no code blocks")
    assert result["composite_score"] == 0


def test_extract_code_blocks():
    from lib.mar_reviewer import _extract_code_blocks
    blocks = _extract_code_blocks("before\n```python\nx=1\n```\nafter\n```js\ny=2\n```")
    assert len(blocks) == 2
    assert blocks[0]["language"] == "python"
    assert blocks[1]["language"] == "js"
