# Part of the EH AI Suite by ERP Heritage.
from odoo.exceptions import AccessError, UserError
from odoo.tests import TransactionCase, tagged

from odoo.addons.eh_ai.models.eh_ai_source import _assert_public_url


@tagged("post_install", "-at_install")
class TestEhAiSecurity(TransactionCase):

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.agent = cls.env["eh.ai.agent"].create({
            "name": "Sec Agent",
            "chat_model_id": cls.env.ref("eh_ai.model_gpt_4_1").id,
            "use_sources": False,
        })
        cls.ai_user = cls.env["res.users"].create({
            "name": "AI User",
            "login": "eh_ai_sec_user",
            "group_ids": [(6, 0, [
                cls.env.ref("base.group_user").id,
                cls.env.ref("eh_ai.group_eh_ai_user").id,
            ])],
        })
        cls.outsider = cls.env["res.users"].create({
            "name": "Outsider",
            "login": "eh_ai_outsider",
            "group_ids": [(6, 0, [cls.env.ref("base.group_user").id])],
        })

    def test_ssrf_blocks_non_public_urls(self):
        for url in (
            "http://127.0.0.1/",
            "http://169.254.169.254/latest/meta-data/",
            "file:///etc/passwd",
            "ftp://example.com/secret",
            # IPv4-mapped and NAT64-embedded IPv6 forms of private/loopback IPs.
            "http://[::ffff:127.0.0.1]/",
            "http://[64:ff9b::192.168.1.1]/",
        ):
            with self.assertRaises(UserError):
                _assert_public_url(url)

    def test_tool_runs_for_regular_user_without_actions_access(self):
        # A regular AI user has no read access to ir.actions.server, yet must be
        # able to execute a tool: the action config is read via sudo while the
        # body runs in the user's environment.
        action = self.env["ir.actions.server"].create({
            "name": "Echo Tool",
            "model_id": self.env.ref("base.model_res_partner").id,
            "state": "code",
            "eh_ai_use_in_tool": True,
            "eh_ai_tool_name": "echo",
            "code": "result['output'] = 'ok'",
        })
        output, error = action.with_user(self.ai_user)._eh_ai_run_tool({})
        self.assertEqual(output, "ok")
        self.assertFalse(error)

    def test_user_cannot_read_embeddings(self):
        with self.assertRaises(AccessError):
            self.env["eh.ai.embedding"].with_user(self.ai_user).search([])

    def test_user_cannot_read_sources(self):
        with self.assertRaises(AccessError):
            self.env["eh.ai.source"].with_user(self.ai_user).search([])

    def test_user_cannot_read_usage_or_budget(self):
        with self.assertRaises(AccessError):
            self.env["eh.ai.usage.log"].with_user(self.ai_user).search([])
        with self.assertRaises(AccessError):
            self.env["eh.ai.budget"].with_user(self.ai_user).search([])

    def test_nl_search_unknown_model_returns_empty(self):
        self.assertEqual(self.agent._nl_search("no.such.model", "anything"), [])

    def test_channel_requires_agent_read_access(self):
        with self.assertRaises(AccessError):
            self.agent.with_user(self.outsider).eh_ai_channel_id()

    def test_search_helpers_are_private(self):
        # The unrestricted retrieval helpers must not be RPC-reachable.
        Embedding = self.env["eh.ai.embedding"]
        self.assertFalse(hasattr(Embedding, "search_similar"))
        self.assertFalse(hasattr(Embedding, "search_hybrid"))
        self.assertFalse(hasattr(Embedding, "search_fulltext"))
        self.assertTrue(hasattr(Embedding, "_search_similar"))
