"""Document processor — PDF, DOCX, text files."""

import io
import tempfile
from pathlib import Path

from lib.ingest import ingest_text


def _extract_pdf(file_bytes: bytes) -> str:
    """Extract text from PDF using PyMuPDF4LLM."""
    try:
        import fitz
        doc = fitz.open(stream=file_bytes, filetype="pdf")
        text = "\n".join([page.get_text() for page in doc])
        return text.strip()
    except Exception:
        return ""


def _extract_docx(file_bytes: bytes) -> str:
    """Extract text from DOCX."""
    try:
        from docx import Document
        doc = Document(io.BytesIO(file_bytes))
        return "\n".join([p.text for p in doc.paragraphs])
    except Exception:
        return ""


def _extract_text(file_bytes: bytes) -> str:
    return file_bytes.decode("utf-8", errors="replace")


def process_document(msg) -> str:
    """Process a document: download → extract → ingest."""
    doc = msg.document
    if doc.file_size > 20 * 1024 * 1024:
        return "Archivo demasiado grande (max 20MB)"

    file = msg.bot.get_file(doc.file_id)
    file_bytes = bytes(file.download_as_bytearray())

    mime = doc.mime_type or ""
    if "pdf" in mime:
        text = _extract_pdf(file_bytes)
    elif "word" in mime or "document" in mime:
        text = _extract_docx(file_bytes)
    elif "text" in mime:
        text = _extract_text(file_bytes)
    else:
        text = _extract_pdf(file_bytes) or _extract_text(file_bytes)

    if not text:
        return "No se pudo extraer texto del documento"

    result = ingest_text(text, title=doc.file_name or "document", source_type=mime, original_ref=f"telegram:{doc.file_id}")
    return f"Documento procesado: {result.get('path', 'ok')}"
