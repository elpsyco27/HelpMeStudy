from typing import List


def chunk_pages(pages: List[dict], max_chars: int = 3000) -> List[dict]:
    """Split page text into chunks while preserving page numbers."""
    chunks: List[dict] = []
    current_text_parts: List[str] = []
    current_pages: List[int] = []
    current_length = 0

    for page in pages:
        page_number = page["page"]
        text = page.get("text", "")

        for part in _split_text(text, max_chars):
            part_length = len(part)

            if current_text_parts and current_length + part_length > max_chars:
                _append_chunk(chunks, current_pages, current_text_parts)
                current_text_parts = []
                current_pages = []
                current_length = 0

            current_text_parts.append(part)
            current_length += part_length

            if page_number not in current_pages:
                current_pages.append(page_number)

    if current_text_parts:
        _append_chunk(chunks, current_pages, current_text_parts)

    return chunks


def _split_text(text: str, max_chars: int) -> List[str]:
    if not text:
        return [""]

    parts: List[str] = []
    paragraphs = [paragraph for paragraph in text.split("\n\n") if paragraph]

    for paragraph in paragraphs:
        if len(paragraph) <= max_chars:
            parts.append(paragraph)
            continue

        for start in range(0, len(paragraph), max_chars):
            parts.append(paragraph[start : start + max_chars])

    return parts


def _append_chunk(chunks: List[dict], pages: List[int], text_parts: List[str]) -> None:
    chunks.append(
        {
            "chunk_id": len(chunks) + 1,
            "pages": pages[:],
            "text": "\n\n".join(text_parts).strip(),
        }
    )
