import numpy as np
from sentence_transformers import SentenceTransformer

def load_model(name:str = "all-MiniLm-L6-v2") -> SentenceTransformer:
    """
    Load a sentence transformer model for embedding text.
    
    Args:
        name (str): The name of the pre-trained model to load. Default is "all-MiniLm-L6-v2".
        
    Returns:
        SentenceTransformer: The loaded sentence transformer model.
    """
    model = SentenceTransformer(name)
    return model

def embed_texts(texts: list[str], model: SentenceTransformer) -> np.ndarray:
    """
    Embed a list of texts using the provided sentence transformer model.
    
    Args:
        texts (list[str]): A list of texts to embed.
        model (SentenceTransformer): The sentence transformer model to use for embedding.
        
    Returns:
        np.ndarray: An array of embeddings corresponding to the input texts.
    """
    embeddings = model.encode(texts, convert_to_numpy=True)
    return embeddings