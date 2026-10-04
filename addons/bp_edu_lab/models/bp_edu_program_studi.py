from odoo import models, fields, _
from odoo.exceptions import UserError


class BpEduProgramStudi(models.Model):
    _inherit = 'bp.edu.program.studi'

    gedung = fields.Char(string='Gedung')
    alamat = fields.Char(string='Alamat')
    telepon = fields.Char(string='Telepon')
    deskripsi = fields.Text(string='Deskripsi')
    kelas_ids = fields.One2many('bp.edu.kelas', 'prodi_id', string='Kelas')

    def unlink(self):
        # Sama seperti lab-app: prodi yang masih punya kelas tidak boleh dihapus.
        if self.env['bp.edu.kelas'].with_context(active_test=False).search_count(
                [('prodi_id', 'in', self.ids)]):
            raise UserError(_('Program studi masih digunakan oleh kelas, tidak bisa dihapus.'))
        return super().unlink()
