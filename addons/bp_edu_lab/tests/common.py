from datetime import timedelta

from odoo.tests import new_test_user
from odoo.tests.common import TransactionCase


class LabDataMixin:
    """Data dasar: 1 prodi, 1 kelas, 2 mahasiswa (1 punya akun portal), 1 mata kuliah,
    pretest/posttest masing-masing 1 soal, dan 1 praktikum hari ini dengan 1 kelompok.
    Password akun portal = loginnya (new_test_user)."""

    @classmethod
    def _setup_lab_data(cls):
        env = cls.env
        # "hari ini" menurut zona waktu aplikasi (default Asia/Makassar), bukan UTC server
        cls.today = env['bp.edu.lab.praktikum']._hari_ini()
        cls.prodi = env['bp.edu.program.studi'].create({'kode': 'TSI', 'nama': 'Sistem Informasi Tes'})
        cls.kelas = env['bp.edu.kelas'].create({
            'nama': 'SI-T', 'kode': 'SI-T-2025', 'angkatan': 2025, 'prodi_id': cls.prodi.id,
        })
        cls.user_mhs = new_test_user(env, login='mhs1@test.example', email='mhs1@test.example',
                                     groups='base.group_portal', name='Mahasiswa Satu')
        cls.mhs = env['bp.edu.mahasiswa'].create({
            'nim': 'T001', 'nama': 'Mahasiswa Satu', 'email': 'MHS1@test.example',
            'prodi_id': cls.prodi.id, 'kelas_id': cls.kelas.id,
        })
        cls.mhs_lain = env['bp.edu.mahasiswa'].create({
            'nim': 'T002', 'nama': 'Mahasiswa Dua', 'email': 'mhs2@test.example',
            'prodi_id': cls.prodi.id, 'kelas_id': cls.kelas.id,
        })
        cls.mk = env['bp.edu.mata.kuliah'].create({'kode': 'TST101', 'nama': 'Praktikum Tes'})
        Survey = env['survey.survey']
        cls.pretest = Survey.create({
            'title': 'Pretest Tes', 'jenis_ujian': 'pra', 'mata_kuliah_id': cls.mk.id,
            'question_and_page_ids': [(0, 0, {
                'title': 'Apa itu HTML?', 'question_type': 'text_box', 'kunci_jawaban': 'Bahasa markup',
            })],
        })
        cls.posttest = Survey.create({
            'title': 'Posttest Tes', 'jenis_ujian': 'post', 'mata_kuliah_id': cls.mk.id,
            'question_and_page_ids': [(0, 0, {
                'title': 'Sebutkan tag tabel', 'question_type': 'text_box', 'kunci_jawaban': '<table>',
            })],
        })
        cls.praktikum = env['bp.edu.lab.praktikum'].create({
            'nama': 'Pertemuan Tes', 'tanggal': cls.today, 'due_date': cls.today + timedelta(days=7),
            'mata_kuliah_id': cls.mk.id, 'pretest_id': cls.pretest.id, 'posttest_id': cls.posttest.id,
            'ruang': 'Lab 1',
        })
        cls.kelompok = env['bp.edu.lab.kelompok'].create({
            'nama': 'Kelompok Tes', 'praktikum_id': cls.praktikum.id, 'kelas_id': cls.kelas.id,
            'peserta_ids': [(0, 0, {'mahasiswa_id': cls.mhs.id})],
        })
        cls.peserta = cls.kelompok.peserta_ids


class LabCommon(LabDataMixin, TransactionCase):

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls._setup_lab_data()
