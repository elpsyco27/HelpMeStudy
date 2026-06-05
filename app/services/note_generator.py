from pathlib import Path
from typing import List, Optional

from app.prompts.note_prompt import build_chunk_note_prompt, build_merge_notes_prompt
from app.services.llm_client import LLMClient


NOTES_DIR = Path(__file__).resolve().parents[1] / "storage" / "notes"


def generate_note(
    chunks: List[dict],
    output_filename: str = "study_note.md",
    llm_client: Optional[LLMClient] = None,
) -> str:
    """Generate a full Markdown note from chunks and save it locally."""
    if not chunks:
        return "生成笔记失败：chunks 不能为空。"

    client = llm_client or LLMClient()

    try:
        partial_notes = []
        for chunk in chunks:
            prompt = build_chunk_note_prompt(chunk)
            partial_note = client.generate(prompt)
            partial_notes.append(_with_source_fallback(partial_note, chunk))

        merge_prompt = build_merge_notes_prompt(partial_notes)
        final_note = client.generate(merge_prompt)
        final_note = final_note.strip()

        if not final_note:
            return "生成笔记失败：LLM 返回了空内容。"

        save_note(final_note, output_filename)
        return final_note
    except Exception as exc:
        return f"生成笔记失败：{exc}"


def save_note(markdown: str, output_filename: str = "study_note.md") -> Path:
    NOTES_DIR.mkdir(parents=True, exist_ok=True)
    safe_filename = _safe_markdown_filename(output_filename)
    output_path = NOTES_DIR / safe_filename
    output_path.write_text(markdown, encoding="utf-8")
    return output_path


def _with_source_fallback(note: str, chunk: dict) -> str:
    pages = ", ".join(str(page) for page in chunk.get("pages", []))
    if "来源" in note:
        return note
    return f"{note.rstrip()}\n\n来源：第 {pages} 页"


def _safe_markdown_filename(filename: str) -> str:
    cleaned = "".join(char for char in filename if char not in r'<>:"/\|?*').strip()
    if not cleaned:
        cleaned = "study_note.md"
    if not cleaned.lower().endswith(".md"):
        cleaned = f"{cleaned}.md"
    return cleaned
