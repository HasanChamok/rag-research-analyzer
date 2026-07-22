import numpy as np
import pytest

from ragcore.chunkers import FixedSizeChunker
from ragcore.embedders import FakeEmbedder
from ragcore.llms import EchoLLM
from ragcore.loaders import BaseLoader
from ragcore.models import Document, Page
from ragcore.pipeline import RAGPipeline
from ragcore.stores import InMemoryStore


class FakeLoader(BaseLoader):
    """Returns a canned Document — no PDF, no disk."""
    def load(self, path: str) -> Document:
        return Document(
            id="fakedoc", title="Fake", source_path=path,
            pages=[Page(number=1, text="Attention uses h = 8 parallel heads. " * 40)],
        )


@pytest.fixture
def pipeline():
    embedder = FakeEmbedder(dim=8)
    return RAGPipeline(
        loader=FakeLoader(),
        chunker=FixedSizeChunker(chunk_size=300, overlap=50, min_chunk_size=20),
        embedder=embedder,
        store=InMemoryStore(dim=embedder.dim),
        llm=EchoLLM(canned="It uses 8 heads (p. 1)."),
    )


def test_ingest_then_ask_returns_cited_answer(pipeline):
    doc = pipeline.ingest("whatever.pdf")
    assert doc.id == "fakedoc"

    answer = pipeline.ask("Attention uses h = 8 parallel heads.")  # identical text → score 1.0
    assert answer.text == "It uses 8 heads (p. 1)."
    assert not answer.is_refusal
    assert answer.citations[0].page == 1
    assert answer.citations[0].doc_id == "fakedoc"


def test_low_confidence_is_refused_without_calling_llm(pipeline):
    pipeline.ingest("whatever.pdf")
    pipeline.min_score = 1.5                      # impossible threshold → forces refusal
    answer = pipeline.ask("unrelated question")
    assert answer.is_refusal
    assert pipeline.llm.last_prompt is None       # the spy proves no LLM call happened


def test_ask_before_ingest_refuses(pipeline):
    assert pipeline.ask("anything").is_refusal