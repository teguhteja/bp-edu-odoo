# Copyright 2026. Developed and maintained by Simplify It S.R.L. (https://simplifyit.com.bo)

from odoo import fields, models


class ResUsersSettings(models.Model):
    _inherit = 'res.users.settings'

    # Same name/type/attrs as web_enterprise's own field: when Enterprise is
    # installed too, Odoo's model registry merges both declarations into the
    # single underlying column (see odoo/orm/model_classes.py, _setup()), so
    # our sidebar and Enterprise's Home Menu end up reading/writing the exact
    # same per-user app order. When Enterprise isn't installed, this addon
    # simply owns the column on its own.
    homemenu_config = fields.Json(string="Home Menu Configuration", readonly=True)
