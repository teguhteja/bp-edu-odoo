import logging
from odoo import models, fields, api

_logger = logging.getLogger(__name__)


class BpEduDosen(models.Model):
    _name = 'bp.edu.dosen'
    _description = 'Dosen'
    _rec_name = 'nama'
    _order = 'nama'

    nama = fields.Char(string='Nama Lengkap', required=True)
    nidn = fields.Char(string='NIDN')
    nuptk = fields.Char(string='NUPTK', help='Nomor Unik Pendidik dan Tenaga Kependidikan')
    pangkat_golongan = fields.Char(string='Pangkat/Golongan', default='-')
    jabatan = fields.Char(string='Jabatan Fungsional', help='Contoh: Asisten Ahli, Lektor, Lektor Kepala')
    email = fields.Char(string='Email')
    user_id = fields.Many2one(
        'res.users', string='Akun Pengguna',
        ondelete='set null', copy=False,
        help='Hubungkan dengan akun login Odoo agar dosen dapat login dan hanya melihat datanya sendiri.',
    )
    tanda_tangan = fields.Binary(string='Tanda Tangan', attachment=True)
    tanda_tangan_filename = fields.Char(string='Nama File TTD')
    active = fields.Boolean(default=True)

    _sql_constraints = [
        ('nidn_unique', 'UNIQUE(nidn)', 'NIDN sudah digunakan oleh dosen lain.'),
    ]

    def _compute_display_name(self):
        for rec in self:
            nidn_part = f' ({rec.nidn})' if rec.nidn else ''
            rec.display_name = f'{rec.nama}{nidn_part}'
