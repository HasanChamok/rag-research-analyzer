import pytest
from fastapi.testclient import TestClient
from app.deps import get_pipeline
from app.main import app
from ragcore.chunkers import FixedSizeChunker
from ragcore.embedders import FakeEmbedder
from ragcore.llms import EchoLLM
from ragcore.loaders import BaseLoader
from ragcore.models import Document, Page
from ragcore.pipeline import RAGPipeline
from ragcore.stores import InMemoryStore


class FakeLoader(BaseLoader):
    def load(self, path: str) -> Document:
        return Document(
            id="fakedoc", title="Fake", source_path=path,
            pages=[Page(number=1, text="Attention uses h = 8 parallel heads. " * 40)],
        )


@pytest.fixture
def client():
    embedder = FakeEmbedder(dim=8)
    fake_pipeline = RAGPipeline(
        loader=FakeLoader(),
        chunker=FixedSizeChunker(chunk_size=300, overlap=50, min_chunk_size=20),
        embedder=embedder,
        store=InMemoryStore(dim=embedder.dim),
        llm=EchoLLM(canned="It uses 8 heads (p. 1)."),
    )
    fake_pipeline.ingest("fake.pdf")
    app.dependency_overrides[get_pipeline] = lambda: fake_pipeline
    yield TestClient(app)
    app.dependency_overrides.clear()


def test_health(client):
    assert client.get("/health").json() == {"status": "ok"}


def test_ask_returns_answer(client):
    r = client.post("/ask", json={"question": "How many heads?", "top_k": 3})
    assert r.status_code == 200
    body = r.json()
    assert body["answer"] == "It uses 8 heads (p. 1)."
    assert body["is_refusal"] is False


def test_ask_rejects_short_question(client):
    r = client.post("/ask", json={"question": "hi"})
    assert r.status_code == 422        # Pydantic min_length=3 enforced


def test_ask_rejects_huge_top_k(client):
    r = client.post("/ask", json={"question": "valid question", "top_k": 9999})
    assert r.status_code == 422        # le=20 enforced


def test_upload_rejects_non_pdf(client):
    r = client.post("/papers", files={"file": ("notes.txt", b"hello", "text/plain")})
    assert r.status_code == 400