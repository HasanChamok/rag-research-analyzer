"""Embedders: text -> vectors.

All embedders fulfill BaseEmbedder, so models (and fakes) are interchangeable.
"""
from abc import ABC, abstractmethod

import numpy as np


class BaseEmbedder(ABC):
    """The job description: turn texts into a (n_texts, dim) matrix."""

    @property
    @abstractmethod
    def dim(self) -> int:
        """Vector dimensionality this embedder produces."""
        ...

    @abstractmethod
    def embed(self, texts: list[str]) -> np.ndarray:
        """Return one vector per text; shape (len(texts), self.dim)."""
        ...


class LocalEmbedder(BaseEmbedder):
    """sentence-transformers on local CPU. Our Phase 1 embedder, with a contract."""

    def __init__(self, model_name: str = "all-MiniLM-L6-v2"):
        # Import here, not at module top: tests that only use FakeEmbedder
        # never pay the torch/sentence-transformers import cost.
        from sentence_transformers import SentenceTransformer
        self._model = SentenceTransformer(model_name)

    @property
    def dim(self) -> int:
        return self._model.get_embedding_dimension()

    def embed(self, texts: list[str]) -> np.ndarray:
        return np.array(self._model.encode(texts, show_progress_bar=False))


class FakeEmbedder(BaseEmbedder):
    """Deterministic fake for tests: same text -> same vector, instantly.

    Not semantically meaningful -- just shaped and behaved like the real thing.
    """

    def __init__(self, dim: int = 8):
        self._dim = dim

    @property
    def dim(self) -> int:
        return self._dim

    def embed(self, texts: list[str]) -> np.ndarray:
        vectors = []
        for text in texts:
            rng = np.random.default_rng(seed=abs(hash(text)) % (2**32))
            vectors.append(rng.random(self._dim))
        return np.array(vectors)
    

class GeminiEmbedder(BaseEmbedder):
    """Google Gemini embedding API — no local model, minimal RAM."""

    def __init__(self, model: str = "gemini-embedding-001", api_key: str | None = None):
        import os
        from google import genai

        key = api_key or os.getenv("GOOGLE_API_KEY")
        if not key:
            raise ValueError("GOOGLE_API_KEY not set for GeminiEmbedder.")
        self._client = genai.Client(api_key=key)
        self._model = model
        self._dim = 768   # gemini-embedding-001 default output dimension

    @property
    def dim(self) -> int:
        return self._dim

    def embed(self, texts: list[str]) -> np.ndarray:
        result = self._client.models.embed_content(
            model=self._model,
            contents=texts,
            config={"output_dimensionality": self._dim},
        )
        return np.array([e.values for e in result.embeddings])