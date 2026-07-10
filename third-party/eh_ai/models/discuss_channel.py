# Part of the EH AI Suite by ERP Heritage.
from odoo import api, fields, models
from odoo.tools import html2plaintext

HISTORY_LIMIT = 20


class DiscussChannel(models.Model):
    _inherit = "discuss.channel"

    eh_ai_agent_id = fields.Many2one("eh.ai.agent", index=True, ondelete="set null")
    eh_ai_is_agent = fields.Boolean(compute="_compute_eh_ai_is_agent")

    @api.depends("eh_ai_agent_id")
    def _compute_eh_ai_is_agent(self):
        for channel in self:
            channel.eh_ai_is_agent = bool(channel.eh_ai_agent_id)

    def _to_store_defaults(self, target):
        # Expose the agent flag so the chat window can hide the call buttons:
        # you cannot place an audio/video call to an AI agent.
        return super()._to_store_defaults(target) + ["eh_ai_is_agent"]

    @api.model
    def _eh_ai_get_or_create(self, agent):
        """Return the user's one-to-one Discuss channel with this agent."""
        agent_partner = agent._get_partner()
        channel = self._get_or_create_chat([agent_partner.id])
        if channel.eh_ai_agent_id != agent:
            channel.eh_ai_agent_id = agent.id
        return channel

    def message_post(self, **kwargs):
        message = super().message_post(**kwargs)
        # Reply only to the human user's own messages in an agent channel. The
        # author_id != agent partner check is a second guard against a reply
        # loop, independent of the eh_ai_skip_agent context flag.
        if (
            self.eh_ai_agent_id
            and not self.env.context.get("eh_ai_skip_agent")
            and message.author_id
            and message.author_id == self.env.user.partner_id
            and message.author_id != self.eh_ai_agent_id.partner_id
        ):
            self._eh_ai_enqueue_reply(message)
        return message

    def _eh_ai_enqueue_reply(self, user_message):
        """Queue the agent's reply and wake the cron, off the request thread.

        The reply involves a slow external LLM call, so it must not run inside
        this RPC; the background cron generates it and posts it back.
        """
        self.env["eh.ai.reply.job"].sudo().create({
            "channel_id": self.id,
            "agent_id": self.eh_ai_agent_id.id,
            "user_id": self.env.user.id,
            "message_id": user_message.id,
            "prompt": html2plaintext(user_message.body or ""),
        })
        self.env.ref("eh_ai.ir_cron_agent_replies").sudo()._trigger()

    def _eh_ai_history(self, exclude_message=None):
        agent_partner = self.eh_ai_agent_id.partner_id
        exclude_id = exclude_message.id if exclude_message else 0
        messages = self.message_ids.filtered(
            lambda m: m.message_type == "comment" and m.id != exclude_id
        ).sorted("id")[-HISTORY_LIMIT:]
        history = []
        for message in messages:
            role = "assistant" if message.author_id == agent_partner else "user"
            history.append({"role": role, "content": html2plaintext(message.body or "")})
        return history
