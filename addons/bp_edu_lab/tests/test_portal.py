from datetime import timedelta
from urllib.parse import parse_qs, urlparse

from odoo import fields
from odoo.tests import HttpCase, new_test_user, tagged

from .common import LabDataMixin


@tagged('post_install', '-at_install')
class TestPortalPraktikum(LabDataMixin, HttpCase):
    """Halaman portal mahasiswa /my/praktikum (pengganti halaman user/* di lab-app)."""

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls._setup_lab_data()
        cls.praktikum.write({'token': 'ABC123', 'token_expired_at': fields.Datetime.now() + timedelta(hours=4)})

    def _pesan(self, response):
        return parse_qs(urlparse(response.url).query).get('pesan', [''])[0]

    def _csrf(self):
        return self.opener.get(self.base_url() + '/my/praktikum').text.split('name="csrf_token" value="')[1].split('"')[0]

    def test_harus_login(self):
        response = self.url_open('/my/praktikum', allow_redirects=False)
        self.assertIn(response.status_code, (302, 303))
        self.assertIn('/web/login', response.headers['Location'])

    def test_halaman_daftar_praktikum(self):
        self.authenticate('mhs1@test.example', 'mhs1@test.example')
        response = self.url_open('/my/praktikum')
        self.assertEqual(response.status_code, 200)
        self.assertIn('Pertemuan Tes', response.text)
        self.assertIn('o_lab_form_presensi', response.text)
        self.assertIn('o_lab_ujian_pra', response.text)

    def test_akun_belum_terhubung(self):
        new_test_user(self.env, login='lepas@test.example', groups='base.group_portal')
        self.authenticate('lepas@test.example', 'lepas@test.example')
        response = self.url_open('/my/praktikum')
        self.assertIn('o_lab_belum_terhubung', response.text)

    def test_presensi_lewat_portal(self):
        self.authenticate('mhs1@test.example', 'mhs1@test.example')
        url = f'/my/praktikum/{self.praktikum.id}/presensi'
        response = self.url_open(url, data={'token': 'SALAH1', 'csrf_token': self._csrf()})
        self.assertIn('Kode token salah', self._pesan(response))
        self.assertFalse(self.peserta.presensi)

        response = self.url_open(url, data={'token': 'abc123', 'csrf_token': self._csrf()})
        self.assertEqual(self._pesan(response), 'Berhasil Presensi')
        self.peserta.invalidate_recordset()
        self.assertTrue(self.peserta.presensi)

    def test_upload_berkas(self):
        self.authenticate('mhs1@test.example', 'mhs1@test.example')
        response = self.url_open(
            f'/my/praktikum/{self.praktikum.id}/berkas',
            data={'csrf_token': self._csrf()},
            files={'berkas': ('laporan.pdf', b'%PDF-1.4 isi laporan', 'application/pdf')},
        )
        self.assertEqual(self._pesan(response), 'Berkas Berhasil Diupload')
        self.peserta.invalidate_recordset()
        self.assertEqual(self.peserta.berkas_nama, 'laporan.pdf')
        self.assertTrue(self.peserta.berkas)

    def test_ujian_diarahkan_ke_survey(self):
        self.authenticate('mhs1@test.example', 'mhs1@test.example')
        response = self.url_open(f'/my/praktikum/{self.praktikum.id}/ujian/pra', allow_redirects=False)
        self.assertIn(response.status_code, (302, 303))
        self.assertIn(f'/survey/start/{self.pretest.access_token}', response.headers['Location'])

    def test_ujian_ditutup(self):
        self.praktikum.write({'tanggal': self.today - timedelta(days=3), 'due_date': self.today - timedelta(days=1)})
        self.authenticate('mhs1@test.example', 'mhs1@test.example')
        response = self.url_open(f'/my/praktikum/{self.praktikum.id}/ujian/post')
        self.assertIn('melewati batas', self._pesan(response))

    def test_retry_survey_kembali_ke_praktikum(self):
        """Route "Take Again" survey tidak boleh membuat jawaban baru tanpa praktikum."""
        answer = self.praktikum.mulai_ujian(self.mhs, 'pra')
        jumlah = self.env['survey.user_input'].search_count([('survey_id', '=', self.pretest.id)])
        self.authenticate('mhs1@test.example', 'mhs1@test.example')
        response = self.url_open(f'/survey/retry/{self.pretest.access_token}/{answer.access_token}',
                                 allow_redirects=False)
        self.assertIn(response.status_code, (302, 303))
        self.assertTrue(response.headers['Location'].endswith('/my/praktikum'))
        self.assertEqual(self.env['survey.user_input'].search_count([('survey_id', '=', self.pretest.id)]), jumlah)

    def test_tour_portal_mahasiswa(self):
        """E2E: mahasiswa presensi dengan token lalu mengerjakan pretest sampai selesai."""
        self.start_tour('/my/praktikum', 'bp_edu_lab_portal_tour', login='mhs1@test.example')
        self.peserta.invalidate_recordset()
        self.assertTrue(self.peserta.presensi)
        answer = self.env['survey.user_input'].search([
            ('praktikum_id', '=', self.praktikum.id), ('mahasiswa_id', '=', self.mhs.id), ('jenis_ujian', '=', 'pra')])
        self.assertEqual(answer.state, 'done')
        self.assertEqual(answer.user_input_line_ids.value_text_box, 'Bahasa markup untuk web')


@tagged('post_install', '-at_install')
class TestTourAdminLab(LabDataMixin, HttpCase):

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls._setup_lab_data()
        cls.admin_lab = new_test_user(cls.env, login='laboran', groups='bp_edu_lab.group_lab_admin',
                                      name='Laboran Tes')

    def test_tour_admin(self):
        """E2E: laboran membuka praktikum, generate token, lalu mengisi nilai di Penilaian."""
        self.start_tour('/odoo/action-bp_edu_lab.bp_edu_lab_praktikum_action', 'bp_edu_lab_admin_tour',
                        login='laboran')
        self.assertTrue(self.praktikum.token)
        self.assertEqual(self.peserta.nilai, 87)
