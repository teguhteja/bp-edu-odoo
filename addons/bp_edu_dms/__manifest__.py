{
    'name': 'BP Edu DMS Bridge',
    'version': '19.0.1.4.0',
    'category': 'Education',
    'summary': 'Folder buku ajar (DMS) otomatis per mata kuliah',
    'description': """
Menghubungkan bp_edu_curriculum (Mata Kuliah) dengan dms (Document
Management System, OCA): setiap mata kuliah otomatis punya satu folder DMS
sendiri di bawah folder "Buku Ajar", diisi oleh dosen pengampu masing-masing.
Latar belakang: notulen rapat prodi SI 28 Agustus 2026, poin "kebutuhan
storage buku ajar" -- satu tempat terpusat, folder per judul mata kuliah.

Untuk membatasi storage server, upload file baru ke DMS (isi content) ditolak
dengan pesan penjelasan (tombol upload tetap terlihat, bukan disembunyikan).
Sebagai gantinya, link Google Drive bisa ditempel di dua tempat: tab "Link
Google Drive" pada form Mata Kuliah, ATAU langsung sebagai dms.file (field
Content disembunyikan, diganti field link + tombol buka + preview inline
untuk PDF/berkas yang didukung Google Drive viewer).
    """,
    'depends': ['bp_edu_curriculum', 'bp_edu_core', 'bp_edu_rps', 'dms'],
    'data': [
        'security/ir.model.access.csv',
        'data/dms_setup.xml',
        'views/bp_edu_mata_kuliah_dms_views.xml',
        'views/dms_file_gdrive_views.xml',
    ],
    'installable': True,
    'application': False,
    'license': 'LGPL-3',
}
