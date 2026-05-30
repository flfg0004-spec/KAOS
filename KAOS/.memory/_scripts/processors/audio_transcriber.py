"""Audio transcriber — faster-whisper local."""

import io
import tempfile
from pathlib import Path

from lib.ingest import ingest_text


def transcribe(audio_bytes: bytes) -> str | None:
    """Transcribe audio bytes using faster-whisper."""
    try:
        from faster_whisper import WhisperModel
        model = WhisperModel("large-v3-turbo", device="cpu", compute_type="int8")

        with tempfile.NamedTemporaryFile(suffix=".wav", delete=False) as tmp:
            tmp.write(audio_bytes)
            tmp_path = tmp.name

        segments, _ = model.transcribe(tmp_path)
        text = "\n".join([s.text for s in segments])
        Path(tmp_path).unlink(missing_ok=True)
        return text if text.strip() else None
    except Exception:
        return None


def process_audio(msg) -> str:
    """Process an audio message: download → transcribe → ingest."""
    audio = msg.audio or msg.voice
    if not audio:
        return "No se encontro audio"

    if audio.file_size > 20 * 1024 * 1024:
        return "Audio demasiado grande (max 20MB)"

    file = msg.bot.get_file(audio.file_id)
    audio_bytes = bytes(file.download_as_bytearray())

    text = transcribe(audio_bytes)
    if not text:
        return "No se pudo transcribir el audio"

    result = ingest_text(text, title=f"audio-{audio.file_id[:8]}", source_type="audio", original_ref=f"telegram:{audio.file_id}")
    return f"Audio transcrito: {result.get('path', 'ok')}"
