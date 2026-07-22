"""RAGPipeline: wires the stages together. The public face of ragcore."""
from ragcore.chunkers import BaseChunker
from ragcore.embedders import BaseEmbedder
from ragcore.llms import BaseLLM
from ragcore.loaders import BaseLoader
from ragcore.models import Answer, Citation, Document
from ragcore.prompts import build_prompt
from ragcore.stores import BaseVectorStore


class RAGPipeline:
    """Ingest documents, answer questions with citations."""

    def __init__(
        self,
        loader: BaseLoader,
        chunker: BaseChunker,
        embedder: BaseEmbedder,
        store: BaseVectorStore,
        llm: BaseLLM,
        min_score: float = 0.35,
        top_k: int = 5,
    ):
        self.loader = loader
        self.chunker = chunker
        self.embedder = embedder
        self.store = store
        self.llm = llm
        self.min_score = min_score
        self.top_k = top_k

    def ingest(self, path: str) -> Document:
        """Load -> chunk -> embed -> store. Returns the ingested Document."""
        document = self.loader.load(path)
        chunks = self.chunker.chunk(document)

        vectors = self.embedder.embed([c.text for c in chunks])
        for chunk, vector in zip(chunks, vectors):
            chunk.embedding = vector

        self.store.add(chunks)
        return document

    def ask(self, question: str) -> Answer:
        """Embed question -> retrieve -> gate -> generate -> Answer with citations."""
        query_vec = self.embedder.embed([question])[0]
        results = self.store.search(query_vec, k=self.top_k)

        if not results or results[0].score < self.min_score:
            return Answer(
                text="Not found in the provided papers (retrieval confidence too low).",
                citations=[],
            )

        text = self.llm.generate(build_prompt(question, results))
        citations = [
            Citation(
                chunk_id=r.chunk.id,
                doc_id=r.chunk.doc_id,
                page=r.chunk.page,
                score=r.score,
                snippet=r.chunk.text[:200],
            )
            for r in results
        ]
        return Answer(text=text, citations=citations)
    
def default_pipeline(**kwargs) -> RAGPipeline:
    """The batteries-included setup: PDF + fixed chunks + local embeddings + memory + Gemini."""
    from ragcore.chunkers import FixedSizeChunker
    from ragcore.embedders import LocalEmbedder
    from ragcore.llms import GeminiLLM
    from ragcore.loaders import PDFLoader
    from ragcore.stores import InMemoryStore

    embedder = LocalEmbedder()
    return RAGPipeline(
        loader=PDFLoader(),
        chunker=FixedSizeChunker(),
        embedder=embedder,
        store=InMemoryStore(dim=embedder.dim),   # dim wired automatically — no mismatch possible
        llm=GeminiLLM(),
        **kwargs,
    )