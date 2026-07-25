"""Paper management endpoints."""
import tempfile
from pathlib import Path

from fastapi import APIRouter, Depends, HTTPException, UploadFile, BackgroundTasks
from ragcore.pipeline import RAGPipeline

from app.deps import get_pipeline
from app.schemas import PaperOut

router = APIRouter(prefix="/papers", tags=["papers"])


@router.get("", response_model=list[PaperOut])
def list_papers(pipeline: RAGPipeline = Depends(get_pipeline)):
    return [PaperOut(id=doc_id) for doc_id in pipeline.store.list_documents()]


@router.post("", status_code=202)
async def upload_paper(
    file: UploadFile,
    background: BackgroundTasks,
    pipeline: RAGPipeline = Depends(get_pipeline),
):
    if not file.filename or not file.filename.lower().endswith(".pdf"):
        raise HTTPException(status_code=400, detail="Only PDF files are accepted.")

    contents = await file.read()
    if len(contents) > 20 * 1024 * 1024:
        raise HTTPException(status_code=413, detail="File too large (max 20MB).")

    def ingest_in_background(data: bytes, filename: str):
        import tempfile
        from pathlib import Path
        with tempfile.TemporaryDirectory() as tmpdir:
            path = Path(tmpdir) / filename
            path.write_bytes(data)
            pipeline.ingest(str(path))

    background.add_task(ingest_in_background, contents, file.filename)
    return {"status": "processing", "filename": file.filename}


@router.delete("/{doc_id}", status_code=204)
def delete_paper(doc_id: str, pipeline: RAGPipeline = Depends(get_pipeline)):
    if doc_id not in pipeline.store.list_documents():
        raise HTTPException(status_code=404, detail=f"No paper with id '{doc_id}'.")
    pipeline.store.delete_document(doc_id)