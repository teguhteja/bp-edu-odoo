import logging
from odoo import models, fields, api
from odoo.exceptions import ValidationError

_logger = logging.getLogger(__name__)


class BpEduKontrakKuliah(models.Model):
    _name = 'bp.edu.kontrak.kuliah'
    _description = 'Kontrak Kuliah'
    _rec_name = 'display_name'
    _order = 'tahun_akademik_id desc, mata_kuliah_id'

    # ── Identitas ───────────────────────────────────────────────
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
    # Identik nama field JSON untuk kemudahan import/export
    periode = fields.Char(string='Periode', help='Contoh: Ganjil, Genap')
    kelas = fields.Char(string='Kelas', default='A')
    hari_jam = fields.Char(string='Hari & Jam', help='Contoh: Selasa, 14:00 - 15:40')
    jenis_mk = fields.Char(
        string='Jenis MK',
        help='Contoh: Mata Kuliah Wajib Umum, Mata Kuliah Wajib Program Studi',
    )
    prasyarat = fields.Char(string='Prasyarat', default='-')

    # ── Bobot Penilaian (%) ─────────────────────────────────────
    bobot_diskusi = fields.Integer(string='Bobot Diskusi (%)', default=10)
    bobot_proyek = fields.Integer(string='Bobot Proyek (%)', default=20)
    bobot_tugas = fields.Integer(string='Bobot Tugas (%)', default=10)
    bobot_kuis = fields.Integer(string='Bobot Kuis (%)', default=10)
    bobot_uts = fields.Integer(string='Bobot UTS (%)', default=20)
    bobot_uas = fields.Integer(string='Bobot UAS (%)', default=30)
    total_bobot = fields.Integer(
        string='Total Bobot (%)', compute='_compute_total_bobot', store=True,
    )

    # ── Jumlah Penugasan ────────────────────────────────────────
    jumlah_kuis_mingguan = fields.Integer(string='Jumlah Kuis Mingguan', default=1)
    jumlah_tugas_terstruktur = fields.Integer(string='Jumlah Tugas Terstruktur', default=8)
    jumlah_proyek = fields.Integer(string='Jumlah Proyek', default=1)

    # ── Wakil Mahasiswa ─────────────────────────────────────────
    wakil_mahasiswa = fields.Char(string='Nama Wakil Mahasiswa')
    nim_wakil = fields.Char(string='NIM Wakil Mahasiswa')

    # ── CPMK (dari mata kuliah, bisa di-override) ───────────────
    cpmk_ids = fields.Many2many(
        'bp.edu.cpmk',
        'bp_edu_kontrak_cpmk_rel',
        'kontrak_id', 'cpmk_id',
        string='CPMK',
    )

    # ── Materi Per Minggu ───────────────────────────────────────
    materi_ids = fields.One2many(
        'bp.edu.kontrak.materi', 'kontrak_id', string='Materi Per Minggu',
    )

    def _compute_display_name(self):
        for rec in self:
            mk = rec.mata_kuliah_id.display_name if rec.mata_kuliah_id else '?'
            ta = rec.tahun_akademik_id.display_name if rec.tahun_akademik_id else ''
            rec.display_name = f'Kontrak – {mk} ({ta})' if ta else f'Kontrak – {mk}'

    @api.depends('bobot_diskusi', 'bobot_proyek', 'bobot_tugas', 'bobot_kuis', 'bobot_uts', 'bobot_uas')
    def _compute_total_bobot(self):
        for rec in self:
            rec.total_bobot = (
                rec.bobot_diskusi + rec.bobot_proyek + rec.bobot_tugas
                + rec.bobot_kuis + rec.bobot_uts + rec.bobot_uas
            )

    @api.constrains('bobot_diskusi', 'bobot_proyek', 'bobot_tugas', 'bobot_kuis', 'bobot_uts', 'bobot_uas')
    def _check_total_bobot(self):
        for rec in self:
            if rec.total_bobot != 100:
                raise ValidationError(
                    f'Total bobot penilaian harus 100%. Saat ini: {rec.total_bobot}%'
                )

    @api.onchange('mata_kuliah_id')
    def _onchange_mata_kuliah_id(self):
        """Auto-isi CPMK dan jenis MK dari mata kuliah yang dipilih."""
        if self.mata_kuliah_id:
            self.cpmk_ids = self.mata_kuliah_id.cpmk_ids
            self.jenis_mk = self.mata_kuliah_id.kategori or ''
            self.prasyarat = self.mata_kuliah_id.matakuliah_syarat or '-'

    def action_buat_materi_kosong(self):
        """Buat 16 baris materi minggu kosong jika belum ada."""
        self.ensure_one()
        if self.materi_ids:
            raise ValidationError('Materi sudah ada. Hapus terlebih dahulu sebelum generate ulang.')
        vals = [{'kontrak_id': self.id, 'minggu': i} for i in range(1, 17)]
        self.env['bp.edu.kontrak.materi'].create(vals)


class BpEduKontrakMateri(models.Model):
    _name = 'bp.edu.kontrak.materi'
    _description = 'Materi Per Minggu – Kontrak Kuliah'
    _rec_name = 'minggu'
    _order = 'kontrak_id, minggu'

    kontrak_id = fields.Many2one(
        'bp.edu.kontrak.kuliah', string='Kontrak Kuliah',
        required=True, ondelete='cascade',
    )
    minggu = fields.Integer(string='Minggu', required=True)
    materi = fields.Text(string='Materi')

    @api.constrains('minggu')
    def _check_minggu(self):
        for rec in self:
            if not (1 <= rec.minggu <= 16):
                raise ValidationError('Nomor minggu harus antara 1 dan 16.')
