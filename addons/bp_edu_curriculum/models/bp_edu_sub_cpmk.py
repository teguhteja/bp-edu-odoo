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
        help='CPMK utama/pemilik baris ini (menentukan letaknya di form CPMK). '
             'Untuk Sub-CPMK yang merujuk banyak CPMK sekaligus, lihat juga field CPMK Terkait.',
    )
    # Beberapa Sub-CPMK di JSON rps_bp merujuk lebih dari satu CPMK sekaligus,
    # mis. "CPMK-3, CPMK-5" atau rentang "CPMK-1 s.d. CPMK-5". cpmk_id di atas
    # tetap menyimpan CPMK pertama/utama (dipakai untuk nesting di form CPMK);
    # cpmk_ids menyimpan seluruh CPMK yang dirujuk, cpmk_text menyimpan teks
    # asli dari JSON -- pola yang sama dengan cpl_text/cpl_ids di bp.edu.cpmk.
    cpmk_ids = fields.Many2many(
        'bp.edu.cpmk',
        'bp_edu_sub_cpmk_cpmk_rel',
        'sub_cpmk_id', 'cpmk_id_rel',
        string='CPMK Terkait',
        help='Seluruh CPMK yang dirujuk Sub-CPMK ini (termasuk CPMK utama di atas).',
    )
    cpmk_text = fields.Char(string='CPMK (teks)', help='Referensi CPMK dalam teks, sesuai format JSON')
    mata_kuliah_id = fields.Many2one(
        related='cpmk_id.mata_kuliah_id',
        string='Mata Kuliah',
        store=True, readonly=True,
    )
    deskripsi = fields.Text(string='Deskripsi', required=True)
    minggu = fields.Char(string='Minggu', help='Contoh: 1–2, 3, 6–7')
    level_bloom = fields.Char(string='Level Bloom', help='Contoh: C2, C3, C3–P4')
