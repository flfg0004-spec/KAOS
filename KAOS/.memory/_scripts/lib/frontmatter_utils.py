"""Shared frontmatter parsing utilities for knowledge modules."""

import yaml


def extract_frontmatter(content: str) -> dict:
    """Extract YAML frontmatter as a dict using yaml.safe_load with manual fallback.

    Uses yaml.safe_load for robust YAML parsing (lists, booleans, multiline).
    Falls back to simple key:value parser if yaml.safe_load fails.
    """
    if not content.startswith("---"):
        return {}
    end = content.find("---", 3)
    if end == -1:
        return {}
    fm_text = content[3:end].strip()
    # Try yaml.safe_load first
    try:
        parsed = yaml.safe_load(fm_text)
        if isinstance(parsed, dict):
            return parsed
    except yaml.YAMLError:
        pass
    # Fallback: simple key:value parser
    result = {}
    for line in fm_text.split("\n"):
        if ":" in line:
            key, _, val = line.partition(":")
            result[key.strip()] = val.strip().strip('"').strip("'")
    return result


def has_frontmatter(content: str) -> bool:
    return content.startswith("---") and content.find("---", 3) != -1


def has_complete_frontmatter(content: str) -> bool:
    fm = extract_frontmatter(content)
    return all(k in fm for k in ("title", "tags", "created"))
