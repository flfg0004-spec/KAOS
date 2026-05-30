"""Ocho métricas de scoring para notas del vault.

Cada función recibe (path: Path, content: str, frontmatter: dict) -> float.
"""

import re
from pathlib import Path

# ---------------------------------------------------------------------------
# 1. has_frontmatter
# ---------------------------------------------------------------------------

REQUIRED_FRONTMATTER_KEYS = {"title", "type", "tags", "created"}
OPTIONAL_KEYS = {"modified", "audience", "aliases", "confidence", "source", "related"}


def has_frontmatter(_path: Path, _content: str, frontmatter: dict) -> float:
    """1.0 si frontmatter completo, 0.5 si parcial, 0.0 si vacío."""
    if not frontmatter:
        return 0.0
    # Comprobar si todos los keys requeridos están presentes
    required_present = sum(1 for k in REQUIRED_FRONTMATTER_KEYS if k in frontmatter)
    optional_present = sum(1 for k in OPTIONAL_KEYS if k in frontmatter)
    # Ideal: 4 requeridos + al menos 2 opcionales = completo
    if required_present >= 3 and optional_present >= 1:
        return 1.0
    if required_present >= 1 or optional_present >= 1:
        return 0.5
    return 0.0


# ---------------------------------------------------------------------------
# 2. has_tags
# ---------------------------------------------------------------------------

TAG_PATTERN = re.compile(r"#[\w\-áéíóúüñ]+")


def has_tags(_path: Path, content: str, frontmatter: dict) -> float:
    """Ratio de tags por cada 100 palabras (cap en 1.0)."""
    inline_tags = TAG_PATTERN.findall(content)
    fm_tags = frontmatter.get("tags", [])
    if isinstance(fm_tags, str):
        fm_tags = [fm_tags]
    total_tags = len(inline_tags) + len(fm_tags)
    word_count = len(content.split())
    if word_count < 1:
        return 0.0
    ratio = total_tags / (word_count / 100.0)
    return min(ratio, 1.0)


# ---------------------------------------------------------------------------
# 3. has_wikilinks
# ---------------------------------------------------------------------------

WIKILINK_PATTERN = re.compile(r"\[\[([^\]|]+)(?:\|[^\]]+)?\]\]")


def has_wikilinks(_path: Path, content: str, _frontmatter: dict) -> float:
    """Ratio de wikilinks por cada 100 palabras (cap en 1.0)."""
    wikilinks = WIKILINK_PATTERN.findall(content)
    total_links = len(wikilinks)
    word_count = len(content.split())
    if word_count < 1:
        return 0.0
    ratio = total_links / (word_count / 100.0)
    return min(ratio, 1.0)


# ---------------------------------------------------------------------------
# 4. min_length
# ---------------------------------------------------------------------------

def min_length(_path: Path, content: str, _frontmatter: dict) -> float:
    """1.0 si >= 300 caracteres, 0.0 si < 50, lineal entre."""
    length = len(content)
    if length >= 300:
        return 1.0
    if length < 50:
        return 0.0
    return (length - 50) / 250.0


# ---------------------------------------------------------------------------
# 5. audience_defined
# ---------------------------------------------------------------------------

def audience_defined(_path: Path, _content: str, frontmatter: dict) -> float:
    """1.0 si audience existe y no está vacío, 0.0 si no."""
    audience = frontmatter.get("audience")
    if audience and str(audience).strip():
        return 1.0
    return 0.0


# ---------------------------------------------------------------------------
# 6. has_backlinks
# ---------------------------------------------------------------------------

def has_backlinks(path: Path, _content: str, _frontmatter: dict) -> float:
    """1.0 si >= 3 backlinks en wiki/, escala lineal hasta 3."""
    # Obtener el nombre base del archivo (sin extensión)
    note_name = path.stem
    wiki_dir = _find_wiki_dir(path)
    if not wiki_dir:
        return 0.0

    count = 0
    for fpath in wiki_dir.rglob("*.md"):
        if fpath.resolve() == path.resolve():
            continue
        try:
            text = fpath.read_text(encoding="utf-8")
            # Buscar [[nombre]] o [[nombre|alias]]
            pattern = re.compile(re.escape(note_name) + r"(?:\||\])")
            count += len(pattern.findall(text))
        except (OSError, UnicodeDecodeError):
            continue

    return min(count / 3.0, 1.0)


def _find_wiki_dir(path: Path) -> Path | None:
    """Busca el directorio wiki/ ascendiendo desde path."""
    for parent in [path] + list(path.parents):
        candidate = parent.parent / "wiki"
        if candidate.is_dir():
            return candidate
        candidate = parent / "wiki"
        if candidate.is_dir():
            return candidate
    return None


# ---------------------------------------------------------------------------
# 7. has_aliases
# ---------------------------------------------------------------------------

def has_aliases(_path: Path, _content: str, frontmatter: dict) -> float:
    """1.0 si aliases existe y no está vacío, 0.0 si no."""
    aliases = frontmatter.get("aliases")
    if aliases and (isinstance(aliases, list) and len(aliases) > 0):
        return 1.0
    if aliases and isinstance(aliases, str) and aliases.strip():
        return 1.0
    return 0.0


# ---------------------------------------------------------------------------
# 8. is_linked
# ---------------------------------------------------------------------------

def is_linked(_path: Path, content: str, _frontmatter: dict) -> float:
    """1.0 si tiene enlaces salientes (wikilinks o markdown links), 0.0 si no."""
    # Wikilinks
    wikilinks = WIKILINK_PATTERN.findall(content)
    # Markdown links: [text](url)
    md_links = re.findall(r"\[([^\]]+)\]\(([^)]+)\)", content)
    if len(wikilinks) > 0 or len(md_links) > 0:
        return 1.0
    return 0.0


# ---------------------------------------------------------------------------
# Registry
# ---------------------------------------------------------------------------

ALL_METRICS = {
    "has_frontmatter": has_frontmatter,
    "has_tags": has_tags,
    "has_wikilinks": has_wikilinks,
    "min_length": min_length,
    "audience_defined": audience_defined,
    "has_backlinks": has_backlinks,
    "has_aliases": has_aliases,
    "is_linked": is_linked,
}
