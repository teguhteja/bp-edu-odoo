# Part of the EH AI Suite by ERP Heritage.
"""pgvector-accelerated store.

When the ``vector`` extension is present, an unconstrained ``vector`` column is
kept alongside the canonical JSON and cosine search runs in PostgreSQL via the
``<=>`` operator. The column is unconstrained so vectors of different dimensions
(different embedding models) can coexist; queries always filter by
``embedding_model_id`` so only same-dimension vectors are compared.
"""
import logging
import math

from .base import EmbeddingStore
from ..pgvector import is_pgvector_available

_logger = logging.getLogger(__name__)


class PgVectorStore(EmbeddingStore):

    name = "pgvector"

    def __init__(self, env):
        super().__init__(env)
        self._available = is_pgvector_available(env)
        if self._available:
            self._ensure_schema()

    @property
    def available(self):
        return self._available

    def _ensure_schema(self):
        try:
            with self.env.cr.savepoint():
                self.env.cr.execute(
                    "ALTER TABLE eh_ai_embedding ADD COLUMN IF NOT EXISTS embedding_vector vector"
                )
        except Exception as error:  # noqa: BLE001 - degrade to JSON-only
            _logger.warning("EH AI: could not add pgvector column, falling back (%s)", error)
            self._available = False

    def sync(self, embeddings):
        if not self._available or not embeddings:
            return
        ids = [embedding.id for embedding in embeddings if embedding.embedding_json]
        if not ids:
            return
        # Cast the stored JSON array straight into the vector column.
        self.env.cr.execute(
            """
            UPDATE eh_ai_embedding
               SET embedding_vector = embedding_json::vector
             WHERE id = ANY(%s) AND embedding_json IS NOT NULL
            """,
            (ids,),
        )

    def search(self, query_vector, embedding_model_id, source_ids, top_n=5,
               min_similarity=0.0):
        if not self._available or not query_vector or not source_ids:
            return []
        # pgvector rejects inf/nan; a corrupt query vector would raise on the
        # ::vector cast, so fail soft to an empty result instead.
        if not all(math.isfinite(value) for value in query_vector):
            _logger.warning("EH AI: query vector has non-finite values; skipping pgvector search")
            return []
        literal = "[" + ",".join(repr(float(value)) for value in query_vector) + "]"
        self.env.cr.execute(
            """
            SELECT id, 1 - (embedding_vector <=> %s::vector) AS similarity
              FROM eh_ai_embedding
             WHERE source_id = ANY(%s)
               AND embedding_model_id = %s
               AND has_failed = FALSE
               AND embedding_vector IS NOT NULL
          ORDER BY embedding_vector <=> %s::vector
             LIMIT %s
            """,
            (literal, list(source_ids), embedding_model_id, literal, top_n),
        )
        rows = self.env.cr.fetchall()
        return [(row[0], row[1]) for row in rows if row[1] is not None and row[1] >= min_similarity]
