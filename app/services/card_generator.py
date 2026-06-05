from pathlib import Path
from typing import Optional

from app.prompts.card_prompt import build_card_prompt
from app.services.llm_client import LLMClient


CARDS_DIR = Path(__file__).resolve().parents[1] / "storage" / "cards"


def generate_cards(
    note_markdown: str,
    output_filename: str = "review_cards.md",
    llm_client: Optional[LLMClient] = None,
) -> str:
    """Generate review cards from Markdown notes and save them locally."""
    if not note_markdown.strip():
        return "生成复习卡片失败：Markdown 笔记内容不能为空。"

    client = llm_client or LLMClient()

    try:
        prompt = build_card_prompt(note_markdown)
        cards_markdown = client.generate(prompt).strip()

        if not cards_markdown:
            return "生成复习卡片失败：LLM 返回了空内容。"

        save_cards(cards_markdown, output_filename)
        return cards_markdown
    except Exception as exc:
        return f"生成复习卡片失败：{exc}"


def save_cards(markdown: str, output_filename: str = "review_cards.md") -> Path:
    CARDS_DIR.mkdir(parents=True, exist_ok=True)
    safe_filename = _safe_markdown_filename(output_filename)
    output_path = CARDS_DIR / safe_filename
    output_path.write_text(markdown, encoding="utf-8")
    return output_path


def _safe_markdown_filename(filename: str) -> str:
    cleaned = "".join(char for char in filename if char not in r'<>:"/\|?*').strip()
    if not cleaned:
        cleaned = "review_cards.md"
    if not cleaned.lower().endswith(".md"):
        cleaned = f"{cleaned}.md"
    return cleaned
