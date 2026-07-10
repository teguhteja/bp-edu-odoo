# Part of the EH AI Suite by ERP Heritage.
from odoo import http
from odoo.http import request


class EhAiSearchController(http.Controller):

    @http.route("/eh_ai/nl_search", type="json", auth="user")
    def nl_search(self, model, query, fields=None):
        # search() already only returns agents the caller may read; the explicit
        # check keeps this endpoint consistent with the chat controller.
        agent = request.env["eh.ai.agent"].search([("active", "=", True)], limit=1)
        if not agent:
            return {"domain": []}
        agent.check_access("read")
        return {"domain": agent._nl_search(model, query, fields or [])}
