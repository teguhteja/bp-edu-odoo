from odoo import models, fields, _
from odoo.exceptions import UserError


class BpEduMataKuliah(models.Model):
    _inherit = 'bp.edu.mata.kuliah'

    dosen_pengampu = fields.Char(
        string='Dosen Pengampu (Lab)',
        help='Nama dosen pengampu praktikum sebagai teks bebas, sesuai data lab-app.',
    )
    praktikum_ids = fields.One2many('bp.edu.lab.praktikum', 'mata_kuliah_id', string='Praktikum')

    def unlink(self):
        if self.env['bp.edu.lab.praktikum'].search_count([('mata_kuliah_id', 'in', self.ids)]):
            raise UserError(_('Mata kuliah masih digunakan oleh praktikum, tidak bisa dihapus.'))
        return super().unlink()
