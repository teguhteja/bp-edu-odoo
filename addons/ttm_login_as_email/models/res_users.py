import logging

from odoo import api, models
from odoo.fields import Domain

_logger = logging.getLogger(__name__)

# Wildcard SQL LIKE yang harus dinetralkan pada input pengguna. Backslash
# harus lebih dulu supaya hasil escape karakter lain tidak ikut ter-escape.
_LIKE_WILDCARDS = ('\\', '%', '_')


def _escape_like(value):
    """Netralkan wildcard SQL LIKE di dalam nilai yang diketik pengguna.

    Operator `=ilike` Odoo diterjemahkan menjadi `ILIKE %s` apa adanya, jadi
    "%" dan "_" pada input ikut diperlakukan sebagai wildcard. Tanpa ini,
    email seperti "john_doe@x.com" juga akan cocok dengan "johnXdoe@x.com".
    """
    for char in _LIKE_WILDCARDS:
        value = value.replace(char, '\\' + char)
    return value


class ResUsers(models.Model):
    _inherit = 'res.users'

    @api.model
    def _get_login_domain(self, login):
        """Terjemahkan email -> login sebelum domain pencarian dibentuk.

        Nilai balik tetap hasil `super()`, jadi tambahan domain dari modul
        lain pada hook yang sama (mis. `website` yang meng-AND-kan
        `website_domain()`) tidak ikut hilang.
        """
        return super()._get_login_domain(self._resolve_login_identifier(login))

    @api.model
    def _resolve_login_identifier(self, login):
        """Kembalikan `login` milik user kalau yang diketik adalah emailnya.

        Kalau tidak bisa dipetakan dengan pasti, kembalikan input apa adanya
        supaya autentikasi gagal lewat jalur normal Odoo.
        """
        if not login or '@' not in login:
            # Bukan bentuk email -> jalur username, tanpa query tambahan.
            return login

        Users = self.sudo()

        # `login` bersifat unik dan terindeks; kalau ada yang persis cocok,
        # dialah pemiliknya. Email tidak boleh menang atas sebuah username.
        if Users.search_count(Domain('login', '=', login), limit=1):
            return login

        # `email` tidak unik dan bisa diubah pengguna sendiri, jadi hanya
        # diterima kalau tepat satu user aktif yang memakainya.
        candidates = Users.search(Domain('email', '=ilike', _escape_like(login)), limit=2)
        if len(candidates) != 1:
            if candidates:
                _logger.info(
                    "Login lewat email ditolak: %s dipakai oleh lebih dari satu user", login,
                )
            return login

        return candidates.login
