"""
Model riwayat perubahan field untuk RPS, SAP, dan Kontrak Kuliah.
"""
from odoo import models, fields


class BpEduFieldHistory(models.Model):
    _name = 'bp.edu.field.history'
    _description = 'Riwayat Perubahan Field'
    _order = 'create_date desc, id desc'
    _rec_name = 'field_label'
    _log_access = True

    model_name = fields.Char('Model', readonly=True, required=True, index=True)
    res_id     = fields.Integer('Record ID', readonly=True, required=True, index=True)
    res_name   = fields.Char('Record', readonly=True)
    field_name  = fields.Char('Field (teknis)', readonly=True, required=True)
    field_label = fields.Char('Field', readonly=True, required=True)
    old_value  = fields.Text('Nilai Lama', readonly=True)
    new_value  = fields.Text('Nilai Baru', readonly=True)
    changed_by = fields.Many2one(
        'res.users', string='Diubah oleh',
        readonly=True, ondelete='set null', index=True,
    )
    # create_date (auto Odoo) = waktu perubahan terjadi
