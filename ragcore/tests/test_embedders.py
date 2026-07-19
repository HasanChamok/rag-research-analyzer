import numpy as np

from ragcore.embedders import BaseEmbedder, FakeEmbedder


def test_fake_embedder_shape():
    emb = FakeEmbedder(dim=8)
    out = emb.embed(["hello", "world", "again"])
    assert out.shape == (3, 8)


def test_fake_embedder_deterministic():
    emb = FakeEmbedder()
    a = emb.embed(["same text"])
    b = emb.embed(["same text"])
    assert np.array_equal(a, b)


def test_fake_embedder_distinguishes_texts():
    emb = FakeEmbedder()
    out = emb.embed(["one text", "another text"])
    assert not np.array_equal(out[0], out[1])


def test_fake_fulfills_contract():
    assert isinstance(FakeEmbedder(), BaseEmbedder)