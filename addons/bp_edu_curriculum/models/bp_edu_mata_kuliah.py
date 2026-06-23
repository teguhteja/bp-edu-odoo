import logging
from odoo import models, fields, api

_logger = logging.getLogger(__name__)


class BpEduMataKuliah(models.Model):
    _name = 'bp.edu.mata.kuliah'
    _description = 'Mata Kuliah'
    _rec_name = 'nama'
    _order = 'semester, kode'

    kode = fields.Char(string='Kode MK', required=True)
    nama = fields.Char(string='Nama Mata Kuliah', required=True)
    sks_teori = fields.Integer(string='SKS Teori', default=2)
    sks_praktik = fields.Integer(string='SKS Praktik', default=0)
    sks_total = fields.Integer(string='Total SKS', compute='_compute_sks_total', store=True)
    semester = fields.Integer(string='Semester', default=1)
    status = fields.Selection([
        ('Wajib', 'Wajib'),
        ('Pilihan', 'Pilihan'),
    ], string='Status', default='Wajib')
    kategori = fields.Selection([
        ('Mata Kuliah Umum', 'Mata Kuliah Umum'),
        ('Mata Kuliah Wajib Program Studi', 'Mata Kuliah Wajib Program Studi'),
        ('Mata Kuliah Pilihan Program Studi', 'Mata Kuliah Pilihan Program Studi'),
    ], string='Kategori')
    prodi_id = fields.Many2one('bp.edu.program.studi', string='Program Studi', ondelete='set null')
    deskripsi_singkat = fields.Text(string='Deskripsi Singkat')
    bahan_kajian = fields.Text(string='Bahan Kajian')
    matakuliah_syarat = fields.Char(string='Prasyarat MK', default='-')

    cpl_ids = fields.Many2many(
        'bp.edu.cpl',
        'bp_edu_mk_cpl_rel',
        'mk_id', 'cpl_id',
        string='CPL Prodi',
    )
    cpmk_ids = fields.One2many('bp.edu.cpmk', 'mata_kuliah_id', string='CPMK')
    pustaka_ids = fields.One2many('bp.edu.pustaka', 'mata_kuliah_id', string='Pustaka')

    _sql_constraints = [
        ('kode_unique', 'UNIQUE(kode)', 'Kode mata kuliah sudah digunakan.'),
    ]

    @api.depends('sks_teori', 'sks_praktik')
    def _compute_sks_total(self):
        for rec in self:
            rec.sks_total = (rec.sks_teori or 0) + (rec.sks_praktik or 0)

    def _compute_display_name(self):
        for rec in self:
            rec.display_name = f'[{rec.kode}] {rec.nama}'
