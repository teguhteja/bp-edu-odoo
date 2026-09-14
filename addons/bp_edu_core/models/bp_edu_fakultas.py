from odoo import models, fields


class BpEduFakultas(models.Model):
    _name = 'bp.edu.fakultas'
    _description = 'Fakultas'
    _rec_name = 'nama'
    _order = 'nama'

    kode = fields.Char(string='Kode Fakultas')
    nama = fields.Char(string='Nama Fakultas', required=True)
    dekan_id = fields.Many2one(
        'bp.edu.dosen', string='Dekan',
        help='Dekan Fakultas. Lewat group Dekan, dosen ini melihat seluruh '
             'mata kuliah di semua program studi di bawah fakultas ini.',
    )
    prodi_ids = fields.One2many('bp.edu.program.studi', 'fakultas_id', string='Program Studi')
    active = fields.Boolean(default=True)

    _sql_constraints = [
        ('kode_unique', 'UNIQUE(kode)', 'Kode fakultas sudah digunakan.'),
    ]
