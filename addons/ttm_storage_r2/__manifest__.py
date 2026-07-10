{
    'name': 'TTM Storage R2 Auto-Setup',
    'version': '19.0.1.0.0',
    'category': 'Technical',
    'summary': 'Auto-provision fs.storage untuk Cloudflare R2 dari environment variable saat install',
    'description': """
Saat modul ini diinstall di database baru, otomatis membuat record fs.storage
untuk Cloudflare R2 (S3-compatible) — kredensial dibaca dari environment
variable, TIDAK disimpan sebagai plaintext di database. Jika env var R2_*
belum diisi, instalasi tetap berhasil tapi tidak membuat record apa pun
(cek log untuk peringatan).

Environment variable yang dipakai (lihat .env.example):
- R2_ACCESS_KEY_ID (wajib)
- R2_SECRET_ACCESS_KEY (wajib)
- R2_ENDPOINT_URL (wajib)
- R2_BUCKET (wajib)
- R2_BASE_URL (opsional — custom domain CDN)
- R2_SET_AS_DEFAULT (opsional — "true" untuk jadikan default storage attachment)
    """,
    'depends': ['fs_storage', 'fs_attachment', 'fs_attachment_s3'],
    'installable': True,
    'application': False,
    'license': 'LGPL-3',
    'post_init_hook': '_setup_r2_storage',
}
