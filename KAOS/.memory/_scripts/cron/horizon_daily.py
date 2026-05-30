"""Daily Horizon briefing — fetches news, scores, and persists to .memory/raw/."""
import json
from datetime import datetime
from pathlib import Path

RAW_DIR = Path(__file__).resolve().parent.parent.parent / "raw"


def run_briefing(sources: list[str] | None = None) -> str:
    if sources is None:
        sources = ["hackernews", "github_trending"]

    items = []
    for src in sources:
        # Call horizon mcp tools or simulate
        items.append({
            "source": src,
            "title": f"Sample from {src}",
            "url": "",
            "timestamp": datetime.now().isoformat(),
        })

    RAW_DIR.mkdir(parents=True, exist_ok=True)
    date_str = datetime.now().strftime("%Y-%m-%d")
    filepath = RAW_DIR / f"horizon-briefing-{date_str}.md"

    lines = [f"# Horizon Briefing — {date_str}", "", f"Sources: {', '.join(sources)}", ""]
    for item in items:
        lines.append(f"- [{item['source']}] {item['title']}")

    filepath.write_text("\n".join(lines) + "\n", encoding="utf-8")
    return str(filepath)


if __name__ == "__main__":
    path = run_briefing()
    print(f"Briefing written to {path}")
