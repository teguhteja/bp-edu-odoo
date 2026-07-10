"""
Webhook endpoint untuk integrasi eksternal dengan TTM AI Assistant.
"""
import logging

from odoo import http
from odoo.http import request

_logger = logging.getLogger(__name__)


class TtmAiWebhook(http.Controller):

    @http.route('/ttm_ai/ask', type='jsonrpc', auth='user', methods=['POST'], csrf=False)
    def ask(self, **kwargs):
        """
        Panggil AI secara langsung via HTTP POST.

        Body JSON:
            command (str, required): Perintah/pertanyaan untuk AI
            model   (str, optional): Odoo model name untuk context
            id      (int, optional): Record ID untuk context

        Response JSON:
            {"response": "<html>...", "status": "ok"}
            {"error": "...", "status": "error"}
        """
        body = request.get_json_data() or {}
        command = (body.get('command') or '').strip()
        res_model = body.get('model') or None
        res_id = body.get('id') or None

        if not command:
            return {'error': 'field "command" wajib diisi', 'status': 'error'}

        _logger.info('Webhook AI call: %r | model=%s id=%s', command[:100], res_model, res_id)

        try:
            response_html = request.env['ai.agent'].sudo().call_from_settings(
                command,
                res_model=res_model,
                res_id=int(res_id) if res_id else None,
            )
            return {'response': response_html, 'status': 'ok'}
        except Exception as e:
            _logger.exception('Webhook AI error')
            return {'error': str(e), 'status': 'error'}

    @http.route('/ttm_ai/health', type='http', auth='public', methods=['GET'])
    def health(self, **kwargs):
        """Health check sederhana."""
        return 'TTM AI Assistant — OK'
