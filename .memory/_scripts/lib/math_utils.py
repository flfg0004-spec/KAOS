"""Math utilities compartidas entre módulos de procesamiento semántico."""

import numpy as np


def cosine_similarity_matrix(embeddings: list[list[float]]) -> np.ndarray:
    """Matriz de similitud coseno NxN usando BLAS-level matmul."""
    embeds = np.array(embeddings, dtype=np.float64)
    norms = np.linalg.norm(embeds, axis=1, keepdims=True)
    norms[norms == 0] = 1e-10
    return (embeds @ embeds.T) / (norms @ norms.T)


def triu_pairs(n: int):
    """Índices del triángulo superior de una matriz NxN (k=1)."""
    return np.triu_indices(n, k=1)
