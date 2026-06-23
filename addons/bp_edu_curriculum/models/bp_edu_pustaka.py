import logging
from odoo import models, fields

_logger = logging.getLogger(__name__)


class BpEduPustaka(models.Model):
    _name = 'bp.edu.pustaka'
    _description = 'Referensi Pustaka'
    _rec_name = 'kode'
    _order = 'mata_kuliah_id, jenis desc, kode'

    kode = fields.Char(string='Kode', required=True, help='Contoh: P1, P2, P3')
    mata_kuliah_id = fields.Many2one(
        'bp.edu.mata.kuliah', string='Mata Kuliah',
        required=True, ondelete='cascade',
    )
    jenis = fields.Selection([
        ('Utama', 'Utama'),
        ('Pendukung', 'Pendukung'),
    ], string='Jenis', required=True, default='Utama')
    referensi = fields.Text(string='Referensi', required=True,
                            help='Teks lengkap referensi dalam format APA/Chicago')
