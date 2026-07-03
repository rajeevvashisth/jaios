import hashlib
import math

from app.config import get_settings
from app.models.knowledge import EMBEDDING_DIM


def embed_text(text: str) -> list[float]:
    """Embed text for storage/search in ``knowledge_chunks.embedding``.

    Uses OpenAI's embedding API when ``OPENAI_API_KEY`` is configured.
    Without it, falls back to a deterministic hash-based vector so the
    ingestion/retrieval pipeline is runnable end-to-end on a machine with no
    API keys at all — it is NOT semantically meaningful and should be
    replaced by a real provider before relying on search quality.
    """
    settings = get_settings()
    if settings.openai_api_key:
        from openai import OpenAI

        client = OpenAI(api_key=settings.openai_api_key)
        resp = client.embeddings.create(model="text-embedding-3-small", input=text)
        return resp.data[0].embedding

    return _deterministic_fallback_embedding(text)


def _deterministic_fallback_embedding(text: str) -> list[float]:
    vec = [0.0] * EMBEDDING_DIM
    digest = hashlib.sha256(text.encode("utf-8")).digest()
    for i, byte in enumerate(digest):
        vec[i % EMBEDDING_DIM] += (byte / 255.0) - 0.5
    norm = math.sqrt(sum(v * v for v in vec)) or 1.0
    return [v / norm for v in vec]
