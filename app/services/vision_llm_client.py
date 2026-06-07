import base64
import mimetypes
import os
from pathlib import Path

from dotenv import load_dotenv
from openai import OpenAI, OpenAIError


class VisionLLMClient:
    """OpenAI-compatible client for multimodal image analysis."""

    def __init__(self, timeout: float = 60.0) -> None:
        load_dotenv()

        self.api_key = os.getenv("VISION_API_KEY")
        self.base_url = os.getenv("VISION_BASE_URL")
        self.model = os.getenv("VISION_MODEL")
        self.api_style = os.getenv("VISION_API_STYLE", "responses").strip().lower()
        self.timeout = timeout

        missing = [
            name
            for name, value in {
                "VISION_API_KEY": self.api_key,
                "VISION_BASE_URL": self.base_url,
                "VISION_MODEL": self.model,
            }.items()
            if not value
        ]
        if missing:
            raise ValueError(f"Missing vision LLM config: {', '.join(missing)}")

        self._client = OpenAI(
            api_key=self.api_key,
            base_url=self.base_url,
            timeout=self.timeout,
        )

    def analyze_image(self, image_path: str, prompt: str) -> str:
        if not prompt.strip():
            raise ValueError("Prompt cannot be empty.")

        data_url = _image_to_data_url(image_path)

        if self.api_style == "chat_completions":
            return self._analyze_image_with_chat_completions(data_url, prompt)

        return self._analyze_image_with_responses(data_url, prompt)

    def _analyze_image_with_responses(self, data_url: str, prompt: str) -> str:
        try:
            response = self._client.responses.create(
                model=self.model,
                input=[
                    {
                        "role": "user",
                        "content": [
                            {
                                "type": "input_image",
                                "image_url": data_url,
                            },
                            {
                                "type": "input_text",
                                "text": prompt,
                            },
                        ],
                    }
                ],
            )
        except OpenAIError as exc:
            raise RuntimeError(f"Vision LLM request failed: {exc}") from exc
        except Exception as exc:
            raise RuntimeError(f"Unexpected vision LLM error: {exc}") from exc

        return _extract_responses_text(response)

    def _analyze_image_with_chat_completions(self, data_url: str, prompt: str) -> str:
        try:
            response = self._client.chat.completions.create(
                model=self.model,
                messages=[
                    {
                        "role": "user",
                        "content": [
                            {
                                "type": "text",
                                "text": prompt,
                            },
                            {
                                "type": "image_url",
                                "image_url": {
                                    "url": data_url,
                                },
                            },
                        ],
                    }
                ],
            )
        except OpenAIError as exc:
            raise RuntimeError(f"Vision LLM request failed: {exc}") from exc
        except Exception as exc:
            raise RuntimeError(f"Unexpected vision LLM error: {exc}") from exc

        content = response.choices[0].message.content
        return content or ""


def _image_to_data_url(image_path: str) -> str:
    path = Path(image_path)
    if not path.exists():
        raise FileNotFoundError(f"Image file not found: {image_path}")
    if not path.is_file():
        raise ValueError(f"Image path is not a file: {image_path}")

    mime_type = mimetypes.guess_type(path.name)[0] or "image/png"
    encoded = base64.b64encode(path.read_bytes()).decode("ascii")
    return f"data:{mime_type};base64,{encoded}"


def _extract_responses_text(response) -> str:
    output_text = getattr(response, "output_text", None)
    if output_text:
        return output_text

    text_parts = []
    for item in getattr(response, "output", []) or []:
        for content in getattr(item, "content", []) or []:
            text = getattr(content, "text", None)
            if text:
                text_parts.append(text)

    return "\n".join(text_parts)
