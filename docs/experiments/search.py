"""Stage 4: cosine similarity search over a vector matrix"""

import numpy as np

def search(q_vec: np.ndarray, vectors: np.ndarray, chunks:list[dict], k: int = 3) -> list[dict]:
    """
    Perform a cosine similarity search over a vector matrix.

    Args:
        q_vec (np.ndarray): The query vector.
        vectors (np.ndarray): The matrix of vectors to search against.
        chunks (list[dict]): The list of chunks corresponding to the vectors.
        k (int): The number of top results to return. Default is 3.

    Returns:
        list[dict]: A list of the top k chunks with their similarity scores.
    """
    # Normalize the query vector
    q_norm = q_vec / np.linalg.norm(q_vec)

    # Normalize the vectors
    v_norm = vectors / np.linalg.norm(vectors, axis=1, keepdims=True)

    scores = v_norm @ q_norm  # Compute cosine similarity scores
    
    # Get the indices of the top k scores
    top_idx= np.argsort(scores)[::-1][:k]

    return [{**chunks[i], "score": float(scores[i])} for i in top_idx]