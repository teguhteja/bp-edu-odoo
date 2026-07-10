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
class TestEhAiDiscuss(TransactionCase):

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.agent = cls.env["eh.ai.agent"].create({
            "name": "Discuss Agent",
            "chat_model_id": cls.env.ref("eh_ai.model_gpt_4_1").id,
            "use_sources": False,
        })

    def test_agent_gets_partner_on_create(self):
        self.assertTrue(self.agent.partner_id, "agent must have a partner identity")

    def test_channel_created_and_tagged(self):
        channel = self.env["discuss.channel"]._eh_ai_get_or_create(self.agent)
        self.assertEqual(channel.eh_ai_agent_id, self.agent)
        members = channel.channel_member_ids.partner_id
        self.assertIn(self.env.user.partner_id, members)
        self.assertIn(self.agent.partner_id, members)

    def test_agent_replies_in_channel(self):
        # Replies are generated asynchronously by a cron, so post then drain the
        # queue within the mocked-provider context.
        channel = self.env["discuss.channel"]._eh_ai_get_or_create(self.agent)
        with patch(_POST_PATH, side_effect=[_openai_text("Hello from the agent!")]):
            channel.message_post(
                body="Hi", message_type="comment", subtype_xmlid="mail.mt_comment")
            self.env["eh.ai.reply.job"]._cron_process()
        self.assertEqual(
            self.env["eh.ai.reply.job"].search_count([("state", "=", "done")]), 1)
        replies = channel.message_ids.filtered(
            lambda m: m.author_id == self.agent.partner_id)
        self.assertTrue(replies, "the agent should post a reply")
        self.assertIn("Hello from the agent", replies[0].body)

    def test_agent_reply_job_reaches_error_state_on_failure(self):
        # A failed generation must drive the job to a terminal 'error' state
        # (never left 'pending' to be retried forever) and still post a
        # friendly, non-leaky message to the channel.
        channel = self.env["discuss.channel"]._eh_ai_get_or_create(self.agent)
        with patch(_POST_PATH, side_effect=RuntimeError("provider down")):
            channel.message_post(
                body="Hi", message_type="comment", subtype_xmlid="mail.mt_comment")
            self.env["eh.ai.reply.job"]._cron_process()
        job = self.env["eh.ai.reply.job"].search([("channel_id", "=", channel.id)])
        self.assertEqual(job.state, "error")
        self.assertFalse(self.env["eh.ai.reply.job"].search([("state", "=", "pending")]))
        replies = channel.message_ids.filtered(
            lambda m: m.author_id == self.agent.partner_id)
        self.assertTrue(replies, "a friendly reply should still be posted")
        self.assertIn("could not generate", replies[0].body)

    def test_agent_reply_does_not_loop(self):
        # The agent's own message must not trigger another reply.
        channel = self.env["discuss.channel"]._eh_ai_get_or_create(self.agent)
        with patch(_POST_PATH, side_effect=[_openai_text("One reply only.")]):
            channel.message_post(
                body="Question", message_type="comment", subtype_xmlid="mail.mt_comment")
            self.env["eh.ai.reply.job"]._cron_process()
        agent_msgs = channel.message_ids.filtered(
            lambda m: m.author_id == self.agent.partner_id)
        self.assertEqual(len(agent_msgs), 1)
        # The reply itself must not have enqueued another job.
        self.assertEqual(self.env["eh.ai.reply.job"].search_count([]), 1)
