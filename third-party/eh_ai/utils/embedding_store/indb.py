# Part of the EH AI Suite by ERP Heritage.
"""In-database cosine store.

Stores vectors as JSON in ``eh.ai.embedding.embedding_json`` and computes cosine
similarity over the candidate set. Uses numpy when available for speed and falls
back to pure Python otherwise. Requires no PostgreSQL extension, so it installs
and runs on any stock database. Adequate for the tens of thousands of chunks a
typical SMB knowledge base holds.
"""
import json
import math

from .base import EmbeddingStore

try:
    import numpy as _np
except ImportError:  # pragma: no cover
    _np = None


class InDbCosineStore(EmbeddingStore):

    name = "indb"

    def search(self, query_vector, embedding_model_id, source_ids, top_n=5,
               min_similarity=0.0):
        if not query_vector or not source_ids:
            return []
        embeddings = self.env["eh.ai.embedding"].search([
            ("source_id", "in", list(source_ids)),
            ("embedding_model_id", "=", embedding_model_id),
            ("has_failed", "=", False),
            ("embedding_json", "!=", False),
        ])
        if not embeddings:
            return []

        scored = []
        if _np is not None:
            query = _np.asarray(query_vector, dtype="float64")
            query_norm = _np.linalg.norm(query)
            if not query_norm:
                return []
            for embedding in embeddings:
                vector = _np.asarray(json.loads(embedding.embedding_json), dtype="float64")
                if vector.shape != query.shape:
                    continue
                denom = query_norm * _np.linalg.norm(vector)
                if denom:
                    scored.append((embedding.id, float(_np.dot(query, vector) / denom)))
        else:
            query_norm = math.sqrt(sum(value * value for value in query_vector))
            if not query_norm:
                return []
            for embedding in embeddings:
                vector = json.loads(embedding.embedding_json)
                if len(vector) != len(query_vector):
                    continue
                dot = sum(a * b for a, b in zip(query_vector, vector))
                norm = math.sqrt(sum(value * value for value in vector))
                if norm:
                    scored.append((embedding.id, dot / (query_norm * norm)))

        scored = [pair for pair in scored if pair[1] >= min_similarity]
        scored.sort(key=lambda pair: pair[1], reverse=True)
        return scored[:top_n]
