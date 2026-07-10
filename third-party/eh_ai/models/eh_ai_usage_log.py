# Part of the EH AI Suite by ERP Heritage.
from odoo import api, fields, models


class EhAiUsageLog(models.Model):
    _name = "eh.ai.usage.log"
    _description = "AI Usage Log"
    _order = "create_date desc, id desc"

    agent_id = fields.Many2one("eh.ai.agent", ondelete="set null", index=True)
    provider_id = fields.Many2one("eh.ai.provider", ondelete="set null", index=True)
    model_id = fields.Many2one("eh.ai.model", ondelete="set null", index=True)
    user_id = fields.Many2one("res.users", index=True)
    company_id = fields.Many2one("res.company", index=True)

    input_tokens = fields.Integer()
    output_tokens = fields.Integer()
    cached_tokens = fields.Integer()
    total_tokens = fields.Integer(compute="_compute_total_tokens", store=True)
    cost = fields.Float(string="Cost (USD)", digits=(12, 6))
    latency_ms = fields.Integer(string="Latency (ms)")
    outcome = fields.Selection(
        selection=[
            ("ok", "OK"),
            ("error", "Error"),
            ("budget_block", "Blocked (budget)"),
        ],
        default="ok",
        index=True,
    )

    @api.depends("input_tokens", "output_tokens", "cached_tokens")
    def _compute_total_tokens(self):
        # cached_tokens are a subset of input_tokens (the provider counts them
        # inside the prompt total), so total = input + output. cached_tokens is
        # in @api.depends only so an independent edit retriggers the compute.
        for record in self:
            record.total_tokens = (record.input_tokens or 0) + (record.output_tokens or 0)

    @api.model
    def _compute_cost(self, model, usage):
        if not model:
            return 0.0
        inp = usage.get("input_tokens", 0) or 0
        out = usage.get("output_tokens", 0) or 0
        cached = usage.get("cached_tokens", 0) or 0
        billed_input = max(inp - cached, 0)
        cached_price = model.price_cached_input_per_mtok or model.price_input_per_mtok
        total = (
            billed_input * model.price_input_per_mtok
            + cached * cached_price
            + out * model.price_output_per_mtok
        )
        return total / 1_000_000.0

    @api.model
    def _record(self, agent, model, usage, latency_ms=0, outcome="ok"):
        # usage is {} for a failed call (outcome="error"): an explicit
        # zero-token, zero-cost audit row, not a billable one (budget._spent
        # filters to outcome="ok").
        usage = usage or {}
        return self.sudo().create({
            "agent_id": agent.id if agent else False,
            "provider_id": model.provider_id.id if model else False,
            "model_id": model.id if model else False,
            "user_id": self.env.uid,
            "company_id": (agent.company_id.id if agent and agent.company_id else self.env.company.id),
            "input_tokens": usage.get("input_tokens", 0),
            "output_tokens": usage.get("output_tokens", 0),
            "cached_tokens": usage.get("cached_tokens", 0),
            "cost": self._compute_cost(model, usage),
            "latency_ms": latency_ms,
            "outcome": outcome,
        })
