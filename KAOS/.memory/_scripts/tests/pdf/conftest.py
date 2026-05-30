"""Shared fixtures and mocks for PDF report tests."""

from pathlib import Path
from unittest.mock import patch

import pytest


@pytest.fixture
def mock_playwright():
    """Mock Playwright to avoid requiring Chromium in tests.

    Replaces sync_playwright with a mock that writes a stub PDF file
    instead of launching a real browser.
    """

    class MockPage:
        def set_content(self, html, **kw):
            self.html = html

        def set_default_timeout(self, t):
            pass

        def pdf(self, **kw):
            Path(kw["path"]).write_bytes(b"stub-pdf")

    class MockBrowser:
        def new_page(self):
            return MockPage()

        def close(self):
            pass

    class MockChromium:
        def launch(self, **kw):
            return MockBrowser()

    class MockPlaywright:
        @property
        def chromium(self):
            return MockChromium()

        def __enter__(self):
            return self

        def __exit__(self, *a):
            pass

    with patch("playwright.sync_api.sync_playwright", return_value=MockPlaywright()):
        yield


@pytest.fixture
def mock_generate_chart():
    """Mock chart generation to return a placeholder base64 string."""
    with patch("lib.pdf_report_generator.generate_chart") as mock:
        mock.return_value = "c3R1Yi1wbGFjZWhvbGRlcg=="  # "stub-placeholder" in base64
        yield mock
