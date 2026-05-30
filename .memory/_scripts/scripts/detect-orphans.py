"""Orphan page detection script.

Scans the KAOS vault and .memory/wiki for markdown files without backlinks.
Generates a report in .memory/schema/orphan-report.md.

Usage:
    py -3 scripts/detect-orphans.py
"""

import sys
from datetime import datetime
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from lib.config import IGNORED_PAGES
from lib.wikilinks import parse

SCHEMA_DIR = Path(__file__).resolve().parent.parent.parent / "schema"


def main():
    data = parse()
    orphans = data.get("orphan_list", [])

    ignored = set(IGNORED_PAGES)
    filtered = [o for o in orphans if o["name"].lower() not in ignored]

    report_path = SCHEMA_DIR / "orphan-report.md"
    SCHEMA_DIR.mkdir(parents=True, exist_ok=True)

    lines = [
        "# Orphan Pages Report",
        f"*Generated: {datetime.now().strftime('%Y-%m-%d %H:%M')}*",
        "",
        f"**Total orphans found:** {len(filtered)}",
        "",
    ]

    if filtered:
        lines.append("## Orphan Pages\n")
        for o in sorted(filtered, key=lambda x: x["name"]):
            lines.append(f"- {o['name']} -- {o['path']}")
        lines.append("")

    lines.append(f"**Pages analyzed:** {data.get('pages', 0)}")
    lines.append(f"**Valid wikilinks:** {data.get('validLinks', 0)}")
    lines.append(f"**Broken wikilinks:** {data.get('brokenLinks', 0)}")
    lines.append(f"**Orphans (total):** {data.get('orphans', 0)}")
    lines.append(f"**Orphans (filtered):** {len(filtered)}")

    report_path.write_text("\n".join(lines), encoding="utf-8")
    print(f"Orphan report written to {report_path}")
    print(f"  Pages: {data.get('pages', 0)}")
    print(f"  Valid links: {data.get('validLinks', 0)}")
    print(f"  Broken links: {data.get('brokenLinks', 0)}")
    print(f"  Orphans (filtered): {len(filtered)}")


if __name__ == "__main__":
    main()
