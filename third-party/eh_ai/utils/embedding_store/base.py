# Part of the EH AI Suite by ERP Heritage.
"""Embedding store strategy interface.

A store decides how chunk vectors are persisted and searched. Every backend
reads and writes the canonical ``embedding_json`` text column on
``eh.ai.embedding``; an accelerated backend (pgvector) may additionally keep a
native vector column in sync. This lets the same agent and cron code run on any
PostgreSQL instance.
"""


class EmbeddingStore:

    name = "base"

    def __init__(self, env):
        self.env = env

    @property
    def available(self):
        return True

    def sync(self, embeddings):
        """Persist vectors for freshly embedded records (no-op for JSON-only)."""
        return None

    def search(self, query_vector, embedding_model_id, source_ids, top_n=5,
               min_similarity=0.0):
        """Return ``[(embedding_id, similarity), ...]`` best-first."""
        raise NotImplementedError
