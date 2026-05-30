"""PR Integration Gate — architecture review for pull requests."""

import logging
import re

logger = logging.getLogger("pr_gate")

VIOLATION_PATTERNS = {
    "layer_violation": [
        r"from\s+controllers\s+import.*models",
        r"from\s+views\s+import.*models\.",
        r"from\s+infrastructure\s+import.*domain\.",
    ],
    "circular_import_risk": [r"from\s+(\w+)\s+import.*\1"],
    "god_component": [r"class\s+\w+\(.*\):.*\n(?:\s+def\s+\w+.*\n){15,}"],
    "missing_error_handling": [r"except\s*:", r"except\s+Exception\s*:"],
    "hardcoded_config": [r"(?:host|port|password|secret|key)\s*=\s*[\"'][^\"']+[\"']"],
}


def analyze_diff(diff_text: str, filename: str = "") -> dict:
    violations = []
    for category, patterns in VIOLATION_PATTERNS.items():
        for p in patterns:
            matches = list(re.finditer(p, diff_text, re.MULTILINE))
            for m in matches:
                line_num = diff_text[: m.start()].count("\n") + 1
                violations.append({"category": category, "line": line_num, "match": m.group()[:100], "file": filename})
    severity_weights = {
        "layer_violation": 5,
        "circular_import_risk": 4,
        "god_component": 4,
        "missing_error_handling": 3,
        "hardcoded_config": 5,
    }
    score = 100
    for v in violations:
        score -= severity_weights.get(v["category"], 2)
    category_counts = {}
    for v in violations:
        c = v["category"]
        category_counts[c] = category_counts.get(c, 0) + 1
    return {
        "score": max(0, score),
        "violations": violations,
        "violation_count": len(violations),
        "category_breakdown": category_counts,
        "has_critical": any(v["category"] in ("layer_violation", "hardcoded_config") for v in violations),
        "files_affected": len(set(v["file"] for v in violations)) if filename else 1,
    }


def generate_pr_comment(analysis: dict, pr_title: str = "") -> str:
    emoji = "🟢" if analysis["score"] >= 80 else "🟡" if analysis["score"] >= 50 else "🔴"
    lines = [f"## {emoji} Architecture Review: Score {analysis['score']}/100", ""]
    if pr_title:
        lines.append(f"**PR**: {pr_title}")
        lines.append("")
    lines.append("### Summary")
    lines.append(f"- **Violations found**: {analysis['violation_count']}")
    lines.append(f"- **Files affected**: {analysis['files_affected']}")
    lines.append(f"- **Critical issues**: {'Yes ⚠️' if analysis.get('has_critical') else 'None ✅'}")
    lines.append("")
    if analysis["category_breakdown"]:
        lines.append("### Violations by Category")
        for cat, count in sorted(analysis["category_breakdown"].items(), key=lambda x: -x[1]):
            sev = "🔴" if cat in ("layer_violation", "hardcoded_config") else "🟡"
            lines.append(f"- {sev} **{cat}**: {count}")
        lines.append("")
    if analysis["violations"]:
        lines.append("### Details")
        for v in analysis["violations"][:10]:
            sev = "🔴" if v["category"] in ("layer_violation", "hardcoded_config") else "🟡"
            file_info = f" in `{v['file']}`" if v.get("file") else ""
            lines.append(f"- {sev} `{v['category']}` at line {v['line']}{file_info}")
            lines.append(f"  ```\n  {v['match']}\n  ```")
    if analysis["score"] < 50:
        lines.append("")
        lines.append("### ❌ Gate Blocked")
        lines.append("This PR does not pass the architecture quality gate. Please address the issues above.")
    elif analysis["score"] < 80:
        lines.append("")
        lines.append("### ⚠️ Gate Warning")
        lines.append("This PR passes but has architectural concerns that should be reviewed.")
    else:
        lines.append("")
        lines.append("### ✅ Gate Passed")
        lines.append("Architecture review passed. No critical issues detected.")
    return "\n".join(lines)


def gate(diff_text: str, filename: str = "", pr_title: str = "", threshold: int = 50) -> dict:
    analysis = analyze_diff(diff_text, filename)
    comment = generate_pr_comment(analysis, pr_title)
    return {
        "passed": analysis["score"] >= threshold,
        "score": analysis["score"],
        "threshold": threshold,
        "analysis": analysis,
        "comment": comment,
    }
