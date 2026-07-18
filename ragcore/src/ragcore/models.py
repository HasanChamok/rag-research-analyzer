""" core data models for ragcore 
These are the noun data models that are used to represent the core concepts of ragcore. 
They are used to define the structure of the data and how it is stored in the database."""


from dataclasses import dataclass, field
import numpy as np

@dataclass
class Document:
    """A document is a piece of text that can be used as a source of information for the RAG model.
    It can be a paragraph, an article, a book, or any other piece of text that can be used to answer questions.
    """
    id: str
    title: str
    source_path: str
    metadata: dict = field(default_factory=dict)
    
@dataclass
class Chunk:
    """A slice of document, small enough to be processed by the RAG model. It can be a sentence, a paragraph, 
    or any other piece of text that can be used to answer questions."""
    id: str
    doc_id: str
    text: str
    page: int
    embedding: np.ndarray | None = None
    
@dataclass
class Citation:
    """Evidence backing an answer: which chunk, which page, how relevant."""
    chunk_id: str
    doc_id: str
    page: int
    score: float
    snippet: str


@dataclass
class Answer:
    """The final product: an answer with its supporting evidence."""
    text: str
    citations: list[Citation] = field(default_factory=list)

    @property
    def is_refusal(self) -> bool:
        return len(self.citations) == 0