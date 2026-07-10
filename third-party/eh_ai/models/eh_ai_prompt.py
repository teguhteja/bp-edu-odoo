# Part of the EH AI Suite by ERP Heritage.
from odoo import _, api, fields, models


class EhAiPrompt(models.Model):
    _name = "eh.ai.prompt"
    _description = "AI Prompt Template"
    _order = "name"

    name = fields.Char(required=True)
    active = fields.Boolean(default=True)
    kind = fields.Selection(
        selection=[
            ("system", "System Prompt"),
            ("rag_instruction", "RAG Instruction"),
            ("tool_guidance", "Tool Guidance"),
        ],
        default="system",
        required=True,
    )
    body = fields.Text(required=True)
    revision_ids = fields.One2many("eh.ai.prompt.revision", "prompt_id", readonly=True)
    current_revision_id = fields.Many2one("eh.ai.prompt.revision", readonly=True)
    version = fields.Integer(related="current_revision_id.version", string="Version", readonly=True)

    @api.model_create_multi
    def create(self, vals_list):
        prompts = super().create(vals_list)
        for prompt in prompts:
            prompt._snapshot_revision()
        return prompts

    def write(self, vals):
        result = super().write(vals)
        if "body" in vals:
            for prompt in self:
                prompt._snapshot_revision()
        return result

    def _snapshot_revision(self):
        self.ensure_one()
        last = max(self.revision_ids.mapped("version") or [0])
        revision = self.env["eh.ai.prompt.revision"].create({
            "prompt_id": self.id,
            "version": last + 1,
            "body": self.body or "",
        })
        # Writing current_revision_id does not include 'body', so no recursion.
        self.current_revision_id = revision


class EhAiPromptRevision(models.Model):
    _name = "eh.ai.prompt.revision"
    _description = "AI Prompt Revision"
    _order = "version desc"

    prompt_id = fields.Many2one("eh.ai.prompt", required=True, ondelete="cascade", index=True)
    version = fields.Integer(required=True)
    body = fields.Text()
    is_current = fields.Boolean(compute="_compute_is_current")

    @api.depends("prompt_id.current_revision_id")
    def _compute_is_current(self):
        for revision in self:
            revision.is_current = revision == revision.prompt_id.current_revision_id

    def action_restore(self):
        self.ensure_one()
        # Writing body snapshots a new revision capturing the restore.
        self.prompt_id.write({"body": self.body})
        return {
            "type": "ir.actions.client",
            "tag": "display_notification",
            "params": {
                "type": "success",
                "message": _("Restored version %s.", self.version),
                "next": {"type": "ir.actions.act_window_close"},
            },
        }
