"""Daily Horizon briefing — 7-step pipeline: Fetch → Dedup → Score → Filter → Enrich → Summarize → Deliver."""
import sys
from datetime import datetime
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
from mcp_horizon import _fetch_hackernews, _fetch_github_trending, _fetch_rss_general  # noqa: E402

RAW_DIR = Path(__file__).resolve().parent.parent.parent / "raw"

HANDLERS = {
    "hackernews": _fetch_hackernews,
    "github_trending": _fetch_github_trending,
    "rss_general": _fetch_rss_general,
}

SOURCE_WEIGHTS = {"hackernews": 1.0, "github_trending": 0.8, "rss_general": 0.6}


def run_briefing(sources: list[str] | None = None) -> str:
    if sources is None:
        sources = ["hackernews", "github_trending"]

    # Step 1: Fetch
    raw_items = []
    for src in sources:
        handler = HANDLERS.get(src)
        if handler:
            try:
                raw_items.extend(handler(limit=10))
            except Exception:
                continue

    # Step 2: Dedup (by URL hash)
    seen = set()
    deduped = []
    for item in raw_items:
        key = item.get("url", "") or item.get("title", "")
        if key and key not in seen:
            seen.add(key)
            deduped.append(item)

    # Step 3: Score (by source weight + recency)
    for item in deduped:
        sw = SOURCE_WEIGHTS.get(item.get("source", ""), 0.5)
        ts = item.get("timestamp", "")
        recency = 1.0 if ts else 0.5
        item["_score"] = round(sw * recency, 2)

    # Step 4: Filter (by min score)
    filtered = [i for i in deduped if i.get("_score", 0) >= 0.5]

    # Step 5: Enrich (top scored items)
    enriched = sorted(filtered, key=lambda x: x.get("_score", 0), reverse=True)[:5]

    # Step 6: Summarize (truncate titles)
    for item in enriched:
        title = item.get("title", "")
        item["title"] = title[:200] if title else "Untitled"

    # Step 7: Deliver
    RAW_DIR.mkdir(parents=True, exist_ok=True)
    date_str = datetime.now().strftime("%Y-%m-%d")
    filepath = RAW_DIR / f"horizon-briefing-{date_str}.md"

    lines = [f"# Horizon Briefing — {date_str}", "", f"Sources: {', '.join(sources)}", ""]
    if not enriched:
        lines.append("_No items met the quality threshold today._")
    else:
        for item in enriched:
            src = item.get("source", "?")
            title = item.get("title", "Untitled")
            url = item.get("url", "")
            score = item.get("_score", 0)
            url_part = f"({url})" if url else ""
            lines.append(f"- **[{src}]** {title} {url_part} (score: {score})")

    lines.append(f"\n---\n_Generated: {datetime.now().isoformat()}_")
    filepath.write_text("\n".join(lines) + "\n", encoding="utf-8")
    return str(filepath)


if __name__ == "__main__":
    path = run_briefing()
    print(f"Briefing written to {path}")
