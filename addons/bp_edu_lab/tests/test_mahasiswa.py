from psycopg2 import IntegrityError

from odoo.exceptions import AccessError, UserError
from odoo.tests import new_test_user, tagged
from odoo.tools import mute_logger

from .common import LabCommon


@tagged('post_install', '-at_install')
class TestMahasiswaUser(LabCommon):
    """Port dari lab-app tests/Feature/MahasiswaUserLinkTest.php"""

    def test_link_saat_mahasiswa_dibuat(self):
        # user dibuat sebelum mahasiswa (email beda kapital) -> tertaut saat create
        self.assertEqual(self.mhs.user_id, self.user_mhs)
        self.assertEqual(self.mhs.email, 'mhs1@test.example')
        self.assertEqual(self.user_mhs._get_mahasiswa(), self.mhs)

    def test_link_saat_user_dibuat(self):
        user = new_test_user(self.env, login='mhs2@test.example', email='mhs2@test.example',
                             groups='base.group_portal')
        self.assertEqual(self.mhs_lain.user_id, user)

    def test_link_saat_email_diubah(self):
        user = new_test_user(self.env, login='baru@test.example', email='baru@test.example',
                             groups='base.group_portal')
        self.assertFalse(self.mhs_lain.user_id)
        self.mhs_lain.email = 'baru@test.example'
        self.assertEqual(self.mhs_lain.user_id, user)

    def test_email_diubah_lepas_tautan_lama(self):
        self.mhs.email = 'tidakada@test.example'
        self.assertFalse(self.mhs.user_id)

    def test_email_duplikat_ditolak(self):
        with mute_logger('odoo.sql_db'), self.assertRaises(IntegrityError), self.cr.savepoint():
            self.env['bp.edu.mahasiswa'].create({
                'nim': 'T003', 'nama': 'Duplikat', 'email': 'mhs2@test.example', 'prodi_id': self.prodi.id,
            })

    def test_nim_duplikat_ditolak(self):
        with mute_logger('odoo.sql_db'), self.assertRaises(IntegrityError), self.cr.savepoint():
            self.env['bp.edu.mahasiswa'].create({
                'nim': 'T001', 'nama': 'Duplikat', 'email': 'x@test.example', 'prodi_id': self.prodi.id,
            })

    def test_buat_akses_portal(self):
        self.mhs_lain.action_buat_akses_portal()
        user = self.mhs_lain.user_id
        self.assertTrue(user)
        self.assertEqual(user.login, 'mhs2@test.example')
        self.assertTrue(user._is_portal())
        # dipanggil ulang tidak membuat akun kedua
        self.mhs_lain.action_buat_akses_portal()
        self.assertEqual(self.mhs_lain.user_id, user)


@tagged('post_install', '-at_install')
class TestGuardDanAkses(LabCommon):
    """Guard hapus dari controller lab-app + hak akses peran."""

    def test_hapus_prodi_berkelas(self):
        with self.assertRaisesRegex(UserError, 'masih digunakan oleh kelas'):
            self.prodi.unlink()

    def test_hapus_kelas_bermahasiswa(self):
        with self.assertRaisesRegex(UserError, 'masih memiliki mahasiswa'):
            self.kelas.unlink()

    def test_hapus_mata_kuliah_berpraktikum(self):
        with self.assertRaisesRegex(UserError, 'masih digunakan oleh praktikum'):
            self.mk.unlink()

    def test_hapus_praktikum_berkelompok(self):
        with self.assertRaisesRegex(UserError, 'sudah memiliki kelompok'):
            self.praktikum.unlink()

    def test_hapus_ujian_dipakai_praktikum(self):
        with self.assertRaisesRegex(UserError, 'masih digunakan oleh praktikum'):
            self.posttest.unlink()

    def test_kelompok_selesai_terkunci(self):
        self.kelompok.action_selesai()
        with self.assertRaisesRegex(UserError, 'Kelompok Sudah Praktikum'):
            self.kelompok.nama = 'Ganti'
        # nilai tetap bisa diisi lewat penilaian
        self.peserta.nilai = 88
        self.kelompok.action_draft()
        self.kelompok.nama = 'Ganti'

    def test_tambah_mahasiswa_kelas(self):
        self.kelompok.action_tambah_mahasiswa_kelas()
        self.assertEqual(set(self.kelompok.peserta_ids.mahasiswa_id.ids), {self.mhs.id, self.mhs_lain.id})

    def test_nilai_di_luar_rentang(self):
        with mute_logger('odoo.sql_db'), self.assertRaises(IntegrityError), self.cr.savepoint():
            self.peserta.nilai = 101
            self.peserta.flush_recordset()

    def test_portal_tidak_bisa_baca_data_lab(self):
        with self.assertRaises(AccessError):
            self.peserta.with_user(self.user_mhs).read(['nilai'])
        with self.assertRaises(AccessError):
            self.mhs_lain.with_user(self.user_mhs).read(['nama'])

    def test_manager_baca_saja(self):
        manager = new_test_user(self.env, login='manager_lab', groups='bp_edu_lab.group_lab_manager')
        self.peserta.with_user(manager).read(['nilai'])
        with self.assertRaises(AccessError):
            self.peserta.with_user(manager).write({'nilai': 50})

    def test_admin_lab_kelola_praktikum(self):
        admin = new_test_user(self.env, login='admin_lab', groups='bp_edu_lab.group_lab_admin')
        praktikum = self.praktikum.with_user(admin)
        praktikum.action_generate_token()
        self.peserta.with_user(admin).write({'nilai': 77})
        self.assertEqual(self.peserta.nilai, 77)
