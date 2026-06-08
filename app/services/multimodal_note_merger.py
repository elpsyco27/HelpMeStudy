from pathlib import Path
from typing import List, Optional

from app.prompts.multimodal_note_prompt import (
    build_multimodal_batch_summary_prompt,
    build_multimodal_final_merge_prompt,
    build_multimodal_note_merge_prompt,
)
from app.services.llm_client import LLMClient


MULTIMODAL_NOTES_DIR = Path(__file__).resolve().parents[1] / "storage" / "notes"
DEFAULT_BATCH_SIZE = 8


def merge_multimodal_notes(
    page_vision_notes: List[dict],
    output_filename: str = "multimodal_note.md",
    llm_client: Optional[LLMClient] = None,
    batch_size: int = DEFAULT_BATCH_SIZE,
) -> str:
    """Merge page-level vision notes into one complete Markdown note."""
    if not page_vision_notes:
        return "合并多模态笔记失败：page_vision_notes 不能为空。"

    client = llm_client or LLMClient(timeout=180.0)

    try:
        prepared_notes = [_with_page_source(note) for note in page_vision_notes]

        if len(prepared_notes) <= batch_size:
            prompt = build_multimodal_note_merge_prompt(prepared_notes)
            merged_markdown = client.generate(prompt).strip()
        else:
            batch_notes = _summarize_batches(
                prepared_notes,
                client=client,
                batch_size=batch_size,
            )
            prompt = build_multimodal_final_merge_prompt(batch_notes)
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


def _summarize_batches(
    page_vision_notes: List[dict],
    client: LLMClient,
    batch_size: int,
) -> List[dict]:
    batch_notes = []

    for batch_index, batch in enumerate(_batched(page_vision_notes, batch_size), start=1):
        prompt = build_multimodal_batch_summary_prompt(batch)
        markdown = client.generate(prompt).strip()
        if not markdown:
            markdown = f"## 第 {batch_index} 批页面小结\n\n该批次合并失败：LLM 返回了空内容。"

        pages = [note.get("page") for note in batch]
        batch_notes.append(
            {
                "page": f"{pages[0]}-{pages[-1]}",
                "markdown": markdown,
            }
        )

    return batch_notes


def _batched(items: List[dict], batch_size: int) -> List[List[dict]]:
    size = max(1, batch_size)
    return [items[index : index + size] for index in range(0, len(items), size)]


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
