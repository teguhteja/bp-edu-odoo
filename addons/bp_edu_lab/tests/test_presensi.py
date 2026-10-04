from datetime import timedelta

from freezegun import freeze_time

from odoo import fields
from odoo.exceptions import UserError
from odoo.tests import tagged

from .common import LabCommon


@tagged('post_install', '-at_install')
class TestPresensiToken(LabCommon):
    """Port dari lab-app tests/Feature/PresensiTokenTest.php"""

    def test_generate_token(self):
        self.praktikum.action_generate_token()
        self.assertRegex(self.praktikum.token, r'^[A-Z0-9]{6}$')
        selisih = self.praktikum.token_expired_at - fields.Datetime.now()
        self.assertAlmostEqual(selisih.total_seconds(), 4 * 3600, delta=60)

    def test_token_salah(self):
        self.praktikum.action_generate_token()
        with self.assertRaisesRegex(UserError, 'Kode token salah'):
            self.praktikum.submit_presensi(self.mhs, 'XXXXXX')
        self.assertFalse(self.peserta.presensi)

    def test_token_kadaluwarsa(self):
        self.praktikum.action_generate_token()
        with freeze_time(fields.Datetime.now() + timedelta(hours=5)):
            with self.assertRaisesRegex(UserError, 'kadaluwarsa'):
                self.praktikum.submit_presensi(self.mhs, self.praktikum.token)
        self.assertFalse(self.peserta.presensi)

    def test_presensi_sukses_tidak_peka_huruf(self):
        self.praktikum.action_generate_token()
        self.praktikum.submit_presensi(self.mhs, self.praktikum.token.lower())
        self.assertTrue(self.peserta.presensi)
        self.assertTrue(self.peserta.waktu_presensi)
        self.assertEqual(self.praktikum.jumlah_hadir, 1)

    def test_tidak_terdaftar(self):
        self.praktikum.action_generate_token()
        with self.assertRaisesRegex(UserError, 'belum terdaftar di kelompok'):
            self.praktikum.submit_presensi(self.mhs_lain, self.praktikum.token)

    def test_akun_belum_terhubung(self):
        self.praktikum.action_generate_token()
        mahasiswa_kosong = self.env['bp.edu.mahasiswa']
        with self.assertRaisesRegex(UserError, 'belum terhubung'):
            self.praktikum.submit_presensi(mahasiswa_kosong, self.praktikum.token)

    def test_belum_ada_token(self):
        with self.assertRaisesRegex(UserError, 'Kode token salah'):
            self.praktikum.submit_presensi(self.mhs, '')
