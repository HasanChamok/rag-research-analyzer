"""Request and response shapes. FastAPI validates against these automatically."""
from pydantic import BaseModel, Field


class AskRequest(BaseModel):
    question: str = Field(min_length=3, max_length=1000)
    top_k: int = Field(default=5, ge=1, le=20)


class CitationOut(BaseModel):
    doc_id: str
    page: int
    score: float
    snippet: str


class AnswerOut(BaseModel):
    answer: str
    is_refusal: bool
    citations: list[CitationOut]


class PaperOut(BaseModel):
    id: str
    chunks: int | None = None