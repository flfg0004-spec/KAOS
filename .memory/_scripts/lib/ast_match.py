"""AST signature matching for CodeExperience — structural error pattern recognition.

Extracts normalized AST structure from code snippets to match structurally
similar errors regardless of variable names or literal values.
"""
import hashlib
import re

_LANGUAGES = {}
_GRAMMAR_CACHE = {}

def _load_language(lang: str):
    if lang in _GRAMMAR_CACHE:
        return _GRAMMAR_CACHE[lang]
    try:
        if lang == "python":
            import tree_sitter_python
            _GRAMMAR_CACHE[lang] = tree_sitter_python.language()
        elif lang == "rust":
            import tree_sitter_rust
            _GRAMMAR_CACHE[lang] = tree_sitter_rust.language()
        elif lang == "javascript":
            import tree_sitter_javascript
            _GRAMMAR_CACHE[lang] = tree_sitter_javascript.language()
        elif lang == "typescript":
            import tree_sitter_typescript
            _GRAMMAR_CACHE[lang] = tree_sitter_typescript.language_typescript()
        elif lang == "go":
            import tree_sitter_go
            _GRAMMAR_CACHE[lang] = tree_sitter_go.language()
        elif lang == "jsx":
            try:
                import tree_sitter_javascript
                _GRAMMAR_CACHE[lang] = tree_sitter_javascript.language()
            except Exception:
                return None
        elif lang == "tsx":
            try:
                import tree_sitter_typescript
                _GRAMMAR_CACHE[lang] = tree_sitter_typescript.language_tsx()
            except Exception:
                return None
        elif lang == "java":
            try:
                import tree_sitter_java
                _GRAMMAR_CACHE[lang] = tree_sitter_java.language()
            except Exception:
                return None
        elif lang == "c":
            try:
                import tree_sitter_c
                _GRAMMAR_CACHE[lang] = tree_sitter_c.language()
            except Exception:
                return None
        elif lang == "cpp":
            try:
                import tree_sitter_cpp
                _GRAMMAR_CACHE[lang] = tree_sitter_cpp.language()
            except Exception:
                return None
        elif lang == "ruby":
            try:
                import tree_sitter_ruby
                _GRAMMAR_CACHE[lang] = tree_sitter_ruby.language()
            except Exception:
                return None
        else:
            return None
        return _GRAMMAR_CACHE[lang]
    except Exception:
        return None

def _normalize_node(node, source: bytes) -> str:
    """Walk AST and produce normalized structural signature."""
    kind = node.type
    children = list(node.children)
    
    # Leaf nodes: normalize identifiers and literals
    if not children:
        text = source[node.start_byte:node.end_byte].decode("utf-8", errors="replace")
        if kind in ("identifier", "variable_name", "property_identifier"):
            return "ID"
        if kind in ("string", "string_literal", "string_content"):
            return "STR"
        if kind in ("integer", "number", "float", "true", "false"):
            return "NUM"
        if kind in ("comment", "ERROR"):
            return ""
        return text.strip()
    
    # Internal nodes: recurse
    child_sigs = [_normalize_node(c, source) for c in children]
    child_sigs = [c for c in child_sigs if c]
    if not child_sigs:
        return ""
    if len(child_sigs) == 1:
        return child_sigs[0]
    return f"({kind} {' '.join(child_sigs)})"

def ast_signature(code: str, language: str = "python") -> str:
    """Extract normalized AST signature from source code.
    
    Args:
        code: Source code snippet containing the error pattern
        language: One of 'python', 'rust', 'javascript'
    
    Returns:
        SHA-256 hash of the normalized AST structure, or empty string on failure
    """
    if not code or not code.strip():
        return ""
    
    lang = _load_language(language)
    if not lang:
        return _token_fallback(code)
    
    try:
        import tree_sitter as ts
        parser = ts.Parser(lang)
        tree = parser.parse(bytes(code, "utf-8"))
        sig = _normalize_node(tree.root_node, bytes(code, "utf-8"))
        if sig:
            return hashlib.sha256(sig.encode()).hexdigest()[:16]
        return _token_fallback(code)
    except Exception:
        return _token_fallback(code)

def _token_fallback(code: str) -> str:
    """Simple token-based structural signature (no tree-sitter dependency)."""
    # Strip strings
    code = re.sub(r'"[^"]*"', 'STR', code)
    code = re.sub(r"'[^']*'", 'STR', code)
    # Strip numbers
    code = re.sub(r'\b\d+\b', 'NUM', code)
    # Strip identifiers (keep keywords)
    keywords = {"if","else","for","while","def","class","return","import","from",
                "let","fn","mut","const","var","match","async","await","pub","use",
                "function","null","undefined","true","false"}
    tokens = re.findall(r'[a-zA-Z_]\w*|[^\w\s]', code)
    normalized = []
    for t in tokens:
        if t in keywords:
            normalized.append(t)
        elif t.isalpha():
            normalized.append("ID")
        else:
            normalized.append(t)
    sig = " ".join(normalized)
    if sig:
        return hashlib.sha256(sig.encode()).hexdigest()[:16]
    return ""

def supported_languages() -> list:
    """Return list of languages with available grammars."""
    langs = []
    for l in ["python", "rust", "javascript", "typescript", "jsx", "tsx", "go", "java", "c", "cpp", "ruby"]:
        if _load_language(l):
            langs.append(l)
    return langs

if __name__ == "__main__":
    # Test Python
    py_code = '''
def process(data):
    result = data["key"]
    return result
'''
    sig1 = ast_signature(py_code, "python")
    print(f"Python signature: {sig1}")
    
    # Test similar pattern (different names)
    py_code2 = '''
def get_value(obj):
    value = obj["name"]
    return value
'''
    sig2 = ast_signature(py_code2, "python")
    print(f"Python similar:  {sig2}")
    print(f"Match: {sig1 == sig2}")
    
    # Test Rust
    rs_code = '''
fn main() {
    let x: i32 = "hello";
}
'''
    sig3 = ast_signature(rs_code, "rust")
    print(f"Rust signature: {sig3}")
    
    # Test JavaScript
    js_code = '''
function process(data) {
    return data.key;
}
'''
    sig4 = ast_signature(js_code, "javascript")
    print(f"JavaScript sig: {sig4}")
    
    print(f"\nSupported: {supported_languages()}")
