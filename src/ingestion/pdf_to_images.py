"""Convert PDF pages to base64-encoded images for OCR."""
import base64
import io
import sys
from pathlib import Path
from typing import Generator

import pypdfium2 as pdfium
from PIL import Image

sys.path.insert(0, str(Path(__file__).parent.parent.parent))
from config import PDF_PATH, PDF_DPI


def pdf_page_to_base64(pdf_path: Path, page_num: int, dpi: int = PDF_DPI) -> str:
    """Render single PDF page → base64 PNG string."""
    doc = pdfium.PdfDocument(str(pdf_path))
    page = doc[page_num]
    scale = dpi / 72
    bitmap = page.render(scale=scale, rotation=0)
    pil_image = bitmap.to_pil()

    # Convert to RGB if needed (removes alpha channel)
    if pil_image.mode != "RGB":
        pil_image = pil_image.convert("RGB")

    buffer = io.BytesIO()
    pil_image.save(buffer, format="PNG")
    doc.close()

    return base64.b64encode(buffer.getvalue()).decode("utf-8")


def get_total_pages(pdf_path: Path = PDF_PATH) -> int:
    doc = pdfium.PdfDocument(str(pdf_path))
    count = len(doc)
    doc.close()
    return count


def iter_pages_as_base64(
    pdf_path: Path = PDF_PATH,
    start: int = 0,
    end: int | None = None,
    dpi: int = PDF_DPI,
) -> Generator[tuple[int, str], None, None]:
    """Yield (page_num, base64_image) for each page in range."""
    total = get_total_pages(pdf_path)
    end = end if end is not None else total
    for i in range(start, min(end, total)):
        yield i, pdf_page_to_base64(pdf_path, i, dpi)
