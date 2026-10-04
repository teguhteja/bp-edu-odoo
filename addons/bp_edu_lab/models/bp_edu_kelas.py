from odoo import models, fields, _
from odoo.exceptions import UserError


class BpEduKelas(models.Model):
    _name = 'bp.edu.kelas'
    _description = 'Kelas'
    _rec_name = 'nama'
    _order = 'angkatan desc, nama'

    nama = fields.Char(string='Nama Kelas', required=True)
    kode = fields.Char(string='Kode Kelas', required=True)
    angkatan = fields.Integer(string='Angkatan')
    prodi_id = fields.Many2one('bp.edu.program.studi', string='Program Studi', required=True)
    deskripsi = fields.Text(string='Deskripsi')
    mahasiswa_ids = fields.One2many('bp.edu.mahasiswa', 'kelas_id', string='Mahasiswa')
    jumlah_mahasiswa = fields.Integer(string='Jumlah Mahasiswa', compute='_compute_jumlah_mahasiswa')
    active = fields.Boolean(default=True)

    _kode_unique = models.Constraint('UNIQUE(kode)', 'Kode kelas sudah digunakan.')

    def _compute_jumlah_mahasiswa(self):
        data = self.env['bp.edu.mahasiswa']._read_group(
            [('kelas_id', 'in', self.ids)], ['kelas_id'], ['__count'])
        counts = {kelas.id: count for kelas, count in data}
        for rec in self:
            rec.jumlah_mahasiswa = counts.get(rec.id, 0)

    def unlink(self):
        if self.env['bp.edu.mahasiswa'].with_context(active_test=False).search_count(
                [('kelas_id', 'in', self.ids)]):
            raise UserError(_('Kelas masih memiliki mahasiswa, tidak bisa dihapus.'))
        return super().unlink()
