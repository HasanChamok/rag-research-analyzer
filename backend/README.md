# Backend — RAG Research Paper Analyzer API

FastAPI service wrapping the `ragcore` engine. Upload PDFs, ask questions, get cited answers.

## Run locally

```bash
cd backend
pip install -r requirements.txt
uvicorn app.main:app --reload
```

Then open http://localhost:8000/docs

## Environment

Requires a `.env` at the project root with:

## Endpoints

| Method | Path | Purpose |
|---|---|---|
| GET | `/health` | Liveness check |
| GET | `/papers` | List ingested papers |
| POST | `/papers` | Upload a PDF (async ingestion, returns 202) |
| DELETE | `/papers/{id}` | Remove a paper and its chunks |
| POST | `/ask` | Ask a question, get a cited answer |

## Tests

```bash
cd backend
pytest tests
```