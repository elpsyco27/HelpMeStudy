from pathlib import Path
from typing import List, Optional

import fitz


PAGE_IMAGES_ROOT = Path(__file__).resolve().parents[1] / "storage" / "page_images"


def render_pdf_pages(
    pdf_path: str,
    zoom: float = 2.0,
    dpi: Optional[int] = None,
) -> List[dict]:
    """Render each PDF page to a PNG image and return image metadata."""
    source_path = Path(pdf_path)
    output_dir = PAGE_IMAGES_ROOT / _safe_dir_name(source_path.stem)
    output_dir.mkdir(parents=True, exist_ok=True)

    rendered_pages: List[dict] = []

    with fitz.open(source_path) as doc:
        page_number_width = max(3, len(str(doc.page_count)))

        for page_index, page in enumerate(doc, start=1):
            image_path = output_dir / f"page_{page_index:0{page_number_width}d}.png"

            if dpi is not None:
                pixmap = page.get_pixmap(dpi=dpi)
            else:
                matrix = fitz.Matrix(zoom, zoom)
                pixmap = page.get_pixmap(matrix=matrix)

            pixmap.save(image_path)
            rendered_pages.append(
                {
                    "page": page_index,
                    "image_path": str(image_path),
                }
            )

    return rendered_pages


def _safe_dir_name(name: str) -> str:
    cleaned = "".join(char for char in name if char not in r'<>:"/\|?*').strip()
    return cleaned or "pdf_pages"
