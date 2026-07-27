"""Multi-modal extraction: turn an uploaded image / scanned PDF / handwritten
letter into text the agent can reason over.

Uses a vision model when a key is set — Gemini (free tier) is preferred, then
Claude. Real OCR of images and PDFs, including handwriting. Without any key it
degrades gracefully — the file is still attached and the citizen provides
written details manually.

Voice notes are transcribed in the browser via the Web Speech API, so they need
no server-side model and arrive here as plain text.
"""
import base64
import os

from .providers import active_provider, anthropic_model, gemini_model

IMAGE_TYPES = {"image/png", "image/jpeg", "image/jpg", "image/webp", "image/gif"}
PDF_TYPE = "application/pdf"

_PROMPT = (
    "This is a citizen's public grievance submitted as a photo, scanned letter, or "
    "handwritten note. Transcribe ALL legible text. If it is handwritten, do your best "
    "to read it. Then, on a new line prefixed 'ISSUE:', state the core civic complaint "
    "in one plain sentence. Output only the transcription and the ISSUE line."
)


def _media_type(content_type: str, filename: str) -> str | None:
    content_type = (content_type or "").lower()
    if content_type == PDF_TYPE or filename.lower().endswith(".pdf"):
        return PDF_TYPE
    if content_type in IMAGE_TYPES:
        return "image/jpeg" if content_type == "image/jpg" else content_type
    if filename.lower().endswith((".png",)):
        return "image/png"
    if filename.lower().endswith((".jpg", ".jpeg")):
        return "image/jpeg"
    if filename.lower().endswith((".webp",)):
        return "image/webp"
    if filename.lower().endswith((".gif",)):
        return "image/gif"
    return None


def _gemini(data: bytes, media: str) -> str:
    from google import genai
    from google.genai import types

    client = genai.Client(api_key=os.getenv("GEMINI_API_KEY"))
    resp = client.models.generate_content(
        model=gemini_model(),
        contents=[types.Part.from_bytes(data=data, mime_type=media), _PROMPT],
    )
    return (resp.text or "").strip()


def _anthropic(data: bytes, media: str) -> str:
    import anthropic

    client = anthropic.Anthropic()
    b64 = base64.standard_b64encode(data).decode()
    if media == PDF_TYPE:
        block = {"type": "document", "source": {"type": "base64", "media_type": PDF_TYPE, "data": b64}}
    else:
        block = {"type": "image", "source": {"type": "base64", "media_type": media, "data": b64}}
    resp = client.messages.create(
        model=anthropic_model(),
        max_tokens=1024,
        messages=[{"role": "user", "content": [block, {"type": "text", "text": _PROMPT}]}],
    )
    return resp.content[0].text.strip()


def extract_text(data: bytes, content_type: str, filename: str = "") -> dict:
    provider = active_provider()
    if provider == "rule-based":
        return {
            "text": "",
            "mode": "unavailable",
            "note": "Automatic OCR needs an AI key (GEMINI_API_KEY or ANTHROPIC_API_KEY). "
                    "File attached — please add the details in the written box below.",
        }

    media = _media_type(content_type, filename)
    if media is None:
        return {"text": "", "mode": "unsupported",
                "note": f"Unsupported file type: {content_type or 'unknown'}. Use an image or PDF."}

    try:
        text = _gemini(data, media) if provider == "gemini" else _anthropic(data, media)
        return {"text": text, "mode": provider, "note": ""}
    except Exception as e:  # noqa: BLE001 — never crash the intake flow
        return {"text": "", "mode": "error",
                "note": f"Extraction failed ({e}). Please type the details manually."}
