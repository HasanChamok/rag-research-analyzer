import numpy as np
import pytest

from ragcore.embedders import FakeEmbedder
from ragcore.models import Chunk
from ragcore.stores import InMemoryStore


@pytest.fixture
def embedder():
    return FakeEmbedder(dim=8)


def make_chunks(embedder, texts):
    chunks = [Chunk(id=f"d:p1:c{i}", doc_id="d", text=t, page=1) for i, t in enumerate(texts)]
    vecs = embedder.embed(texts)
    for c, v in zip(chunks, vecs):
        c.embedding = v
    return chunks


def test_search_finds_identical_text_first(embedder):
    store = InMemoryStore(dim=8)
    store.add(make_chunks(embedder, ["alpha", "beta", "gamma"]))
    q = embedder.embed(["beta"])[0]          # identical text → identical fake vector
    results = store.search(q, k=3)
    assert results[0].chunk.text == "beta"
    assert results[0].score == pytest.approx(1.0)


def test_unembedded_chunk_rejected(embedder):
    store = InMemoryStore(dim=8)
    with pytest.raises(ValueError, match="no embedding"):
        store.add([Chunk(id="d:p1:c0", doc_id="d", text="bare", page=1)])


def test_dimension_mismatch_rejected(embedder):
    store = InMemoryStore(dim=16)            # store expects 16, fake makes 8
    with pytest.raises(ValueError, match="dim"):
        store.add(make_chunks(embedder, ["alpha"]))


def test_add_twice_searches_across_both(embedder):
    store = InMemoryStore(dim=8)
    store.add(make_chunks(embedder, ["first batch"]))
    store.add(make_chunks(embedder, ["second batch"]))
    q = embedder.embed(["second batch"])[0]
    assert store.search(q, k=1)[0].chunk.text == "second batch"


def test_empty_store_returns_empty():
    assert InMemoryStore(dim=8).search(np.ones(8)) == []