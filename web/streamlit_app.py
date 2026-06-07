from pathlib import Path
import sys

import streamlit as st


PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from app.services.card_generator import generate_cards
from app.services.chunker import chunk_pages
from app.services.multimodal_note_merger import merge_multimodal_notes
from app.services.note_generator import generate_note
from app.services.page_vision_analyzer import (
    PAGE_VISION_NOTES_ROOT,
    analyze_single_page_image,
)
from app.services.pdf_page_renderer import render_pdf_pages
from app.services.pdf_parser import parse_pdf
from app.services.text_cleaner import clean_pages
from app.services.vision_llm_client import VisionLLMClient


UPLOADS_DIR = PROJECT_ROOT / "app" / "storage" / "uploads"


def main() -> None:
    st.set_page_config(page_title="study-agent", page_icon="📘", layout="wide")
    st.title("study-agent")

    _init_state()
    _show_flash_message()

    uploaded_file = st.file_uploader("上传 PDF 课件", type=["pdf"])
    if uploaded_file is not None:
        saved_path = _save_uploaded_pdf(uploaded_file)
        if st.session_state.get("pdf_path") != saved_path:
            st.session_state["pages"] = None
            st.session_state["chunks"] = None
            st.session_state["page_images"] = None
            st.session_state["page_vision_notes"] = None
            st.session_state["multimodal_note_markdown"] = ""
            st.session_state["note_markdown"] = ""
            st.session_state["cards_markdown"] = ""
        st.session_state["pdf_path"] = saved_path
        st.success(f"PDF 已保存：{saved_path.name}")

    pdf_path = st.session_state.get("pdf_path")
    parse_disabled = pdf_path is None
    render_disabled = pdf_path is None
    vision_disabled = not st.session_state.get("page_images")
    multimodal_note_disabled = not st.session_state.get("page_vision_notes")
    note_disabled = not st.session_state.get("chunks")
    cards_disabled = not st.session_state.get("note_markdown")

    render_zoom = st.number_input(
        "页面图片缩放倍数",
        min_value=1.0,
        max_value=4.0,
        value=2.0,
        step=0.5,
        help="默认 2.0，数值越大图片越清晰，但渲染更慢、文件更大。",
    )
    force_vision_reanalyze = st.checkbox(
        "重新分析已有页面",
        value=False,
        help="默认会跳过已有的成功页面解释；勾选后会重新调用视觉模型覆盖已有结果。",
    )

    col1, col2, col3, col4, col5, col6 = st.columns(6)
    with col1:
        if st.button("解析 PDF", disabled=parse_disabled, use_container_width=True):
            if _parse_pdf(pdf_path):
                st.session_state["flash_message"] = "PDF 解析完成，可以生成 Markdown 笔记。"
                st.rerun()

    with col2:
        if st.button(
            "将 PDF 渲染为逐页图片",
            disabled=render_disabled,
            use_container_width=True,
        ):
            if _render_pdf_pages(pdf_path, render_zoom):
                st.session_state["flash_message"] = "PDF 页面图片渲染完成。"
                st.rerun()

    with col3:
        if st.button(
            "逐页解释课件图片",
            disabled=vision_disabled,
            use_container_width=True,
        ):
            if _analyze_page_images(pdf_path, force_reanalyze=force_vision_reanalyze):
                st.session_state["flash_message"] = "课件图片逐页解释完成。"
                st.rerun()

    with col4:
        if st.button(
            "合并多模态笔记",
            disabled=multimodal_note_disabled,
            use_container_width=True,
        ):
            if _merge_multimodal_note():
                st.session_state["flash_message"] = "多模态 Markdown 笔记已生成。"
                st.rerun()

    with col5:
        if st.button("生成 Markdown 笔记", disabled=note_disabled, use_container_width=True):
            if _generate_note():
                st.session_state["flash_message"] = "Markdown 笔记已生成，可以生成复习卡片。"
                st.rerun()

    with col6:
        if st.button("生成复习卡片", disabled=cards_disabled, use_container_width=True):
            if _generate_cards():
                st.session_state["flash_message"] = "复习卡片已生成。"
                st.rerun()

    _show_parse_summary()
    _show_page_image_preview()
    _show_page_vision_notes()
    _show_multimodal_note_result()
    _show_note_result()
    _show_cards_result()


def _init_state() -> None:
    defaults = {
        "pdf_path": None,
        "pages": None,
        "chunks": None,
        "page_images": None,
        "page_vision_notes": None,
        "multimodal_note_markdown": "",
        "note_markdown": "",
        "cards_markdown": "",
        "flash_message": "",
    }
    for key, value in defaults.items():
        st.session_state.setdefault(key, value)


def _show_flash_message() -> None:
    message = st.session_state.get("flash_message")
    if message:
        st.success(message)
        st.session_state["flash_message"] = ""


def _save_uploaded_pdf(uploaded_file) -> Path:
    UPLOADS_DIR.mkdir(parents=True, exist_ok=True)
    filename = _safe_filename(uploaded_file.name, default="uploaded.pdf")
    output_path = UPLOADS_DIR / filename
    output_path.write_bytes(uploaded_file.getbuffer())
    return output_path


def _parse_pdf(pdf_path: Path) -> bool:
    try:
        with st.status("正在解析 PDF...", expanded=True) as status:
            st.write("读取 PDF 文本")
            pages = parse_pdf(str(pdf_path))

            st.write("清洗文本")
            cleaned_pages = clean_pages(pages)

            st.write("切分文本块")
            chunks = chunk_pages(cleaned_pages)

            st.session_state["pages"] = cleaned_pages
            st.session_state["chunks"] = chunks
            st.session_state["note_markdown"] = ""
            st.session_state["cards_markdown"] = ""

            status.update(label="PDF 解析完成", state="complete")
            return True
    except Exception as exc:
        st.error(f"解析 PDF 失败：{exc}")
        return False


def _render_pdf_pages(pdf_path: Path, zoom: float) -> bool:
    try:
        with st.status("正在将 PDF 渲染为逐页图片...", expanded=True) as status:
            st.write(f"使用 {zoom}x 缩放渲染页面")
            page_images = render_pdf_pages(str(pdf_path), zoom=zoom)

            st.session_state["page_images"] = page_images
            st.session_state["page_vision_notes"] = None
            st.session_state["multimodal_note_markdown"] = ""

            status.update(label="PDF 页面图片渲染完成", state="complete")
            return True
    except Exception as exc:
        st.error(f"渲染 PDF 页面图片失败：{exc}")
        return False


def _analyze_page_images(pdf_path: Path, force_reanalyze: bool = False) -> bool:
    page_images = st.session_state.get("page_images")
    if not page_images:
        st.error("请先将 PDF 渲染为逐页图片。")
        return False

    try:
        output_dir = PAGE_VISION_NOTES_ROOT / _safe_filename(
            pdf_path.stem,
            default="pdf_pages",
        )
        vision_client = VisionLLMClient()
        total_pages = len(page_images)
        skip_existing = not force_reanalyze
        page_vision_notes = []
        skipped_count = 0
        analyzed_count = 0

        st.session_state["page_vision_notes"] = page_vision_notes
        st.session_state["multimodal_note_markdown"] = ""

        progress_bar = st.progress(0, text="准备逐页解释课件图片...")
        summary_placeholder = st.empty()
        latest_placeholder = st.empty()
        results_placeholder = st.empty()

        for index, page_image in enumerate(page_images, start=1):
            page = page_image.get("page")
            progress_bar.progress(
                (index - 1) / total_pages,
                text=f"正在处理第 {page} 页（{index}/{total_pages}）",
            )

            result = analyze_single_page_image(
                page_image,
                output_dir=output_dir,
                vision_client=vision_client,
                skip_existing=skip_existing,
            )

            page_vision_notes.append(result)
            st.session_state["page_vision_notes"] = page_vision_notes

            if result.get("skipped"):
                skipped_count += 1
            else:
                analyzed_count += 1

            summary_placeholder.info(
                f"已完成 {index}/{total_pages} 页；"
                f"新分析 {analyzed_count} 页，跳过 {skipped_count} 页。"
            )
            with latest_placeholder.container():
                skipped_label = "（已存在，已跳过调用）" if result.get("skipped") else ""
                st.subheader(f"刚完成：第 {result['page']} 页 {skipped_label}")
                st.markdown(result["markdown"])

            _render_page_vision_notes_preview(results_placeholder, page_vision_notes)

        progress_bar.progress(
            1.0,
            text=f"逐页解释完成：新分析 {analyzed_count} 页，跳过 {skipped_count} 页",
        )
        return True
    except Exception as exc:
        st.error(f"逐页解释课件图片失败：{exc}")
        return False


def _merge_multimodal_note() -> bool:
    page_vision_notes = st.session_state.get("page_vision_notes")
    if not page_vision_notes:
        st.error("请先完成逐页视觉解释。")
        return False

    with st.spinner("正在合并多模态 Markdown 笔记..."):
        multimodal_note = merge_multimodal_notes(
            page_vision_notes,
            output_filename="multimodal_note.md",
        )

    if _is_error(multimodal_note):
        st.error(multimodal_note)
        return False

    st.session_state["multimodal_note_markdown"] = multimodal_note
    st.success("多模态 Markdown 笔记已生成。")
    return True


def _generate_note() -> bool:
    chunks = st.session_state.get("chunks")
    if not chunks:
        st.error("请先解析 PDF。")
        return False

    with st.spinner("正在生成 Markdown 笔记..."):
        note_markdown = generate_note(chunks, output_filename="note.md")

    if _is_error(note_markdown):
        st.error(note_markdown)
        return False

    st.session_state["note_markdown"] = note_markdown
    st.session_state["cards_markdown"] = ""
    st.success("Markdown 笔记已生成。")
    return True


def _generate_cards() -> bool:
    note_markdown = st.session_state.get("note_markdown", "")
    if not note_markdown:
        st.error("请先生成 Markdown 笔记。")
        return False

    with st.spinner("正在生成复习卡片..."):
        cards_markdown = generate_cards(note_markdown, output_filename="cards.md")

    if _is_error(cards_markdown):
        st.error(cards_markdown)
        return False

    st.session_state["cards_markdown"] = cards_markdown
    st.success("复习卡片已生成。")
    return True


def _show_parse_summary() -> None:
    pages = st.session_state.get("pages")
    chunks = st.session_state.get("chunks")
    if not pages or not chunks:
        return

    st.divider()
    col1, col2 = st.columns(2)
    col1.metric("页数", len(pages))
    col2.metric("文本块", len(chunks))


def _show_page_image_preview() -> None:
    page_images = st.session_state.get("page_images")
    if not page_images:
        return

    st.divider()
    st.subheader("逐页图片预览")
    st.caption(f"共渲染 {len(page_images)} 页，以下展示前 3 页。")

    preview_columns = st.columns(min(3, len(page_images)))
    for column, page_image in zip(preview_columns, page_images[:3]):
        with column:
            st.image(
                page_image["image_path"],
                caption=f"第 {page_image['page']} 页",
                use_container_width=True,
            )


def _show_page_vision_notes() -> None:
    page_vision_notes = st.session_state.get("page_vision_notes")
    if not page_vision_notes:
        return

    full_markdown = _combine_page_vision_notes(page_vision_notes)

    st.divider()
    st.subheader("逐页视觉解释")
    st.download_button(
        "下载 page_vision_notes.md",
        data=full_markdown.encode("utf-8"),
        file_name="page_vision_notes.md",
        mime="text/markdown",
    )

    for note in page_vision_notes:
        skipped_label = "（已存在，已跳过调用）" if note.get("skipped") else ""
        with st.expander(f"第 {note['page']} 页 {skipped_label}", expanded=False):
            st.markdown(note["markdown"])


def _render_page_vision_notes_preview(placeholder, page_vision_notes: list[dict]) -> None:
    with placeholder.container():
        st.subheader("当前已完成页面")
        full_markdown = _combine_page_vision_notes(page_vision_notes)
        st.download_button(
            "下载当前 page_vision_notes.md",
            data=full_markdown.encode("utf-8"),
            file_name="page_vision_notes.md",
            mime="text/markdown",
            key=f"download_page_vision_notes_{len(page_vision_notes)}",
        )
        for note in page_vision_notes:
            skipped_label = "（已存在，已跳过调用）" if note.get("skipped") else ""
            with st.expander(f"第 {note['page']} 页 {skipped_label}", expanded=False):
                st.markdown(note["markdown"])


def _show_multimodal_note_result() -> None:
    multimodal_note = st.session_state.get("multimodal_note_markdown", "")
    if not multimodal_note:
        return

    st.divider()
    st.subheader("多模态 Markdown 笔记")
    st.download_button(
        "下载 multimodal_note.md",
        data=multimodal_note.encode("utf-8"),
        file_name="multimodal_note.md",
        mime="text/markdown",
    )
    st.markdown(multimodal_note)


def _show_note_result() -> None:
    note_markdown = st.session_state.get("note_markdown", "")
    if not note_markdown:
        return

    st.divider()
    st.subheader("Markdown 笔记")
    st.download_button(
        "下载 note.md",
        data=note_markdown.encode("utf-8"),
        file_name="note.md",
        mime="text/markdown",
    )
    st.markdown(note_markdown)


def _show_cards_result() -> None:
    cards_markdown = st.session_state.get("cards_markdown", "")
    if not cards_markdown:
        return

    st.divider()
    st.subheader("复习卡片")
    st.download_button(
        "下载 cards.md",
        data=cards_markdown.encode("utf-8"),
        file_name="cards.md",
        mime="text/markdown",
    )
    st.markdown(cards_markdown)


def _safe_filename(filename: str, default: str) -> str:
    cleaned = "".join(char for char in filename if char not in r'<>:"/\|?*').strip()
    return cleaned or default


def _is_error(result: str) -> bool:
    return result.startswith(("生成", "合并")) and "失败" in result


def _combine_page_vision_notes(page_vision_notes: list[dict]) -> str:
    parts = []
    for note in page_vision_notes:
        page = note.get("page")
        markdown = note.get("markdown", "").strip()
        parts.append(f"<!-- page: {page} -->\n\n{markdown}")
    return "\n\n---\n\n".join(parts)


if __name__ == "__main__":
    main()
