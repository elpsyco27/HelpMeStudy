from pathlib import Path
import sys
from typing import List

import fitz


def parse_pdf(pdf_path: str) -> List[dict]:
    """Parse a PDF file and return text grouped by page."""
    pages: List[dict] = []

    with fitz.open(Path(pdf_path)) as doc:
        for page_index, page in enumerate(doc, start=1):
            text = page.get_text("text") or ""
            pages.append(
                {
                    "page": page_index,
                    "text": text,
                }
            )

    return pages


def print_first_pages(pdf_path: str, limit: int = 3) -> None:
    """Simple manual test helper: print the first pages of a PDF."""
    pages = parse_pdf(pdf_path)

    for page in pages[:limit]:
        _safe_print(f"--- Page {page['page']} ---")
        _safe_print(page["text"])
        _safe_print("")


def _safe_print(value: str) -> None:
    encoding = sys.stdout.encoding or "utf-8"
    printable_value = value.encode(encoding, errors="replace").decode(encoding)
    print(printable_value)
