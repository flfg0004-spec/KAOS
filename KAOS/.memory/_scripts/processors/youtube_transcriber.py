"""YouTube transcriber — subtitles + fallback whisper."""
import re
import json
import subprocess
import tempfile
from pathlib import Path

from lib.ingest import ingest_text


def get_youtube_id(url: str) -> str | None:
    patterns = [
        r"v=([a-zA-Z0-9_-]{11})",
        r"youtu\.be/([a-zA-Z0-9_-]{11})",
        r"youtube\.com/shorts/([a-zA-Z0-9_-]{11})",
        r"embed/([a-zA-Z0-9_-]{11})",
    ]
    for p in patterns:
        m = re.search(p, url)
        if m:
            return m.group(1)
    return None


def get_transcript(video_id: str) -> str | None:
    """Get YouTube subtitles via API."""
    try:
        from youtube_transcript_api import get_transcript as yt_get
        transcript = yt_get(video_id)
        return "\n".join([t["text"] for t in transcript])
    except Exception:
        return None


def transcribe_audio(audio_path: str) -> str | None:
    """Transcribe audio file using faster-whisper."""
    try:
        from faster_whisper import WhisperModel
        model = WhisperModel("large-v3-turbo", device="cpu", compute_type="int8")
        segments, _ = model.transcribe(audio_path)
        return "\n".join([s.text for s in segments])
    except Exception:
        return None


def process_youtube(url: str) -> str:
    """Process a YouTube URL: get transcript → ingest to vault."""
    video_id = get_youtube_id(url)
    if not video_id:
        return "URL de YouTube no valida"

    text = get_transcript(video_id)
    if text is None:
        try:
            with tempfile.TemporaryDirectory() as tmp:
                audio = str(Path(tmp) / "audio.mp3")
                subprocess.run(
                    ["yt-dlp", "-x", "--audio-format", "mp3", "-o", audio, url],
                    capture_output=True, timeout=120,
                )
                text = transcribe_audio(audio)
        except Exception:
            return "No se pudo transcribir el video"

    if not text:
        return "Transcripcion vacia"

    result = ingest_text(text, title=f"youtube-{video_id}", source_type="youtube", original_ref=url)
    return f"Transcrito: {result.get('path', video_id)}"
