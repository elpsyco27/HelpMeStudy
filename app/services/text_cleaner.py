import re
from typing import List


def clean_text(text: str) -> str:
    """Clean extracted PDF text while keeping basic paragraph structure."""
    if not text:
        return ""

    text = text.replace("\r\n", "\n").replace("\r", "\n")
    text = re.sub(r"[ \t\f\v]+", " ", text)

    lines = [line.strip() for line in text.split("\n")]
    paragraphs: List[str] = []
    current = ""

    for line in lines:
        if not line:
            if current:
                paragraphs.append(current.strip())
                current = ""
            continue

        if not current:
            current = line
        elif _should_merge_lines(current, line):
            current = f"{current}{line}"
        else:
            current = f"{current}\n{line}"

    if current:
        paragraphs.append(current.strip())

    cleaned = "\n\n".join(paragraphs)
    cleaned = re.sub(r" {2,}", " ", cleaned)
    cleaned = re.sub(r"\n{3,}", "\n\n", cleaned)

    return cleaned.strip()


def clean_pages(pages: List[dict]) -> List[dict]:
    """Clean text in a page list returned by the PDF parser."""
    return [
        {
            "page": page["page"],
            "text": clean_text(page.get("text", "")),
        }
        for page in pages
    ]


def _should_merge_lines(previous: str, current: str) -> bool:
    if not previous or not current:
        return False

    if _is_list_item(current):
        return False

    if _is_list_item(previous) and len(previous) <= 20:
        return False

    if previous.endswith((".", "。", "!", "！", "?", "？", ":", "：", ";", "；")):
        return False

    if re.match(r"^\d+(\.\d+)*\s+", current):
        return False

    if re.match(r"^\d+(\.\d+)*\s+", previous):
        return False

    if current.endswith((".", "。", "!", "！", "?", "？")):
        return True

    if len(previous) <= 30 and len(current) <= 30 and not previous.endswith(("，", ",", "、")):
        return False

    return True


def _is_list_item(line: str) -> bool:
    return line.startswith(("•", "-", "–", "—", "", "", ""))
