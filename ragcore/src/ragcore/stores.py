"""Vector stores: remember chunks, find similar ones.

All stores fulfill BaseVectorStore, so backends are interchangeable.
"""
from abc import ABC, abstractmethod

import numpy as np

from ragcore.models import Chunk, SearchResult


class BaseVectorStore(ABC):
    """The job description: add chunks with embeddings, search by vector."""

    @abstractmethod
    def add(self, chunks: list[Chunk]) -> None:
        """Store chunks. Every chunk must already have an embedding."""
        ...

    @abstractmethod
    def search(self, query_vec: np.ndarray, k: int = 5) -> list[SearchResult]:
        """Return the k most similar chunks, best first."""
        ...


class InMemoryStore(BaseVectorStore):
    """Numpy-backed store. Phase 1's search(), now with a contract and guards."""

    def __init__(self, dim: int):
        self._dim = dim
        self._chunks: list[Chunk] = []
        self._vectors: np.ndarray | None = None   # built lazily on first add

    def add(self, chunks: list[Chunk]) -> None:
        new_vecs = []
        for c in chunks:
            if c.embedding is None:
                raise ValueError(f"Chunk {c.id} has no embedding — embed before adding.")
            if c.embedding.shape != (self._dim,):
                raise ValueError(
                    f"Chunk {c.id}: embedding dim {c.embedding.shape} != store dim ({self._dim},). "
                    "Did you switch embedding models without re-embedding?"
                )
            new_vecs.append(c.embedding)
        self._chunks.extend(chunks)
        stacked = np.array(new_vecs)
        self._vectors = stacked if self._vectors is None else np.vstack([self._vectors, stacked])

    def search(self, query_vec: np.ndarray, k: int = 5) -> list[SearchResult]:
        if self._vectors is None:
            return []
        q = query_vec / np.linalg.norm(query_vec)
        v = self._vectors / np.linalg.norm(self._vectors, axis=1, keepdims=True)
        scores = v @ q
        top = np.argsort(scores)[::-1][:k]
        return [SearchResult(chunk=self._chunks[i], score=float(scores[i])) for i in top]