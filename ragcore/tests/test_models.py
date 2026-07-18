from ragcore.models import Answer, Chunk, Citation


def test_chunk_creation():
    c = Chunk(id="d1:c0", doc_id="d1", text="hello", page=3)
    assert c.page == 3
    assert c.embedding is None


def test_answer_refusal_logic():
    assert Answer(text="Not found.").is_refusal
    cited = Answer(text="h=8 (p.5)", citations=[
        Citation(chunk_id="d1:c17", doc_id="d1", page=5, score=0.55, snippet="...")
    ])
    assert not cited.is_refusal


def test_metadata_not_shared_between_documents():
    from ragcore.models import Document
    a = Document(id="a", title="A", source_path="a.pdf")
    b = Document(id="b", title="B", source_path="b.pdf")
    a.metadata["k"] = "v"
    assert b.metadata == {}   # would FAIL if we'd written metadata: dict = {}