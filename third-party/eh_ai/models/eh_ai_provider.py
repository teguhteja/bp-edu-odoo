# Part of the EH AI Suite by ERP Heritage.
import json
import os

from odoo import _, api, fields, models


class EhAiProvider(models.Model):
    _name = "eh.ai.provider"
    _description = "AI Provider"
    _order = "sequence, name"

    name = fields.Char(required=True)
    code = fields.Selection(
        selection=[
            ("openai", "OpenAI"),
            ("google", "Google"),
            ("azure_openai", "Azure OpenAI"),
            ("ollama", "Ollama / Local"),
            ("openai_compatible", "OpenAI-compatible endpoint"),
        ],
        required=True,
        default="openai",
        help="Determines which wire format adapter is used to talk to the provider. "
             "Additional providers can be added by extending modules.",
    )
    sequence = fields.Integer(default=10)
    active = fields.Boolean(default=True)
    base_url = fields.Char(
        required=True,
        help="API root, without a trailing slash. For example "
             "https://api.openai.com/v1 or http://localhost:11434/v1.",
    )
    auth_scheme = fields.Selection(
        selection=[
            ("bearer", "Bearer token"),
            ("header_key", "API key header"),
            ("none", "No authentication"),
        ],
        default="bearer",
        required=True,
        help="How the API key is sent. Bearer for OpenAI-style, API key header "
             "for Azure, none for an unauthenticated local endpoint.",
    )
    api_key = fields.Char(
        help="Stored key for this provider. Leave empty to fall back to the "
             "system parameter or environment variable below.",
        groups="base.group_system",
    )
    config_param_key = fields.Char(
        string="System Parameter",
        help="Optional ir.config_parameter name used as a fallback source for the key.",
    )
    env_var = fields.Char(
        string="Environment Variable",
        help="Optional environment variable used as a final fallback for the key.",
    )
    extra_headers = fields.Text(
        help="Optional JSON object of additional HTTP headers to send with every request.",
    )
    model_ids = fields.One2many("eh.ai.model", "provider_id", string="Models")
    model_count = fields.Integer(compute="_compute_model_count")
    has_key = fields.Boolean(compute="_compute_has_key", string="Key Configured")

    @api.depends("model_ids")
    def _compute_model_count(self):
        for provider in self:
            provider.model_count = len(provider.model_ids)

    def _compute_has_key(self):
        for provider in self:
            provider.has_key = bool(provider.sudo()._get_api_key())

    def _get_api_key(self):
        self.ensure_one()
        if self.api_key:
            return self.api_key
        if self.config_param_key:
            param = self.env["ir.config_parameter"].sudo().get_param(self.config_param_key)
            if param:
                return param
        if self.env_var:
            value = os.getenv(self.env_var)
            if value:
                return value
        return False

    def _get_extra_headers(self):
        self.ensure_one()
        if not self.extra_headers:
            return {}
        try:
            data = json.loads(self.extra_headers)
            if isinstance(data, dict):
                return {str(k): str(v) for k, v in data.items()}
        except (ValueError, TypeError):
            pass
        return {}

    def get_adapter(self):
        """Return an instantiated provider adapter for this record."""
        self.ensure_one()
        from odoo.addons.eh_ai.utils.providers import build_provider
        return build_provider(self.env, self)
