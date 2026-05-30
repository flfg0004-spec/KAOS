#!/usr/bin/env python3
"""Horizon MCP Server — news discovery via scraping (no external APIs required)."""
import json
import sys
import urllib.request
import urllib.error
import http.client
import socket
import xml.etree.ElementTree as ET
from datetime import datetime
from html.parser import HTMLParser

TOOLS = [
    {
        "name": "horizon_fetch_items",
        "description": "Fetch recent items from a news/trending source",
        "inputSchema": {
            "type": "object",
            "properties": {
                "source": {
                    "type": "string",
                    "description": "Source name: 'hackernews', 'github_trending', or 'rss_general'",
                    "enum": ["hackernews", "github_trending", "rss_general"],
                },
                "limit": {
                    "type": "number",
                    "description": "Maximum number of items to fetch (default: 5, max: 20)",
                    "default": 5,
                },
            },
            "required": ["source"],
        },
    },
    {
        "name": "horizon_summarize",
        "description": "Generate a short summary of items",
        "inputSchema": {
            "type": "object",
            "properties": {
                "items": {
                    "type": "array",
                    "description": "List of items with 'title', 'source', 'url' fields",
                    "items": {
                        "type": "object",
                        "properties": {
                            "title": {"type": "string"},
                            "source": {"type": "string"},
                            "url": {"type": "string"},
                        },
                    },
                },
            },
            "required": ["items"],
        },
    },
]


def _fetch_hackernews(limit: int) -> list[dict]:
    """Fetch top stories from Hacker News Firebase API."""
    try:
        resp = urllib.request.urlopen(
            "https://hacker-news.firebaseio.com/v0/topstories.json",
            timeout=10,
        )
        story_ids = json.loads(resp.read().decode())[:limit]
        items = []
        for sid in story_ids:
            try:
                item_resp = urllib.request.urlopen(
                    f"https://hacker-news.firebaseio.com/v0/item/{sid}.json",
                    timeout=10,
                )
                data = json.loads(item_resp.read().decode())
                items.append({
                    "title": data.get("title", "Untitled"),
                    "url": data.get("url", f"https://news.ycombinator.com/item?id={sid}"),
                    "source": "hackernews",
                    "score": data.get("score", 0),
                    "by": data.get("by", "unknown"),
                    "timestamp": datetime.fromtimestamp(data.get("time", 0)).isoformat() if data.get("time") else "",
                })
            except (json.JSONDecodeError, urllib.error.URLError, KeyError):
                continue
        return items
    except (urllib.error.URLError, json.JSONDecodeError) as e:
        return [{"title": f"Error fetching HN: {e}", "url": "", "source": "hackernews"}]


def _fetch_github_trending(limit: int) -> list[dict]:
    """Scrape GitHub trending repositories."""
    try:
        resp = urllib.request.urlopen(
            "https://github.com/trending",
            timeout=10,
        )
        html = resp.read().decode("utf-8", errors="replace")

        class TrendingParser(HTMLParser):
            def __init__(self):
                super().__init__()
                self.in_h2 = False
                self.in_link = False
                self.repos = []
                self.current = {}
                self._collected = 0
                self._limit = limit

            def handle_starttag(self, tag, attrs):
                if self._collected >= self._limit:
                    return
                attrs_dict = dict(attrs)
                if tag == "h2":
                    classes = attrs_dict.get("class", "")
                    if "h3" in classes.split():
                        self.in_h2 = True
                if tag == "a" and self.in_h2:
                    self.in_link = True
                    self._href = attrs_dict.get("href", "")
                if tag == "article":
                    self.current = {}

            def handle_data(self, data):
                if self._collected >= self._limit:
                    return
                if self.in_link and self.in_h2:
                    name = data.strip()
                    if name:
                        self.current["title"] = name

            def handle_endtag(self, tag):
                if tag == "h2":
                    self.in_h2 = False
                if tag == "a":
                    if self.in_link and self.current.get("title"):
                        self.current["source"] = "github_trending"
                        href = getattr(self, "_href", "")
                        self.current["url"] = f"https://github.com{href}" if href else "https://github.com/trending"
                        self.current["timestamp"] = datetime.now().isoformat()
                        exists = any(r.get("title") == self.current["title"] for r in self.repos)
                        if not exists:
                            self.repos.append(dict(self.current))
                            self._collected += 1
                        self.current = {}
                        self._href = ""
                    self.in_link = False
                if tag == "article":
                    self.in_h2 = False
                    self.in_link = False

        parser = TrendingParser()
        parser.feed(html)
        return parser.repos[:limit]

    except (urllib.error.URLError, ConnectionResetError, socket.timeout, http.client.RemoteDisconnected) as e:
        return [
            {"title": f"GitHub Trending unavailable", "url": "https://github.com/trending", "source": "github_trending", "score": 0},
        ]


def _fetch_rss_general(limit: int) -> list[dict]:
    """Parse a general RSS feed (fallback to a public tech feed)."""
    urls_to_try = [
        "https://hnrss.org/frontpage?count=5",
        "https://rss.nytimes.com/services/xml/rss/nyt/Technology.xml",
    ]
    for feed_url in urls_to_try:
        try:
            resp = urllib.request.urlopen(feed_url, timeout=10)
            raw = resp.read()
            root = ET.fromstring(raw)
            items = []
            for entry in root.iter("item"):
                if len(items) >= limit:
                    break
                title_el = entry.find("title")
                link_el = entry.find("link")
                items.append({
                    "title": title_el.text if title_el is not None else "Untitled",
                    "url": link_el.text if link_el is not None else "",
                    "source": "rss_general",
                    "timestamp": datetime.now().isoformat(),
                })
            if items:
                return items
        except (urllib.error.URLError, ET.ParseError, ConnectionError):
            continue
    return [{"title": "No RSS items available", "url": "", "source": "rss_general"}]


HANDLERS = {
    "hackernews": _fetch_hackernews,
    "github_trending": _fetch_github_trending,
    "rss_general": _fetch_rss_general,
}


def _respond(id_val, result=None, error=None):
    msg = {"jsonrpc": "2.0", "id": id_val}
    if error:
        msg["error"] = error
    else:
        msg["result"] = result
    sys.stdout.write(json.dumps(msg) + "\n")
    sys.stdout.flush()


def _run_mcp():
    for line in sys.stdin:
        line = line.strip()
        if not line:
            continue
        try:
            msg = json.loads(line)
        except json.JSONDecodeError:
            continue
        method = msg.get("method")
        req_id = msg.get("id")
        params = msg.get("params") or {}
        if method == "initialize":
            _respond(req_id, {
                "protocolVersion": "2026-03-26",
                "capabilities": {"tools": {}},
                "serverInfo": {"name": "horizon", "version": "1.0.0"},
            })
        elif method == "notifications/initialized":
            pass
        elif method == "tools/list":
            _respond(req_id, {"tools": TOOLS})
        elif method == "tools/call":
            tool_name = params.get("name", "")
            args = params.get("arguments", {})
            try:
                if tool_name == "horizon_fetch_items":
                    source = args.get("source", "")
                    limit = min(int(args.get("limit", 5)), 20)
                    handler = HANDLERS.get(source)
                    if not handler:
                        _respond(req_id, error={"code": -32602, "message": f"Unknown source: {source}. Valid: {list(HANDLERS.keys())}"})
                        continue
                    items = handler(limit)
                    text = json.dumps(items, indent=2, ensure_ascii=False)
                    _respond(req_id, {"content": [{"type": "text", "text": text}]})
                elif tool_name == "horizon_summarize":
                    raw_items = args.get("items", [])
                    if not raw_items:
                        _respond(req_id, error={"code": -32602, "message": "items list is required"})
                        continue
                    summary_lines = [f"## Horizon Summary ({len(raw_items)} items)", ""]
                    for i, item in enumerate(raw_items, 1):
                        title = item.get("title", "Untitled")
                        src = item.get("source", "unknown")
                        url = item.get("url", "")
                        summary_lines.append(f"{i}. **[{src}]** {title}")
                        if url:
                            summary_lines.append(f"   {url}")
                    text = "\n".join(summary_lines)
                    _respond(req_id, {"content": [{"type": "text", "text": text}]})
                else:
                    _respond(req_id, error={"code": -32601, "message": f"Tool not found: {tool_name}"})
            except Exception as e:
                _respond(req_id, error={"code": -32603, "message": str(e)})
        elif method == "prompts/list":
            _respond(req_id, {"prompts": []})
        else:
            _respond(req_id, error={"code": -32601, "message": f"Method not found: {method}"})


if __name__ == "__main__":
    _run_mcp()
