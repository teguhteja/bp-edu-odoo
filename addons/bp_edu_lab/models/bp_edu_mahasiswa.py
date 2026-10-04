from odoo import api, models, fields, _
from odoo.exceptions import UserError


class BpEduMahasiswa(models.Model):
    _name = 'bp.edu.mahasiswa'
    _description = 'Mahasiswa'
    _inherit = ['mail.thread', 'mail.activity.mixin']
    _rec_name = 'nama'
    _order = 'nim'

    nim = fields.Char(string='NIM', required=True, tracking=True)
    nama = fields.Char(string='Nama Mahasiswa', required=True, tracking=True)
    email = fields.Char(string='Email', required=True, tracking=True)
    telepon = fields.Char(string='Telepon')
    alamat = fields.Char(string='Alamat')
    tanggal_lahir = fields.Date(string='Tanggal Lahir')
    gender = fields.Selection([
        ('laki', 'Laki-laki'),
        ('perempuan', 'Perempuan'),
    ], string='Jenis Kelamin')
    foto = fields.Image(string='Foto', max_width=512, max_height=512)
    prodi_id = fields.Many2one('bp.edu.program.studi', string='Program Studi', required=True)
    kelas_id = fields.Many2one('bp.edu.kelas', string='Kelas',
                               domain="[('prodi_id', '=', prodi_id)]")
    angkatan = fields.Integer(related='kelas_id.angkatan', store=True, string='Angkatan')
    tahun = fields.Integer(string='Tahun Masuk')
    deskripsi = fields.Text(string='Deskripsi')
    user_id = fields.Many2one('res.users', string='Akun Pengguna', copy=False, tracking=True,
                              help='Akun login (portal) mahasiswa. Ditautkan otomatis '
                                   'berdasarkan kesamaan email.')
    peserta_ids = fields.One2many('bp.edu.lab.peserta', 'mahasiswa_id', string='Riwayat Praktikum')
    active = fields.Boolean(default=True)

    _nim_unique = models.Constraint('UNIQUE(nim)', 'NIM sudah digunakan.')
    _email_unique = models.Constraint('UNIQUE(email)', 'Email mahasiswa sudah digunakan.')
    _user_unique = models.Constraint('UNIQUE(user_id)', 'Akun pengguna sudah tertaut ke mahasiswa lain.')

    def _compute_display_name(self):
        for rec in self:
            rec.display_name = f'[{rec.nim}] {rec.nama}' if rec.nim else rec.nama

    @api.model
    def _normalize_email(self, email):
        return (email or '').strip().lower()

    @api.model_create_multi
    def create(self, vals_list):
        for vals in vals_list:
            if vals.get('email'):
                vals['email'] = self._normalize_email(vals['email'])
        records = super().create(vals_list)
        records._link_user()
        return records

    def write(self, vals):
        if vals.get('email'):
            vals['email'] = self._normalize_email(vals['email'])
        res = super().write(vals)
        if 'email' in vals:
            # Email berubah: tautan lama tidak lagi sahih, cari ulang berdasarkan email baru
            # (perilaku sama dengan Mahasiswa::linkKeUser di lab-app).
            for rec in self.filtered('user_id'):
                if self._normalize_email(rec.user_id.login) != rec.email \
                        and self._normalize_email(rec.user_id.email) != rec.email:
                    rec.user_id = False
            self._link_user()
        return res

    def _link_user(self):
        """Tautkan mahasiswa ke res.users yang login/email-nya sama, bila belum tertaut."""
        Users = self.env['res.users'].sudo().with_context(active_test=False)
        for rec in self.filtered(lambda m: m.email and not m.user_id):
            user = Users.search(['|', ('login', '=ilike', rec.email), ('email', '=ilike', rec.email)],
                                limit=1)
            if user and not self.search_count([('user_id', '=', user.id)]):
                rec.user_id = user

    def action_buat_akses_portal(self):
        """Buat akun portal untuk mahasiswa yang belum punya akun."""
        portal_group = self.env.ref('base.group_portal')
        Users = self.env['res.users'].sudo().with_context(no_reset_password=True)
        for rec in self:
            if rec.user_id:
                continue
            rec._link_user()
            if rec.user_id:
                continue
            if not rec.email:
                raise UserError(_('Mahasiswa %s belum punya email.', rec.nama))
            rec.user_id = Users.create({
                'name': rec.nama,
                'login': rec.email,
                'email': rec.email,
                'group_ids': [(6, 0, [portal_group.id])],
            })
        return True
