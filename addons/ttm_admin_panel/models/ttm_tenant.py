import logging
import urllib.request
import urllib.error
import json

from odoo import models, fields, api, _
from odoo.exceptions import UserError, ValidationError

_logger = logging.getLogger(__name__)


class TtmTenant(models.Model):
    _name = 'ttm.tenant'
    _description = 'TTM Tenant Manager'
    _rec_name = 'name'

    name = fields.Char(string='Nama Tenant', required=True)
    name_database = fields.Char(string='Nama Database', required=True)
    subdomain = fields.Char(string='Subdomain', required=True,
                            help='Prefix subdomain, mis. "cak1" → cak1.teguhteja.com')
    admin_email = fields.Char(string='Email Admin', required=True)
    admin_name = fields.Char(string='Login Admin', default='admin',
                             help='Username login untuk database baru')
    admin_password = fields.Char(string='Password Admin', required=True)
    active = fields.Boolean(string='Aktif', default=True)
    state = fields.Selection([
        ('draft', 'Draft'),
        ('active', 'Aktif'),
        ('error', 'Error'),
    ], string='Status', default='draft', readonly=True)
    full_url = fields.Char(string='URL Lengkap', compute='_compute_full_url', store=False)
    npm_proxy_host_id = fields.Integer(string='NPM Proxy Host ID', readonly=True)
    error_message = fields.Text(string='Pesan Error', readonly=True)

    @api.depends('subdomain')
    def _compute_full_url(self):
        base_domain = self.env['ir.config_parameter'].sudo().get_param(
            'ttm.base.domain', 'teguhteja.com'
        )
        for rec in self:
            if rec.subdomain:
                rec.full_url = f'{rec.subdomain}.{base_domain}'
            else:
                rec.full_url = False

    @api.constrains('name_database', 'subdomain')
    def _check_unique_fields(self):
        for rec in self:
            if self.search_count([
                ('name_database', '=', rec.name_database),
                ('id', '!=', rec.id),
            ]):
                raise ValidationError(_('Nama database "%s" sudah digunakan.') % rec.name_database)
            if self.search_count([
                ('subdomain', '=', rec.subdomain),
                ('id', '!=', rec.id),
            ]):
                raise ValidationError(_('Subdomain "%s" sudah digunakan.') % rec.subdomain)

    def _get_npm_config(self):
        get = self.env['ir.config_parameter'].sudo().get_param
        return {
            'url': get('ttm.npm.url', 'http://npm:81'),
            'email': get('ttm.npm.email', 'teguh.teja@gmail.com'),
            'password': get('ttm.npm.password', 'changeme'),
            'base_domain': get('ttm.base.domain', 'teguhteja.com'),
        }

    def _npm_request(self, method, path, token=None, data=None):
        cfg = self._get_npm_config()
        url = f"{cfg['url'].rstrip('/')}{path}"
        headers = {'Content-Type': 'application/json'}
        if token:
            headers['Authorization'] = f'Bearer {token}'
        body = json.dumps(data).encode() if data else None
        req = urllib.request.Request(url, data=body, headers=headers, method=method)
        try:
            with urllib.request.urlopen(req, timeout=30) as resp:
                return json.loads(resp.read().decode())
        except urllib.error.HTTPError as e:
            error_body = e.read().decode()
            raise UserError(_('NPM API error %s: %s') % (e.code, error_body))

    def _get_npm_token(self):
        cfg = self._get_npm_config()
        result = self._npm_request('POST', '/api/tokens', data={
            'identity': cfg['email'],
            'secret': cfg['password'],
        })
        token = result.get('token')
        if not token:
            raise UserError(_('Gagal login ke NPM API: %s') % result)
        return token

    def action_create_tenant(self):
        self.ensure_one()
        if self.state == 'active':
            raise UserError(_('Tenant sudah aktif.'))

        self.write({'state': 'draft', 'error_message': False})

        try:
            self._do_create_tenant()
        except Exception as e:
            _logger.exception('Gagal membuat tenant %s', self.name_database)
            self.write({'state': 'error', 'error_message': str(e)})
            raise UserError(_('Gagal membuat tenant: %s') % str(e))

    def _do_create_tenant(self):
        from odoo.service import db as odoo_db

        _logger.info('Membuat database Odoo: %s', self.name_database)
        odoo_db.exp_create_database(
            self.name_database,
            False,
            'en_US',
            self.admin_password,
            self.admin_name or 'admin',
            None,
            None,
        )
        _logger.info('Database %s berhasil dibuat', self.name_database)

        cfg = self._get_npm_config()
        full_domain = f"{self.subdomain}.{cfg['base_domain']}"
        token = self._get_npm_token()

        _logger.info('Membuat NPM proxy host untuk %s', full_domain)
        proxy = self._npm_request('POST', '/api/nginx/proxy-hosts', token=token, data={
            'domain_names': [full_domain],
            'forward_scheme': 'http',
            'forward_host': 'nginx',
            'forward_port': 80,
            'ssl_forced': False,
            'block_exploits': True,
            'allow_websocket_upgrade': True,
        })
        proxy_id = proxy.get('id')
        if not proxy_id:
            raise UserError(_('NPM tidak mengembalikan proxy host ID: %s') % proxy)

        _logger.info('Meminta SSL cert untuk %s', full_domain)
        cert = self._npm_request('POST', '/api/nginx/certificates', token=token, data={
            'provider': 'letsencrypt',
            'domain_names': [full_domain],
            'meta': {'dns_challenge': False},
        })
        cert_id = cert.get('id')

        if cert_id:
            _logger.info('SSL cert ID %s diterima, update proxy host', cert_id)
            self._npm_request('PUT', f'/api/nginx/proxy-hosts/{proxy_id}', token=token, data={
                'domain_names': [full_domain],
                'forward_scheme': 'http',
                'forward_host': 'nginx',
                'forward_port': 80,
                'ssl_forced': True,
                'block_exploits': True,
                'allow_websocket_upgrade': True,
                'certificate_id': cert_id,
                'http2_support': True,
            })
        else:
            _logger.warning('SSL cert gagal untuk %s, proxy host tetap HTTP', full_domain)

        self.write({
            'state': 'active',
            'npm_proxy_host_id': proxy_id,
            'error_message': False,
        })
        _logger.info('Tenant %s berhasil dibuat di %s', self.name_database, full_domain)

    def action_delete_tenant(self):
        self.ensure_one()
        if self.state != 'active':
            raise UserError(_('Hanya tenant aktif yang bisa dihapus.'))

        try:
            self._do_delete_tenant()
        except Exception as e:
            _logger.exception('Gagal menghapus tenant %s', self.name_database)
            self.write({'state': 'error', 'error_message': str(e)})
            raise UserError(_('Gagal menghapus tenant: %s') % str(e))

    def _do_delete_tenant(self):
        from odoo.service import db as odoo_db

        if self.npm_proxy_host_id:
            token = self._get_npm_token()
            try:
                self._npm_request('DELETE', f'/api/nginx/proxy-hosts/{self.npm_proxy_host_id}', token=token)
                _logger.info('NPM proxy host %s dihapus', self.npm_proxy_host_id)
            except Exception as e:
                _logger.warning('Gagal hapus NPM proxy host: %s', e)

        _logger.info('Menghapus database: %s', self.name_database)
        odoo_db.exp_drop(self.name_database)

        self.write({
            'active': False,
            'state': 'draft',
            'npm_proxy_host_id': 0,
        })
