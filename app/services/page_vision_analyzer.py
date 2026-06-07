from pathlib import Path
from typing import List, Optional

from app.prompts.page_vision_prompt import build_page_vision_prompt
from app.services.vision_llm_client import VisionLLMClient


PAGE_VISION_NOTES_ROOT = (
    Path(__file__).resolve().parents[1] / "storage" / "page_vision_notes"
)


def analyze_page_images(
    page_images: List[dict],
    pdf_stem: Optional[str] = None,
    vision_client: Optional[VisionLLMClient] = None,
    skip_existing: bool = True,
) -> List[dict]:
    """Analyze rendered PDF page images one by one with a vision model."""
    if not page_images:
        return []

    output_dir = PAGE_VISION_NOTES_ROOT / _resolve_pdf_stem(page_images, pdf_stem)
    output_dir.mkdir(parents=True, exist_ok=True)

    results: List[dict] = []
    client: Optional[VisionLLMClient] = None
    client_error = ""

    if vision_client is not None:
        client = vision_client
    else:
        try:
            client = VisionLLMClient()
        except Exception as exc:
            client_error = str(exc)

    for page_image in page_images:
        page = page_image.get("page")
        image_path = page_image.get("image_path", "")
        output_path = _page_markdown_path(output_dir, page)

        if skip_existing and output_path.exists():
            markdown = output_path.read_text(encoding="utf-8")
            if not _is_failure_markdown(markdown):
                results.append(
                    {
                        "page": page,
                        "image_path": image_path,
                        "markdown": markdown,
                        "skipped": True,
                    }
                )
                continue

        try:
            if client is None:
                raise RuntimeError(client_error or "视觉模型客户端初始化失败。")

            prompt = build_page_vision_prompt(page)
            markdown = client.analyze_image(image_path=image_path, prompt=prompt).strip()

            if not markdown:
                markdown = _failure_markdown(page, image_path, "视觉模型返回了空内容。")
        except Exception as exc:
            markdown = _failure_markdown(page, image_path, str(exc))

        _save_page_markdown(output_dir, page, markdown)
        results.append(
            {
                "page": page,
                "image_path": image_path,
                "markdown": markdown,
                "skipped": False,
            }
        )

    return results


def analyze_single_page_image(
    page_image: dict,
    output_dir: Path,
    vision_client: VisionLLMClient,
    skip_existing: bool = True,
) -> dict:
    """Analyze one rendered page image and save its Markdown result."""
    output_dir.mkdir(parents=True, exist_ok=True)

    page = page_image.get("page")
    image_path = page_image.get("image_path", "")
    output_path = _page_markdown_path(output_dir, page)

    if skip_existing and output_path.exists():
        markdown = output_path.read_text(encoding="utf-8")
        if not _is_failure_markdown(markdown):
            return {
                "page": page,
                "image_path": image_path,
                "markdown": markdown,
                "skipped": True,
            }

    try:
        prompt = build_page_vision_prompt(page)
        markdown = vision_client.analyze_image(
            image_path=image_path,
            prompt=prompt,
        ).strip()

        if not markdown:
            markdown = _failure_markdown(page, image_path, "视觉模型返回了空内容。")
    except Exception as exc:
        markdown = _failure_markdown(page, image_path, str(exc))

    _save_page_markdown(output_dir, page, markdown)
    return {
        "page": page,
        "image_path": image_path,
        "markdown": markdown,
        "skipped": False,
    }


def _save_page_markdown(output_dir: Path, page: int, markdown: str) -> Path:
    output_path = _page_markdown_path(output_dir, page)
    output_path.write_text(markdown, encoding="utf-8")
    return output_path


def _page_markdown_path(output_dir: Path, page: int) -> Path:
    return output_dir / f"page_{page:03d}.md"


def _resolve_pdf_stem(page_images: List[dict], pdf_stem: Optional[str]) -> str:
    if pdf_stem:
        return _safe_dir_name(pdf_stem)

    first_image_path = page_images[0].get("image_path", "")
    inferred_name = Path(first_image_path).parent.name if first_image_path else "pdf_pages"
    return _safe_dir_name(inferred_name)


def _failure_markdown(page: int, image_path: str, error: str) -> str:
    return f"""## 第 {page} 页说明

该页视觉分析失败。

- 图片路径：`{image_path}`
- 失败原因：{error}
"""


def _is_failure_markdown(markdown: str) -> bool:
    return "视觉分析失败" in markdown or "Vision LLM request failed" in markdown


def _safe_dir_name(name: str) -> str:
    cleaned = "".join(char for char in name if char not in r'<>:"/\|?*').strip()
    return cleaned or "pdf_pages"
