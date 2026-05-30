"""Tests for AST Skill Library — mining, searching, recording."""

import os, sys
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))
os.environ["KAOS_TESTING"] = "1"


def _clean_skill_db():
    from lib.skill_library import SKILL_DB
    if SKILL_DB.exists():
        try:
            SKILL_DB.unlink()
        except PermissionError:
            pass


def test_init_creates_tables():
    from lib.skill_library import status
    _clean_skill_db()
    s = status()
    assert "total_skills" in s
    assert "avg_confidence" in s


def test_mine_skills_dry_run():
    from lib.skill_library import mine_skills
    _clean_skill_db()
    result = mine_skills(dry_run=True)
    assert "skills_mined" in result
    assert "dry_run" in result
    assert result["dry_run"] is True


def test_mine_skills_execute():
    from lib.skill_library import mine_skills, status
    _clean_skill_db()
    
    # Populate some high-confidence experiences
    from lib.code_memory import init, store, feedback
    init()
    for i in range(3):
        r = store(
            error_message=f"SkillTest Error {i}: pattern type failure",
            language="python",
            code_snippet="x = broken_func()",
        )
        if r["status"] == "created":
            feedback(r["hash"], success=True)
            feedback(r["hash"], success=True)
    
    result = mine_skills(dry_run=False)
    assert "skills_mined" in result
    assert result["dry_run"] is False
    
    s = status()
    assert s["total_skills"] >= 0


def test_search_skills():
    from lib.skill_library import search_skills
    _clean_skill_db()
    skills = search_skills("error", language="python", top_k=5)
    assert isinstance(skills, list)


def test_record_usage():
    from lib.skill_library import record_usage, status
    _clean_skill_db()
    result = record_usage(skill_id=1)
    assert result["status"] == "updated"


def test_extract_skill_name():
    from lib.skill_library import _extract_skill_name
    name = _extract_skill_name("TypeError: cannot unpack non-iterable NoneType object")
    assert len(name) > 0
    assert "TypeError" not in name  # Should strip common prefixes
