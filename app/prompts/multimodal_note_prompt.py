def build_multimodal_note_merge_prompt(page_vision_notes: list[dict]) -> str:
    notes_text = "\n\n---\n\n".join(
        _format_page_note(note) for note in page_vision_notes
    )

    return f"""你是一个学习笔记整理助手。

请将下面逐页视觉解析得到的 Markdown 内容，合并成一篇完整的 Markdown 学习笔记。

要求：
- 按章节或主题组织，不要机械地按页堆叠。
- 合并重复内容，保留重要差异。
- 必须保留页码来源，例如“来源：第 3 页”。
- 保留并整理图表、流程图、公式、例题、易错点。
- 如果某页分析失败，请不要混入正文，在文末“附录：分析失败页面”中标记。
- 最后生成“复习重点”和“复习卡片”两个部分。
- 复习卡片使用 Markdown 表格，列为：问题 | 答案 | 易错点 | 来源。
- 不要编造逐页内容中没有的信息。
- 只输出完整 Markdown，不要输出解释性前言。

逐页视觉解析内容：
\"\"\"
{notes_text}
\"\"\"
"""


def build_multimodal_batch_summary_prompt(page_vision_notes: list[dict]) -> str:
    notes_text = "\n\n---\n\n".join(
        _format_page_note(note) for note in page_vision_notes
    )
    pages = ", ".join(str(note.get("page", "")) for note in page_vision_notes)

    return f"""你是一个学习笔记整理助手。

请将下面这些页面的视觉解析内容整理成一个阶段性 Markdown 小结。

要求：
- 覆盖页码范围：第 {pages} 页。
- 按主题组织，不要逐页机械堆叠。
- 合并重复内容。
- 保留页码来源。
- 保留图表、流程图、公式、例题、易错点。
- 如果某页分析失败，请在“小结中的失败页面”部分标记。
- 输出 Markdown，不要输出解释性前言。

页面视觉解析内容：
\"\"\"
{notes_text}
\"\"\"
"""


def build_multimodal_final_merge_prompt(batch_notes: list[dict]) -> str:
    notes_text = "\n\n---\n\n".join(
        _format_page_note(note) for note in batch_notes
    )

    return f"""你是一个学习笔记整理助手。

请将下面多个阶段性 Markdown 小结合并为一篇完整、连贯、适合复习的 Markdown 学习笔记。

要求：
- 按章节或主题组织，不要机械堆叠。
- 合并重复内容，保留重要差异。
- 必须保留页码来源。
- 保留图表、流程图、公式、例题、易错点。
- 如果某页分析失败，请在文末“附录：分析失败页面”中标记。
- 最后生成“复习重点”和“复习卡片”两个部分。
- 复习卡片使用 Markdown 表格，列为：问题 | 答案 | 易错点 | 来源。
- 不要编造小结中没有的信息。
- 只输出完整 Markdown，不要输出解释性前言。

阶段性小结：
\"\"\"
{notes_text}
\"\"\"
"""


def _format_page_note(note: dict) -> str:
    page = note.get("page", "")
    markdown = note.get("markdown", "")
    return f"<!-- page: {page} -->\n\n{markdown}"
