"""Web scraper — Crawl4AI + fallback Jina Reader."""
import json
import urllib.request
from datetime import datetime
from pathlib import Path

from lib.ingest import ingest_text

CRAWL4AI_URL = "http://127.0.0.1:11235/crawl"


def crawl(url: str) -> str:
    """Crawl a URL using Crawl4AI (Docker). Returns markdown content."""
    payload = json.dumps({"urls": [url]}).encode()
    req = urllib.request.Request(
        CRAWL4AI_URL,
        data=payload,
        headers={"Content-Type": "application/json"},
        method="POST",
    )
    try:
        resp = urllib.request.urlopen(req, timeout=30)
        data = json.loads(resp.read())
        results = data.get("results", [])
        if results:
            md = results[0].get("markdown", {})
            if isinstance(md, dict):
                return md.get("raw_markdown", "") or ""
            return str(md) if md else ""
    except Exception:
        pass
    return ""


def process_url(text_or_url: str) -> str:
    """Process a URL: crawl → ingest to vault."""
    urls = [u for u in text_or_url.split() if u.startswith("http")]
    if not urls:
        return "No se encontraron URLs"

    url = urls[0]
    content = crawl(url)
    if not content:
        return f"No se pudo extraer contenido de {url}"

    result = ingest_text(content, title=url, source_type="url", original_ref=url)
    slug = result.get("path", url)
    return f"Ingestado: {slug}"
