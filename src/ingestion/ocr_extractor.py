"""OCR: send page images to Groq vision model, extract Hindi text."""
import json
import sys
import time
from pathlib import Path

from groq import Groq

sys.path.insert(0, str(Path(__file__).parent.parent.parent))
from config import GROQ_API_KEY, OCR_MODEL, OCR_DELAY_SEC

_client: Groq | None = None


def _get_client() -> Groq:
    global _client
    if _client is None:
        _client = Groq(api_key=GROQ_API_KEY)
    return _client


OCR_SYSTEM_PROMPT = """You are an expert OCR system specializing in Hindi (Devanagari script) text extraction.
Extract ALL text from the provided image exactly as written.
- Preserve Hindi text in Devanagari script
- Preserve paragraph structure with newlines
- Do NOT translate or summarize
- Do NOT add commentary
- If image has no readable text, return empty string
- Return ONLY the extracted text, nothing else"""


def extract_text_from_image(base64_image: str, page_num: int) -> str:
    """Send image to Groq vision model, return extracted Hindi text."""
    client = _get_client()
    try:
        response = client.chat.completions.create(
            model=OCR_MODEL,
            messages=[
                {"role": "system", "content": OCR_SYSTEM_PROMPT},
                {
                    "role": "user",
                    "content": [
                        {
                            "type": "image_url",
                            "image_url": {
                                "url": f"data:image/png;base64,{base64_image}"
                            },
                        },
                        {
                            "type": "text",
                            "text": "Extract all text from this page exactly as written.",
                        },
                    ],
                },
            ],
            temperature=0,
            max_tokens=4096,
        )
        return response.choices[0].message.content or ""
    except Exception as e:
        print(f"  [OCR ERROR] Page {page_num}: {e}")
        return ""


def extract_pages_to_json(
    pages_iter,
    output_path: Path,
    delay: float = OCR_DELAY_SEC,
) -> dict[int, str]:
    """
    OCR all pages, save to JSON file.
    Resumes from existing file to avoid re-processing.
    """
    extracted: dict[int, str] = {}

    # Resume from existing output
    if output_path.exists():
        with open(output_path, "r", encoding="utf-8") as f:
            existing = json.load(f)
        extracted = {int(k): v for k, v in existing.items()}
        print(f"Resuming: {len(extracted)} pages already extracted.")

    for page_num, base64_img in pages_iter:
        if page_num in extracted:
            print(f"  Skip page {page_num + 1} (already done)")
            continue

        print(f"  OCR page {page_num + 1}...", end=" ", flush=True)
        text = extract_text_from_image(base64_img, page_num)

        if not text.strip():
            # Don't save empty/rate-limited pages — allow retry on next run
            print(f"[skipped - empty]")
            continue

        extracted[page_num] = text
        print(f"[{len(text)} chars]")

        # Save after every page (crash-safe)
        with open(output_path, "w", encoding="utf-8") as f:
            json.dump(extracted, f, ensure_ascii=False, indent=2)

        time.sleep(delay)

    return extracted
