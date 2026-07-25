"""FastAPI application entrypoint."""
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.routers import papers

app = FastAPI(
    title="RAG Research Paper Analyzer",
    description="Upload academic papers, ask questions, get cited answers.",
    version="0.1.0",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000"],   # Phase 6: add the Vercel URL
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(papers.router)


@app.get("/health", tags=["system"])
def health():
    return {"status": "ok"}