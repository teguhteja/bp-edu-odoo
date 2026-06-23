import logging
from odoo import models, fields

_logger = logging.getLogger(__name__)


class BpEduDocxTemplate(models.Model):
    _name = 'bp.edu.docx.template'
    _description = 'Template DOCX'
    _rec_name = 'name'
    _order = 'document_type, name'

    name = fields.Char(string='Nama Template', required=True)
    document_type = fields.Selection([
        ('rps', 'RPS'),
        ('sap', 'SAP'),
        ('kontrak', 'Kontrak Kuliah'),
    ], string='Jenis Dokumen', required=True)
    template_file = fields.Binary(
        string='File Template (.docx)',
        attachment=True,
        required=True,
    )
    template_filename = fields.Char(string='Nama File')
    description = fields.Text(string='Keterangan')
    active = fields.Boolean(default=True)

    def _compute_display_name(self):
        label_map = dict(self._fields['document_type'].selection)
        for rec in self:
            rec.display_name = f'[{label_map.get(rec.document_type, "")}] {rec.name}'
