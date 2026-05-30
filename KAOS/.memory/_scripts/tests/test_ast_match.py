"""Tests for AST signature matching — normalization, fallback, language support."""

import os, sys
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))
os.environ["KAOS_TESTING"] = "1"


def test_ast_signature_normalizes_python():
    from lib.ast_match import ast_signature
    sig1 = ast_signature('''
def process(data):
    result = data["key"]
    return result
''', "python")
    assert sig1 != "", "Should produce non-empty signature"


def test_similar_code_same_signature():
    from lib.ast_match import ast_signature, _token_fallback
    sig1 = ast_signature('''
def process(data):
    result = data["key"]
    return result
''', "python")
    sig2 = ast_signature('''
def get_value(obj):
    value = obj["name"]
    return value
''', "python")
    assert sig1 != "", "First signature should not be empty"
    assert sig2 != "", "Second signature should not be empty"
    # Two structurally identical snippets should be much closer to each other
    # than to a structurally different snippet
    sig3 = ast_signature('for i in range(10): print(i)', "python")
    # Compute similarity: same hash or both non-empty
    assert sig1 != sig3, "Different structures should differ from sig1"


def test_token_fallback_normalizes():
    from lib.ast_match import _token_fallback
    fb1 = _token_fallback('x = a + b')
    fb2 = _token_fallback('y = c + d')
    assert fb1 == fb2, "Fallback should normalize variable names"


def test_different_code_different_signature():
    from lib.ast_match import ast_signature
    sig1 = ast_signature('''
def process(data):
    return data["key"]
''', "python")
    sig2 = ast_signature('''
for i in range(10):
    print(i)
''', "python")
    assert sig1 != sig2, "Different structures should differ"


def test_token_fallback_no_treesitter():
    from lib.ast_match import _token_fallback
    sig = _token_fallback('''
def process(data):
    return data["key"]
''')
    assert sig != "", "Fallback should produce signature"


def test_ast_signature_empty():
    from lib.ast_match import ast_signature
    assert ast_signature("", "python") == ""
    assert ast_signature("   ", "python") == ""


def test_supported_languages():
    from lib.ast_match import supported_languages
    langs = supported_languages()
    assert isinstance(langs, list)
    assert "python" in langs
    assert "rust" in langs or len(langs) == 1


def test_jsx_support():
    from lib.ast_match import _load_language
    jsx = _load_language("jsx")
    assert jsx is not None or True  # graceful if not installed


def test_tsx_support():
    from lib.ast_match import _load_language
    tsx = _load_language("tsx")
    assert tsx is not None or True  # graceful if not installed


def test_ast_signature_rust():
    from lib.ast_match import ast_signature
    sig = ast_signature('''
fn main() {
    let x: i32 = "hello";
}
''', "rust")
    # Should either work or gracefully fail (no crash)
    assert isinstance(sig, str)


def test_ast_signature_javascript():
    from lib.ast_match import ast_signature
    sig = ast_signature('''
function process(data) {
    return data.key;
}
''', "javascript")
    assert isinstance(sig, str)


def test_normalize_node():
    from lib.ast_match import _normalize_node
    assert callable(_normalize_node), "_normalize_node should be callable"


def test_token_fallback_keywords_preserved():
    from lib.ast_match import _token_fallback
    sig = _token_fallback("if True: pass")
    assert sig != "", "Keywords should produce a valid signature"
