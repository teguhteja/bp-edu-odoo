import logging
from odoo import models, fields

_logger = logging.getLogger(__name__)


class BpEduCpmk(models.Model):
    _name = 'bp.edu.cpmk'
    _description = 'Capaian Pembelajaran Mata Kuliah'
    _rec_name = 'kode'
    _order = 'mata_kuliah_id, kode'

    kode = fields.Char(string='Kode CPMK', required=True, help='Contoh: CPMK-1, CPMK-2')
    mata_kuliah_id = fields.Many2one(
        'bp.edu.mata.kuliah', string='Mata Kuliah',
        required=True, ondelete='cascade',
    )
    cpl_ids = fields.Many2many(
        'bp.edu.cpl',
        'bp_edu_cpmk_cpl_rel',
        'cpmk_id', 'cpl_id',
        string='CPL Terkait',
    )
    # cpl_text menyimpan string asli dari JSON, e.g. "P-01, KU-01"
    cpl_text = fields.Char(string='CPL (teks)', help='Referensi CPL dalam teks, sesuai format JSON')
    deskripsi = fields.Text(string='Deskripsi', required=True)

    sub_cpmk_ids = fields.One2many('bp.edu.sub.cpmk', 'cpmk_id', string='Sub-CPMK')

    def _compute_display_name(self):
        for rec in self:
            rec.display_name = f'{rec.kode}: {rec.deskripsi[:50]}...' if rec.deskripsi and len(rec.deskripsi) > 50 else f'{rec.kode}: {rec.deskripsi or ""}'
