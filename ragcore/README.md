# ragcore

A reusable RAG (Retrieval-Augmented Generation) engine for document analysis.
Ingest PDFs, ask questions, get answers grounded in the source with page citations.

## Install
## Install

```bash
# core
pip install "git+https://github.com/HasanChamok/rag-research-analyzer.git#subdirectory=ragcore"

# with local embeddings (pulls PyTorch, ~2GB)
pip install "ragcore[local] @ git+https://github.com/HasanChamok/rag-research-analyzer.git#subdirectory=ragcore"
```

## Quick start

```python
from dotenv import load_dotenv
from ragcore import default_pipeline

load_dotenv()                      # needs GOOGLE_API_KEY

pipeline = default_pipeline()
pipeline.ingest("paper.pdf")

answer = pipeline.ask("How many attention heads does the model use?")
print(answer.text)                 # "The model employs h = 8 ... (p. 5)"
for c in answer.citations:
    print(c.doc_id, c.page, c.score)
```

## Architecture

Every stage sits behind an abstract base class, so components are swappable:

| Stage | Contract | Implementations |
|---|---|---|
| Load | `BaseLoader` | `PDFLoader` |
| Chunk | `BaseChunker` | `FixedSizeChunker` |
| Embed | `BaseEmbedder` | `LocalEmbedder`, `FakeEmbedder` |
| Store | `BaseVectorStore` | `InMemoryStore` |
| Generate | `BaseLLM` | `GeminiLLM`, `EchoLLM` |

Custom wiring:

```python
from ragcore import RAGPipeline, PDFLoader, FixedSizeChunker, LocalEmbedder, InMemoryStore, GeminiLLM

embedder = LocalEmbedder("all-mpnet-base-v2")
pipeline = RAGPipeline(
    loader=PDFLoader(),
    chunker=FixedSizeChunker(chunk_size=1500, overlap=300),
    embedder=embedder,
    store=InMemoryStore(dim=embedder.dim),
    llm=GeminiLLM(),
    min_score=0.4,
)
```

## Configuration

| Env var | Purpose | Default |
|---|---|---|
| `GOOGLE_API_KEY` | Gemini API key (required) | — |
| `GEMINI_MODEL` | Model name | `gemini-3-flash-preview` |

## Known limitations

- Fixed-size chunking is structure-blind (no section awareness)
- Retrieval can miss on vocabulary mismatch between question and paper wording
- `InMemoryStore` does not persist across restarts

## Development

```bash
pip install -e ./ragcore
pytest ./ragcore
```