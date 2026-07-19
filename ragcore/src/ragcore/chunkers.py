"""Chunker: Document -> list[Chunk].
All chunker fulfill BaseChunker, so strategies are interchangebale."""

from abc import ABC, abstractmethod
from ragcore.models import Chunk, Document


class BaseChunker(ABC):
    """The job description every chunker must fulfill."""
    
    @abstractmethod
    def chunk(self, document: Document) -> list[Chunk]:
        """Split a document's pages into chunks with citation metadata."""
        ...

class FixedSizeChunker(BaseChunker):
    """ Fixed-size chunks with overlap, cut at word bounderies ( Phase 1logic). """
    def __init__(self, chunk_size: int = 1000, overlap: int = 200, min_chunk_size: int = 50):
        if overlap >= chunk_size:
            raise ValueError("Overlap must be smaller than chunk size.")
        self.chunk_size = chunk_size
        self.overlap = overlap
        self.min_chunk_size = min_chunk_size
        
    def chunk(self, document: Document) -> list[Chunk]:
        chunks: list[Chunk] = []
        for page in document.pages:
            text = page.text
            start = 0
            while start < len(text):
                end = start + self.chunk_size
                if end < len(text):
                    # Don't cut a word in half: extend to the next space (if not at text end)
                    next_space = text.find(" ", end)
                    if next_space != -1:
                        end = next_space
                chunk_text = text[start:end].strip()
                if len(chunk_text) >= self.min_chunk_size:
                    chunks.append(Chunk(
                        id=f"{document.id}:p{page.number}:c{len(chunks)}",
                        doc_id=document.id,
                        text=chunk_text,
                        page=page.number,
                    ))
                start = end - self.overlap
                
        return chunks