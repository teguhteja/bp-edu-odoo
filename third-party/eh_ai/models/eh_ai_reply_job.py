# Part of the EH AI Suite by ERP Heritage.
import logging
from datetime import timedelta

from odoo import _, api, fields, models
from odoo.exceptions import UserError
from odoo.tools import plaintext2html

_logger = logging.getLogger(__name__)

PROCESS_LIMIT = 20
# Finished jobs are an audit trail, not state; drop them after this many days.
JOB_RETENTION_DAYS = 7
# Cap the stored error text so a verbose traceback cannot bloat the row.
ERROR_MAX_CHARS = 2000


class EhAiReplyJob(models.Model):
    """A queued agent reply.

    Generating a reply means a blocking call to an external LLM, which can take
    seconds to minutes. Doing that inside ``message_post`` would tie up the HTTP
    worker that served the user's message for the whole round-trip. Instead the
    channel enqueues a job and triggers a cron, so the reply is generated in a
    background worker and posted back when it is ready (the chat updates live
    over the bus, the same way Enterprise behaves).
    """

    _name = "eh.ai.reply.job"
    _description = "Pending AI Agent Reply"
    _order = "id"

    channel_id = fields.Many2one("discuss.channel", required=True, ondelete="cascade", index=True)
    agent_id = fields.Many2one("eh.ai.agent", required=True, ondelete="cascade")
    user_id = fields.Many2one("res.users", required=True, ondelete="cascade")
    message_id = fields.Many2one("mail.message", ondelete="cascade")
    prompt = fields.Text(required=True)
    state = fields.Selection(
        selection=[("pending", "Pending"), ("done", "Done"), ("error", "Error")],
        default="pending",
        required=True,
        index=True,
    )
    error = fields.Text()

    @api.model
    def _cron_process(self):
        jobs = self.search([("state", "=", "pending")], limit=PROCESS_LIMIT)
        for job in jobs:
            # Isolate each job in a savepoint so one failure (even a database
            # error that aborts the cursor) cannot roll back the whole batch or
            # leave the job stuck 'pending' to be retried forever.
            try:
                with self.env.cr.savepoint():
                    job._process()
            except Exception:  # noqa: BLE001 - never abort the batch on one job
                _logger.exception("EH AI: reply job %s aborted", job.id)
                job._mark_error(_("Processing aborted."))
        self._gc_finished_jobs()
        if self.search_count([("state", "=", "pending")]):
            self.env.ref("eh_ai.ir_cron_agent_replies")._trigger()

    @api.model
    def _gc_finished_jobs(self):
        cutoff = fields.Datetime.now() - timedelta(days=JOB_RETENTION_DAYS)
        stale = self.search([
            ("state", "in", ("done", "error")),
            ("create_date", "<", cutoff),
        ])
        if stale:
            stale.unlink()

    def _process(self):
        self.ensure_one()
        channel = self.channel_id
        agent = self.agent_id
        ok = True
        try:
            history = channel._eh_ai_history(exclude_message=self.message_id)
            # Run as the human who asked, so budgets and tool record-rules are
            # attributed to them rather than to the cron's superuser.
            result = agent.with_user(self.user_id).generate_response(self.prompt, history=history)
            text = result.get("text") or ""
        except UserError as error:
            # User-facing by design (e.g. an exhausted budget): show it.
            text = str(error)
            self.error = str(error)[:ERROR_MAX_CHARS]
            ok = False
        except Exception as error:  # noqa: BLE001 - keep the cron alive, hide internals
            # Log the full traceback server-side, but never surface internal
            # error detail to chat participants.
            _logger.exception("EH AI: reply job %s failed", self.id)
            text = _("Sorry, I could not generate a reply. Please try again.")
            self.error = str(error)[:ERROR_MAX_CHARS]
            ok = False

        # Posting is also fallible (access/DB), so guard it too: the job must
        # always reach a terminal state and never linger as 'pending'.
        try:
            channel.with_context(eh_ai_skip_agent=True).message_post(
                body=plaintext2html(text),
                author_id=agent.partner_id.id,
                message_type="comment",
                subtype_xmlid="mail.mt_comment",
            )
        except Exception as error:  # noqa: BLE001 - never leave the job pending
            _logger.exception("EH AI: failed to post reply for job %s", self.id)
            self.error = ("post failed: %s" % error)[:ERROR_MAX_CHARS]
            ok = False
        self.state = "done" if ok else "error"

    def _mark_error(self, message):
        self.ensure_one()
        self.write({"state": "error", "error": (message or "")[:ERROR_MAX_CHARS]})
