import secrets
import string
from datetime import datetime, time, timedelta

import pytz

from odoo import api, models, fields, _
from odoo.exceptions import UserError

TOKEN_CHARS = string.ascii_uppercase + string.digits
TOKEN_LENGTH = 6
TOKEN_BERLAKU_JAM = 4
TZ_DEFAULT = 'Asia/Makassar'

JENIS_UJIAN = [('pra', 'Pretest'), ('post', 'Posttest')]


class BpEduLabPraktikum(models.Model):
    _name = 'bp.edu.lab.praktikum'
    _description = 'Sesi Praktikum'
    _inherit = ['mail.thread', 'mail.activity.mixin']
    _rec_name = 'nama'
    _order = 'tanggal desc, id desc'

    nama = fields.Char(string='Nama Praktikum', required=True, tracking=True)
    ruang = fields.Char(string='Ruang')
    tanggal = fields.Date(string='Tanggal Praktikum', required=True, tracking=True,
                          default=fields.Date.context_today)
    due_date = fields.Date(string='Batas Posttest', tracking=True,
                           help='Posttest bisa dikerjakan sejak tanggal praktikum sampai tanggal ini.')
    mata_kuliah_id = fields.Many2one('bp.edu.mata.kuliah', string='Mata Kuliah', required=True,
                                     tracking=True)
    pretest_id = fields.Many2one('survey.survey', string='Pretest',
                                 domain="[('jenis_ujian', '=', 'pra')]")
    posttest_id = fields.Many2one('survey.survey', string='Posttest',
                                  domain="[('jenis_ujian', '=', 'post')]")
    deskripsi = fields.Text(string='Deskripsi')
    token = fields.Char(string='Token Presensi', copy=False, readonly=True)
    token_expired_at = fields.Datetime(string='Token Berlaku Sampai', copy=False, readonly=True)
    kelompok_ids = fields.One2many('bp.edu.lab.kelompok', 'praktikum_id', string='Kelompok')
    peserta_ids = fields.One2many('bp.edu.lab.peserta', 'praktikum_id', string='Peserta')
    jumlah_kelompok = fields.Integer(compute='_compute_jumlah', string='Jumlah Kelompok')
    jumlah_peserta = fields.Integer(compute='_compute_jumlah', string='Jumlah Peserta')
    jumlah_hadir = fields.Integer(compute='_compute_jumlah', string='Jumlah Hadir')

    @api.depends('kelompok_ids', 'peserta_ids.presensi')
    def _compute_jumlah(self):
        for rec in self:
            rec.jumlah_kelompok = len(rec.kelompok_ids)
            rec.jumlah_peserta = len(rec.peserta_ids)
            rec.jumlah_hadir = len(rec.peserta_ids.filtered('presensi'))

    def unlink(self):
        if self.env['bp.edu.lab.kelompok'].search_count([('praktikum_id', 'in', self.ids)]):
            raise UserError(_('Praktikum sudah memiliki kelompok, tidak bisa dihapus.'))
        return super().unlink()

    # ------------------------------------------------------------------
    # Token presensi
    # ------------------------------------------------------------------
    def action_generate_token(self):
        for rec in self:
            rec.write({
                'token': ''.join(secrets.choice(TOKEN_CHARS) for _i in range(TOKEN_LENGTH)),
                'token_expired_at': fields.Datetime.now() + timedelta(hours=TOKEN_BERLAKU_JAM),
            })
        return True

    def submit_presensi(self, mahasiswa, token):
        """Presensi mahasiswa memakai token. Mengembalikan peserta, atau UserError dengan
        pesan yang sama seperti AbsensiController::submitPresensi di lab-app."""
        self.ensure_one()
        if not mahasiswa:
            raise UserError(_('Akun Anda belum terhubung ke data mahasiswa, hubungi admin.'))
        if not self.token or (token or '').strip().upper() != self.token.upper():
            raise UserError(_('Kode token salah.'))
        if not self.token_expired_at or fields.Datetime.now() > self.token_expired_at:
            raise UserError(_('Kode token sudah kadaluwarsa, minta kode baru ke dosen/laboran.'))
        peserta = self._get_peserta(mahasiswa)
        if not peserta:
            raise UserError(_('Anda belum terdaftar di kelompok untuk praktikum ini, hubungi admin.'))
        peserta.write({'presensi': True, 'waktu_presensi': fields.Datetime.now()})
        return peserta

    def _get_peserta(self, mahasiswa):
        self.ensure_one()
        return self.env['bp.edu.lab.peserta'].sudo().search(
            [('praktikum_id', '=', self.id), ('mahasiswa_id', '=', mahasiswa.id)], limit=1)

    # ------------------------------------------------------------------
    # Pretest / posttest
    # ------------------------------------------------------------------
    def _get_survey(self, jenis):
        self.ensure_one()
        return self.pretest_id if jenis == 'pra' else self.posttest_id

    @api.model
    def _get_tz(self):
        return pytz.timezone(self.env.user.tz or TZ_DEFAULT)

    def _hari_ini(self):
        return datetime.now(self._get_tz()).date()

    def cek_jendela_waktu(self, jenis, hari_ini=None):
        """Mengembalikan pesan kegagalan, atau False bila ujian boleh dikerjakan.
        Pretest: sampai akhir tanggal praktikum. Posttest: tanggal praktikum s/d due date."""
        self.ensure_one()
        hari_ini = hari_ini or self._hari_ini()
        if jenis == 'pra':
            if self.tanggal and hari_ini > self.tanggal:
                return _('Pretest hanya bisa dikerjakan sebelum/pada tanggal praktikum.')
            return False
        if self.tanggal and hari_ini < self.tanggal:
            return _('Posttest baru bisa dikerjakan mulai tanggal praktikum berlangsung.')
        if self.due_date and hari_ini > self.due_date:
            return _('Posttest sudah melewati batas waktu (due date).')
        return False

    def _batas_waktu_ujian(self, jenis):
        """Akhir jendela waktu ujian dalam UTC naif (untuk survey.user_input.deadline)."""
        self.ensure_one()
        tanggal_akhir = self.tanggal if jenis == 'pra' else self.due_date
        if not tanggal_akhir:
            return False
        akhir_lokal = self._get_tz().localize(datetime.combine(tanggal_akhir, time.max))
        return akhir_lokal.astimezone(pytz.utc).replace(tzinfo=None, microsecond=0)

    def mulai_ujian(self, mahasiswa, jenis):
        """Validasi lalu kembalikan survey.user_input milik mahasiswa untuk ujian ini.
        Satu jawaban per (praktikum, mahasiswa, jenis); mengerjakan ulang selama jendela
        waktu masih terbuka memakai jawaban yang sama (seperti updateOrCreate di lab-app)."""
        self.ensure_one()
        if jenis not in ('pra', 'post'):
            raise UserError(_('Jenis ujian tidak dikenal.'))
        if not mahasiswa:
            raise UserError(_('Akun Anda belum terhubung ke data mahasiswa, hubungi admin.'))
        if not self._get_peserta(mahasiswa):
            raise UserError(_('Anda tidak terdaftar di praktikum ini.'))
        survey = self.sudo()._get_survey(jenis)
        if not survey or not survey.question_ids:
            raise UserError(_('Tidak ada soal untuk jenis ujian ini.'))
        pesan = self.cek_jendela_waktu(jenis)
        if pesan:
            raise UserError(pesan)

        UserInput = self.env['survey.user_input'].sudo()
        answer = UserInput.search([
            ('praktikum_id', '=', self.id),
            ('mahasiswa_id', '=', mahasiswa.id),
            ('jenis_ujian', '=', jenis),
            ('survey_id', '=', survey.id),
        ], limit=1)
        deadline = self._batas_waktu_ujian(jenis)
        if answer:
            vals = {'deadline': deadline}
            if answer.state == 'done':
                vals['state'] = 'in_progress'
            answer.write(vals)
            return answer
        user = mahasiswa.user_id
        return survey._create_answer(
            user=user, check_attempts=False,
            praktikum_id=self.id, mahasiswa_id=mahasiswa.id, jenis_ujian=jenis,
            deadline=deadline,
        )

    # ------------------------------------------------------------------
    # Navigasi
    # ------------------------------------------------------------------
    def action_buka_penilaian(self):
        self.ensure_one()
        action = self.env['ir.actions.act_window']._for_xml_id('bp_edu_lab.bp_edu_lab_peserta_penilaian_action')
        action['domain'] = [('praktikum_id', '=', self.id)]
        action['context'] = {'default_praktikum_id': self.id}
        action['display_name'] = _('Penilaian - %s', self.nama)
        return action
