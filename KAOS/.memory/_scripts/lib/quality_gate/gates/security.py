"""Security gate — checks for dangerous patterns."""

import re

DANGEROUS_PATTERNS = [
    (r"eval\s*\(", "eval() usage"),
    (r"exec\s*\(", "exec() usage"),
    (r"__import__\s*\(", "dynamic import"),
    (r"pickle\.loads?\s*\(", "unsafe deserialization"),
    (r"os\.system\s*\(", "shell injection risk"),
    (r"subprocess\.\w+.*shell\s*=\s*True", "shell=True risk"),
    (r"(?i)password\s*=\s*['\"]", "hardcoded password"),
    (r"(?i)api_key\s*=\s*['\"]", "hardcoded API key"),
    (r"(?i)secret\s*=\s*['\"]", "hardcoded secret"),
    (r"(?i)token\s*=\s*['\"]", "hardcoded token"),
]


def gate_security(content: str) -> dict:
    findings = []
    for pattern, desc in DANGEROUS_PATTERNS:
        if re.search(pattern, content):
            findings.append(desc)

    score = max(0, 10 - len(findings) * 2)
    return {"gate": "security", "passed": score >= 6, "score": score,
            "detail": f"{len(findings)} issues: {', '.join(findings)}" if findings else "No issues"}
