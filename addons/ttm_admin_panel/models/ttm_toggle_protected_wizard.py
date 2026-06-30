from odoo import models, fields, api, _
from odoo.exceptions import UserError, AccessDenied


class TtmToggleProtectedWizard(models.TransientModel):
    _name = 'ttm.toggle.protected.wizard'
    _description = 'Ubah Status Proteksi Tenant'

    tenant_id = fields.Many2one('ttm.tenant', required=True, readonly=True)
    is_protected = fields.Boolean(related='tenant_id.is_protected', readonly=True)
    current_password = fields.Char(string='Password Anda', required=True)

    def action_confirm(self):
        self.ensure_one()
        if not self.current_password:
            raise UserError(_('Password tidak boleh kosong.'))

        try:
            self.env.user.sudo()._check_credentials(
                self.current_password,
                {'interactive': False},
            )
        except AccessDenied:
            raise UserError(_('Password salah. Silakan coba lagi.'))

        self.tenant_id.write({'is_protected': not self.tenant_id.is_protected})
        return {'type': 'ir.actions.act_window_close'}
