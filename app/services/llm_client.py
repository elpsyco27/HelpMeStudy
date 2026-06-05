import os

from dotenv import load_dotenv
from openai import OpenAI, OpenAIError


class LLMClient:
    """Small wrapper around an OpenAI-compatible chat completion API."""

    def __init__(self, timeout: float = 60.0) -> None:
        load_dotenv()

        self.api_key = os.getenv("LLM_API_KEY")
        self.base_url = os.getenv("LLM_BASE_URL")
        self.model = os.getenv("LLM_MODEL")
        self.timeout = timeout

        missing = [
            name
            for name, value in {
                "LLM_API_KEY": self.api_key,
                "LLM_BASE_URL": self.base_url,
                "LLM_MODEL": self.model,
            }.items()
            if not value
        ]
        if missing:
            raise ValueError(f"Missing LLM config: {', '.join(missing)}")

        self._client = OpenAI(
            api_key=self.api_key,
            base_url=self.base_url,
            timeout=self.timeout,
        )

    def generate(self, prompt: str) -> str:
        if not prompt.strip():
            raise ValueError("Prompt cannot be empty.")

        try:
            response = self._client.chat.completions.create(
                model=self.model,
                messages=[
                    {
                        "role": "user",
                        "content": prompt,
                    }
                ],
            )
        except OpenAIError as exc:
            raise RuntimeError(f"LLM request failed: {exc}") from exc
        except Exception as exc:
            raise RuntimeError(f"Unexpected LLM error: {exc}") from exc

        content = response.choices[0].message.content
        return content or ""
