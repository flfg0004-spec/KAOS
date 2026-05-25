"""Tests for lib.crystallize (F4 dedup+ merge)."""
import sys, os, tempfile, json
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))


def test_md5_same():
    from lib.crystallize import _md5
    assert _md5("hello") == _md5("hello")
    assert _md5("hello") != _md5("world")


def test_levenshtein_ratio():
    from lib.crystallize import _levenshtein_ratio
    assert _levenshtein_ratio("same", "same") == 1.0
    assert _levenshtein_ratio("abc", "xyz") < 0.5
    assert _levenshtein_ratio("hello", "helo") >= 0.8
    assert _levenshtein_ratio("", "") == 1.0
    assert _levenshtein_ratio("a", "") == 0.0


def test_jaccard_similarity():
    from lib.crystallize import _jaccard_similarity
    assert _jaccard_similarity("the cat sat", "the cat sat") == 1.0
    assert _jaccard_similarity("hello world", "goodbye world") > 0
    assert _jaccard_similarity("", "") == 1.0
    assert _jaccard_similarity("abc", "xyz") == 0.0


def test_find_candidates_empty():
    """Test with nonexistent path shouldn't break."""
    result = []
    # Don't call actual find_candidates (it tries to load MCP). Test only the helpers.
    from lib.crystallize import _get_all_concept_files
    files = _get_all_concept_files()
    assert isinstance(files, list)


def test_crystallize_missing_file():
    from lib.crystallize import crystallize
    result = crystallize("/nonexistent/a.md", "/nonexistent/b.md", dry_run=True)
    assert "error" in result


def test_crystallize_dry_run():
    from lib.crystallize import crystallize
    import tempfile, os
    with tempfile.NamedTemporaryFile(mode="w", suffix=".md", delete=False, encoding="utf-8") as fa:
        fa.write("---\ntitle: Note A\n---\n\nContent of note A about machine learning.")
        path_a = fa.name
    with tempfile.NamedTemporaryFile(mode="w", suffix=".md", delete=False, encoding="utf-8") as fb:
        fb.write("---\ntitle: Note B\n---\n\nContent of note B also about machine learning.")
        path_b = fb.name
    try:
        result = crystallize(path_a, path_b, dry_run=True)
        assert "modified" in result
        assert result["modified"] is False
        assert os.path.exists(path_a)
        assert os.path.exists(path_b)
    finally:
        os.unlink(path_a)
        os.unlink(path_b)


def test_get_all_concept_files():
    from lib.crystallize import _get_all_concept_files, _jaccard_similarity
    files = _get_all_concept_files()
    assert isinstance(files, list)
    # jaccard should be 0 for different content
    assert _jaccard_similarity("abc def ghi", "xyz uvw") == 0.0


def test_cocitation_similarity_empty():
    from lib.crystallize import _cocitation_similarity
    result = _cocitation_similarity([])
    assert result == []
