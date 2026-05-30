"""Shared language detection utilities — extracted from agent_executor, orchestrator, quality_gate."""

import re

CODE_BLOCK_PATTERN = re.compile(r"```(\w+)", re.MULTILINE)
LANGUAGE_EXTENSIONS = {
    ".py": "python",
    ".js": "javascript",
    ".ts": "typescript",
    ".rs": "rust",
    ".go": "go",
    ".java": "java",
    ".c": "c",
    ".cpp": "cpp",
    ".rb": "ruby",
    ".kt": "kotlin",
}

LANG_KEYWORDS = {
    "python": [
        "def ",
        "import ",
        "class ",
        "if __name__",
        "print(",
        "lambda ",
        "yield ",
        "async def",
        "None",
        "True",
        "False",
    ],
    "rust": ["fn ", "let mut", "impl ", "pub ", "match ", "unwrap(", "println!", "struct ", "enum ", "trait "],
    "javascript": [
        "function ",
        "const ",
        "let ",
        "var ",
        "=>",
        "console.log",
        "document.",
        "require(",
        "export ",
        "import ",
    ],
    "typescript": [": string", ": number", ": boolean", "interface ", "type ", "as any", "React.FC", ": void"],
    "go": ["func ", "package ", "import (", "defer ", "goroutine", "chan ", "go func", "error "],
    "java": ["public class", "private ", "protected ", "void main", "System.out", "@Override", "import java"],
    "c": ["#include <", "int main(", "printf(", "malloc(", "free(", "void*", "struct "],
    "cpp": ["std::", "template ", "class ", "virtual ", "int main(", "cout <<", "->", "::"],
    "ruby": ["def ", "end", "puts ", "require ", "class ", "attr_", "gem ", "do |"],
    "kotlin": ["fun ", "val ", "var ", "class ", "import ", "println(", "suspend "],
    "swift": ["func ", "var ", "let ", "class ", "struct ", "import UIKit", "print("],
}

RUST_KEYWORDS = {"fn", "let", "mut", "use", "impl", "struct", "enum", "match", "pub", "crate"}
TYPESCRIPT_KEYWORDS = {"interface", "type", "const", "let", "function", "=>", "as", "any", "never"}
GO_KEYWORDS = {"func", "package", "import", "defer", "go", "chan", "goroutine", "interface", "struct"}


def detect_code_language(text: str) -> str:
    """Detect programming language from topic text, path, or code blocks.
    
    Detection priority:
    1. Code block markers (```python, etc.)
    2. File extensions (.py, .rs, .js, etc.)
    3. Code content keywords (def, import, fn, etc.)
    Falls back to "python" if nothing matches.
    """
    if not text:
        return "python"
    tl = text.lower()

    # 1. Code block markers
    m = CODE_BLOCK_PATTERN.search(tl)
    if m:
        raw = m.group(1).lower()
        block_map = {
            "py": "python", "python": "python",
            "js": "javascript", "javascript": "javascript",
            "ts": "typescript", "typescript": "typescript",
            "rs": "rust", "rust": "rust",
            "go": "go", "golang": "go",
            "java": "java",
            "c": "c", "h": "c",
            "cpp": "cpp", "cc": "cpp", "cxx": "cpp", "hpp": "cpp",
            "rb": "ruby", "ruby": "ruby",
            "kt": "kotlin", "kotlin": "kotlin",
        }
        if raw in block_map:
            return block_map[raw]

    # 2. File extensions and language keywords in text
    ext_map = {
        ".py": "python", "python": "python",
        ".rs": "rust", "rust": "rust",
        ".js": "javascript", ".jsx": "javascript", "javascript": "javascript", "node": "javascript",
        ".ts": "typescript", ".tsx": "typescript", "typescript": "typescript",
        ".go": "go", "golang": "go",
        ".java": "java", "java": "java",
        ".c": "c", ".h": "c",
        ".cpp": "cpp", ".cc": "cpp", ".cxx": "cpp", ".hpp": "cpp",
        ".rb": "ruby", "ruby": "ruby",
        ".kt": "kotlin", "kotlin": "kotlin",
    }
    for key, lang in ext_map.items():
        if key in tl:
            return lang

    # 3. Code content keywords
    for lang, keywords in LANG_KEYWORDS.items():
        if any(kw in tl for kw in keywords):
            return lang

    # 4. Early detection for Rust / TypeScript / Go by signature patterns
    if "fn main" in tl or "use std::" in tl:
        return "rust"
    if "package main" in tl and "func main" in tl:
        return "go"
    if "interface " in tl or "type " in tl or ": string" in tl:
        return "typescript"

    return "python"


def detect_code_languages(content: str) -> list[str]:
    """Detect all programming languages present in markdown code blocks."""
    return list(set(re.findall(r"```(\w+)\n", content)))


def detect_language(text: str) -> str:
    if not text:
        return "en"
    spanish_words = {
        "el",
        "la",
        "los",
        "las",
        "de",
        "del",
        "en",
        "un",
        "una",
        "y",
        "que",
        "es",
        "por",
        "para",
        "con",
        "su",
        "al",
        "lo",
        "como",
        "mas",
        "pero",
        "sus",
        "le",
        "ya",
        "este",
        "entre",
        "porque",
        "cuando",
        "muy",
        "sin",
        "sobre",
        "tambien",
        "todo",
        "desde",
        "hasta",
        "nos",
        "modo",
        "bien",
        "solo",
        "era",
        "han",
        "cada",
        "esa",
        "otro",
        "vez",
        "dos",
        "asi",
        "si",
        "despues",
        "aunque",
        "ella",
        "ello",
        "ante",
        "segun",
        "tras",
        "mediante",
        "durante",
    }
    words = set(text.lower().split())
    spanish_count = len(words & spanish_words)
    return "es" if spanish_count > 2 else "en"
