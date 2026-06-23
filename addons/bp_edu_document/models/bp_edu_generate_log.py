import logging
from odoo import models, fields

_logger = logging.getLogger(__name__)


class BpEduGenerateLog(models.Model):
    _name = 'bp.edu.generate.log'
    _description = 'History Generate Dokumen'
    _rec_name = 'name'
    _order = 'create_date desc'

    name = fields.Char(string='Nama Dokumen', required=True)
    document_type = fields.Selection([
        ('rps', 'RPS'),
        ('sap', 'SAP'),
        ('kontrak', 'Kontrak Kuliah'),
    ], string='Jenis', required=True)
    mata_kuliah_id = fields.Many2one('bp.edu.mata.kuliah', string='Mata Kuliah')
    template_id = fields.Many2one('bp.edu.docx.template', string='Template')
    attachment_id = fields.Many2one('ir.attachment', string='File Hasil')
    user_id = fields.Many2one('res.users', string='Dibuat oleh', default=lambda self: self.env.user)
    create_date = fields.Datetime(string='Waktu Generate', readonly=True)

    def action_download(self):
        self.ensure_one()
        if not self.attachment_id:
            return
        return {
            'type': 'ir.actions.act_url',
            'url': f'/web/content/{self.attachment_id.id}?download=true',
            'target': 'new',
        }
