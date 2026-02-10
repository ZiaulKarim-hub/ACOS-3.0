"""Ollama embedding client for the ACOS RAG system."""

import requests


class EmbeddingError(Exception):
    """Raised when embedding fails."""


OLLAMA_BASE = "http://localhost:11434"
MODEL = "nomic-embed-text"
EMBED_DIM = 768


def is_ollama_available() -> bool:
    """Check if Ollama is running and the embedding model is available."""
    try:
        resp = requests.get(f"{OLLAMA_BASE}/api/tags", timeout=3)
        if resp.status_code != 200:
            return False
        models = [m["name"] for m in resp.json().get("models", [])]
        return any(MODEL in m for m in models)
    except (requests.ConnectionError, requests.Timeout, KeyError, ValueError):
        return False


def embed_single(text: str) -> list[float]:
    """Embed a single text string. Returns a 768-dim vector."""
    try:
        resp = requests.post(
            f"{OLLAMA_BASE}/api/embed",
            json={"model": MODEL, "input": text},
            timeout=30,
        )
        resp.raise_for_status()
        data = resp.json()
        embeddings = data.get("embeddings")
        if not embeddings or len(embeddings) == 0:
            raise EmbeddingError(f"Empty embedding response: {data}")
        return embeddings[0]
    except requests.RequestException as e:
        raise EmbeddingError(f"Ollama request failed: {e}") from e
    except (KeyError, IndexError, ValueError) as e:
        raise EmbeddingError(f"Unexpected response format: {e}") from e


def embed_texts(texts: list[str]) -> list[list[float]]:
    """Embed multiple texts in a single request (batch). Returns list of vectors."""
    if not texts:
        return []

    try:
        resp = requests.post(
            f"{OLLAMA_BASE}/api/embed",
            json={"model": MODEL, "input": texts},
            timeout=120,
        )
        resp.raise_for_status()
        data = resp.json()
        embeddings = data.get("embeddings")
        if not embeddings or len(embeddings) != len(texts):
            raise EmbeddingError(
                f"Expected {len(texts)} embeddings, got {len(embeddings) if embeddings else 0}"
            )
        return embeddings
    except requests.RequestException as e:
        raise EmbeddingError(f"Ollama batch request failed: {e}") from e
    except (KeyError, ValueError) as e:
        raise EmbeddingError(f"Unexpected response format: {e}") from e
