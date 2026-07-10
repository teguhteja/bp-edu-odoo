# Part of the EH AI Suite by ERP Heritage.
import base64
import json
from unittest.mock import patch

from odoo.tests import TransactionCase, tagged

from odoo.addons.eh_ai.utils.chunking import chunk_text
from odoo.addons.eh_ai.utils.embedding_store.indb import InDbCosineStore
from odoo.addons.eh_ai.utils.providers.openai_provider import OpenAICompatibleProvider

_POST_PATH = "odoo.addons.eh_ai.utils.providers.base.BaseProvider._post"


def _openai_text(text):
    return {
        "choices": [{"message": {"role": "assistant", "content": text}, "finish_reason": "stop"}],
        "usage": {"prompt_tokens": 5, "completion_tokens": 5},
    }


@tagged("post_install", "-at_install")
class TestEhAiRag(TransactionCase):

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.chat_model = cls.env.ref("eh_ai.model_gpt_4_1")
        cls.embed_model = cls.env.ref("eh_ai.model_openai_text_embedding_3_small")
        cls.agent = cls.env["eh.ai.agent"].create({
            "name": "RAG Agent",
            "chat_model_id": cls.chat_model.id,
            "embedding_model_id": cls.embed_model.id,
            "use_sources": True,
            "system_prompt": "You answer from sources.",
        })

    def test_chunking_overlap(self):
        paragraph = ("Sentence number {n} carries some weight. ".format(n=1)) * 40
        text = "\n\n".join("Para %d. %s" % (i, paragraph) for i in range(6))
        chunks = chunk_text(text, target=800, overlap=100, hard_max=2000)
        self.assertGreater(len(chunks), 1)
        for chunk in chunks:
            self.assertLessEqual(len(chunk), 2000)

    def test_indb_cosine_ranking(self):
        source = self.env["eh.ai.source"].create({
            "name": "Vectors",
            "agent_id": self.agent.id,
            "type": "url",
            "url": "https://example.com",
        })
        Embedding = self.env["eh.ai.embedding"]
        e_x = Embedding.create({
            "source_id": source.id, "embedding_model_id": self.embed_model.id,
            "content": "x", "embedding_json": json.dumps([1.0, 0.0]),
        })
        Embedding.create({
            "source_id": source.id, "embedding_model_id": self.embed_model.id,
            "content": "y", "embedding_json": json.dumps([0.0, 1.0]),
        })
        e_near = Embedding.create({
            "source_id": source.id, "embedding_model_id": self.embed_model.id,
            "content": "near-x", "embedding_json": json.dumps([0.9, 0.1]),
        })

        store = InDbCosineStore(self.env)
        hits = store.search([1.0, 0.0], self.embed_model.id, [source.id], top_n=2)
        self.assertEqual(len(hits), 2)
        ranked_ids = [hit_id for hit_id, _ in hits]
        self.assertEqual(ranked_ids[0], e_x.id)
        self.assertEqual(ranked_ids[1], e_near.id)
        self.assertAlmostEqual(hits[0][1], 1.0, places=5)

    def test_hybrid_search_surfaces_keyword_match(self):
        # All vectors are equal, so only keyword search can distinguish chunks.
        source = self.env["eh.ai.source"].create({
            "name": "Catalog", "agent_id": self.agent.id, "type": "url",
            "url": "https://example.com",
        })
        Embedding = self.env["eh.ai.embedding"]
        for content in ("alpha apple device", "beta banana machine", "gamma cherry widget"):
            Embedding.create({
                "source_id": source.id, "embedding_model_id": self.embed_model.id,
                "content": content, "embedding_json": json.dumps([1.0, 0.0]),
            })
        hits = Embedding._search_hybrid(
            "banana", [1.0, 0.0], self.embed_model.id, source.ids, top_n=1, over_fetch=10)
        self.assertEqual(len(hits), 1)
        self.assertIn("banana", hits[0][0].content)

    def test_source_indexing_cron(self):
        attachment = self.env["ir.attachment"].create({
            "name": "kb.txt",
            "mimetype": "text/plain",
            "datas": base64.b64encode(
                b"The warranty period for the X100 pump is 24 months from purchase. "
                b"Returns require the original invoice."),
        })
        source = self.env["eh.ai.source"].create({
            "name": "Warranty KB",
            "agent_id": self.agent.id,
            "type": "binary",
            "attachment_id": attachment.id,
        })

        def fake_embed(self_provider, model, inputs, dimensions=None):
            return [[1.0, 0.0] for _ in inputs]

        with patch.object(OpenAICompatibleProvider, "embed", fake_embed):
            self.env["eh.ai.embedding"]._cron_generate_embeddings()

        self.assertEqual(source.status, "indexed")
        self.assertTrue(source.embedding_ids)
        self.assertTrue(all(e.embedding_json for e in source.embedding_ids))

    def test_embedding_retry_recovers_from_transient_failure(self):
        attachment = self.env["ir.attachment"].create({
            "name": "flaky.txt",
            "mimetype": "text/plain",
            "datas": base64.b64encode(b"The pump warranty runs for 24 months from purchase."),
        })
        source = self.env["eh.ai.source"].create({
            "name": "Flaky KB", "agent_id": self.agent.id,
            "type": "binary", "attachment_id": attachment.id,
        })
        calls = {"n": 0}

        def flaky_embed(self_provider, model, inputs, dimensions=None):
            calls["n"] += 1
            if calls["n"] == 1:
                raise RuntimeError("rate limited")
            return [[1.0, 0.0] for _ in inputs]

        with patch.object(OpenAICompatibleProvider, "embed", flaky_embed):
            # First run creates chunks and fails the batch: source stays
            # processing, chunks are queued for retry (not permanently failed).
            self.env["eh.ai.embedding"]._cron_generate_embeddings()
            # Force a re-read from the database to prove retry_count persisted
            # (not just buffered in the cache).
            self.env.invalidate_all()
            self.assertEqual(source.status, "processing")
            self.assertTrue(all(not e.has_failed for e in source.embedding_ids))
            self.assertTrue(all(e.retry_count == 1 for e in source.embedding_ids))
            # Second run retries and succeeds.
            self.env["eh.ai.embedding"]._cron_generate_embeddings()

        self.assertEqual(source.status, "indexed")
        self.assertTrue(all(e.embedding_json for e in source.embedding_ids))

    def test_embedding_permanently_fails_after_max_retries(self):
        from odoo.addons.eh_ai.models.eh_ai_embedding import MAX_EMBED_RETRIES
        attachment = self.env["ir.attachment"].create({
            "name": "broken.txt",
            "mimetype": "text/plain",
            "datas": base64.b64encode(b"This content can never be embedded by the stub."),
        })
        source = self.env["eh.ai.source"].create({
            "name": "Broken KB", "agent_id": self.agent.id,
            "type": "binary", "attachment_id": attachment.id,
        })

        def always_fail(self_provider, model, inputs, dimensions=None):
            raise RuntimeError("embedding service down")

        with patch.object(OpenAICompatibleProvider, "embed", always_fail):
            for _ in range(MAX_EMBED_RETRIES):
                self.env["eh.ai.embedding"]._cron_generate_embeddings()
                # Drop the cache between runs so retry_count must come from the
                # database, the way successive cron transactions actually see it.
                self.env.invalidate_all()

        self.assertEqual(source.status, "failed")
        self.assertTrue(source.embedding_ids)
        self.assertTrue(all(e.has_failed for e in source.embedding_ids))

    def test_indb_full_pipeline_without_pgvector(self):
        # Force the in-DB store so this proves the no-pgvector path end to end.
        self.env["ir.config_parameter"].sudo().set_param("eh_ai.embedding_store", "indb")
        attachment = self.env["ir.attachment"].create({
            "name": "manual.txt",
            "mimetype": "text/plain",
            "datas": base64.b64encode(b"The device operates between 0 and 40 degrees Celsius."),
        })
        source = self.env["eh.ai.source"].create({
            "name": "Manual",
            "agent_id": self.agent.id,
            "type": "binary",
            "attachment_id": attachment.id,
        })

        def fake_embed(self_provider, model, inputs, dimensions=None):
            return [[1.0, 0.0] for _ in inputs]

        with patch.object(OpenAICompatibleProvider, "embed", fake_embed):
            self.env["eh.ai.embedding"]._cron_generate_embeddings()

        self.assertEqual(source.status, "indexed")
        hits = self.env["eh.ai.embedding"]._search_similar(
            [1.0, 0.0], self.embed_model.id, source.ids, top_n=3)
        self.assertTrue(hits)

    def test_agent_rag_end_to_end_with_citations(self):
        attachment = self.env["ir.attachment"].create({
            "name": "policy.txt",
            "mimetype": "text/plain",
            "datas": base64.b64encode(b"Refunds are processed within 14 business days."),
        })
        source = self.env["eh.ai.source"].create({
            "name": "Refund Policy",
            "agent_id": self.agent.id,
            "type": "binary",
            "attachment_id": attachment.id,
        })

        def fake_embed(self_provider, model, inputs, dimensions=None):
            return [[1.0, 0.0] for _ in inputs]

        with patch.object(OpenAICompatibleProvider, "embed", fake_embed):
            self.env["eh.ai.embedding"]._cron_generate_embeddings()
        self.assertEqual(source.status, "indexed")

        chat = _openai_text("Refunds take 14 business days [SOURCE:%d]." % source.id)
        with patch.object(OpenAICompatibleProvider, "embed", fake_embed), \
                patch(_POST_PATH, side_effect=[chat]) as mocked:
            result = self.agent.generate_response("How long do refunds take?")

        # The chat request must have carried the retrieved chunk in the system prompt.
        system_sent = mocked.call_args_list[0].args[2]["messages"][0]
        self.assertEqual(system_sent["role"], "system")
        self.assertIn("Refund Policy", system_sent["content"])

        # Citations rewritten to a numbered reference plus a Sources list.
        self.assertIn("[1]", result["text"])
        self.assertIn("Sources:", result["text"])
        self.assertIn("Refund Policy", result["text"])
        self.assertNotIn("[SOURCE:", result["text"])
