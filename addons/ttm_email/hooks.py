"""
post_init_hook — auto-provision Outgoing (ir.mail_server) dan Incoming
(fetchmail.server) mail server saat install, dibaca dari environment
variable.

CATATAN KEAMANAN: berbeda dengan fs_storage (yang punya mekanisme
eval_options_from_env untuk menghindari plaintext secret di database),
ir.mail_server dan fetchmail.server TIDAK punya mekanisme serupa di Odoo
inti — field smtp_pass/password memang dirancang sebagai Char biasa yang
tersimpan langsung di database. Jadi hook ini menulis nilai asli password
ke DB (satu-satunya cara yang didukung Odoo untuk model-model ini).
"""
import logging
import os

_logger = logging.getLogger(__name__)


def _get_bool_env(name, default=False):
    val = os.getenv(name)
    if val is None:
        return default
    return val.strip().lower() == 'true'


def _setup_email_servers(env):
    _setup_smtp_server(env)
    _setup_fetchmail_server(env)


# ─── Outgoing (SMTP) ──────────────────────────────────────────────────────

SMTP_REQUIRED_ENV_VARS = ('EMAIL_SMTP_HOST', 'EMAIL_SMTP_USER', 'EMAIL_SMTP_PASS')
SMTP_ENCRYPTION_VALUES = {'none', 'starttls_strict', 'starttls', 'ssl_strict', 'ssl'}
SMTP_AUTHENTICATION_VALUES = {'login', 'certificate', 'cli'}


def _setup_smtp_server(env):
    MailServer = env['ir.mail_server'].sudo()

    name = os.getenv('EMAIL_SMTP_NAME') or 'SMTP'
    existing = MailServer.search([('name', '=', name)], limit=1)
    if existing:
        _logger.info(
            "ir.mail_server dengan name='%s' sudah ada (id=%s) — dilewati, tidak ditimpa.",
            name, existing.id,
        )
        return

    missing = [v for v in SMTP_REQUIRED_ENV_VARS if not os.getenv(v)]
    if missing:
        _logger.warning(
            "Auto-setup SMTP (Outgoing Mail Server) dilewati — environment variable "
            "belum diisi: %s. Isi di .env lalu install ulang, atau buat manual via UI.",
            ', '.join(missing),
        )
        return

    encryption = (os.getenv('EMAIL_SMTP_ENCRYPTION') or 'starttls_strict').strip()
    if encryption not in SMTP_ENCRYPTION_VALUES:
        _logger.warning(
            "EMAIL_SMTP_ENCRYPTION=%r tidak valid, gunakan salah satu dari %s. "
            "Fallback ke 'starttls_strict'.", encryption, sorted(SMTP_ENCRYPTION_VALUES),
        )
        encryption = 'starttls_strict'

    authentication = (os.getenv('EMAIL_SMTP_AUTHENTICATION') or 'login').strip()
    if authentication not in SMTP_AUTHENTICATION_VALUES:
        _logger.warning(
            "EMAIL_SMTP_AUTHENTICATION=%r tidak valid, gunakan salah satu dari %s. "
            "Fallback ke 'login'.", authentication, sorted(SMTP_AUTHENTICATION_VALUES),
        )
        authentication = 'login'

    try:
        port = int(os.getenv('EMAIL_SMTP_PORT') or 587)
    except ValueError:
        _logger.warning("EMAIL_SMTP_PORT tidak valid, fallback ke 587.")
        port = 587

    try:
        priority = int(os.getenv('EMAIL_SMTP_PRIORITY') or 10)
    except ValueError:
        priority = 10

    vals = {
        'name': name,
        'smtp_host': os.getenv('EMAIL_SMTP_HOST'),
        'smtp_port': port,
        'smtp_authentication': authentication,
        'smtp_user': os.getenv('EMAIL_SMTP_USER'),
        'smtp_pass': os.getenv('EMAIL_SMTP_PASS'),
        'smtp_encryption': encryption,
        'sequence': priority,
    }

    try:
        server = MailServer.create(vals)
    except Exception:
        _logger.exception("Gagal membuat ir.mail_server '%s' otomatis. Buat manual via UI.", name)
        return

    _logger.info("ir.mail_server '%s' (id=%s) berhasil dibuat otomatis.", name, server.id)

    if _get_bool_env('EMAIL_SMTP_TEST_CONNECTION', True):
        try:
            server.test_smtp_connection()
            _logger.info("Test koneksi SMTP '%s' berhasil.", name)
        except Exception as e:
            _logger.warning(
                "Test koneksi SMTP '%s' gagal (record tetap dibuat): %s", name, e,
            )


# ─── Incoming (IMAP/POP) ──────────────────────────────────────────────────

FETCH_REQUIRED_ENV_VARS = ('EMAIL_FETCH_SERVER', 'EMAIL_FETCH_USER', 'EMAIL_FETCH_PASSWORD')
FETCH_SERVER_TYPE_VALUES = {'imap', 'pop', 'local'}


def _setup_fetchmail_server(env):
    Fetchmail = env['fetchmail.server'].sudo()

    name = os.getenv('EMAIL_FETCH_NAME') or 'Incoming Mail'
    existing = Fetchmail.search([('name', '=', name)], limit=1)
    if existing:
        _logger.info(
            "fetchmail.server dengan name='%s' sudah ada (id=%s) — dilewati, tidak ditimpa.",
            name, existing.id,
        )
        return

    missing = [v for v in FETCH_REQUIRED_ENV_VARS if not os.getenv(v)]
    if missing:
        _logger.warning(
            "Auto-setup Incoming Mail Server dilewati — environment variable belum "
            "diisi: %s. Isi di .env lalu install ulang, atau buat manual via UI.",
            ', '.join(missing),
        )
        return

    server_type = (os.getenv('EMAIL_FETCH_TYPE') or 'imap').strip()
    if server_type not in FETCH_SERVER_TYPE_VALUES:
        _logger.warning(
            "EMAIL_FETCH_TYPE=%r tidak valid, gunakan salah satu dari %s. Fallback ke 'imap'.",
            server_type, sorted(FETCH_SERVER_TYPE_VALUES),
        )
        server_type = 'imap'

    try:
        port = int(os.getenv('EMAIL_FETCH_PORT') or 993)
    except ValueError:
        _logger.warning("EMAIL_FETCH_PORT tidak valid, fallback ke 993.")
        port = 993

    try:
        priority = int(os.getenv('EMAIL_FETCH_PRIORITY') or 5)
    except ValueError:
        priority = 5

    vals = {
        'name': name,
        'server_type': server_type,
        'server': os.getenv('EMAIL_FETCH_SERVER'),
        'port': port,
        'is_ssl': _get_bool_env('EMAIL_FETCH_SSL', True),
        'user': os.getenv('EMAIL_FETCH_USER'),
        'password': os.getenv('EMAIL_FETCH_PASSWORD'),
        'priority': priority,
    }

    try:
        server = Fetchmail.create(vals)
    except Exception:
        _logger.exception("Gagal membuat fetchmail.server '%s' otomatis. Buat manual via UI.", name)
        return

    _logger.info("fetchmail.server '%s' (id=%s) berhasil dibuat otomatis.", name, server.id)

    if _get_bool_env('EMAIL_FETCH_CONFIRM', True):
        try:
            server.button_confirm_login()
            _logger.info("Konfirmasi login fetchmail '%s' berhasil (state=done).", name)
        except Exception as e:
            _logger.warning(
                "Konfirmasi login fetchmail '%s' gagal, record tetap dibuat dengan "
                "state='draft': %s", name, e,
            )
