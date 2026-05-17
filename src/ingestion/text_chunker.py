"""Split extracted text into overlapping chunks with page metadata."""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent.parent))
from config import CHUNK_SIZE, CHUNK_OVERLAP


def chunk_text(text: str, chunk_size: int = CHUNK_SIZE, overlap: int = CHUNK_OVERLAP) -> list[str]:
    """Split text into overlapping chunks by character count."""
    if not text.strip():
        return []
    chunks = []
    start = 0
    while start < len(text):
        end = start + chunk_size
        chunks.append(text[start:end])
        start += chunk_size - overlap
    return [c.strip() for c in chunks if c.strip()]


def build_chunks_with_metadata(
    pages: dict[int, str],
) -> list[dict]:
    """
    Convert page dict → list of chunk dicts with metadata.
    Returns: [{"text": str, "page": int, "chunk_id": str}]
    """
    all_chunks = []
    chunk_idx = 0

    for page_num in sorted(pages.keys()):
        text = pages[page_num]
        if not text.strip():
            continue

        page_chunks = chunk_text(text)
        for chunk in page_chunks:
            all_chunks.append(
                {
                    "text": chunk,
                    "page": page_num + 1,  # 1-indexed for display
                    "chunk_id": f"p{page_num + 1}_c{chunk_idx}",
                }
            )
            chunk_idx += 1

    print(f"Total chunks: {len(all_chunks)} from {len(pages)} pages")
    return all_chunks
