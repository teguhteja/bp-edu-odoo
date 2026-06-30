from odoo import models, fields, api, _
from odoo.exceptions import UserError


class TtmChangePasswordWizard(models.TransientModel):
    _name = 'ttm.change.password.wizard'
    _description = 'Ganti Password Admin Tenant'

    tenant_id = fields.Many2one('ttm.tenant', required=True, readonly=True)
    new_password = fields.Char(string='Password Baru', required=True)
    confirm_password = fields.Char(string='Konfirmasi Password', required=True)

    def action_confirm(self):
        self.ensure_one()
        if not self.new_password:
            raise UserError(_('Password tidak boleh kosong.'))
        if self.new_password != self.confirm_password:
            raise UserError(_('Password baru dan konfirmasi tidak cocok.'))
        self.tenant_id.write({'admin_password': self.new_password})
        return {'type': 'ir.actions.act_window_close'}
