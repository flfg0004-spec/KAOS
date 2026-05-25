"""Slow tests for lib.tagger (requires DSOL/Gemini Flash API)."""
import sys, os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))


def _slow(func):
    func._slow = True
    return func


@_slow
def test_suggest_tags_with_content():
    from lib.tagger import suggest_tags
    content = "Machine learning is a subset of artificial intelligence focused on data-driven algorithms. Deep learning uses neural networks with multiple layers to model complex patterns."
    result = suggest_tags(content, title="Machine Learning Overview")
    assert isinstance(result, list)
    assert len(result) > 0
    for tag in result:
        assert "/" in tag or tag.islower(), f"Tag '{tag}' should be categorized or lowercase"


@_slow
def test_suggest_tags_with_spanish():
    from lib.tagger import suggest_tags
    content = "El aprendizaje automático es una rama de la inteligencia artificial que permite a los sistemas aprender patrones a partir de datos sin ser programados explícitamente."
    result = suggest_tags(content, title="Aprendizaje Automático")
    assert isinstance(result, list)
    assert len(result) > 0


@_slow
def test_suggest_tags_empty():
    from lib.tagger import suggest_tags
    result = suggest_tags("", title="")
    assert isinstance(result, list)
    assert len(result) == 0


@_slow
def test_tag_file_dry_run():
    from lib.tagger import tag_file
    test_path = os.path.join(os.path.dirname(__file__), "..", "wiki", "index.md")
    if os.path.exists(test_path):
        result = tag_file(test_path, dry_run=True)
        assert "error" not in result, f"Unexpected error: {result.get('error')}"
        assert "path" in result
