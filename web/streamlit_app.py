from pathlib import Path
import sys

import streamlit as st


PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from app.services.card_generator import generate_cards
from app.services.chunker import chunk_pages
from app.services.note_generator import generate_note
from app.services.pdf_parser import parse_pdf
from app.services.text_cleaner import clean_pages


UPLOADS_DIR = PROJECT_ROOT / "app" / "storage" / "uploads"


def main() -> None:
    st.set_page_config(page_title="study-agent", page_icon="📘", layout="wide")
    st.title("study-agent")

    _init_state()
    _show_flash_message()

    uploaded_file = st.file_uploader("上传 PDF 课件", type=["pdf"])
    if uploaded_file is not None:
        saved_path = _save_uploaded_pdf(uploaded_file)
        st.session_state["pdf_path"] = saved_path
        st.success(f"PDF 已保存：{saved_path.name}")

    pdf_path = st.session_state.get("pdf_path")
    parse_disabled = pdf_path is None
    note_disabled = not st.session_state.get("chunks")
    cards_disabled = not st.session_state.get("note_markdown")

    col1, col2, col3 = st.columns(3)
    with col1:
        if st.button("解析 PDF", disabled=parse_disabled, use_container_width=True):
            if _parse_pdf(pdf_path):
                st.session_state["flash_message"] = "PDF 解析完成，可以生成 Markdown 笔记。"
                st.rerun()

    with col2:
        if st.button("生成 Markdown 笔记", disabled=note_disabled, use_container_width=True):
            if _generate_note():
                st.session_state["flash_message"] = "Markdown 笔记已生成，可以生成复习卡片。"
                st.rerun()

    with col3:
        if st.button("生成复习卡片", disabled=cards_disabled, use_container_width=True):
            if _generate_cards():
                st.session_state["flash_message"] = "复习卡片已生成。"
                st.rerun()

    _show_parse_summary()
    _show_note_result()
    _show_cards_result()


def _init_state() -> None:
    defaults = {
        "pdf_path": None,
        "pages": None,
        "chunks": None,
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
    return result.startswith("生成") and "失败" in result


if __name__ == "__main__":
    main()
