# Part of the EH AI Suite by ERP Heritage.
from odoo import api, fields, models


class EhAiModel(models.Model):
    _name = "eh.ai.model"
    _description = "AI Model"
    _order = "provider_id, sequence, name"

    name = fields.Char(string="Display Name", required=True)
    technical_name = fields.Char(
        required=True,
        help="The model identifier sent to the provider, for example gpt-4.1 or gemini-2.5-flash.",
    )
    provider_id = fields.Many2one("eh.ai.provider", required=True, ondelete="cascade")
    provider_code = fields.Selection(related="provider_id.code", store=True)
    sequence = fields.Integer(default=10)
    active = fields.Boolean(default=True)

    kind = fields.Selection(
        selection=[("chat", "Chat"), ("embedding", "Embedding")],
        default="chat",
        required=True,
    )

    # Capability descriptor. Drives request shaping and, later, cost reporting.
    supports_tools = fields.Boolean(default=True)
    supports_vision = fields.Boolean(default=False)
    supports_temperature = fields.Boolean(
        default=True,
        help="Some reasoning models reject sampling parameters. Disable to omit "
             "temperature from requests for this model.",
    )
    context_window = fields.Integer(help="Maximum input tokens.")
    max_output_tokens = fields.Integer(default=4096)
    embedding_dimensions = fields.Integer(help="Vector size for embedding models.")

    price_input_per_mtok = fields.Float(
        string="Input $/MTok", digits=(12, 4),
        help="Cost per million input tokens, used for usage reporting.",
    )
    price_output_per_mtok = fields.Float(string="Output $/MTok", digits=(12, 4))
    price_cached_input_per_mtok = fields.Float(string="Cached Input $/MTok", digits=(12, 4))

    display_label = fields.Char(compute="_compute_display_label")

    @api.depends("name", "provider_id.name")
    def _compute_display_label(self):
        for record in self:
            provider = record.provider_id.name or ""
            record.display_label = "%s / %s" % (provider, record.name) if provider else record.name

    @api.depends("name", "provider_id.name", "technical_name")
    def _compute_display_name(self):
        for record in self:
            record.display_name = "%s (%s)" % (record.name, record.technical_name)
