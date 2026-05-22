"""Kratos CodeReview — autonomous PR review with AST matching + CodeExperience."""
import sys, re, json, subprocess
from pathlib import Path

SCRIPTS = Path(__file__).resolve().parent.parent / ".memory" / "_scripts"
sys.path.insert(0, str(SCRIPTS))
from lib.code_memory import search
from lib.ast_match import ast_signature, supported_languages

def review_diff(diff_text: str, language: str = "python") -> dict:
    """Review a diff and return findings.
    
    Args:
        diff_text: Unified diff output
        language: Programming language for AST matching
    
    Returns:
        dict with review findings, severity, and suggestions
    """
    findings = []
    
    # Parse diff for added lines (potential issues)
    added_lines = []
    for line in diff_text.split("\n"):
        if line.startswith("+") and not line.startswith("+++"):
            added_lines.append(line[1:])
    
    # Check each added line for known error patterns
    for line in added_lines:
        line = line.strip()
        if not line:
            continue
        
        # Check for common anti-patterns via AST
        ast_sig = ""
        if language in supported_languages():
            try:
                ast_sig = ast_signature(line, language)
            except Exception:
                pass
        
        # Search CodeExperience for similar error patterns
        results = search(line[:100], code_snippet=line, language=language)
        if results:
            for r in results[:2]:
                if r["confidence"] > 0.6:
                    findings.append({
                        "severity": "warning",
                        "match": line[:80],
                        "known_error": r["error"][:80],
                        "confidence": r["confidence"],
                        "solution_hint": r["solution"][:100] if r["solution"] else ""
                    })
    
    summary = {
        "language": language,
        "lines_reviewed": len(added_lines),
        "findings": findings,
        "severity_counts": {
            "warning": sum(1 for f in findings if f["severity"] == "warning"),
            "error": sum(1 for f in findings if f["severity"] == "error"),
        }
    }
    
    return summary

def review_git_diff(branch: str = "HEAD", base: str = "main") -> dict:
    """Review changes in a git branch.
    
    Args:
        branch: Branch to review (default: current working tree)
        base: Base branch to compare against (default: main)
    
    Returns:
        dict with review results
    """
    try:
        result = subprocess.run(
            ["git", "diff", f"{base}..{branch}", "--", "*.py", "*.rs", "*.js", "*.ts", "*.go"],
            capture_output=True, text=True, cwd=str(SCRIPTS.parent),
            timeout=30
        )
        diff = result.stdout
    except Exception as e:
        return {"error": str(e), "findings": []}
    
    if not diff.strip():
        return {"message": "No changes to review", "findings": []}
    
    # Detect language from file extensions in diff
    lang_hints = {"py": "python", "rs": "rust", "js": "javascript", "ts": "typescript", "go": "go"}
    detected_lang = "python"
    for ext, lang in lang_hints.items():
        if f".{ext}" in diff[:500]:
            detected_lang = lang
            break
    
    return review_diff(diff, detected_lang)

if __name__ == "__main__":
    import argparse
    p = argparse.ArgumentParser()
    p.add_argument("--branch", default="HEAD", help="Branch to review")
    p.add_argument("--base", default="main", help="Base branch")
    args = p.parse_args()
    
    review = review_git_diff(args.branch, args.base)
    print(f"CodeReview: {review.get('lines_reviewed', 0)} lines reviewed, {len(review.get('findings', []))} findings")
    for f in review.get("findings", []):
        print(f"  [{f['severity']}] {f['match']}")
        if f.get("solution_hint"):
            print(f"    -> Hint: {f['solution_hint']}")
