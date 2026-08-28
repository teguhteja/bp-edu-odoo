"""
Struktur data tambahan RPS hasil sinkronisasi dengan skema JSON rps_bp terbaru:
  - korelasi              : matriks CPMK x Minggu (kolom m1..m12)
  - korelasi_cpl          : matriks Sub-CPMK x CPL (kolom p1..p20)
  - penilaian             : matriks Jenis Penilaian x Level Taksonomi (kolom c1..c10)
  - rancangan_tugas_proyek: rancangan tugas proyek (opsional, 1 per RPS)
  - rubrik_penilaian      : rubrik holistik (baris) + rubrik deskriptif (1 per RPS)

Jumlah kolom m1..m12 / p1..p20 / c1..c10 mengikuti batas maksimum yang
disediakan template DOCX (lihat rps_bp/RPS_MK_TSI0000.docx); JSON tiap MK
hanya mengisi sebagian, sisanya dibiarkan kosong.
"""
from odoo import models, fields


_M_COLS = [f'm{i}' for i in range(1, 13)]
_P_COLS = [f'p{i}' for i in range(1, 21)]
_C_COLS = [f'c{i}' for i in range(1, 11)]


class BpEduRpsKorelasi(models.Model):
    _name = 'bp.edu.rps.korelasi'
    _description = 'Korelasi CPMK - Minggu'
    _order = 'rps_id, sequence, id'

    rps_id = fields.Many2one('bp.edu.rps', string='RPS', required=True, ondelete='cascade')
    sequence = fields.Integer(default=10)
    cpmk = fields.Char(string='CPMK')
    m1 = fields.Char(string='M1')
    m2 = fields.Char(string='M2')
    m3 = fields.Char(string='M3')
    m4 = fields.Char(string='M4')
    m5 = fields.Char(string='M5')
    m6 = fields.Char(string='M6')
    m7 = fields.Char(string='M7')
    m8 = fields.Char(string='M8')
    m9 = fields.Char(string='M9')
    m10 = fields.Char(string='M10')
    m11 = fields.Char(string='M11')
    m12 = fields.Char(string='M12')


class BpEduRpsKorelasiCpl(models.Model):
    _name = 'bp.edu.rps.korelasi.cpl'
    _description = 'Korelasi Sub-CPMK - CPL'
    _order = 'rps_id, sequence, id'

    rps_id = fields.Many2one('bp.edu.rps', string='RPS', required=True, ondelete='cascade')
    sequence = fields.Integer(default=10)
    sub = fields.Char(string='Sub-CPMK')
    bobot = fields.Char(string='Bobot')
    minggu = fields.Char(string='Minggu')
    p1 = fields.Char(string='P1')
    p2 = fields.Char(string='P2')
    p3 = fields.Char(string='P3')
    p4 = fields.Char(string='P4')
    p5 = fields.Char(string='P5')
    p6 = fields.Char(string='P6')
    p7 = fields.Char(string='P7')
    p8 = fields.Char(string='P8')
    p9 = fields.Char(string='P9')
    p10 = fields.Char(string='P10')
    p11 = fields.Char(string='P11')
    p12 = fields.Char(string='P12')
    p13 = fields.Char(string='P13')
    p14 = fields.Char(string='P14')
    p15 = fields.Char(string='P15')
    p16 = fields.Char(string='P16')
    p17 = fields.Char(string='P17')
    p18 = fields.Char(string='P18')
    p19 = fields.Char(string='P19')
    p20 = fields.Char(string='P20')


class BpEduRpsPenilaian(models.Model):
    _name = 'bp.edu.rps.penilaian'
    _description = 'Matriks Penilaian - Jenis x Taksonomi'
    _order = 'rps_id, sequence, id'

    rps_id = fields.Many2one('bp.edu.rps', string='RPS', required=True, ondelete='cascade')
    sequence = fields.Integer(default=10)
    jenis = fields.Char(string='Jenis Penilaian')
    bobot = fields.Char(string='Bobot')
    c1 = fields.Char(string='C1')
    c2 = fields.Char(string='C2')
    c3 = fields.Char(string='C3')
    c4 = fields.Char(string='C4')
    c5 = fields.Char(string='C5')
    c6 = fields.Char(string='C6')
    c7 = fields.Char(string='C7')
    c8 = fields.Char(string='C8')
    c9 = fields.Char(string='C9')
    c10 = fields.Char(string='C10')


class BpEduRpsRancanganTugas(models.Model):
    _name = 'bp.edu.rps.rancangan.tugas'
    _description = 'Rancangan Tugas Proyek'
    _rec_name = 'rps_id'

    rps_id = fields.Many2one(
        'bp.edu.rps', string='RPS', required=True, ondelete='cascade',
    )

    tujuan = fields.Text(string='Tujuan Tugas')
    kompetensi = fields.Text(
        string='Kompetensi', help='Satu kompetensi per baris.',
    )

    # uraian_tugas
    objek_garapan = fields.Text(string='Objek Garapan')
    langkah_kerja = fields.Text(string='Langkah Kerja', help='Satu langkah per baris.')
    topik = fields.Text(string='Pilihan Topik', help='Satu topik per baris.')
    metode_kerja = fields.Text(string='Metode Kerja', help='Satu metode per baris.')
    luaran_tugas = fields.Text(string='Luaran Tugas', help='Satu luaran per baris.')

    # kriteria_penilaian (4 kriteria tetap sesuai template rps_bp)
    kriteria_proposal_bobot = fields.Char(string='Bobot - Penyusunan Proposal')
    kriteria_proposal_deskripsi = fields.Text(string='Deskripsi - Penyusunan Proposal')
    kriteria_implementasi_bobot = fields.Char(string='Bobot - Pengimplementasian Proyek')
    kriteria_implementasi_deskripsi = fields.Text(string='Deskripsi - Pengimplementasian Proyek')
    kriteria_laporan_bobot = fields.Char(string='Bobot - Penyusunan Laporan')
    kriteria_laporan_deskripsi = fields.Text(string='Deskripsi - Penyusunan Laporan')
    kriteria_presentasi_bobot = fields.Char(string='Bobot - Presentasi')
    kriteria_presentasi_deskripsi = fields.Text(string='Deskripsi - Presentasi')


class BpEduRpsRubrikHolistik(models.Model):
    _name = 'bp.edu.rps.rubrik.holistik'
    _description = 'Rubrik Holistik Proposal/Laporan'
    _order = 'rps_id, skor_min'

    rps_id = fields.Many2one('bp.edu.rps', string='RPS', required=True, ondelete='cascade')
    grade = fields.Char(string='Grade', required=True)
    skor_min = fields.Integer(string='Skor Min')
    skor_max = fields.Integer(string='Skor Max')
    kriteria = fields.Text(string='Kriteria')


class BpEduRpsRubrikDeskriptif(models.Model):
    _name = 'bp.edu.rps.rubrik.deskriptif'
    _description = 'Rubrik Deskriptif Presentasi'
    _rec_name = 'rps_id'

    rps_id = fields.Many2one(
        'bp.edu.rps', string='RPS', required=True, ondelete='cascade',
    )
    aspek_yang_dinilai = fields.Text(
        string='Aspek yang Dinilai', help='Satu aspek per baris.',
    )
    format_penilaian = fields.Char(string='Format Penilaian')

    # skala_penilaian (5 pita nilai tetap sesuai template rps_bp)
    skala_sangat_kurang_min = fields.Integer(string='Sangat Kurang - Min')
    skala_sangat_kurang_max = fields.Integer(string='Sangat Kurang - Max')
    skala_kurang_min = fields.Integer(string='Kurang - Min')
    skala_kurang_max = fields.Integer(string='Kurang - Max')
    skala_cukup_min = fields.Integer(string='Cukup - Min')
    skala_cukup_max = fields.Integer(string='Cukup - Max')
    skala_baik_min = fields.Integer(string='Baik - Min')
    skala_baik_max = fields.Integer(string='Baik - Max')
    skala_sangat_baik_min = fields.Integer(string='Sangat Baik - Min')
    skala_sangat_baik_max = fields.Integer(string='Sangat Baik - Max')


class BpEduRpsExtMatriks(models.Model):
    _inherit = 'bp.edu.rps'

    korelasi_ids = fields.One2many(
        'bp.edu.rps.korelasi', 'rps_id', string='Korelasi CPMK-Minggu',
    )
    korelasi_cpl_ids = fields.One2many(
        'bp.edu.rps.korelasi.cpl', 'rps_id', string='Korelasi Sub-CPMK-CPL',
    )
    penilaian_ids = fields.One2many(
        'bp.edu.rps.penilaian', 'rps_id', string='Matriks Penilaian',
    )
    rancangan_tugas_ids = fields.One2many(
        'bp.edu.rps.rancangan.tugas', 'rps_id', string='Rancangan Tugas Proyek',
    )
    rubrik_holistik_ids = fields.One2many(
        'bp.edu.rps.rubrik.holistik', 'rps_id', string='Rubrik Holistik',
    )
    rubrik_deskriptif_ids = fields.One2many(
        'bp.edu.rps.rubrik.deskriptif', 'rps_id', string='Rubrik Deskriptif',
    )
