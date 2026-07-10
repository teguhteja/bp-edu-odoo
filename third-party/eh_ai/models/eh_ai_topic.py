# Part of the EH AI Suite by ERP Heritage.
from odoo import fields, models


class EhAiTopic(models.Model):
    _name = "eh.ai.topic"
    _description = "AI Topic"
    _order = "name"

    name = fields.Char(required=True)
    active = fields.Boolean(default=True)
    description = fields.Char(help="Short note shown to administrators.")
    instructions = fields.Text(
        help="Behavioural guidance added to the system prompt when an agent uses this topic.",
    )
    tool_ids = fields.Many2many(
        "ir.actions.server",
        "eh_ai_topic_tool_rel",
        "topic_id",
        "action_id",
        string="Tools",
        domain=[("eh_ai_use_in_tool", "=", True)],
        help="Server actions exposed to the model as callable tools for this topic.",
    )
