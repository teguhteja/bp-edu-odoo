"""
Daftar field yang dilacak per model lewat mekanisme tracking bawaan Odoo
(tracking=True + mail.thread -> mail.message/mail.tracking.value).

Dipakai bp_edu_history_tracking.py (history_count) dan
bp_edu_mail_message_history.py (rekonstruksi kondisi sebelum perubahan).
"""

TRACKED_FIELDS_BY_MODEL = {
    'bp.edu.rps': [
        'mata_kuliah_id', 'dosen_id', 'dosen_ids', 'tahun_akademik_id',
        'tanggal_penyusunan', 'state',
    ],
    'bp.edu.sap': ['mata_kuliah_id', 'dosen_id', 'dosen_ids', 'tahun_akademik_id', 'rps_id'],
    'bp.edu.kontrak.kuliah': [
        'mata_kuliah_id', 'dosen_id', 'dosen_ids', 'tahun_akademik_id',
        'periode', 'kelas', 'hari_jam', 'jenis_mk', 'prasyarat',
        'bobot_diskusi', 'bobot_proyek', 'bobot_tugas',
        'bobot_kuis', 'bobot_uts', 'bobot_uas',
        'jumlah_kuis_mingguan', 'jumlah_tugas_terstruktur', 'jumlah_proyek',
        'wakil_mahasiswa', 'nim_wakil',
    ],
}
