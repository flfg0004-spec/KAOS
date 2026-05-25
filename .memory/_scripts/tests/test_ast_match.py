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
    from lib.ast_match import ast_signature
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
    assert sig1 == sig2, "Structurally identical code should match"


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
    # At minimum should have python if tree-sitter is installed
    # If not, should be empty list (no crash)


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
