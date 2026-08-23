import logging
import odoo
import odoo.api
import odoo.sql_db

_logger = logging.getLogger(__name__)


def sync_mail_servers(env):
    """Copy ir.mail_server records from the source DB to env's DB."""
    source_db = env['ir.config_parameter'].sudo().get_param(
        'ttm.email_config.source_db', 'teguhteja'
    )
    try:
        with odoo.sql_db.db_connect(source_db).cursor() as src_cr:
            src_env = odoo.api.Environment(src_cr, odoo.SUPERUSER_ID, {})
            servers = src_env['ir.mail_server'].sudo().search([])
            server_data = []
            for s in servers:
                server_data.append({
                    'name': s.name,
                    'smtp_host': s.smtp_host,
                    'smtp_port': s.smtp_port,
                    'smtp_user': s.smtp_user,
                    'smtp_pass': s.smtp_pass,
                    'smtp_encryption': s.smtp_encryption,
                    'from_filter': s.from_filter or False,
                    'active': s.active,
                    'sequence': s.sequence,
                })
    except Exception:
        _logger.exception('ttm_email_config: gagal membaca mail server dari DB %s', source_db)
        return

    if not server_data:
        _logger.warning('ttm_email_config: tidak ada mail server di %s', source_db)
        return

    # Hapus server lama agar tidak duplikasi
    existing = env['ir.mail_server'].sudo().search([])
    if existing:
        existing.unlink()

    for d in server_data:
        env['ir.mail_server'].sudo().create(d)
        _logger.info('ttm_email_config: created mail server "%s"', d['name'])
