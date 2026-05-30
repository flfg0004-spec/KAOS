import re
from datetime import datetime
from pathlib import Path

from lib.config import VAULT_ROOT


def get_description(content: str) -> str:
    m = re.search(r'description:\s*(.+)', content)
    if m:
        return m.group(1).strip().strip('"').strip("'")
    return "-"


def collect_md(directory: Path) -> list[Path]:
    return sorted(directory.glob("*.md"))


def regenerate() -> str:
    vault = VAULT_ROOT
    now = datetime.now().strftime("%Y-%m-%d %H:%M")
    lines = [
        "# KAOS Memory Vault - Index",
        "",
        f"*Auto-generated: {now}*",
        "",
    ]

    sections = [
        ("Agentes", vault / "wiki" / "entities", "entities/"),
        ("Conceptos", vault / "wiki" / "concepts", "concepts/"),
        ("Fuentes", vault / "wiki" / "sources", "sources/"),
    ]

    for title, directory, prefix in sections:
        files = collect_md(directory)
        if files:
            lines.append(f"## {title}")
            lines.append("")
            for f in files:
                content = f.read_text(encoding="utf-8", errors="replace")
                desc = get_description(content)
                lines.append(f"- [{f.stem}]({prefix}{f.name}) - {desc}")
            lines.append("")

    raw_files = collect_md(vault / "raw")
    if raw_files:
        lines.append("## Investigaciones (raw/)")
        lines.append("")
        for f in raw_files:
            if f.parent.name == "archive":
                continue
            mtime = datetime.fromtimestamp(f.stat().st_mtime)
            lines.append(f"- [{f.stem}](../raw/{f.name}) - {mtime.strftime('%Y-%m-%d')}")
        lines.append("")

    adr_files = sorted((vault / "schema").glob("adr-*.md"))
    if adr_files:
        lines.append("## ADRs (schema/)")
        lines.append("")
        for f in adr_files:
            content = f.read_text(encoding="utf-8", errors="replace")
            title = f.stem
            m = re.search(r'^# ADR-\d+:\s+(.+)$', content, re.MULTILINE)
            if m:
                title = m.group(1).strip()
            lines.append(f"- [{f.stem}](../schema/{f.name}) - {title}")
        lines.append("")

    schema_files = sorted(f for f in (vault / "schema").glob("*.md") if not f.name.startswith("adr-"))
    if schema_files:
        lines.append("## Schema")
        lines.append("")
        for f in schema_files:
            lines.append(f"- [{f.stem}](../schema/{f.name})")
        lines.append("")

    lines.append("---")
    lines.append(f"*Ultima actualizacion: {now}*")
    lines.append("")

    index_path = vault / "wiki" / "index.md"
    index_path.write_text("\n".join(lines), encoding="utf-8")

    total = (
        len(collect_md(vault / "wiki" / "entities"))
        + len(collect_md(vault / "wiki" / "concepts"))
        + len(collect_md(vault / "wiki" / "sources"))
        + len([f for f in collect_md(vault / "raw") if f.parent.name != "archive"])
        + len(adr_files)
        + len(schema_files)
    )
    return f"index.md regenerated with {total} entries"
