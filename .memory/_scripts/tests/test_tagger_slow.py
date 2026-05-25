"""Slow tests for lib.tagger (requires DSOL/Gemini Flash API)."""
import sys, os, tempfile
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))


def _slow(func):
    func._slow = True
    return func


@_slow
def test_suggest_tags_with_content():
    from lib.tagger import suggest_tags
    content = "Machine learning is a subset of artificial intelligence focused on data-driven algorithms."
    result = suggest_tags(content, title="Machine Learning Overview")
    assert isinstance(result, list)
    assert len(result) > 0
    has_category = any("/" in t for t in result)
    assert has_category, f"No category prefix found in tags: {result}"


@_slow
def test_tag_file_dry_run():
    from lib.tagger import tag_file
    with tempfile.NamedTemporaryFile(mode="w", suffix=".md", delete=False, encoding="utf-8") as f:
        f.write("---\ntitle: Test Note\n---\n\nContent about machine learning algorithms.")
        fpath = f.name
    try:
        result = tag_file(fpath, dry_run=True)
        assert "added" in result
        assert result["modified"] is False
    finally:
        os.unlink(fpath)


@_slow
def test_tag_file_actual_write():
    from lib.tagger import tag_file
    with tempfile.NamedTemporaryFile(mode="w", suffix=".md", delete=False, encoding="utf-8") as f:
        f.write("---\ntitle: Test Write\n---\n\nContent about deep learning and neural networks.")
        fpath = f.name
    try:
        result = tag_file(fpath, dry_run=False)
        assert result["modified"] is True
        with open(fpath, "r", encoding="utf-8") as f:
            content = f.read()
        assert "tags:" in content
    finally:
        os.unlink(fpath)
