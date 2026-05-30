"""Structure gate — checks sections, docstrings, tests."""

import re


def gate_structure(content: str) -> dict:
    has_sections = bool(re.search(r"(?m)^#{1,3}\s", content))
    has_docstrings = "docstring" in content.lower() or '"""' in content or "'''" in content
    has_tests = "def test_" in content or "class Test" in content or "assert " in content

    checks = sum([has_sections, has_docstrings, has_tests])
    score = (checks / 3) * 10
    return {"gate": "structure", "passed": score >= 5, "score": round(score, 1),
            "detail": f"sections={has_sections}, docs={has_docstrings}, tests={has_tests}"}
