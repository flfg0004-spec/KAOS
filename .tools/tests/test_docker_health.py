"""
Tests: Docker service health checks.
Requires Docker containers to be running.
"""
import requests

CRAWL4AI_URL = "http://127.0.0.1:11235"
SEARXNG_URL = "http://127.0.0.1:8888"


def test_crawl4ai_health():
    """Verifica que Crawl4AI responde en /health."""
    try:
        r = requests.get(f"{CRAWL4AI_URL}/health", timeout=10)
        assert r.status_code == 200
        data = r.json()
        assert data.get("status") == "ok"
    except requests.exceptions.ConnectionError:
        assert False, "Crawl4AI is not reachable. Start: docker compose up -d"


def test_crawl4ai_crawl():
    """Verifica que Crawl4AI puede crawlear URLs."""
    try:
        r = requests.post(f"{CRAWL4AI_URL}/crawl",
                          json={"urls": ["https://example.com"]}, timeout=30)
        assert r.status_code == 200
        data = r.json()
        assert data.get("success") is True
        assert len(data.get("results", [])) > 0
    except requests.exceptions.ConnectionError:
        assert False, "Crawl4AI is not reachable"


def test_searxng_connect():
    """Verifica que SearXNG responde en /search."""
    try:
        r = requests.get(f"{SEARXNG_URL}/search?format=json&q=test", timeout=10)
        assert r.status_code == 200
    except requests.exceptions.ConnectionError:
        assert False, "SearXNG is not reachable. Start: docker compose up -d"
