import pytest

from ragcore.loaders import BaseLoader, PDFLoader


def test_missing_file_raises():
    with pytest.raises(FileNotFoundError):
        PDFLoader().load("no/such/file.pdf")


def test_base_loader_cannot_be_instantiated():
    with pytest.raises(TypeError):
        BaseLoader()


def test_incomplete_loader_cannot_be_instantiated():
    class BrokenLoader(BaseLoader):
        pass  # "forgot" to implement load()

    with pytest.raises(TypeError):
        BrokenLoader()