import pytest

from ragcore.chunkers import BaseChunker, FixedSizeChunker
from ragcore.models import Document, Page


@pytest.fixture
def doc() -> Document:
    """A tiny fake document — no PDF needed, tests run in milliseconds."""
    text = "word " * 500   # 2500 chars of predictable text
    return Document(id="testdoc", title="Test", source_path="fake.pdf",
                    pages=[Page(number=1, text=text), Page(number=2, text=text)])


def test_chunks_have_citation_metadata(doc):
    chunks = FixedSizeChunker().chunk(doc)
    assert all(c.doc_id == "testdoc" for c in chunks)
    assert all(c.page in (1, 2) for c in chunks)
    assert chunks[0].id.startswith("testdoc:p1:")


def test_min_chunk_size_filters_junk(doc):
    chunks = FixedSizeChunker(min_chunk_size=50).chunk(doc)
    assert all(len(c.text) >= 50 for c in chunks)     # the min=2 bug, dead forever


def test_overlap_repeats_text(doc):
    chunks = FixedSizeChunker(chunk_size=1000, overlap=200).chunk(doc)
    tail = chunks[0].text[-50:]
    assert tail in chunks[1].text                      # overlap really overlaps


def test_invalid_config_rejected():
    with pytest.raises(ValueError):
        FixedSizeChunker(chunk_size=100, overlap=100)


def test_incomplete_chunker_cannot_instantiate():
    class Broken(BaseChunker):
        pass
    with pytest.raises(TypeError):
        Broken()