import logging
from odoo import models, fields

_logger = logging.getLogger(__name__)


class BpEduCpl(models.Model):
    _name = 'bp.edu.cpl'
    _description = 'Capaian Pembelajaran Lulusan'
    _rec_name = 'kode'
    _order = 'prodi_id, tipe, kode'

    # Tipe menggunakan nilai string yang identik dengan JSON rps_bp untuk kemudahan import
    TIPE_SELECTION = [
        ('Sikap', 'Sikap'),
        ('Pengetahuan', 'Pengetahuan'),
        ('Keterampilan Umum', 'Keterampilan Umum'),
        ('Keterampilan Khusus', 'Keterampilan Khusus'),
    ]

    kode = fields.Char(string='Kode CPL', required=True, help='Contoh: S-09, P-01, KU-01, KK-01')
    tipe = fields.Selection(TIPE_SELECTION, string='Tipe', required=True)
    deskripsi = fields.Text(string='Deskripsi', required=True)
    prodi_id = fields.Many2one('bp.edu.program.studi', string='Program Studi', ondelete='set null')

    _sql_constraints = [
        ('kode_prodi_unique', 'UNIQUE(kode, prodi_id)', 'Kode CPL sudah ada untuk program studi ini.'),
    ]

    def _compute_display_name(self):
        for rec in self:
            rec.display_name = f'{rec.kode} – {rec.deskripsi[:60]}...' if rec.deskripsi and len(rec.deskripsi) > 60 else f'{rec.kode} – {rec.deskripsi or ""}'
