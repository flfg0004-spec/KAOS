"""Image processor — Gemini Vision (description) + Tesseract (OCR)."""

import io
import tempfile
from pathlib import Path

from lib.ingest import ingest_text


def _describe_with_gemini(image_bytes: bytes) -> str:
    """Get image description using Gemini 2.5 Flash."""
    try:
        import google.genai as genai
        import os
        client = genai.Client(api_key=os.environ.get("GEMINI_API_KEY", ""))
        response = client.models.generate_content(
            model="gemini-2.5-flash-preview",
            contents=["Describe esta imagen en detalle", genai.types.Part.from_bytes(data=image_bytes, mime_type="image/jpeg")],
        )
        return response.text if response else ""
    except Exception:
        return ""


def _ocr_tesseract(image_bytes: bytes) -> str:
    """Extract text using Tesseract OCR."""
    try:
        import pytesseract
        from PIL import Image
        img = Image.open(io.BytesIO(image_bytes))
        text = pytesseract.image_to_string(img)
        return text.strip()
    except Exception:
        return ""


def process_image(msg) -> str:
    """Process an image message: download → describe → OCR → ingest."""
    photo = msg.photo[-1]
    file = msg.bot.get_file(photo.file_id)
    image_bytes = file.download_as_bytearray()

    description = _describe_with_gemini(bytes(image_bytes))
    ocr_text = _ocr_tesseract(bytes(image_bytes))

    caption = msg.caption or ""
    content = f"# Image Analysis\n\n## Caption\n{caption}\n\n## Description\n{description}\n\n## OCR Text\n{ocr_text}"
    result = ingest_text(content, title=f"image-{photo.file_id[:8]}", source_type="image", original_ref=f"telegram:{photo.file_id}")

    return f"Imagen procesada: {result.get('path', 'ok')}"
