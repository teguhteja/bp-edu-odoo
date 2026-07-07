"""
post_init_hook — auto-provision fs.storage untuk Cloudflare R2 saat install.

Kredensial S3 (key/secret/endpoint_url) TIDAK disimpan sebagai nilai plaintext
di database — hanya referensi "$ENV_VAR_NAME" yang disimpan, dan fs_storage
sendiri yang me-resolve nilai asli dari environment variable saat runtime
(lihat fs_storage.models.fs_storage._eval_options_from_env). Jadi dump
database atau backup tidak akan pernah berisi secret asli.
"""
import json
import logging
import os

_logger = logging.getLogger(__name__)

STORAGE_CODE = 'r2'

REQUIRED_ENV_VARS = (
    'R2_ACCESS_KEY_ID',
    'R2_SECRET_ACCESS_KEY',
    'R2_ENDPOINT_URL',
    'R2_BUCKET',
)


def _setup_r2_storage(env):
    Storage = env['fs.storage'].sudo()

    existing = Storage.search([('code', '=', STORAGE_CODE)], limit=1)
    if existing:
        _logger.info(
            "fs.storage dengan code='%s' sudah ada (id=%s) — dilewati, tidak ditimpa.",
            STORAGE_CODE, existing.id,
        )
        return

    missing = [name for name in REQUIRED_ENV_VARS if not os.getenv(name)]
    if missing:
        _logger.warning(
            "Auto-setup R2 storage dilewati — environment variable belum diisi: %s. "
            "Isi di .env lalu install ulang, atau buat record fs.storage manual.",
            ', '.join(missing),
        )
        return

    bucket = os.getenv('R2_BUCKET')
    base_url = os.getenv('R2_BASE_URL') or False
    set_as_default = (os.getenv('R2_SET_AS_DEFAULT') or 'false').strip().lower() == 'true'

    options = {
        'key': '$R2_ACCESS_KEY_ID',
        'secret': '$R2_SECRET_ACCESS_KEY',
        'endpoint_url': '$R2_ENDPOINT_URL',
        'client_kwargs': {'region_name': 'auto'},
    }

    # NB: base_url dan use_as_default_for_attachments adalah field yang di-transform
    # jadi computed+inverse oleh server_environment (server.env.mixin) — inverse-nya
    # tidak konsisten terpanggil saat di-set lewat create() (Odoo ORM quirk), jadi
    # keduanya di-write() terpisah setelah record dibuat, bukan dimasukkan ke vals awal.
    vals = {
        'name': 'Cloudflare R2',
        'code': STORAGE_CODE,
        'protocol': 's3',
        'directory_path': bucket,
        'options': json.dumps(options),
        'eval_options_from_env': True,
        'check_connection_method': 'marker_file',
    }

    try:
        storage = Storage.create(vals)
    except Exception:
        _logger.exception(
            "Gagal membuat fs.storage Cloudflare R2 otomatis (kemungkinan ada storage "
            "lain yang sudah jadi default, atau constraint lain). Buat manual via UI."
        )
        return

    followup_vals = {}
    if 'use_as_default_for_attachments' in storage._fields:
        followup_vals['use_as_default_for_attachments'] = set_as_default
    if base_url and 'base_url' in storage._fields:
        followup_vals['base_url'] = base_url

    if followup_vals:
        try:
            storage.write(followup_vals)
        except Exception:
            _logger.exception(
                "fs.storage R2 (id=%s) dibuat, tapi gagal set base_url/default "
                "attachment. Set manual via UI kalau perlu.",
                storage.id,
            )

    _logger.info(
        "fs.storage Cloudflare R2 (id=%s, code='%s', bucket='%s') berhasil dibuat otomatis. "
        "Kredensial dibaca dari environment variable, tidak disimpan sebagai plaintext.",
        storage.id, STORAGE_CODE, bucket,
    )
