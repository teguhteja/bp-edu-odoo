# Part of the EH AI Suite by ERP Heritage.
import logging

from odoo import _, api, fields, models

_logger = logging.getLogger(__name__)


class EhAiBudget(models.Model):
    _name = "eh.ai.budget"
    _description = "AI Spend Budget"
    _order = "name"

    name = fields.Char(required=True)
    active = fields.Boolean(default=True)
    scope = fields.Selection(
        selection=[
            ("global", "Everyone"),
            ("company", "Company"),
            ("agent", "Agent"),
            ("user", "User"),
        ],
        required=True,
        default="global",
    )
    agent_id = fields.Many2one("eh.ai.agent", ondelete="cascade")
    user_id = fields.Many2one("res.users", ondelete="cascade")
    company_id = fields.Many2one("res.company", default=lambda self: self.env.company)
    period = fields.Selection(
        selection=[("daily", "Daily"), ("monthly", "Monthly")],
        required=True,
        default="monthly",
    )
    limit_amount = fields.Float(string="Limit (USD)", digits=(12, 2), required=True)
    mode = fields.Selection(
        selection=[("soft_warn", "Warn only"), ("hard_stop", "Block requests")],
        required=True,
        default="hard_stop",
    )
    spent = fields.Float(string="Spent (USD)", compute="_compute_spent", digits=(12, 4))
    remaining = fields.Float(string="Remaining (USD)", compute="_compute_spent", digits=(12, 4))

    def _compute_spent(self):
        for budget in self:
            spent = budget._spent()
            budget.spent = spent
            budget.remaining = budget.limit_amount - spent

    # -- evaluation ----------------------------------------------------------

    def _period_start(self):
        self.ensure_one()
        # fields.Datetime.now() is naive UTC, matching how create_date is stored;
        # derive the boundary from it by truncation so the comparison stays in
        # the same (UTC) frame on any server.
        now = fields.Datetime.now()
        start = now.replace(hour=0, minute=0, second=0, microsecond=0)
        if self.period == "daily":
            return start
        return start.replace(day=1)

    def _scope_domain(self):
        self.ensure_one()
        if self.scope == "company":
            return [("company_id", "=", self.company_id.id)]
        if self.scope == "agent":
            return [("agent_id", "=", self.agent_id.id)]
        if self.scope == "user":
            return [("user_id", "=", self.user_id.id)]
        return []

    def _spent(self):
        self.ensure_one()
        domain = [
            ("create_date", ">=", self._period_start()),
            ("outcome", "=", "ok"),
        ] + self._scope_domain()
        groups = self.env["eh.ai.usage.log"].sudo()._read_group(domain, [], ["cost:sum"])
        return groups[0][0] or 0.0 if groups else 0.0

    def _applies_to(self, agent):
        self.ensure_one()
        if self.scope == "global":
            return True
        if self.scope == "company":
            return self.company_id == (agent.company_id or self.env.company)
        if self.scope == "agent":
            return self.agent_id == agent
        if self.scope == "user":
            return self.user_id.id == self.env.uid
        return False

    @api.model
    def _enforce(self, agent):
        """Check every applicable budget before an agent call.

        Raises if a hard-stop budget is exhausted; logs a warning for a
        soft-warn budget that is over.
        """
        from odoo.exceptions import UserError

        budgets = self.sudo().search([("active", "=", True)])
        for budget in budgets:
            if not budget._applies_to(agent) or budget.limit_amount <= 0:
                continue
            spent = budget._spent()
            if spent < budget.limit_amount:
                continue
            if budget.mode == "hard_stop":
                _logger.warning(
                    "EH AI: hard budget '%s' blocked a request (%.2f / %.2f USD)",
                    budget.name, spent, budget.limit_amount,
                )
                raise UserError(_(
                    "AI budget '%(name)s' is exhausted (%(spent).2f / %(limit).2f USD "
                    "this %(period)s). The request was blocked.",
                    name=budget.name, spent=spent, limit=budget.limit_amount,
                    period=budget.period,
                ))
            _logger.warning(
                "EH AI: soft budget '%s' over (%.2f / %.2f USD)",
                budget.name, spent, budget.limit_amount,
            )
