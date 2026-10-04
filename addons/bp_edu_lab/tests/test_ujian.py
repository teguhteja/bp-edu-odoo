from datetime import timedelta

from odoo.exceptions import UserError
from odoo.tests import tagged

from .common import LabCommon


@tagged('post_install', '-at_install')
class TestUjian(LabCommon):
    """Port dari lab-app tests/Feature/NilaiUjianTest.php (bagian ujian)."""

    def test_jendela_pretest(self):
        p = self.praktikum
        self.assertFalse(p.cek_jendela_waktu('pra', p.tanggal - timedelta(days=3)))
        self.assertFalse(p.cek_jendela_waktu('pra', p.tanggal))
        self.assertIn('Pretest hanya bisa', p.cek_jendela_waktu('pra', p.tanggal + timedelta(days=1)))

    def test_jendela_posttest(self):
        p = self.praktikum
        self.assertIn('baru bisa dikerjakan', p.cek_jendela_waktu('post', p.tanggal - timedelta(days=1)))
        self.assertFalse(p.cek_jendela_waktu('post', p.tanggal))
        self.assertFalse(p.cek_jendela_waktu('post', p.due_date))
        self.assertIn('melewati batas', p.cek_jendela_waktu('post', p.due_date + timedelta(days=1)))

    def test_posttest_tanpa_due_date_terbuka(self):
        self.praktikum.due_date = False
        self.assertFalse(self.praktikum.cek_jendela_waktu('post', self.praktikum.tanggal + timedelta(days=60)))

    def test_mulai_ujian_membuat_jawaban_dengan_deadline(self):
        answer = self.praktikum.mulai_ujian(self.mhs, 'pra')
        self.assertEqual(answer.survey_id, self.pretest)
        self.assertEqual(answer.mahasiswa_id, self.mhs)
        self.assertEqual(answer.praktikum_id, self.praktikum)
        self.assertEqual(answer.jenis_ujian, 'pra')
        self.assertEqual(answer.partner_id, self.user_mhs.partner_id)
        self.assertTrue(answer.deadline, 'deadline survey dipakai untuk menutup ujian setelah jendela waktu')

    def test_kerjakan_ulang_tidak_duplikat(self):
        pertama = self.praktikum.mulai_ujian(self.mhs, 'pra')
        question = self.pretest.question_ids
        pertama._save_lines(question, 'Jawaban awal')
        pertama._mark_done()
        self.assertEqual(pertama.state, 'done')

        kedua = self.praktikum.mulai_ujian(self.mhs, 'pra')
        self.assertEqual(kedua, pertama)
        self.assertEqual(kedua.state, 'in_progress')
        kedua._save_lines(question, 'Jawaban revisi')
        self.assertEqual(len(kedua.user_input_line_ids), 1)
        self.assertEqual(kedua.user_input_line_ids.value_text_box, 'Jawaban revisi')
        self.assertEqual(self.env['survey.user_input'].search_count([
            ('praktikum_id', '=', self.praktikum.id), ('mahasiswa_id', '=', self.mhs.id)]), 1)

    def test_tidak_terdaftar_ditolak(self):
        with self.assertRaisesRegex(UserError, 'tidak terdaftar'):
            self.praktikum.mulai_ujian(self.mhs_lain, 'pra')

    def test_di_luar_jendela_ditolak(self):
        self.praktikum.write({'tanggal': self.today - timedelta(days=2), 'due_date': self.today - timedelta(days=1)})
        with self.assertRaisesRegex(UserError, 'Pretest hanya bisa'):
            self.praktikum.mulai_ujian(self.mhs, 'pra')
        with self.assertRaisesRegex(UserError, 'melewati batas'):
            self.praktikum.mulai_ujian(self.mhs, 'post')

    def test_tanpa_soal(self):
        self.praktikum.pretest_id = False
        with self.assertRaisesRegex(UserError, 'Tidak ada soal'):
            self.praktikum.mulai_ujian(self.mhs, 'pra')

    def test_lihat_jawaban(self):
        answer = self.praktikum.mulai_ujian(self.mhs, 'post')
        self.assertEqual(self.peserta.jawaban_ids, answer)
        action = self.peserta.action_lihat_jawaban()
        self.assertEqual(action['domain'], [('id', 'in', answer.ids)])

    def test_survey_ujian_memakai_pengaturan_lab(self):
        self.assertEqual(self.pretest.access_mode, 'token')
        self.assertTrue(self.pretest.users_login_required)
        self.assertEqual(self.pretest.scoring_type, 'no_scoring')
        self.assertEqual(self.pretest.question_ids.kunci_jawaban, 'Bahasa markup')
