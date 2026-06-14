"""
embedder.py — Pluggable text embeddings.

Two backends, selected via config.EMBED_PROVIDER:

    "voyage" → Voyage AI API (no torch; production default). Asymmetric:
               input_type="document" for stored chunks, "query" for searches.
    "nomic"  → local nomic-embed-text-v1.5 via sentence-transformers (the
               original local stack). Asymmetric via "search_document:" /
               "search_query:" prefixes.

Both expose the same API:
    encode_documents(texts)  → list[list[float]]   (use at ingest time)
    encode_query(text)       → list[float]         (use at retrieval time)
    encode_queries(texts)    → list[list[float]]

Import the shared lazy `embedder` singleton everywhere; the underlying model /
API client is only constructed on first use, so importing this module never
pulls in torch in the production (Voyage) configuration.

NOTE: queries and documents must be embedded by the *same* backend — switching
EMBED_PROVIDER requires rebuilding the ChromaDB index (re-run ingestion).
"""

from __future__ import annotations

import config

# Voyage processes many texts per call; keep batches comfortably within limits.
_VOYAGE_BATCH = 96


class VoyageEmbedder:
    """Voyage AI embeddings (production default — no local model)."""

    def __init__(self):
        import voyageai

        self.model = config.VOYAGE_EMBED_MODEL
        self.client = voyageai.Client(api_key=config.VOYAGE_API_KEY or None)

    def _embed(self, texts: list[str], input_type: str) -> list[list[float]]:
        out: list[list[float]] = []
        for start in range(0, len(texts), _VOYAGE_BATCH):
            batch = texts[start:start + _VOYAGE_BATCH]
            res = self.client.embed(batch, model=self.model, input_type=input_type)
            out.extend(res.embeddings)
        return out

    def encode_documents(self, texts: list[str]) -> list:
        return self._embed(texts, "document")

    def encode_query(self, text: str) -> list:
        return self._embed([text], "query")[0]

    def encode_queries(self, texts: list[str]) -> list:
        return self._embed(texts, "query")


class NomicEmbedder:
    """
    Local nomic-embed-text-v1.5 (the original local stack).

    Nomic was trained asymmetrically — queries and documents live in different
    subspaces, so the required task prefixes ('search_document:' /
    'search_query:') must be applied or similarity scores become unreliable.
    """

    def __init__(self):
        from sentence_transformers import SentenceTransformer  # lazy: pulls torch

        self.model = SentenceTransformer(config.NOMIC_EMBED_MODEL, trust_remote_code=True)

    def encode_documents(self, texts: list[str]) -> list:
        prefixed = [f"search_document: {t}" for t in texts]
        return self.model.encode(prefixed, normalize_embeddings=True).tolist()

    def encode_query(self, text: str) -> list:
        return self.model.encode(f"search_query: {text}", normalize_embeddings=True).tolist()

    def encode_queries(self, texts: list[str]) -> list:
        prefixed = [f"search_query: {t}" for t in texts]
        return self.model.encode(prefixed, normalize_embeddings=True).tolist()


def _build_embedder():
    if config.EMBED_PROVIDER == "nomic":
        return NomicEmbedder()
    return VoyageEmbedder()


class _LazyEmbedder:
    """Defers construction of the real backend until first attribute access, so
    importing this module never loads torch / requires an API key prematurely."""

    _impl = None

    def _ensure(self):
        if _LazyEmbedder._impl is None:
            _LazyEmbedder._impl = _build_embedder()
        return _LazyEmbedder._impl

    def __getattr__(self, name):
        return getattr(self._ensure(), name)


# Single shared instance — import this everywhere.
embedder = _LazyEmbedder()


def get_embedder():
    """Explicit accessor (returns the same lazily-built backend)."""
    return embedder._ensure()
