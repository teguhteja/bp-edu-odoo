# Copyright 2026. Developed and maintained by Simplify It S.R.L. (https://simplifyit.com.bo)

from odoo import fields, models

from .theme_branding import LOGIN_BRANDING_PARAMS

MODULE_NAME = 'simplifyit_linear_backend_theme'


class ResConfigSettings(models.TransientModel):
    _inherit = 'res.config.settings'

    slt_theme_version = fields.Char(
        string='Theme version',
        compute='_compute_slt_theme_version',
    )

    def _compute_slt_theme_version(self):
        module = self.env['ir.module.module'].sudo().search(
            [('name', '=', MODULE_NAME)], limit=1,
        )
        version = module.installed_version or module.latest_version or ''
        for settings in self:
            settings.slt_theme_version = version

    slt_login_claim = fields.Char(
        string='Login claim',
        config_parameter=LOGIN_BRANDING_PARAMS['claim'],
    )
    slt_login_subclaim = fields.Char(
        string='Login subclaim',
        config_parameter=LOGIN_BRANDING_PARAMS['subclaim'],
    )
    slt_login_footer = fields.Char(
        string='Login footer',
        config_parameter=LOGIN_BRANDING_PARAMS['footer'],
    )
