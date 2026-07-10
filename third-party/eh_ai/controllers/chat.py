# Part of the EH AI Suite by ERP Heritage.
from odoo import http
from odoo.http import request


class EhAiChatController(http.Controller):

    @http.route("/eh_ai/agent/message", type="json", auth="user")
    def agent_message(self, agent_id, message, history=None, context=None):
        agent = request.env["eh.ai.agent"].browse(int(agent_id))
        agent.check_access("read")
        result = agent.generate_response(
            message, history=history or [], extra_context=context or None)
        return {"text": result.get("text", "")}
