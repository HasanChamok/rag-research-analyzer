import os

import pytest
from dotenv import load_dotenv

from ragcore.embedders import FakeEmbedder
from ragcore.models import Chunk

load_dotenv()

pytestmark = pytest.mark.integration

needs_creds = pytest.mark.skipif(
    not (os.getenv("SUPABASE_URL") and os.getenv("SUPABASE_KEY")),
    reason="Supabase credentials not set",
)


@needs_creds
def test_supabase_roundtrip():
    from ragcore.stores import SupabaseStore

    embedder = FakeEmbedder(dim=384)      # match the DB column dimension
    store = SupabaseStore(dim=384)
    doc_id = "pytest-temp-doc"

    try:
        texts = ["alpha chunk", "beta chunk"]
        chunks = [
            Chunk(id=f"{doc_id}:p1:c{i}", doc_id=doc_id, text=t, page=1)
            for i, t in enumerate(texts)
        ]
        for c, v in zip(chunks, embedder.embed(texts)):
            c.embedding = v

        store.add(chunks)
        assert doc_id in store.list_documents()

        results = store.search(embedder.embed(["alpha chunk"])[0], k=2)
        assert results[0].chunk.text == "alpha chunk"
        assert results[0].score > 0.9
    finally:
        store.delete_document(doc_id)      # always clean up, even on failure
        assert doc_id not in store.list_documents()