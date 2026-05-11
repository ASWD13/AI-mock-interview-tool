"""Embedding utilities using sentence-transformers (§3, §8.3)."""

import os
os.environ["USE_TF"] = "0"
os.environ["TRANSFORMERS_NO_TF"] = "1"

from typing import List, Optional
from functools import lru_cache


@lru_cache(maxsize=1)
def _get_model():
    """Lazy-load the sentence-transformers model."""
    try:
        from sentence_transformers import SentenceTransformer
        return SentenceTransformer("all-MiniLM-L6-v2")
    except ImportError:
        print("sentence-transformers not installed")
        return None


def generate_embedding(text: str) -> Optional[List[float]]:
    """Generate embedding vector for text using all-MiniLM-L6-v2.

    Args:
        text: Input text to embed

    Returns:
        List of floats (384-dimensional) or None if model unavailable
    """
    model = _get_model()
    if model is None:
        return None

    # Truncate to avoid memory issues
    text = text[:5000]
    embedding = model.encode(text, convert_to_numpy=True)
    return embedding.tolist()


def generate_embeddings_batch(texts: List[str]) -> List[List[float]]:
    """Generate embeddings for a batch of texts.

    Args:
        texts: List of input texts

    Returns:
        List of embedding vectors
    """
    model = _get_model()
    if model is None:
        return [[] for _ in texts]

    # Truncate each text
    texts = [t[:2000] for t in texts]
    embeddings = model.encode(texts, convert_to_numpy=True, show_progress_bar=False)
    return [e.tolist() for e in embeddings]
