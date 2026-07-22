"""Prompt construction. One place, so every LLM shares the same grounding rules."""
from ragcore.models import SearchResult

SYSTEM_RULES = """You are a research assistant analyzing academic papers.

Rules:
- Answer using ONLY the context below.
- Cite the page number for every claim, like (p. 7).
- If the context does not contain the answer, say exactly: "Not found in the provided papers."
- Be precise with numbers, metrics, and dataset names. Never add outside knowledge."""


def build_prompt(question: str, results: list[SearchResult]) -> str:
    context = "\n\n".join(
        f"[{r.chunk.doc_id}, page {r.chunk.page}]\n{r.chunk.text}" for r in results
    )
    return f"{SYSTEM_RULES}\n\nContext:\n{context}\n\nQuestion: {question}\n\nAnswer:"