from odoo import fields, models


class SbsResCompany(models.Model):
    _inherit = "res.company"

    sbs_appbar_image = fields.Binary(
        string="Apps Menu Footer Image",
        attachment=True,
    )
    sbs_favicon = fields.Binary(
        string="Company Favicon",
        attachment=True,
    )
    sbs_background_image = fields.Binary(
        string="Apps Menu Background Image",
        attachment=True,
    )
