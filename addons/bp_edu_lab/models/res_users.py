from odoo import api, models


class ResUsers(models.Model):
    _inherit = 'res.users'

    @api.model_create_multi
    def create(self, vals_list):
        users = super().create(vals_list)
        # Pengganti RegisterController + mahasiswa:link-users di lab-app: akun baru dengan
        # email yang sama otomatis tertaut ke data mahasiswa yang belum punya akun.
        Mahasiswa = self.env['bp.edu.mahasiswa'].sudo()
        for user in users:
            email = Mahasiswa._normalize_email(user.email or user.login)
            if not email:
                continue
            mahasiswa = Mahasiswa.search([('email', '=', email), ('user_id', '=', False)], limit=1)
            if mahasiswa and not Mahasiswa.search_count([('user_id', '=', user.id)]):
                mahasiswa.user_id = user
        return users

    def _get_mahasiswa(self):
        self.ensure_one()
        return self.env['bp.edu.mahasiswa'].sudo().search([('user_id', '=', self.id)], limit=1)
