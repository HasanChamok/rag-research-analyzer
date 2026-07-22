"""LLM wrappers: prompt in, text out. Nothing else.

Prompt construction lives in prompts.py so every LLM shares the same rules.
"""
import os
from abc import ABC, abstractmethod


class BaseLLM(ABC):
    """The job description: turn a prompt into generated text."""

    @abstractmethod
    def generate(self, prompt: str) -> str:
        ...


class GeminiLLM(BaseLLM):
    """Google Gemini via the free tier."""

    def __init__(self, api_key: str | None = None, model: str | None = None):
        from google import genai  # lazy: only importers of GeminiLLM pay

        key = api_key or os.getenv("GOOGLE_API_KEY")
        if not key:
            raise ValueError(
                "No API key. Pass api_key= or set GOOGLE_API_KEY "
                "(copy .env.example to .env and fill it in)."
            )
        self._client = genai.Client(api_key=key)
        self._model = model or os.getenv("GEMINI_MODEL", "gemini-3-flash-preview")

    def generate(self, prompt: str) -> str:
        response = self._client.models.generate_content(
            model=self._model,
            contents=prompt,
        )
        return response.text


class EchoLLM(BaseLLM):
    """Test double: returns a canned answer, never touches the network."""

    def __init__(self, canned: str = "Test answer (p. 1)"):
        self.canned = canned
        self.last_prompt: str | None = None

    def generate(self, prompt: str) -> str:
        self.last_prompt = prompt   # lets tests assert what we ASKED the model
        return self.canned