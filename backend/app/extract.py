"""Multi-modal extraction: turn an uploaded image / scanned PDF / handwritten
letter into text the agent can reason over.

Uses Claude vision when ANTHROPIC_API_KEY is set (real OCR of images and PDFs,
including handwriting). Without a key it degrades gracefully — the file is still
attached and the citizen provides written details manually.

Voice notes are transcribed in the browser via the Web Speech API, so they need
no server-side model and arrive here as plain text.
"""
import base64
import os

IMAGE_TYPES = {"image/png", "image/jpeg", "image/jpg", "image/webp", "image/gif"}
PDF_TYPE = "application/pdf"

_PROMPT = (
    "This is a citizen's public grievance submitted as a photo, scanned letter, or "
    "handwritten note. Transcribe ALL legible text. If it is handwritten, do your best "
    "to read it. Then, on a new line prefixed 'ISSUE:', state the core civic complaint "
    "in one plain sentence. Output only the transcription and the ISSUE line."
)


def extract_text(data: bytes, content_type: str, filename: str = "") -> dict:
    content_type = (content_type or "").lower()

    if not os.getenv("ANTHROPIC_API_KEY"):
        return {
            "text": "",
            "mode": "unavailable",
            "note": "Automatic OCR needs the LLM key (ANTHROPIC_API_KEY). "
                    "File attached — please add the details in the written box below.",
        }

    try:
        import anthropic

        client = anthropic.Anthropic()
        model = os.getenv("LLM_MODEL", "claude-haiku-4-5-20251001")
        b64 = base64.standard_b64encode(data).decode()

        if content_type == PDF_TYPE or filename.lower().endswith(".pdf"):
            source = {"type": "base64", "media_type": PDF_TYPE, "data": b64}
            block = {"type": "document", "source": source}
        elif content_type in IMAGE_TYPES or filename.lower().endswith((".png", ".jpg", ".jpeg", ".webp", ".gif")):
            media = "image/jpeg" if content_type in ("image/jpg", "") else content_type
            block = {"type": "image", "source": {"type": "base64", "media_type": media, "data": b64}}
        else:
            return {"text": "", "mode": "unsupported",
                    "note": f"Unsupported file type: {content_type or 'unknown'}. Use an image or PDF."}

        resp = client.messages.create(
            model=model,
            max_tokens=1024,
            messages=[{"role": "user", "content": [block, {"type": "text", "text": _PROMPT}]}],
        )
        text = resp.content[0].text.strip()
        return {"text": text, "mode": "llm", "note": ""}
    except Exception as e:  # noqa: BLE001 — never crash the intake flow
        return {"text": "", "mode": "error",
                "note": f"Extraction failed ({e}). Please type the details manually."}
