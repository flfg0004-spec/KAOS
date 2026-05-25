"""Tests for lib.tagger (F1 auto-tagging) — fast tests only (no DSOL)."""
import sys, os, json, tempfile
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))


def test_tagger_imports():
    from lib.tagger import TAXONOMY_CATEGORIES, BLOCKED_TAGS, ALIAS_MAP
    assert "subject" in TAXONOMY_CATEGORIES
    assert "todo" in BLOCKED_TAGS
    assert "ai" in ALIAS_MAP
    assert "llm" in ALIAS_MAP


def test_suggest_tags_empty():
    from lib.tagger import suggest_tags
    result = suggest_tags("", title="")
    assert isinstance(result, list)


def test_suggest_tags_aliases():
    """Aliases should be resolved without DSOL."""
    from lib.tagger import suggest_tags
    content = "This note discusses LLM and MCP implementation patterns."
    result = suggest_tags(content, title="LLM MCP Patterns")
    tags_str = " ".join(result)
    assert "llm" in tags_str or "large-language-models" in tags_str


def test_suggest_tags_keywords():
    """Fuzzy matching on existing tags works without DSOL."""
    from lib.tagger import suggest_tags
    content = "A note about machine learning and data science."
    result = suggest_tags(content, title="ML Overview")
    assert isinstance(result, list)


def test_tag_file_missing():
    from lib.tagger import tag_file
    result = tag_file("/nonexistent/file.md", dry_run=True)
    assert "error" in result


def test_update_frontmatter_adds_tags():
    from lib.tagger import _update_frontmatter
    content = "---\ntitle: Test\n---\n\nBody text."
    updated = _update_frontmatter(content, ["subject/test", "practice/test"])
    assert 'tags: ["subject/test", "practice/test"]' in updated


def test_update_frontmatter_existing():
    from lib.tagger import _update_frontmatter
    content = '---\ntitle: Test\ntags: ["existing"]\n---\n\nBody.'
    updated = _update_frontmatter(content, ["existing", "new-tag"])
    assert "new-tag" in updated


def test_update_frontmatter_no_frontmatter():
    from lib.tagger import _update_frontmatter
    content = "Just body text without frontmatter."
    updated = _update_frontmatter(content, ["subject/test"])
    assert "tags:" in updated
    assert "---" in updated


def test_get_frontmatter():
    from lib.tagger import _get_frontmatter
    content = "---\ntitle: Hello\ntags: [\"a\", \"b\"]\n---\n\nBody."
    fm = _get_frontmatter(content)
    assert fm.get("title") == "Hello"
    assert "tags" in fm


def test_existing_tags():
    from lib.tagger import _existing_tags
    result = _existing_tags()
    assert isinstance(result, set)


def test_fuzzy_match():
    from lib.tagger import _fuzzy_match
    existing = {"subject/machine-learning", "practice/testing"}
    match = _fuzzy_match("machine learning", existing)
    assert match is not None
    no_match = _fuzzy_match("xyzabc", existing)
    assert no_match is None


def test_blocked_tags_filtered():
    from lib.tagger import suggest_tags, BLOCKED_TAGS
    for blocked in BLOCKED_TAGS:
        result = suggest_tags(f"note about {blocked}", title=blocked)
        assert blocked not in result, f"Blocked tag '{blocked}' should not appear"
