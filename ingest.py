"""
Run once to build the RAG knowledge base.

Pipeline:
  PDF → images → Groq OCR → text chunks → embeddings → ChromaDB

Usage:
  python ingest.py                    # process all pages
  python ingest.py --start 0 --end 20 # process pages 0-19 only
  python ingest.py --skip-ocr         # re-embed from existing OCR output
"""
import argparse
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))

from config import PDF_PATH, EXTRACTED_DIR, GROQ_API_KEY
from src.ingestion.pdf_to_images import iter_pages_as_base64, get_total_pages
from src.ingestion.ocr_extractor import extract_pages_to_json
from src.ingestion.text_chunker import build_chunks_with_metadata
from src.ingestion.embedder import embed_and_store

OCR_OUTPUT = EXTRACTED_DIR / "pages_ocr.json"


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--start", type=int, default=0, help="Start page (0-indexed)")
    parser.add_argument("--end", type=int, default=None, help="End page (exclusive)")
    parser.add_argument("--skip-ocr", action="store_true", help="Skip OCR, use existing JSON")
    args = parser.parse_args()

    if not GROQ_API_KEY:
        print("ERROR: GROQ_API_KEY not set in .env file")
        sys.exit(1)

    if not PDF_PATH.exists():
        print(f"ERROR: PDF not found at {PDF_PATH}")
        sys.exit(1)

    EXTRACTED_DIR.mkdir(parents=True, exist_ok=True)

    total = get_total_pages(PDF_PATH)
    print(f"PDF: {PDF_PATH.name} | {total} pages total")

    # --- Step 1: OCR ---
    if not args.skip_ocr:
        print(f"\n[1/3] OCR: pages {args.start} to {args.end or total}")
        pages_iter = iter_pages_as_base64(PDF_PATH, start=args.start, end=args.end)
        pages = extract_pages_to_json(pages_iter, OCR_OUTPUT)
    else:
        print(f"\n[1/3] OCR: loading existing {OCR_OUTPUT}")
        if not OCR_OUTPUT.exists():
            print(f"ERROR: {OCR_OUTPUT} not found. Run without --skip-ocr first.")
            sys.exit(1)
        with open(OCR_OUTPUT, "r", encoding="utf-8") as f:
            raw = json.load(f)
        pages = {int(k): v for k, v in raw.items()}
        print(f"  Loaded {len(pages)} pages from file.")

    # --- Step 2: Chunk ---
    print(f"\n[2/3] Chunking text...")
    chunks = build_chunks_with_metadata(pages)

    # --- Step 3: Embed + store ---
    print(f"\n[3/3] Embedding and storing in ChromaDB...")
    embed_and_store(chunks)

    print("\nIngestion complete. Run `python app.py` to chat.")


if __name__ == "__main__":
    main()
