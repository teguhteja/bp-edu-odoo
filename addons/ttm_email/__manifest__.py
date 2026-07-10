{
    'name': 'TTM Email Auto-Setup',
    'version': '19.0.1.0.0',
    'category': 'Technical',
    'summary': 'Auto-provision Outgoing/Incoming Mail Server dari environment variable saat install',
    'description': """
Saat modul ini diinstall di database baru, otomatis membuat:
- ir.mail_server (Outgoing Mail Server / SMTP) — dari env var EMAIL_SMTP_*
- fetchmail.server (Incoming Mail Server / IMAP-POP) — dari env var EMAIL_FETCH_*

Idempotent: kalau record dengan nama yang sama sudah ada, dilewati (tidak
ditimpa). Kalau env var wajib belum diisi, instalasi tetap berhasil tapi
tidak membuat record apa pun (cek log untuk peringatan).

CATATAN: Odoo tidak punya mekanisme baca-password-dari-env-var bawaan untuk
ir.mail_server / fetchmail.server (beda dengan fs_storage yang punya
eval_options_from_env). Jadi password SMTP/IMAP tetap tersimpan sebagai
nilai asli di database — ini keterbatasan model inti Odoo, bukan modul ini.

Environment variable yang dipakai (lihat .env.example):

Outgoing (SMTP):
- EMAIL_SMTP_NAME (opsional, default "SMTP")
- EMAIL_SMTP_HOST (wajib)
- EMAIL_SMTP_PORT (opsional, default 587)
- EMAIL_SMTP_USER (wajib)
- EMAIL_SMTP_PASS (wajib)
- EMAIL_SMTP_ENCRYPTION (opsional, default starttls_strict)
- EMAIL_SMTP_AUTHENTICATION (opsional, default login)
- EMAIL_SMTP_PRIORITY (opsional, default 10)
- EMAIL_SMTP_TEST_CONNECTION (opsional, "true"/"false", default true)

Incoming (IMAP/POP):
- EMAIL_FETCH_NAME (opsional, default "Incoming Mail")
- EMAIL_FETCH_TYPE (opsional, "imap"/"pop", default imap)
- EMAIL_FETCH_SERVER (wajib)
- EMAIL_FETCH_PORT (opsional, default 993)
- EMAIL_FETCH_SSL (opsional, "true"/"false", default true)
- EMAIL_FETCH_USER (wajib)
- EMAIL_FETCH_PASSWORD (wajib)
- EMAIL_FETCH_PRIORITY (opsional, default 5)
- EMAIL_FETCH_CONFIRM (opsional, "true"/"false", default true)
    """,
    'depends': ['base', 'mail'],
    'installable': True,
    'application': False,
    'license': 'LGPL-3',
    'post_init_hook': '_setup_email_servers',
}
