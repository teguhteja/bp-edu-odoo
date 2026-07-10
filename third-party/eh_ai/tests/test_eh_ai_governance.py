# Part of the EH AI Suite by ERP Heritage.
from unittest.mock import patch

from odoo.exceptions import UserError
from odoo.tests import TransactionCase, tagged

from odoo.addons.eh_ai.utils.providers.openai_provider import OpenAICompatibleProvider

_POST_PATH = "odoo.addons.eh_ai.utils.providers.base.BaseProvider._post"


def _openai_text(text, prompt_tokens=1000, completion_tokens=500):
    return {
        "choices": [{"message": {"role": "assistant", "content": text}, "finish_reason": "stop"}],
        "usage": {"prompt_tokens": prompt_tokens, "completion_tokens": completion_tokens},
    }


@tagged("post_install", "-at_install")
class TestEhAiGovernance(TransactionCase):

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.model_gpt = cls.env.ref("eh_ai.model_gpt_4_1")  # $2 in / $8 out per MTok
        cls.agent = cls.env["eh.ai.agent"].create({
            "name": "Gov Agent",
            "chat_model_id": cls.model_gpt.id,
            "use_sources": False,
        })
        cls.UsageLog = cls.env["eh.ai.usage.log"]

    def test_cost_computation(self):
        cost = self.UsageLog._compute_cost(
            self.model_gpt,
            {"input_tokens": 1000, "output_tokens": 500, "cached_tokens": 0},
        )
        # (1000*2 + 500*8) / 1e6 = 0.006
        self.assertAlmostEqual(cost, 0.006, places=9)

    def test_usage_logged_on_call(self):
        with patch(_POST_PATH, side_effect=[_openai_text("Hello.")]):
            self.agent.generate_response("hi")
        logs = self.UsageLog.search([("agent_id", "=", self.agent.id)])
        self.assertEqual(len(logs), 1)
        self.assertEqual(logs.outcome, "ok")
        self.assertEqual(logs.input_tokens, 1000)
        self.assertEqual(logs.output_tokens, 500)
        self.assertAlmostEqual(logs.cost, 0.006, places=9)
        self.assertGreaterEqual(logs.latency_ms, 0)

    def test_failed_call_records_no_usage_row(self):
        # A failed call must not leave a misleading zero-cost usage row; the
        # exception propagates to the caller and the failure is only logged.
        with patch(_POST_PATH, side_effect=RuntimeError("provider down")):
            with self.assertRaises(Exception):
                self.agent.generate_response("hi")
        self.assertFalse(self.UsageLog.search([("agent_id", "=", self.agent.id)]))

    def test_budget_hard_stop_blocks(self):
        self.UsageLog.create({
            "agent_id": self.agent.id, "model_id": self.model_gpt.id,
            "cost": 10.0, "outcome": "ok",
        })
        self.env["eh.ai.budget"].create({
            "name": "Cap", "scope": "global", "period": "monthly",
            "limit_amount": 5.0, "mode": "hard_stop",
        })
        with patch(_POST_PATH, side_effect=[_openai_text("should not be called")]) as mocked:
            with self.assertRaises(UserError):
                self.agent.generate_response("hi")
        # Blocked before any provider call, so nothing is spent.
        self.assertEqual(mocked.call_count, 0)

    def test_budget_soft_warn_allows(self):
        self.UsageLog.create({
            "agent_id": self.agent.id, "model_id": self.model_gpt.id,
            "cost": 10.0, "outcome": "ok",
        })
        self.env["eh.ai.budget"].create({
            "name": "Soft Cap", "scope": "global", "period": "monthly",
            "limit_amount": 5.0, "mode": "soft_warn",
        })
        with patch(_POST_PATH, side_effect=[_openai_text("Allowed.")]) as mocked:
            result = self.agent.generate_response("hi")
        self.assertEqual(mocked.call_count, 1)
        self.assertIn("Allowed", result["text"])

    def test_budget_spent_computation(self):
        budget = self.env["eh.ai.budget"].create({
            "name": "Track", "scope": "agent", "agent_id": self.agent.id,
            "period": "monthly", "limit_amount": 100.0, "mode": "hard_stop",
        })
        self.UsageLog.create({
            "agent_id": self.agent.id, "model_id": self.model_gpt.id,
            "cost": 3.5, "outcome": "ok",
        })
        self.UsageLog.create({
            "agent_id": self.agent.id, "model_id": self.model_gpt.id,
            "cost": 1.5, "outcome": "ok",
        })
        # Blocked rows must not count toward spend.
        self.UsageLog.create({
            "agent_id": self.agent.id, "model_id": self.model_gpt.id,
            "cost": 99.0, "outcome": "budget_block",
        })
        self.assertAlmostEqual(budget._spent(), 5.0, places=4)

    def test_prompt_versioning_and_restore(self):
        prompt = self.env["eh.ai.prompt"].create({"name": "Greeter", "body": "version one"})
        self.assertEqual(prompt.version, 1)
        prompt.body = "version two"
        self.assertEqual(prompt.version, 2)

        first = prompt.revision_ids.filtered(lambda r: r.version == 1)
        first.action_restore()
        self.assertEqual(prompt.version, 3)
        self.assertEqual(prompt.body, "version one")

    def test_agent_uses_prompt_template(self):
        prompt = self.env["eh.ai.prompt"].create({"name": "Role", "body": "You are a tax expert."})
        self.agent.system_prompt_id = prompt
        system = self.agent._build_system_prompt()
        self.assertIn("tax expert", system)
