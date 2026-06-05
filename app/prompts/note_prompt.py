def build_chunk_note_prompt(chunk: dict) -> str:
    pages = ", ".join(str(page) for page in chunk.get("pages", []))
    text = chunk.get("text", "")

    return f"""你是一个学习笔记整理助手。

请根据下面的课件文本，生成局部 Markdown 学习笔记。

要求：
- 使用清晰的 Markdown 层级标题。
- 提炼核心概念、关键结论、公式含义和易错点。
- 不要编造原文没有的信息。
- 必须保留来源页码，格式为：来源：第 {pages} 页。
- 如果文本中有表格或列表，请尽量整理成 Markdown 表格或列表。

chunk_id：{chunk.get("chunk_id")}
来源页码：第 {pages} 页

课件文本：
\"\"\"
{text}
\"\"\"
"""


def build_merge_notes_prompt(partial_notes: list[str]) -> str:
    notes_text = "\n\n---\n\n".join(partial_notes)

    return f"""你是一个学习笔记整理助手。

请将下面多个局部 Markdown 笔记合并成一份完整、连贯、适合复习的 Markdown 学习笔记。

要求：
- 保留所有重要知识点。
- 合并重复内容，调整章节顺序。
- 保留来源页码信息，不要删除页码。
- 使用 Markdown 标题、列表、表格组织内容。
- 输出完整 Markdown，不要输出解释性前言。

局部笔记：
\"\"\"
{notes_text}
\"\"\"
"""
