from odoo import _, fields, models


class SbsIrActionsServer(models.Model):
    _inherit = "ir.actions.server"

    state = fields.Selection(
        selection_add=[("sbs_refresh", "Reload Views")],
        ondelete={"sbs_refresh": "cascade"},
    )
    sbs_refresh_view_types = fields.Char(
        string="View Types",
        help=(
            "Comma-separated list of view types to reload (for example, list, "
            "kanban). Leave empty to reload all view types."
        ),
    )

    def _generate_action_name(self):
        if self.state == "sbs_refresh":
            return _("Reload Views")
        return super()._generate_action_name()

    def _run_action_sbs_refresh_multi(self, eval_context=None):
        eval_context = eval_context or {}
        records = eval_context.get("records") or eval_context.get("record")
        message = {
            "model": self.model_id.model,
            "view_types": [
                view_type.strip()
                for view_type in (self.sbs_refresh_view_types or "").split(",")
                if view_type.strip()
            ],
            "rec_ids": records.ids if records else [],
        }
        self.env["bus.bus"]._sendone(
            "broadcast",
            "sbs_custom_style.reload",
            message,
        )
