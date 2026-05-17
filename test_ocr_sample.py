"""
Test OCR on first 3 pages to verify setup before full ingest.
Run: python test_ocr_sample.py
"""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))

from config import PDF_PATH, GROQ_API_KEY
from src.ingestion.pdf_to_images import pdf_page_to_base64, get_total_pages
from src.ingestion.ocr_extractor import extract_text_from_image

if not GROQ_API_KEY or GROQ_API_KEY == "your_groq_api_key_here":
    print("ERROR: Set GROQ_API_KEY in .env first!")
    sys.exit(1)

print(f"PDF: {PDF_PATH.name} ({get_total_pages(PDF_PATH)} pages)")
print("Testing OCR on pages 1-3...\n")

for i in range(3):
    print(f"--- Page {i + 1} ---")
    b64 = pdf_page_to_base64(PDF_PATH, i)
    text = extract_text_from_image(b64, i)
    print(text[:500] if text else "[no text extracted]")
    print()
