import logging
from odoo import api, SUPERUSER_ID

_logger = logging.getLogger(__name__)


def post_init_hook(env):
    """Jalankan sync mail server langsung setelah modul di-install."""
    _logger.info('ttm_email_config: running post_init_hook, syncing mail servers...')
    from .models.ttm_mail_server_sync import sync_mail_servers
    sync_mail_servers(env)
    _logger.info('ttm_email_config: post_init_hook selesai')
