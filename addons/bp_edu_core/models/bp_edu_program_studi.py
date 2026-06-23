import logging
from odoo import models, fields

_logger = logging.getLogger(__name__)


class BpEduProgramStudi(models.Model):
    _name = 'bp.edu.program.studi'
    _description = 'Program Studi'
    _rec_name = 'nama'
    _order = 'jenjang, nama'

    kode = fields.Char(string='Kode Prodi', required=True)
    nama = fields.Char(string='Nama Program Studi', required=True)
    jenjang = fields.Selection([
        ('d3', 'D3'),
        ('s1', 'S1'),
        ('s2', 'S2'),
        ('s3', 'S3'),
    ], string='Jenjang', default='s1', required=True)
    active = fields.Boolean(default=True)

    _sql_constraints = [
        ('kode_unique', 'UNIQUE(kode)', 'Kode program studi sudah digunakan.'),
    ]

    def _compute_display_name(self):
        for rec in self:
            rec.display_name = f'[{rec.jenjang.upper() if rec.jenjang else ""}] {rec.nama}'
