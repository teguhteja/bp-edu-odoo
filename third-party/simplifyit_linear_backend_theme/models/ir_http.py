# Copyright 2026. Developed and maintained by Simplify It S.R.L. (https://simplifyit.com.bo)

from odoo import models
from odoo.http import request


class IrHttp(models.AbstractModel):
    _inherit = 'ir.http'

    def color_scheme(self):
        """Let the systray toggle's `color_scheme` cookie pick the theme.

        Core `web` always renders "light" and only `web_enterprise` reads
        this cookie, so on Community the dark bundle (`web.assets_web_dark`)
        would never be selected without this override.
        """
        cookie_scheme = request.httprequest.cookies.get('color_scheme')
        if cookie_scheme in ('light', 'dark'):
            return cookie_scheme
        return super().color_scheme()

    def session_info(self):
        """Expose the current company's accent palette to the client.

        Read synchronously from `session` on boot (see palette.js) instead of
        an extra RPC, so the CSS variable override lands before first paint.
        """
        info = super().session_info()
        info['slt_palette'] = request.env.company.slt_palette or 'indigo'
        return info
