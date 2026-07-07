"""
Log setiap interaksi dengan AI Assistant — pertanyaan, respons, dan error.
"""
from odoo import models, fields


class AiAgentLog(models.Model):
    _name = 'ai.agent.log'
    _description = 'AI Assistant Log'
    _order = 'create_date desc'
    _rec_name = 'command'

    agent_id = fields.Many2one('ai.agent', string='Agent', ondelete='set null')
    user_id = fields.Many2one(
        'res.users', string='User',
        default=lambda self: self.env.uid, readonly=True,
    )
    command = fields.Text(string='Pertanyaan/Perintah', required=True)
    response = fields.Html(string='Respons AI')
    error_message = fields.Text(string='Pesan Error')
    state = fields.Selection([
        ('success', 'Berhasil'),
        ('error', 'Error'),
    ], string='Status', default='success', required=True)
    res_model = fields.Char(string='Model Terkait')
    res_id = fields.Integer(string='Record ID Terkait')
    duration = fields.Float(string='Durasi (detik)')

    def _compute_display_name(self):
        for rec in self:
            text = (rec.command or '').strip().replace('\n', ' ')
            rec.display_name = (text[:60] + '...') if len(text) > 60 else (text or f'Log #{rec.id}')
