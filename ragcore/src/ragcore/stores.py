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
        
    @abstractmethod
    def list_documents(self) -> list[str]:
        """Return the doc_ids currently stored."""
        ...

    @abstractmethod
    def delete_document(self, doc_id: str) -> None:
        """Remove a document and all its chunks."""
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
    
    def list_documents(self) -> list[str]:
        return sorted({c.doc_id for c in self._chunks})

    def delete_document(self, doc_id: str) -> None:
        keep = [i for i, c in enumerate(self._chunks) if c.doc_id != doc_id]
        self._chunks = [self._chunks[i] for i in keep]
        self._vectors = self._vectors[keep] if keep and self._vectors is not None else None
    
    
class SupabaseStore(BaseVectorStore):
    """Postgres + pgvector store. Persists across restarts."""

    def __init__(self, dim: int, url: str | None = None, key: str | None = None):
        import os
        from supabase import create_client

        url = url or os.getenv("SUPABASE_URL")
        key = key or os.getenv("SUPABASE_KEY")
        if not url or not key:
            raise ValueError(
                "Supabase credentials missing. Set SUPABASE_URL and SUPABASE_KEY "
                "(copy .env.example to .env)."
            )
        self._dim = dim
        self._client = create_client(url, key)

    def add(self, chunks: list[Chunk]) -> None:
        if not chunks:
            return

        rows = []
        for c in chunks:
            if c.embedding is None:
                raise ValueError(f"Chunk {c.id} has no embedding — embed before adding.")
            if c.embedding.shape != (self._dim,):
                raise ValueError(
                    f"Chunk {c.id}: embedding dim {c.embedding.shape} != store dim ({self._dim},)."
                )
            rows.append({
                "id": c.id,
                "doc_id": c.doc_id,
                "text": c.text,
                "page": c.page,
                "embedding": c.embedding.tolist(),
            })

        # Parent row must exist first (foreign key constraint)
        doc_ids = {c.doc_id for c in chunks}
        self._client.table("documents").upsert(
            [{"id": d, "title": d} for d in doc_ids]
        ).execute()

        self._client.table("chunks").upsert(rows).execute()

    def search(self, query_vec: np.ndarray, k: int = 5) -> list[SearchResult]:
        response = self._client.rpc(
            "match_chunks",
            {"query_embedding": query_vec.tolist(), "match_count": k},
        ).execute()

        return [
            SearchResult(
                chunk=Chunk(
                    id=row["id"], doc_id=row["doc_id"],
                    text=row["text"], page=row["page"],
                ),
                score=float(row["score"]),
            )
            for row in response.data
        ]
        
    def list_documents(self) -> list[str]:
        response = self._client.table("documents").select("id").execute()
        return sorted(row["id"] for row in response.data)

    def delete_document(self, doc_id: str) -> None:
        self._client.table("documents").delete().eq("id", doc_id).execute()