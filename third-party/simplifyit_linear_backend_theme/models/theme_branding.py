# Copyright 2026. Developed and maintained by Simplify It S.R.L. (https://simplifyit.com.bo)

from odoo import _, api, models

# Whitelist: only these ir.config_parameter keys can ever be read from the
# public login page. Never expose an arbitrary get_param to public templates.
LOGIN_BRANDING_PARAMS = {
    'claim': 'simplifyit_theme.login_claim',
    'subclaim': 'simplifyit_theme.login_subclaim',
    'footer': 'simplifyit_theme.login_footer',
}


def _login_preview_rows():
    """Rows for the decorative backend mini-preview on the login page.

    Built in Python (translated via _()) rather than as static QWeb text:
    each row is a `<div>` of several adjacent `<span>` siblings, and QWeb's
    xml_translate bundles adjacent inline elements (span is one of
    TRANSLATED_ELEMENTS) into a single combined term instead of one term per
    span — so a plain per-span msgid in i18n/*.po silently never matches.
    Status labels are the only part worth translating; ref codes and names
    are either data-shaped or proper nouns.
    """
    return [
        {'status': 'success', 'ref': 'INV-2045', 'name': 'Simplify It S.R.L.', 'amount': '$ 4,200', 'label': _('Paid')},
        {'status': 'warning', 'ref': 'QUO-0118', 'name': 'Odoo Apps', 'amount': '$ 1,890', 'label': _('Quotation')},
        {'status': 'teal', 'ref': 'SO-3092', 'name': 'Your Company', 'amount': '$ 960', 'label': _('Confirmed')},
    ]


class SimplifyitThemeBranding(models.AbstractModel):
    _name = 'simplifyit.theme.branding'
    _description = 'SimplifyIT Theme - Login Branding'

    @api.model
    def get_login_branding(self):
        """Branding values for the public login page.

        Reads a fixed whitelist of ir.config_parameter keys (via sudo) plus
        the main company name. Values left unset fall back to the defaults
        defined in the QWeb template.
        """
        icp = self.env['ir.config_parameter'].sudo()
        values = {
            alias: icp.get_param(key) or False
            for alias, key in LOGIN_BRANDING_PARAMS.items()
        }
        company = self.env['res.company'].sudo().search([], limit=1, order='id')
        values['company_name'] = company.name or ''
        values['preview_rows'] = _login_preview_rows()
        return values
