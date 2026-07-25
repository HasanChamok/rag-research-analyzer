"""Question-answering endpoint."""
from fastapi import APIRouter, Depends
from ragcore.pipeline import RAGPipeline

from app.deps import get_pipeline
from app.schemas import AnswerOut, AskRequest, CitationOut

router = APIRouter(tags=["chat"])


@router.post("/ask", response_model=AnswerOut)
def ask(request: AskRequest, pipeline: RAGPipeline = Depends(get_pipeline)):
    pipeline.top_k = request.top_k
    answer = pipeline.ask(request.question)

    return AnswerOut(
        answer=answer.text,
        is_refusal=answer.is_refusal,
        citations=[
            CitationOut(doc_id=c.doc_id, page=c.page, score=c.score, snippet=c.snippet)
            for c in answer.citations
        ],
    )