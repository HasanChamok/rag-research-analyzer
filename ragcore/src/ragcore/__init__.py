"""ragcore — a reusable RAG engine for document analysis.

Quick start:
    from ragcore import default_pipeline
    p = default_pipeline()
    p.ingest("paper.pdf")
    print(p.ask("What datasets were used?").text)
"""
from ragcore.chunkers import BaseChunker, FixedSizeChunker
from ragcore.embedders import BaseEmbedder, FakeEmbedder, LocalEmbedder
from ragcore.llms import BaseLLM, EchoLLM, GeminiLLM
from ragcore.loaders import BaseLoader, PDFLoader
from ragcore.models import Answer, Chunk, Citation, Document, Page, SearchResult
from ragcore.pipeline import RAGPipeline, default_pipeline
from ragcore.stores import BaseVectorStore, InMemoryStore

__version__ = "0.1.0"

__all__ = [
    "RAGPipeline", "default_pipeline",
    "Answer", "Chunk", "Citation", "Document", "Page", "SearchResult",
    "BaseLoader", "PDFLoader",
    "BaseChunker", "FixedSizeChunker",
    "BaseEmbedder", "LocalEmbedder", "FakeEmbedder",
    "BaseVectorStore", "InMemoryStore",
    "BaseLLM", "GeminiLLM", "EchoLLM",
]