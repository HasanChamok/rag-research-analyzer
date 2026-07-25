"""Shared dependencies. The pipeline is built once and reused."""
from functools import lru_cache

from dotenv import load_dotenv
from ragcore.pipeline import RAGPipeline, default_pipeline

load_dotenv()


@lru_cache(maxsize=1)
def get_pipeline() -> RAGPipeline:
    """Build the pipeline once per process (the embedding model is expensive)."""
    return default_pipeline(use_cloud=True)