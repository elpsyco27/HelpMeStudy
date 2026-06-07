from pathlib import Path
from typing import List, Optional

from app.prompts.multimodal_note_prompt import build_multimodal_note_merge_prompt
from app.services.llm_client import LLMClient


MULTIMODAL_NOTES_DIR = Path(__file__).resolve().parents[1] / "storage" / "notes"


def merge_multimodal_notes(
    page_vision_notes: List[dict],
    output_filename: str = "multimodal_note.md",
    llm_client: Optional[LLMClient] = None,
) -> str:
    """Merge page-level vision notes into one complete Markdown note."""
    if not page_vision_notes:
        return "合并多模态笔记失败：page_vision_notes 不能为空。"

    client = llm_client or LLMClient()

    try:
        prepared_notes = [_with_page_source(note) for note in page_vision_notes]
        prompt = build_multimodal_note_merge_prompt(prepared_notes)
        merged_markdown = client.generate(prompt).strip()

        if not merged_markdown:
            return "合并多模态笔记失败：LLM 返回了空内容。"

        save_multimodal_note(merged_markdown, output_filename)
        return merged_markdown
    except Exception as exc:
        return f"合并多模态笔记失败：{exc}"


def save_multimodal_note(markdown: str, output_filename: str) -> Path:
    MULTIMODAL_NOTES_DIR.mkdir(parents=True, exist_ok=True)
    output_path = MULTIMODAL_NOTES_DIR / _safe_markdown_filename(output_filename)
    output_path.write_text(markdown, encoding="utf-8")
    return output_path


def _with_page_source(note: dict) -> dict:
    page = note.get("page")
    markdown = note.get("markdown", "")

    if "来源" in markdown or "分析失败" in markdown:
        return note

    updated_note = note.copy()
    updated_note["markdown"] = f"{markdown.rstrip()}\n\n来源：第 {page} 页"
    return updated_note


def _safe_markdown_filename(filename: str) -> str:
    cleaned = "".join(char for char in filename if char not in r'<>:"/\|?*').strip()
    if not cleaned:
        cleaned = "multimodal_note.md"
    if not cleaned.lower().endswith(".md"):
        cleaned = f"{cleaned}.md"
    return cleaned
