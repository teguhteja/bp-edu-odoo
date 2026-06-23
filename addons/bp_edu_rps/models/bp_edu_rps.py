import logging
from odoo import models, fields, api
from odoo.exceptions import ValidationError

_logger = logging.getLogger(__name__)


class BpEduRps(models.Model):
    _name = 'bp.edu.rps'
    _description = 'Rencana Pembelajaran Semester'
    _rec_name = 'display_name'
    _order = 'tahun_akademik_id desc, mata_kuliah_id'

    mata_kuliah_id = fields.Many2one(
        'bp.edu.mata.kuliah', string='Mata Kuliah',
        required=True, ondelete='restrict',
    )
    dosen_id = fields.Many2one(
        'bp.edu.dosen', string='Dosen Pengampu',
        required=True, ondelete='restrict',
    )
    tahun_akademik_id = fields.Many2one(
        'bp.edu.tahun.akademik', string='Tahun Akademik',
        ondelete='restrict',
    )
    tanggal_penyusunan = fields.Date(string='Tanggal Penyusunan')
    state = fields.Selection([
        ('draft', 'Draft'),
        ('final', 'Final'),
    ], string='Status', default='draft', required=True)

    # Computed dari mata_kuliah_id untuk kemudahan template
    kode_mk = fields.Char(related='mata_kuliah_id.kode', string='Kode MK', store=True)
    nama_mk = fields.Char(related='mata_kuliah_id.nama', string='Nama MK', store=True)

    detail_ids = fields.One2many('bp.edu.rps.detail', 'rps_id', string='Detail Per Minggu')

    def _compute_display_name(self):
        for rec in self:
            mk = rec.mata_kuliah_id.display_name if rec.mata_kuliah_id else '?'
            ta = rec.tahun_akademik_id.display_name if rec.tahun_akademik_id else ''
            rec.display_name = f'RPS – {mk} ({ta})' if ta else f'RPS – {mk}'

    def action_finalize(self):
        self.write({'state': 'final'})

    def action_reset_draft(self):
        self.write({'state': 'draft'})

    def action_buat_detail_kosong(self):
        """Buat 16 baris detail kosong jika belum ada."""
        self.ensure_one()
        if self.detail_ids:
            raise ValidationError('Detail sudah ada. Hapus terlebih dahulu sebelum generate ulang.')
        vals = [{'rps_id': self.id, 'minggu': i} for i in range(1, 17)]
        self.env['bp.edu.rps.detail'].create(vals)


class BpEduRpsDetail(models.Model):
    _name = 'bp.edu.rps.detail'
    _description = 'Detail RPS per Minggu'
    _rec_name = 'minggu'
    _order = 'rps_id, minggu'

    rps_id = fields.Many2one(
        'bp.edu.rps', string='RPS',
        required=True, ondelete='cascade',
    )
    minggu = fields.Integer(string='Minggu', required=True)

    # Kolom identik dengan field di JSON rps_bp
    deskripsi = fields.Text(
        string='Deskripsi / Sub-CPMK',
        help='Sub-CPMK yang dicapai pada minggu ini',
    )
    indikator = fields.Text(string='Indikator Penilaian')
    kriteria = fields.Text(string='Kriteria & Bentuk Penilaian')
    tatap_muka = fields.Text(string='Tatap Muka')
    daring = fields.Text(string='Daring / Blended')
    materi = fields.Text(string='Materi / Pokok Bahasan')
    bobot = fields.Char(string='Bobot (%)', help='Contoh: 3%, 15%')

    @api.constrains('minggu')
    def _check_minggu(self):
        for rec in self:
            if not (1 <= rec.minggu <= 16):
                raise ValidationError('Nomor minggu harus antara 1 dan 16.')
