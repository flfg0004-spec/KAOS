"""Content classifier — detects content type from Telegram messages."""
import re

YOUTUBE_PATTERNS = [
    r"youtube\.com/watch\?v=",
    r"youtu\.be/",
    r"youtube\.com/shorts/",
    r"m\.youtube\.com/watch",
    r"youtube\.com/embed/",
]

URL_PATTERN = re.compile(r"https?://[^\s]+")


def classify(text: str = "", mime_type: str = "", has_photo: bool = False,
             has_video: bool = False, has_document: bool = False,
             has_audio: bool = False) -> str:
    """Classify incoming content type.

    Returns: 'youtube', 'url', 'image', 'video', 'document', 'audio', 'text'
    """
    if has_photo:
        return "image"
    if has_video:
        return "video"
    if has_audio:
        return "audio"
    if has_document:
        if "pdf" in (mime_type or ""):
            return "pdf"
        if "word" in (mime_type or "") or "document" in (mime_type or ""):
            return "document"
        if "text" in (mime_type or ""):
            return "text_file"
        return "document"

    urls = URL_PATTERN.findall(text)
    for url in urls:
        for pattern in YOUTUBE_PATTERNS:
            if re.search(pattern, url):
                return "youtube"
    if urls:
        return "url"

    if text and len(text.strip()) > 10:
        return "text"
    return "unknown"


def extract_urls(text: str) -> list[str]:
    """Extract all URLs from text."""
    return URL_PATTERN.findall(text)
