#!/usr/bin/env python3
"""Validate all KAOS skills against agentskills.io standard spec.

The agentskills.io standard (Addy Osmani, 27K⭐) defines that a SKILL.md
must contain:
  - # Skill Name
  - ## Description
  - ## Triggers
  - ## Steps (numbered)
  - ## Requirements
  - ## Examples
  - ## Metadata (name, version, author, tags)

Usage:
    py -3 _scripts/validate_skills.py          # validate project skills
    py -3 _scripts/validate_skills.py --all    # validate project + user skills
"""
from __future__ import annotations

import os
import re
import sys
from pathlib import Path

# ── Configuration ──────────────────────────────────────────────────────────

SKILLS_DIR = Path(__file__).resolve().parent.parent / ".opencode" / "skills"
USER_SKILLS_DIR = Path.home() / ".agents" / "skills"

REQUIRED_SECTIONS = [
    "Description",
    "Triggers",
    "Steps",
    "Requirements",
    "Examples",
    "Metadata",
]

REQUIRED_METADATA = ["name", "version", "author", "tags"]

# Sections that should never appear (content must be non-trivial)
MIN_SECTION_LENGTH = {
    "Description": 20,
    "Triggers": 50,
    "Steps": 30,
    "Requirements": 20,
    "Examples": 30,
}

# ── Helpers ────────────────────────────────────────────────────────────────

def extract_section(content: str, section_name: str) -> str | None:
    """Extract the content of a ## section from markdown."""
    pattern = rf"^## {re.escape(section_name)}\s*$"
    lines = content.split("\n")
    in_section = False
    section_lines: list[str] = []
    for line in lines:
        if re.match(pattern, line.strip()):
            in_section = True
            continue
        if in_section:
            if line.startswith("## "):
                break
            section_lines.append(line)
    text = "\n".join(section_lines).strip()
    return text if text else None


def validate_skill(skill_path: Path) -> list[str]:
    """Validate a single SKILL.md against spec. Returns list of error strings."""
    errors: list[str] = []
    content = skill_path.read_text(encoding="utf-8")

    # ── Check required sections ──
    for section in REQUIRED_SECTIONS:
        heading = f"## {section}"
        if heading not in content:
            errors.append(f"Missing required section: {heading}")
        else:
            # Check for minimum content length
            section_text = extract_section(content, section)
            if section_text is None:
                errors.append(f"Section '{section}' is empty")
            elif section in MIN_SECTION_LENGTH and len(section_text) < MIN_SECTION_LENGTH[section]:
                errors.append(
                    f"Section '{section}' is too short "
                    f"({len(section_text)} chars, min {MIN_SECTION_LENGTH[section]})"
                )

    # ── Validate Metadata ──
    if "## Metadata" in content:
        meta_text = extract_section(content, "Metadata") or ""
        for field in REQUIRED_METADATA:
            marker = f"- {field}:"
            if marker not in meta_text:
                errors.append(f"Missing metadata field: '{field}'")
            else:
                # Extract value after marker
                for line in meta_text.split("\n"):
                    if line.strip().startswith(marker):
                        value = line.split(marker, 1)[1].strip()
                        if not value:
                            errors.append(f"Metadata field '{field}' has empty value")
                        break
    else:
        errors.append("Missing required section: ## Metadata (this was caught above but double-checked)")

    # ── Check for numbered steps in Steps section ──
    if "## Steps" in content:
        steps_text = extract_section(content, "Steps") or ""
        has_numbered = bool(re.search(r"^\d+\.\s", steps_text, re.MULTILINE))
        if not has_numbered:
            errors.append("Section 'Steps' does not contain numbered steps (1., 2., etc.)")

    # ── Check for YAML frontmatter (optional, not required by spec) ──
    if not content.startswith("---"):
        pass  # Not required by agentskills.io spec, but recommended for agent tool routing

    # ── Check for top-level heading ──
    if not re.search(r"^#\s+\S", content, re.MULTILINE):
        errors.append("Missing top-level heading (# Skill Name)")

    return errors


def validate_skills_in_dir(skills_dir: Path, label: str) -> bool:
    """Validate all skills in a directory. Returns True if errors found."""
    if not skills_dir.exists():
        print(f"ℹ️  {label}: directory not found at {skills_dir}")
        return False

    errors_found = False
    for skill_dir in sorted(skills_dir.iterdir()):
        if not skill_dir.is_dir() or skill_dir.name.startswith("_"):
            continue
        skill_file = skill_dir / "SKILL.md"
        if not skill_file.exists():
            print(f"❌ [{label}] {skill_dir.name}: SKILL.md not found")
            errors_found = True
            continue

        errors = validate_skill(skill_file)
        if errors:
            print(f"❌ [{label}] {skill_dir.name}:")
            for e in errors:
                print(f"   • {e}")
            errors_found = True
        else:
            print(f"✅ [{label}] {skill_dir.name}: valid")

    return errors_found


# ── Main ───────────────────────────────────────────────────────────────────

def main() -> int:
    include_user = "--all" in sys.argv
    errors_found = False

    # Validate project-level skills (.opencode/skills/)
    proj_label = "project"
    if validate_skills_in_dir(SKILLS_DIR, proj_label):
        errors_found = True

    print()  # separator

    # Validate user-level skills (~/.agents/skills/) if --all
    if include_user:
        user_label = "user"
        if validate_skills_in_dir(USER_SKILLS_DIR, user_label):
            errors_found = True
    else:
        print("ℹ️  Run with --all to also validate user-level skills (~/.agents/skills/)")

    print()
    if errors_found:
        print("❌ Validation failed — some skills need fixes")
    else:
        print("✅ All skills valid against agentskills.io spec")

    return 1 if errors_found else 0


if __name__ == "__main__":
    sys.exit(main())
