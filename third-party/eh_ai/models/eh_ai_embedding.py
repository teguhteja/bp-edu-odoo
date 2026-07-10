# Part of the EH AI Suite by ERP Heritage.
import json
import logging

from odoo import api, fields, models

_logger = logging.getLogger(__name__)

# Conservative per-request batch sizes for the embedding API.
EMBED_BATCH_SIZE = 64
CRON_SOURCE_LIMIT = 20
# A chunk is retried on later cron runs until this many attempts have failed,
# then it is marked permanently failed so it stops being picked up.
MAX_EMBED_RETRIES = 3


class EhAiEmbedding(models.Model):
    _name = "eh.ai.embedding"
    _description = "AI Embedding Chunk"
    _order = "source_id, sequence, id"

    source_id = fields.Many2one("eh.ai.source", required=True, ondelete="cascade", index=True)
    agent_id = fields.Many2one(related="source_id.agent_id", store=True, index=True)
    embedding_model_id = fields.Many2one("eh.ai.model", required=True, ondelete="restrict", index=True)
    sequence = fields.Integer(default=0)
    content = fields.Text(required=True)
    embedding_json = fields.Text(help="The chunk vector, stored as a JSON array of floats.")
    dimensions = fields.Integer()
    retry_count = fields.Integer(default=0)
    has_failed = fields.Boolean(default=False)

    # -- generation cron -----------------------------------------------------

    @api.model
    def _cron_generate_embeddings(self):
        Source = self.env["eh.ai.source"]
        sources = Source.search([
            ("status", "=", "processing"),
            ("is_active", "=", True),
        ], limit=CRON_SOURCE_LIMIT)

        # 1. Turn sources without chunks into chunk rows.
        for source in sources:
            if not source.embedding_ids:
                source._create_chunks()

        # 2. Embed pending chunks in batches, grouped by model.
        pending = self.search([
            ("embedding_json", "=", False),
            ("has_failed", "=", False),
            ("source_id.status", "=", "processing"),
            ("source_id.is_active", "=", True),
        ], limit=EMBED_BATCH_SIZE)

        if pending:
            for model in pending.embedding_model_id:
                batch = pending.filtered(lambda e, m=model: e.embedding_model_id == m)
                batch._embed_batch(model)

        # 3. Close out fully-embedded sources.
        for source in sources:
            source._update_status_after_embedding()

        # 4. Re-arm if work remains.
        remaining = self.search_count([
            ("embedding_json", "=", False),
            ("has_failed", "=", False),
            ("source_id.status", "=", "processing"),
        ])
        if remaining:
            self.env.ref("eh_ai.ir_cron_generate_embeddings")._trigger()

    def _embed_batch(self, model):
        adapter = model.provider_id.get_adapter()
        contents = [embedding.content for embedding in self]
        try:
            vectors = adapter.embed(model.technical_name, contents,
                                    dimensions=model.embedding_dimensions or None)
        except Exception as error:  # noqa: BLE001 - mark the batch, keep the cron alive
            _logger.warning("EH AI: embedding batch failed for model %s: %s",
                            model.technical_name, error)
            self._register_failed_attempt()
            return

        if len(vectors) != len(self):
            _logger.warning("EH AI: embedding count mismatch (%s vs %s)", len(vectors), len(self))
            self._register_failed_attempt()
            return

        for embedding, vector in zip(self, vectors):
            embedding.write({
                "embedding_json": json.dumps(vector),
                "dimensions": len(vector),
            })

        from odoo.addons.eh_ai.utils.embedding_store import get_embedding_store
        get_embedding_store(self.env).sync(self)

    def _register_failed_attempt(self):
        """Count a failed embedding attempt; only give up after MAX_EMBED_RETRIES.

        Until the cap is reached the chunk keeps has_failed=False, so a later
        cron run retries it (transient provider errors recover on their own).
        """
        for embedding in self:
            attempts = embedding.retry_count + 1
            vals = {"retry_count": attempts}
            if attempts >= MAX_EMBED_RETRIES:
                vals["has_failed"] = True
            embedding.write(vals)

    # -- retrieval -----------------------------------------------------------

    # These retrieval helpers run unrestricted SQL over chunk content, so they
    # are private (not callable over RPC) and must only be invoked from a
    # trusted, source-scoped caller such as _build_rag_context.
    @api.model
    def _search_similar(self, query_vector, embedding_model_id, source_ids, top_n=5,
                        min_similarity=0.0):
        from odoo.addons.eh_ai.utils.embedding_store import get_embedding_store
        store = get_embedding_store(self.env)
        hits = store.search(query_vector, embedding_model_id, source_ids,
                            top_n=top_n, min_similarity=min_similarity)
        return self._order_hits(hits)

    @api.model
    def _search_fulltext(self, query_text, embedding_model_id, source_ids, limit=20):
        """Keyword search over chunk text using PostgreSQL full-text search."""
        if not query_text or not source_ids:
            return []
        self.env.cr.execute(
            """
            SELECT id, ts_rank(to_tsvector('english', content), query) AS rank
              FROM eh_ai_embedding, plainto_tsquery('english', %s) query
             WHERE source_id = ANY(%s)
               AND embedding_model_id = %s
               AND has_failed = FALSE
               AND to_tsvector('english', content) @@ query
          ORDER BY rank DESC
             LIMIT %s
            """,
            (query_text, list(source_ids), embedding_model_id, limit),
        )
        return [(row[0], row[1]) for row in self.env.cr.fetchall()]

    @api.model
    def _search_hybrid(self, query_text, query_vector, embedding_model_id, source_ids,
                       top_n=5, over_fetch=20, rrf_k=60):
        """Fuse vector and keyword rankings with Reciprocal Rank Fusion.

        Vector search catches semantic matches; keyword search catches exact
        terms, codes and ids that embeddings miss. RRF blends the two rank lists
        without needing comparable score scales.
        """
        from odoo.addons.eh_ai.utils.embedding_store import get_embedding_store
        store = get_embedding_store(self.env)
        vector_hits = store.search(query_vector, embedding_model_id, source_ids, top_n=over_fetch)
        keyword_hits = self._search_fulltext(query_text, embedding_model_id, source_ids, over_fetch)

        scores = {}
        for rank, (hit_id, __) in enumerate(vector_hits):
            scores[hit_id] = scores.get(hit_id, 0.0) + 1.0 / (rrf_k + rank + 1)
        for rank, (hit_id, __) in enumerate(keyword_hits):
            scores[hit_id] = scores.get(hit_id, 0.0) + 1.0 / (rrf_k + rank + 1)

        ranked = sorted(scores.items(), key=lambda pair: pair[1], reverse=True)[:top_n]
        return self._order_hits(ranked)

    @api.model
    def _order_hits(self, hits):
        """Map ranked ``[(id, score)]`` to ``[(record, score)]`` preserving order."""
        by_id = {hit_id: score for hit_id, score in hits}
        records = self.browse(list(by_id))
        return [(record, by_id[record.id]) for record in records if record.exists()]
