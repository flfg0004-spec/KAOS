"""Multi-Agent Review (MAR) — 3 críticos debaten la calidad del código Kratos.

Arquitectura:
  - Syntax Reviewer: Verifica estructura, convenciones, estilo
  - Logic Reviewer: Analiza corrección algorítmica, edge cases
  - Security Reviewer: Detecta vulnerabilidades, malas prácticas
  - Meta-Reviewer: Resuelve conflictos entre revisores, produce feedback consolidado

Cada revisor opera en su propio contexto. Si hay desacuerdo, Meta-Reviewer arbitra.
Output: feedback estructurado con prioridad (critical/major/minor) y sugerencias.
"""

import json
import re
from pathlib import Path
from typing import Optional

SCRIPTS = Path(__file__).resolve().parent


def _count_lines(code: str) -> int:
    return len([l for l in code.split("\n") if l.strip()])


def _extract_code_blocks(text: str) -> list[dict]:
    """Extract code blocks from agent output with their language."""
    blocks = []
    for m in re.finditer(r"```(\w*)\n(.*?)```", text, re.DOTALL):
        blocks.append({
            "language": m.group(1) or "unknown",
            "code": m.group(2),
        })
    return blocks


class SyntaxReviewer:
    """Reviews code syntax, structure, and style conventions."""
    
    name = "syntax"
    
    def review(self, code_blocks: list[dict]) -> dict:
        issues = []
        score = 10.0
        
        for block in code_blocks:
            code = block["code"]
            lang = block["language"]
            
            # Check line length
            for i, line in enumerate(code.split("\n"), 1):
                if len(line) > 100:
                    issues.append({
                        "severity": "minor",
                        "category": "line_length",
                        "message": f"Line {i} exceeds 100 chars ({len(line)})",
                        "suggestion": "Break long lines for readability",
                    })
                    score -= 0.1
            
            # Check function length (very rough)
            funcs = re.findall(r"def \w+|fn \w+|function \w+", code)
            for f in funcs:
                score += 0.5  # bonus for having functions
            
            # Check imports at top
            if lang == "python":
                imports = re.findall(r"^(?:import |from )", code, re.MULTILINE)
                if imports:
                    first_import_line = code.find(imports[0])
                    has_code_before = bool(re.search(r"^[^#\n\s]", code[:first_import_line].strip(), re.MULTILINE)) if first_import_line > 0 else False
                    if has_code_before:
                        issues.append({
                            "severity": "minor",
                            "category": "import_order",
                            "message": "Imports should be at the top of the file",
                            "suggestion": "Move all imports before other code",
                        })
                        score -= 0.3
            
            # Check naming conventions (Python)
            if lang == "python":
                for m in re.finditer(r"^[a-z_][a-zA-Z0-9_]*\s*=\s*[A-Z]", code, re.MULTILINE):
                    issues.append({
                        "severity": "info",
                        "category": "naming",
                        "message": f"Variable '{m.group(0).split('=')[0].strip()}' looks like a constant (use UPPER_CASE)",
                        "suggestion": "Use UPPER_CASE for constants",
                    })
        
        return {
            "reviewer": self.name,
            "score": round(max(0, min(10, score)), 1),
            "issues": issues[:20],
            "issue_count": len(issues),
        }


class LogicReviewer:
    """Reviews code logic, algorithm correctness, and edge cases."""
    
    name = "logic"
    
    def review(self, code_blocks: list[dict]) -> dict:
        issues = []
        score = 10.0
        
        for block in code_blocks:
            code = block["code"]
            lang = block["language"]
            
            # Check for bare except
            if re.search(r"except\s*:", code):
                issues.append({
                    "severity": "major",
                    "category": "bare_except",
                    "message": "Bare 'except:' catches ALL exceptions including SystemExit",
                    "suggestion": "Use 'except Exception:' or specific exception types",
                })
                score -= 1.0
            
            # Check for mutable default args
            for m in re.finditer(r"def \w+\(.*?=\s*(\[\]|\{\}|set\(\))", code):
                issues.append({
                    "severity": "major",
                    "category": "mutable_default",
                    "message": f"Mutable default argument in '{m.group(0).split('(')[0]}'",
                    "suggestion": "Use None as default and initialize inside function",
                })
                score -= 1.0
            
            # Check for missing return type hints
            if lang == "python":
                funcs = re.findall(r"def \w+\(.*?\):", code)
                for f in funcs:
                    if "->" not in f:
                        issues.append({
                            "severity": "minor",
                            "category": "missing_return_type",
                            "message": f"Missing return type hint: {f.strip()}",
                            "suggestion": "Add -> ReturnType to function signature",
                        })
                        score -= 0.3
            
            # Check for print statements in production code
            if re.search(r"print\s*\(", code) and "def test" not in code:
                issues.append({
                    "severity": "info",
                    "category": "print_usage",
                    "message": "print() found outside tests",
                    "suggestion": "Use logging module instead of print()",
                })
                score -= 0.2
            
            # Check empty functions/branches
            if re.search(r"pass\s*#?\s*TODO", code, re.IGNORECASE):
                issues.append({
                    "severity": "major",
                    "category": "unimplemented",
                    "message": "Unimplemented function with TODO/pass",
                    "suggestion": "Implement or raise NotImplementedError",
                })
                score -= 1.0
            
            # Check for recursion without base case
            func_bodies = re.findall(r"def (\w+)\(.*?\):(.*?)(?=\ndef |\Z)", code, re.DOTALL)
            for name, body in func_bodies:
                if name in body and "if" not in body[:200]:
                    issues.append({
                        "severity": "critical",
                        "category": "recursion",
                        "message": f"'{name}' recurses without visible base case",
                        "suggestion": "Add base case condition before recursive call",
                    })
                    score -= 2.0
        
        return {
            "reviewer": self.name,
            "score": round(max(0, min(10, score)), 1),
            "issues": issues[:20],
            "issue_count": len(issues),
        }


class SecurityReviewer:
    """Reviews code for security vulnerabilities and bad practices."""
    
    name = "security"
    
    def review(self, code_blocks: list[dict]) -> dict:
        issues = []
        score = 10.0
        
        dangerous_patterns = [
            (r"eval\s*\(", "critical", "eval_usage", "eval() executes arbitrary code", "Use ast.literal_eval() or a proper parser", -2.0),
            (r"exec\s*\(", "critical", "exec_usage", "exec() is dangerous in production", "Refactor to avoid dynamic code execution", -2.0),
            (r"__import__\s*\(", "major", "dynamic_import", "Dynamic import can be exploited", "Import statically or use importlib with validation", -1.5),
            (r"pickle\.(load|loads)\s*\(", "critical", "pickle_danger", "Unpickling untrusted data is RCE", "Use JSON or a safe serialization format", -2.0),
            (r"os\.system\s*\(", "major", "shell_injection", "Potential shell injection", "Use subprocess.run with list args", -1.5),
            (r"subprocess\.\w+.*shell\s*=\s*True", "major", "shell_true", "shell=True enables shell injection", "Pass args as list, not string", -1.5),
            (r"(?:password|passwd|pwd)\s*=\s*['\"][^'\"]+['\"]", "critical", "hardcoded_password", "Hardcoded credential", "Use environment variables or secrets manager", -2.0),
            (r"(?:api_key|apikey|secret|token)\s*=\s*['\"][^'\"]{8,}['\"]", "critical", "hardcoded_secret", "Hardcoded API key or token", "Use environment variable or vault", -2.0),
            (r"sql\.execute\s*\(\s*f['\"]|raw_sql.*f['\"]", "critical", "sql_injection", "f-string in SQL query = SQL injection", "Use parameterized queries", -2.0),
            (r"mark_safe|safe\s*\|", "major", "xss_risk", "Marking content as safe can enable XSS", "Sanitize before marking safe", -1.5),
        ]
        
        for block in code_blocks:
            code = block["code"]
            for pattern, severity, category, msg, suggestion, penalty in dangerous_patterns:
                for m in re.finditer(pattern, code, re.IGNORECASE):
                    issues.append({
                        "severity": severity,
                        "category": category,
                        "message": msg,
                        "suggestion": suggestion,
                        "context": code[max(0, m.start()-30):m.end()+30],
                    })
                    score += penalty
        
        # Bonus: check for good practices
        if re.search(r"(?:def test_|class Test)", " ".join(b["code"] for b in code_blocks)):
            score += 1.0  # bonus for having tests
        
        if re.search(r"(?:logging\.)", " ".join(b["code"] for b in code_blocks)):
            score += 0.5  # bonus for using logging
        
        return {
            "reviewer": self.name,
            "score": round(max(0, min(10, score)), 1),
            "issues": issues[:20],
            "issue_count": len(issues),
        }


class MetaReviewer:
    """Resolves conflicts between reviewers and produces consolidated feedback."""
    
    name = "meta"
    
    def consolidate(self, reviews: list[dict]) -> dict:
        all_issues = []
        total_score = 0
        
        for review in reviews:
            total_score += review["score"]
            for issue in review["issues"]:
                all_issues.append({
                    **issue,
                    "reviewer": review["reviewer"],
                })
        
        avg_score = round(total_score / max(1, len(reviews)), 1)
        
        # Prioritize issues
        critical = [i for i in all_issues if i["severity"] == "critical"]
        major = [i for i in all_issues if i["severity"] == "major"]
        minor = [i for i in all_issues if i["severity"] == "minor"]
        info = [i for i in all_issues if i["severity"] == "info"]
        
        # Deduplicate similar issues
        seen = set()
        unique_issues = []
        for issue in all_issues:
            key = (issue["category"], issue["message"][:50])
            if key not in seen:
                seen.add(key)
                unique_issues.append(issue)
        
        return {
            "composite_score": avg_score,
            "reviewer_scores": {r["reviewer"]: r["score"] for r in reviews},
            "issues": {
                "critical": critical,
                "major": major,
                "minor": minor,
                "info": info,
            },
            "total_issues": len(all_issues),
            "unique_issues": len(unique_issues),
            "summary": (
                f"MAR Score: {avg_score}/10. "
                f"{len(critical)} critical, {len(major)} major, "
                f"{len(minor)} minor, {len(info)} info issues."
            ),
        }


def review_code(kratos_output: str) -> dict:
    """Run full MAR review pipeline on Kratos output.
    
    Args:
        kratos_output: The code generated by Kratos
    
    Returns:
        dict with consolidated review from all reviewers
    """
    code_blocks = _extract_code_blocks(kratos_output)
    
    if not code_blocks:
        return {
            "composite_score": 0,
            "reviewer_scores": {},
            "issues": {},
            "total_issues": 0,
            "summary": "No code blocks found in Kratos output",
        }
    
    reviewers = [SyntaxReviewer(), LogicReviewer(), SecurityReviewer()]
    reviews = [r.review(code_blocks) for r in reviewers]
    
    meta = MetaReviewer()
    return meta.consolidate(reviews)


if __name__ == "__main__":
    import json
    
    sample_code = """
def process(data: list) -> dict:
    result = {}
    for item in data:
        try:
            result[item['id']] = item['value']
        except:
            pass
    return result

# Test
def test_process():
    data = [{'id': 1, 'value': 'a'}]
    assert process(data) == {1: 'a'}
"""
    result = review_code(f"```python\n{sample_code}\n```")
    print(json.dumps(result, indent=2, default=str))
