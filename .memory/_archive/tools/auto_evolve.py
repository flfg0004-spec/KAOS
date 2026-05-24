"""Auto-evolution: Kratos improves own skill based on CodeExperience results."""
import json, sys
from pathlib import Path

SCRIPTS = Path(__file__).resolve().parent.parent / ".memory" / "_scripts"
sys.path.insert(0, str(SCRIPTS))
from lib.code_memory import status, DB

SKILL_PATH = SCRIPTS.parent / ".opencode" / "skills" / "kratos" / "SKILL.md"
EVOLUTION_LOG = SCRIPTS.parent / ".memory" / "cache" / "skill-evolution.json"

def analyze_patterns() -> dict:
    """Analyze CodeExperience to find patterns for skill improvement."""
    import sqlite3
    conn = sqlite3.connect(str(DB))
    
    # Best patterns (high confidence, many retrievals)
    best = conn.execute("""
        SELECT pattern_category, confidence, retrieval_count, language
        FROM code_experiences
        WHERE confidence > 0.7 AND retrieval_count > 3 AND pattern_category != ''
        ORDER BY confidence DESC LIMIT 5
    """).fetchall()
    
    # Worst patterns (low confidence, abandoned)
    worst = conn.execute("""
        SELECT pattern_category, confidence, retrieval_count, language
        FROM code_experiences
        WHERE confidence < 0.2 AND retrieval_count < 2 AND pattern_category != ''
        ORDER BY confidence ASC LIMIT 5
    """).fetchall()
    
    # Languages used
    langs = conn.execute("""
        SELECT language, COUNT(*) as c FROM code_experiences
        WHERE confidence > 0
        GROUP BY language ORDER BY c DESC
    """).fetchall()
    
    conn.close()
    
    return {
        "best_patterns": [{"category": b[0], "confidence": b[1], "retrievals": b[2], "lang": b[3]} for b in best],
        "worst_patterns": [{"category": w[0], "confidence": w[1], "retrievals": w[2], "lang": w[3]} for w in worst],
        "top_languages": [{"lang": l[0], "count": l[1]} for l in langs[:3]]
    }

def suggest_improvements(patterns: dict) -> list:
    """Generate skill improvement suggestions from patterns."""
    suggestions = []
    
    if patterns["best_patterns"]:
        cats = [p["category"] for p in patterns["best_patterns"]]
        suggestions.append(f"Priorizar deteccion de patrones: {', '.join(cats[:3])}")
    
    if patterns["worst_patterns"]:
        cats = [p["category"] for p in patterns["worst_patterns"]]
        suggestions.append(f"Revisar patrones de baja confianza: {', '.join(cats[:3])}")
    
    if patterns["top_languages"]:
        langs = [l["lang"] for l in patterns["top_languages"]]
        suggestions.append(f"Optimizar AST matching para: {', '.join(langs)}")
    
    return suggestions

def evolve():
    """Run auto-evolution cycle."""
    patterns = analyze_patterns()
    suggestions = suggest_improvements(patterns)
    
    evolution = {"timestamp": "2026-05-21", "patterns": patterns, "suggestions": suggestions}
    EVOLUTION_LOG.parent.mkdir(parents=True, exist_ok=True)
    
    # Load existing log
    entries = []
    if EVOLUTION_LOG.exists():
        entries = json.loads(EVOLUTION_LOG.read_text())
    entries.append(evolution)
    EVOLUTION_LOG.write_text(json.dumps(entries[-100:], indent=2))
    
    print(f"Auto-evolution: {len(suggestions)} suggestions from {len(patterns['best_patterns'])} best + {len(patterns['worst_patterns'])} worst patterns")
    for s in suggestions:
        print(f"  -> {s}")
    
    # Update SKILL.md with new insights
    if SKILL_PATH.exists():
        skill = SKILL_PATH.read_text()
        # Add evolution section if not present
        if "## Auto-Evolution" not in skill:
            skill += "\n## Auto-Evolution\n"
            skill += f"*Ultima evolucion: 2026-05-21*\n"
            for s in suggestions:
                skill += f"- {s}\n"
            SKILL_PATH.write_text(skill)
            print(f"  SKILL.md updated with {len(suggestions)} suggestions")
    
    return evolution

if __name__ == "__main__":
    evolve()
