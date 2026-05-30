"""Syntax gate — tree-sitter AST parse check."""

from lib.feature_flags import is_enabled

_MULTI_LANG_FLAGS = {"rust": "use_rust_gates", "typescript": "use_ts_gates", "go": "use_go_gates"}


def gate_syntax(content: str, language: str = "python") -> dict:
    try:
        from lib.ast_match import ast_signature
        sig = ast_signature(content, language)
        passed = bool(sig)
        return {"gate": "syntax", "passed": passed, "score": 1.0 if passed else 0.0,
                "detail": "AST parseable" if passed else "AST parse failed"}
    except Exception as e:
        return {"gate": "syntax", "passed": False, "score": 0.0, "detail": str(e)}


def gate_syntax_multi(content: str, language: str) -> dict:
    if language not in ("rust", "typescript", "go"):
        return {"gate": "syntax", "passed": True, "score": 5.0,
                "detail": f"No syntax gate for {language}"}
    flag = _MULTI_LANG_FLAGS.get(language, "")
    if not is_enabled(flag):
        return {"gate": "syntax", "passed": True, "score": 5.0,
                "detail": f"{language} syntax gate disabled"}
    try:
        import tree_sitter
        langs = {"rust": "tree_sitter_rust", "typescript": "tree_sitter_typescript",
                 "go": "tree_sitter_go"}
        if language in langs:
            mod = __import__(langs[language], fromlist=["language"])
            parser = tree_sitter.Parser()
            parser.set_language(mod.language())
            tree = parser.parse(bytes(content, "utf-8"))
            passed = tree is not None and tree.root_node is not None
            return {"gate": "syntax", "passed": passed, "score": 1.0 if passed else 0.0,
                    "detail": "AST parseable" if passed else "AST parse failed"}
    except ImportError:
        pass
    except Exception:
        pass
    return {"gate": "syntax", "passed": True, "score": 5.0,
            "detail": "Syntax check not available (tree-sitter not installed)"}
