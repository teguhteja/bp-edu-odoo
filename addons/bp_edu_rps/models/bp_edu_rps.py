import logging
from odoo import models, fields, api
from odoo.exceptions import ValidationError

_logger = logging.getLogger(__name__)


class BpEduRps(models.Model):
    _name = 'bp.edu.rps'
    _description = 'Rencana Pembelajaran Semester'
    _inherit = ['mail.thread', 'mail.activity.mixin']
    _rec_name = 'display_name'
    _order = 'tahun_akademik_id desc, mata_kuliah_id'

    mata_kuliah_id = fields.Many2one(
        'bp.edu.mata.kuliah', string='Mata Kuliah',
        required=True, ondelete='restrict', tracking=True,
    )
    dosen_id = fields.Many2one(
        'bp.edu.dosen', string='Dosen Koordinator',
        required=True, ondelete='restrict', tracking=True,
        help='Dosen penanggung jawab (koordinator) mata kuliah ini. '
             'Hanya dia yang dapat mengubah RPS ini.',
    )
    dosen_ids = fields.Many2many(
        'bp.edu.dosen', 'bp_edu_rps_dosen_rel', 'rps_id', 'dosen_id',
        string='Dosen Pengampu', tracking=True,
        help='Dosen-dosen yang mengampu mata kuliah ini. Mereka ikut dapat '
             'melihat RPS ini walaupun bukan dosen koordinatornya.',
    )
    tahun_akademik_id = fields.Many2one(
        'bp.edu.tahun.akademik', string='Tahun Akademik',
        ondelete='restrict', tracking=True,
    )
    tanggal_penyusunan = fields.Date(string='Tanggal Penyusunan', tracking=True)
    state = fields.Selection([
        ('draft', 'Draft'),
        ('final', 'Final'),
    ], string='Status', default='draft', required=True, tracking=True)

    # Computed dari mata_kuliah_id untuk kemudahan template
    kode_mk = fields.Char(related='mata_kuliah_id.kode', string='Kode MK', store=True)
    nama_mk = fields.Char(related='mata_kuliah_id.nama', string='Nama MK', store=True)
    semester = fields.Integer(related='mata_kuliah_id.semester', string='Semester', store=True)
    prodi_id = fields.Many2one(
        'bp.edu.program.studi', related='mata_kuliah_id.prodi_id',
        string='Program Studi', store=True,
    )

    pustaka_ids = fields.One2many(
        related='mata_kuliah_id.pustaka_ids',
        string='Buku Ajar / Pustaka',
        readonly=True,
    )

    detail_ids = fields.One2many('bp.edu.rps.detail', 'rps_id', string='Detail Per Minggu')

    def copy(self, default=None):
        default = dict(default or {})
        default.setdefault('tahun_akademik_id', False)
        return super().copy(default)

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
