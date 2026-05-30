"""Tests for lang_utils — language detection functions."""

import os, sys
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))
os.environ["KAOS_TESTING"] = "1"


def test_detect_code_language_from_extension():
    from lib.lang_utils import detect_code_language
    assert detect_code_language("file.py") == "python"
    assert detect_code_language("main.rs") == "rust"
    assert detect_code_language("app.ts") == "typescript"
    assert detect_code_language("app.js") == "javascript"
    assert detect_code_language("main.go") == "go"
    assert detect_code_language("Main.java") == "java"


def test_detect_code_language_from_keywords():
    from lib.lang_utils import detect_code_language
    assert detect_code_language("def hello(): pass") == "python"
    assert detect_code_language("fn main() {}") == "rust"
    assert detect_code_language("function hello() {}") == "javascript"


def test_detect_code_language_from_code_block():
    from lib.lang_utils import detect_code_language
    assert detect_code_language("```python\ndef foo(): pass\n```") == "python"
    assert detect_code_language("```rust\nfn main() {}\n```") == "rust"
    assert detect_code_language("```go\nfunc main() {}\n```") == "go"


def test_detect_code_language_empty():
    from lib.lang_utils import detect_code_language
    assert detect_code_language("") == "python"
    assert detect_code_language(None) == "python"


def test_detect_code_language_fallback():
    from lib.lang_utils import detect_code_language
    assert detect_code_language("some random text without code") == "python"


def test_detect_code_languages():
    from lib.lang_utils import detect_code_languages
    result = detect_code_languages("```python\nx=1\n```\n```rust\nfn main() {}\n```")
    assert "python" in result
    assert "rust" in result


def test_detect_code_language_from_code_block_marker():
    """detect_code_language detects language from code block markers."""
    from lib.lang_utils import detect_code_language
    assert detect_code_language("```python\nx = 1\n```") == "python"
    assert detect_code_language("```rust\nfn main() {}\n```") == "rust"
    assert detect_code_language("```go\npackage main\n```") == "go"


def test_detect_code_language_topic_string():
    from lib.lang_utils import detect_code_language
    assert detect_code_language("implement a REST API in python") == "python"
    assert detect_code_language("write a rust module for file parsing") == "rust"
    assert detect_code_language("create typescript interface for User") == "typescript"
