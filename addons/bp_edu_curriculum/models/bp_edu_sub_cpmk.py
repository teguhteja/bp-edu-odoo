import logging
from odoo import models, fields

_logger = logging.getLogger(__name__)


class BpEduSubCpmk(models.Model):
    _name = 'bp.edu.sub.cpmk'
    _description = 'Sub-Capaian Pembelajaran Mata Kuliah'
    _rec_name = 'kode'
    _order = 'cpmk_id, kode'

    kode = fields.Char(string='Kode Sub-CPMK', required=True, help='Contoh: Sub-CPMK 1')
    cpmk_id = fields.Many2one(
        'bp.edu.cpmk', string='CPMK',
        required=True, ondelete='cascade',
    )
    mata_kuliah_id = fields.Many2one(
        related='cpmk_id.mata_kuliah_id',
        string='Mata Kuliah',
        store=True, readonly=True,
    )
    deskripsi = fields.Text(string='Deskripsi', required=True)
    minggu = fields.Char(string='Minggu', help='Contoh: 1–2, 3, 6–7')
    level_bloom = fields.Char(string='Level Bloom', help='Contoh: C2, C3, C3–P4')
