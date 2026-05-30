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


def detect_code_language(text: str) -> str:
    if not text:
        return "python"
    m = CODE_BLOCK_PATTERN.search(text)
    if m:
        lang = m.group(1).lower()
        if lang in ("python", "py"):
            return "python"
        if lang in ("javascript", "js"):
            return "javascript"
        if lang in ("typescript", "ts"):
            return "typescript"
        if lang in ("rust", "rs"):
            return "rust"
        if lang in ("go", "golang"):
            return "go"
        if lang in ("java",):
            return "java"
    for ext, lang in LANGUAGE_EXTENSIONS.items():
        if ext in text:
            return lang
    # Detect from code content keywords
    for lang, keywords in LANG_KEYWORDS.items():
        if any(kw in text for kw in keywords):
            return lang
    return "python"


def detect_code_language(topic_or_path: str) -> str:
    """Detect programming language from topic text or path."""
    tl = topic_or_path.lower()
    code_map = {
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
    for key, lang in code_map.items():
        if key in tl:
            return lang
    return "unknown"


def detect_code_languages(content: str) -> list[str]:
    """Detect all programming languages present in markdown code blocks."""
    return list(set(re.findall(r"```(\w+)\n", content)))


def detect_code_language_from_blocks(text: str, default: str = "python") -> str:
    """Detect primary language from code blocks in text."""
    blocks = re.findall(r"```(\w+)", text)
    if not blocks:
        return default
    lang_map = {"py": "python", "js": "javascript", "ts": "typescript", "rs": "rust"}
    return lang_map.get(blocks[0], blocks[0])


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
