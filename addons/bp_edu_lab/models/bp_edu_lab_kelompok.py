from odoo import api, models, fields, _
from odoo.exceptions import UserError


class BpEduLabKelompok(models.Model):
    _name = 'bp.edu.lab.kelompok'
    _description = 'Kelompok Praktikum'
    _inherit = ['mail.thread']
    _rec_name = 'nama'
    _order = 'praktikum_id desc, nama'

    nama = fields.Char(string='Nama Kelompok', required=True)
    praktikum_id = fields.Many2one('bp.edu.lab.praktikum', string='Praktikum', required=True,
                                   ondelete='restrict', tracking=True)
    kelas_id = fields.Many2one('bp.edu.kelas', string='Kelas')
    prodi_id = fields.Many2one('bp.edu.program.studi', string='Program Studi',
                               compute='_compute_dari_kelas', store=True, readonly=False)
    angkatan = fields.Integer(string='Angkatan', compute='_compute_dari_kelas', store=True,
                              readonly=False)
    deskripsi = fields.Text(string='Deskripsi')
    state = fields.Selection([
        ('draft', 'Belum Praktikum'),
        ('selesai', 'Sudah Praktikum'),
    ], string='Status', default='draft', required=True, tracking=True)
    peserta_ids = fields.One2many('bp.edu.lab.peserta', 'kelompok_id', string='Anggota')
    jumlah_anggota = fields.Integer(compute='_compute_jumlah_anggota', string='Jumlah Anggota')

    @api.depends('kelas_id')
    def _compute_dari_kelas(self):
        for rec in self:
            if rec.kelas_id:
                rec.prodi_id = rec.kelas_id.prodi_id
                rec.angkatan = rec.kelas_id.angkatan

    @api.depends('peserta_ids')
    def _compute_jumlah_anggota(self):
        for rec in self:
            rec.jumlah_anggota = len(rec.peserta_ids)

    def write(self, vals):
        # Lab-app menolak mengubah kelompok yang sudah praktikum; nilai/presensi tetap bisa
        # diisi lewat menu Penilaian (yang menulis ke bp.edu.lab.peserta langsung).
        terkunci = {'nama', 'praktikum_id', 'kelas_id', 'peserta_ids'}
        if terkunci & set(vals) and self.filtered(lambda k: k.state == 'selesai'):
            raise UserError(_('Kelompok Sudah Praktikum! Kembalikan ke status draft untuk mengubah.'))
        return super().write(vals)

    def action_tambah_mahasiswa_kelas(self):
        """Isi anggota dengan semua mahasiswa aktif di kelas yang belum menjadi anggota."""
        for rec in self:
            if not rec.kelas_id:
                raise UserError(_('Pilih kelas terlebih dahulu.'))
            sudah = rec.praktikum_id.peserta_ids.mahasiswa_id
            baru = rec.kelas_id.mahasiswa_ids - sudah
            rec.write({'peserta_ids': [(0, 0, {'mahasiswa_id': m.id}) for m in baru]})
        return True

    def action_selesai(self):
        self.write({'state': 'selesai'})

    def action_draft(self):
        self.write({'state': 'draft'})


class BpEduLabPeserta(models.Model):
    _name = 'bp.edu.lab.peserta'
    _description = 'Peserta Praktikum'
    _rec_name = 'mahasiswa_id'
    _order = 'praktikum_id desc, kelompok_id, mahasiswa_id'

    kelompok_id = fields.Many2one('bp.edu.lab.kelompok', string='Kelompok', required=True,
                                  ondelete='cascade', index=True)
    praktikum_id = fields.Many2one(related='kelompok_id.praktikum_id', store=True, index=True,
                                   string='Praktikum')
    mata_kuliah_id = fields.Many2one(related='praktikum_id.mata_kuliah_id', store=True,
                                     string='Mata Kuliah')
    tanggal = fields.Date(related='praktikum_id.tanggal', store=True, string='Tanggal')
    mahasiswa_id = fields.Many2one('bp.edu.mahasiswa', string='Mahasiswa', required=True,
                                   ondelete='restrict', index=True)
    nim = fields.Char(related='mahasiswa_id.nim', string='NIM')
    kelas_id = fields.Many2one(related='mahasiswa_id.kelas_id', store=True, string='Kelas')
    angkatan = fields.Integer(related='mahasiswa_id.angkatan', store=True, string='Angkatan')
    presensi = fields.Boolean(string='Hadir')
    waktu_presensi = fields.Datetime(string='Waktu Presensi')
    berkas = fields.Binary(string='Berkas', attachment=True)
    berkas_nama = fields.Char(string='Nama Berkas')
    nilai = fields.Float(string='Nilai', digits=(5, 2), aggregator='avg')
    jawaban_ids = fields.One2many('survey.user_input', compute='_compute_jawaban_ids',
                                  string='Jawaban Ujian')

    _praktikum_mahasiswa_unique = models.Constraint(
        'UNIQUE(praktikum_id, mahasiswa_id)',
        'Mahasiswa sudah terdaftar di kelompok lain pada praktikum ini.',
    )
    _nilai_range = models.Constraint(
        'CHECK(nilai >= 0 AND nilai <= 100)', 'Nilai harus di antara 0 dan 100.',
    )

    def _compute_jawaban_ids(self):
        UserInput = self.env['survey.user_input'].sudo()
        for rec in self:
            rec.jawaban_ids = UserInput.search([
                ('praktikum_id', '=', rec.praktikum_id.id),
                ('mahasiswa_id', '=', rec.mahasiswa_id.id),
            ])

    def action_lihat_jawaban(self):
        self.ensure_one()
        return {
            'type': 'ir.actions.act_window',
            'name': _('Jawaban %s', self.mahasiswa_id.nama),
            'res_model': 'survey.user_input',
            'view_mode': 'list,form',
            'domain': [('id', 'in', self.jawaban_ids.ids)],
            'context': {'create': False},
        }
