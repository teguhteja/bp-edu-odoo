# Part of the EH AI Suite by ERP Heritage.
from unittest.mock import patch

from odoo.tests import TransactionCase, tagged

_POST_PATH = "odoo.addons.eh_ai.utils.providers.base.BaseProvider._post"


def _openai_text(text):
    return {
        "choices": [{"message": {"role": "assistant", "content": text}, "finish_reason": "stop"}],
        "usage": {"prompt_tokens": 5, "completion_tokens": 5},
    }


@tagged("post_install", "-at_install")
class TestEhAiSearch(TransactionCase):

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.agent = cls.env["eh.ai.agent"].create({
            "name": "Search Agent",
            "chat_model_id": cls.env.ref("eh_ai.model_gpt_4_1").id,
            "use_sources": False,
        })

    def test_nl_search_builds_domain(self):
        with patch(_POST_PATH, side_effect=[_openai_text('[["city", "ilike", "Sydney"]]')]):
            domain = self.agent._nl_search("res.partner", "customers in Sydney", ["name", "city"])
        self.assertEqual(domain, [["city", "ilike", "Sydney"]])

    def test_nl_search_rejects_unknown_field(self):
        with patch(_POST_PATH, side_effect=[_openai_text('[["secret", "=", "x"]]')]):
            domain = self.agent._nl_search("res.partner", "anything", ["name", "city"])
        self.assertEqual(domain, [])

    def test_nl_search_rejects_bad_operator(self):
        with patch(_POST_PATH, side_effect=[_openai_text('[["name", "DROP", "x"]]')]):
            domain = self.agent._nl_search("res.partner", "anything", ["name"])
        self.assertEqual(domain, [])

    def test_nl_search_handles_garbage(self):
        with patch(_POST_PATH, side_effect=[_openai_text("I cannot help with that.")]):
            domain = self.agent._nl_search("res.partner", "anything", ["name"])
        self.assertEqual(domain, [])
