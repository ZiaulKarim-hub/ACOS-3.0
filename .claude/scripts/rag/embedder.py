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


# Max inputs per /api/embed request. Large files produce many chunks; sending them
# all at once exceeds Ollama's request limit and 400s, failing the whole file. We
# sub-batch, and on any sub-batch failure fall back to per-item embedding (a single
# ~2KB chunk always fits), so one oversized file can no longer poison the index.
BATCH_SIZE = 16


def embed_texts(texts: list[str]) -> list[list[float]]:
    """Embed multiple texts. Sub-batches, with per-item fallback on batch failure.

    Returns a list of vectors aligned 1:1 with `texts`. Raises EmbeddingError only
    if an individual text genuinely cannot be embedded.
    """
    if not texts:
        return []

    out: list[list[float]] = []
    for i in range(0, len(texts), BATCH_SIZE):
        sub = texts[i:i + BATCH_SIZE]
        try:
            resp = requests.post(
                f"{OLLAMA_BASE}/api/embed",
                json={"model": MODEL, "input": sub},
                timeout=120,
            )
            resp.raise_for_status()
            data = resp.json()
            embeddings = data.get("embeddings")
            if not embeddings or len(embeddings) != len(sub):
                raise EmbeddingError(
                    f"Expected {len(sub)} embeddings, got {len(embeddings) if embeddings else 0}"
                )
            out.extend(embeddings)
        except (requests.RequestException, EmbeddingError, KeyError, ValueError):
            # Batch-level failure (e.g. too many inputs/tokens) — retry one at a time.
            for text in sub:
                out.append(embed_single(text))
    return out
