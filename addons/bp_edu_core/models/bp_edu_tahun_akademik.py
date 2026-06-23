import logging
from odoo import models, fields, api
from odoo.exceptions import ValidationError

_logger = logging.getLogger(__name__)


class BpEduTahunAkademik(models.Model):
    _name = 'bp.edu.tahun.akademik'
    _description = 'Tahun Akademik'
    _rec_name = 'nama'
    _order = 'nama desc, semester'

    nama = fields.Char(string='Tahun Akademik', required=True, help='Contoh: 2025/2026')
    semester = fields.Selection([
        ('ganjil', 'Ganjil'),
        ('genap', 'Genap'),
    ], string='Semester', required=True)
    tanggal_mulai = fields.Date(string='Tanggal Mulai')
    tanggal_selesai = fields.Date(string='Tanggal Selesai')
    aktif = fields.Boolean(string='Semester Aktif', default=False)

    def _compute_display_name(self):
        for rec in self:
            semester_label = dict(rec._fields['semester'].selection).get(rec.semester, '')
            rec.display_name = f'{rec.nama} {semester_label}'

    @api.constrains('aktif')
    def _check_single_active(self):
        for rec in self:
            if rec.aktif:
                others = self.search([('aktif', '=', True), ('id', '!=', rec.id)])
                if others:
                    raise ValidationError(
                        'Hanya satu tahun akademik yang boleh aktif. '
                        f'Nonaktifkan terlebih dahulu: {others[0].display_name}'
                    )

    def action_set_active(self):
        self.search([('aktif', '=', True)]).write({'aktif': False})
        self.write({'aktif': True})
