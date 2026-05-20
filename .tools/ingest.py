"""
KAOS Ingest Engine — Massive information ingestion pipeline.
Handles URLs, files, and batch ingestion with SHA-256 deduplication.
"""
import hashlib
import json
import re
import sys
from datetime import datetime
from pathlib import Path
from urllib.parse import urlparse

BASE = Path(__file__).resolve().parent.parent
RAW_DIR = BASE / ".memory" / "raw"
QUEUE_DIR = BASE / ".memory" / "ingest" / "queue"
MANIFEST_PATH = QUEUE_DIR / "manifest.json"
PYTHON = "py" if sys.platform == "win32" else "python3"


def _sha256(content: str) -> str:
    return hashlib.sha256(content.encode("utf-8")).hexdigest()


def _load_manifest() -> dict:
    if MANIFEST_PATH.exists():
        try:
            return json.loads(MANIFEST_PATH.read_text(encoding="utf-8"))
        except Exception:
            pass
    return {"version": 1, "items": [], "total_ingested": 0, "total_deduped": 0, "last_updated": ""}


def _save_manifest(manifest: dict) -> None:
    QUEUE_DIR.mkdir(parents=True, exist_ok=True)
    manifest["last_updated"] = datetime.now().isoformat()
    MANIFEST_PATH.write_text(json.dumps(manifest, indent=2, ensure_ascii=False), encoding="utf-8")


def _clean_slug(text: str) -> str:
    slug = text.lower().strip()[:60]
    slug = re.sub(r"[^\w\s-]", "", slug)
    slug = re.sub(r"[\s_]+", "-", slug)
    return slug.strip("-") or "untitled"


def _create_frontmatter(source_type: str, original_ref: str, sha: str, profile: str = "standard") -> str:
    return (f"---\ntype: ingest\n"
            f"source: {source_type}\n"
            f"original_ref: {original_ref}\n"
            f"sha256: {sha}\n"
            f"ingested_at: {datetime.now().isoformat()}\n"
            f"profile: {profile}\n"
            f"pipeline_id: P-{datetime.now().strftime('%Y%m%d-%H%M%S')}\n---\n\n")


def _is_duplicate(sha: str, manifest: dict) -> bool:
    for item in manifest["items"]:
        if item.get("sha256") == sha:
            return True
    return False


MIN_CONTENT_LENGTH = 50


def ingest_text(text: str, title: str, source_type: str = "text", original_ref: str = "", profile: str = "standard") -> dict:
    """Ingest raw text into raw/ with frontmatter and SHA-256 dedup."""
    body = text.strip()
    if len(body) < MIN_CONTENT_LENGTH:
        return {"status": "error", "message": f"Content too short ({len(body)} chars, min {MIN_CONTENT_LENGTH})"}

    sha = _sha256(text)
    manifest = _load_manifest()

    if _is_duplicate(sha, manifest):
        manifest["total_deduped"] += 1
        _save_manifest(manifest)
        return {"status": "deduped", "sha256": sha, "path": ""}

    slug = _clean_slug(title)
    path = RAW_DIR / f"{slug}.md"
    disambiguator = 1
    while path.exists():
        disambiguator += 1
        path = RAW_DIR / f"{slug}-{disambiguator}.md"

    frontmatter = _create_frontmatter(source_type, original_ref or title, sha, profile)
    content = frontmatter + text
    path.write_text(content, encoding="utf-8")

    manifest["items"].append({
        "sha256": sha,
        "path": str(path.relative_to(BASE)),
        "source_type": source_type,
        "original_ref": original_ref or title,
        "ingested_at": datetime.now().isoformat(),
        "profile": profile,
    })
    manifest["total_ingested"] += 1
    _save_manifest(manifest)

    return {"status": "ingested", "sha256": sha, "path": str(path.relative_to(BASE))}


def ingest_url(url: str, profile: str = "standard") -> dict:
    """Ingest a URL using Crawl4AI. Returns error if unavailable."""
    parsed = urlparse(url)
    path = parsed.path.replace("/", "-").strip("-")
    # Shorten well-known domains
    domain = parsed.netloc.replace("www.", "")
    if "wikipedia.org" in domain:
        domain = "wiki"
    elif "github.com" in domain:
        domain = "gh"
    title = f"{domain}-{path}"[:60] or "web-page"

    try:
        import requests
        resp = requests.post(f"http://127.0.0.1:11235/crawl", json={"urls": [url]}, timeout=30)
        resp.raise_for_status()
        data = resp.json()
        results = data.get("results", [])
        text = ""
        if results:
            md = results[0].get("markdown", {})
            if isinstance(md, dict):
                text = md.get("raw_markdown", "") or results[0].get("html", "")
            elif isinstance(md, str):
                text = md
        if not text.strip():
            return {"status": "error", "message": f"Crawl4AI returned empty content for {url}"}
    except ImportError:
        return {"status": "error", "message": "requests module not available"}
    except requests.exceptions.ConnectionError:
        return {"status": "error", "message": "Crawl4AI not available at localhost:11235. Start: docker compose up -d"}
    except Exception as e:
        return {"status": "error", "message": f"Crawl4AI error: {e}"}

    return ingest_text(text, title, "url", url, profile)


def ingest_file(file_path: str, profile: str = "standard") -> dict:
    """Ingest a local file (MD or text) into raw/."""
    path = Path(file_path)
    if not path.exists():
        return {"status": "error", "message": f"File not found: {file_path}"}

    text = path.read_text(encoding="utf-8", errors="replace")
    return ingest_text(text, path.stem, "file", str(path), profile)


def _wikipedia_api_search(topic: str, limit: int = 10) -> list[str]:
    """Fallback: search Wikipedia directly via their API."""
    import requests
    from urllib.parse import quote
    headers = {"User-Agent": "KAOS-Ingest/1.0 (kaos@local)"}
    params = {
        "action": "query",
        "list": "search",
        "srsearch": topic,
        "format": "json",
        "srlimit": min(limit, 50),
    }
    try:
        resp = requests.get("https://en.wikipedia.org/w/api.php", params=params, headers=headers, timeout=15)
        data = resp.json()
        pages = data.get("query", {}).get("search", [])
        urls = []
        for p in pages:
            title = p["title"]
            url_title = title.replace(" ", "_")
            urls.append(f"https://en.wikipedia.org/wiki/{quote(url_title)}")
        return urls[:limit]
    except Exception as e:
        print(f"Wikipedia API fallback error: {e}")
        return []


def ingest_wikipedia_topic(topic: str, max_articles: int = 10, profile: str = "deep") -> dict:
    """Ingest Wikipedia articles on a topic. Tries SearXNG first, then Wikipedia API fallback.
    Uses ThreadPoolExecutor for parallel ingestion."""
    import time
    from concurrent.futures import ThreadPoolExecutor, as_completed

    urls = []

    # Try SearXNG first
    try:
        import requests
        query = f"site:wikipedia.org {topic}"
        resp = requests.get(
            f"http://127.0.0.1:8888/search?format=json&q={query}",
            timeout=15
        )
        results = resp.json().get("results", [])
        urls = [r["url"] for r in results if "wikipedia.org" in r.get("url", "")][:max_articles]
    except Exception:
        pass

    # Fallback: Wikipedia API direct
    if not urls:
        print("SearXNG unavailable. Using Wikipedia API fallback...")
        urls = _wikipedia_api_search(topic, max_articles)

    if not urls:
        return {"status": "error", "message": "No Wikipedia articles found for topic"}

    # Parallel ingestion with rate limiting
    ingested = []
    with ThreadPoolExecutor(max_workers=4) as pool:
        futures = {pool.submit(ingest_url, url, profile): url for url in urls}
        for i, f in enumerate(as_completed(futures)):
            ingested.append(f.result())
            if i > 0 and i % 5 == 0 and "wikipedia" in str(futures[f]):
                time.sleep(1)  # Rate limit: pause every 5 requests

    return {"status": "batch", "total": len(ingested), "ingested": ingested}


def queue_status() -> str:
    """Show queue status."""
    manifest = _load_manifest()
    lines = [
        "## Ingest Queue Status",
        f"- Total ingested: {manifest['total_ingested']}",
        f"- Total deduplicated: {manifest['total_deduped']}",
        f"- Last updated: {manifest['last_updated']}",
        "",
    ]
    if manifest["items"]:
        lines.append("### Recent items (last 10):")
        for item in manifest["items"][-10:]:
            lines.append(f"- {item['source_type']}: {item['original_ref'][:50]} → {item['path']}")
    return "\n".join(lines)


def _ingest_single(source: dict, profile: str) -> dict:
    """Helper for parallel batch ingestion."""
    if source["type"] == "url":
        return ingest_url(source["ref"], profile)
    elif source["type"] == "file":
        return ingest_file(source["ref"], profile)
    elif source["type"] == "text":
        return ingest_text(source["ref"], source.get("title", "untitled"), "text", "", profile)
    return {"status": "error", "message": f"Unknown source type: {source.get('type')}"}


def batch_ingest(sources: list[dict], profile: str = "standard", parallel: bool = True) -> list[dict]:
    """Ingest multiple sources in parallel. Sources: [{'type':'url','ref':'https://...'}, ...]."""
    if not parallel or len(sources) < 2:
        results = []
        for source in sources:
            results.append(_ingest_single(source, profile))
        return results

    from concurrent.futures import ThreadPoolExecutor, as_completed
    results = []
    with ThreadPoolExecutor(max_workers=4) as pool:
        futures = {pool.submit(_ingest_single, s, profile): s for s in sources}
        for f in as_completed(futures):
            results.append(f.result())
    return results


if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser(description="KAOS Ingest Engine")
    parser.add_argument("action", choices=["url", "file", "text", "wikipedia", "batch", "status", "queue"])
    parser.add_argument("--ref", help="URL, file path, or text content")
    parser.add_argument("--title", default="", help="Title for text ingestion")
    parser.add_argument("--profile", default="standard", choices=["flash", "standard", "deep", "massive"])
    parser.add_argument("--max", type=int, default=10, help="Max articles for Wikipedia batch")
    args = parser.parse_args()

    if args.action == "status" or args.action == "queue":
        print(queue_status())
    elif args.action == "url" and args.ref:
        result = ingest_url(args.ref, args.profile)
        print(json.dumps(result, indent=2))
    elif args.action == "file" and args.ref:
        result = ingest_file(args.ref, args.profile)
        print(json.dumps(result, indent=2))
    elif args.action == "text" and args.ref:
        result = ingest_text(args.ref, args.title or "ingested-text", "text", "", args.profile)
        print(json.dumps(result, indent=2))
    elif args.action == "wikipedia" and args.ref:
        result = ingest_wikipedia_topic(args.ref, args.max, args.profile)
        print(json.dumps(result, indent=2))
    elif args.action == "batch":
        import sys
        batch_data = json.loads(sys.stdin.read())
        results = batch_ingest(batch_data, args.profile)
        print(json.dumps(results, indent=2))
    else:
        parser.print_help()
