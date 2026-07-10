# Part of the EH AI Suite by ERP Heritage.
from odoo import fields, models


class ResConfigSettings(models.TransientModel):
    _inherit = "res.config.settings"

    eh_ai_openai_key = fields.Char(
        string="OpenAI API Key",
        config_parameter="eh_ai.openai_key",
    )
    eh_ai_google_key = fields.Char(
        string="Google Gemini API Key",
        config_parameter="eh_ai.google_key",
    )
    eh_ai_xai_key = fields.Char(
        string="xAI (Grok) API Key",
        config_parameter="eh_ai.xai_key",
    )
