from odoo import fields, models


class SbsResUsers(models.Model):
    _inherit = "res.users"

    @property
    def SELF_READABLE_FIELDS(self):
        return super().SELF_READABLE_FIELDS + [
            "sbs_sidebar_type",
            "sbs_chatter_position",
            "sbs_dialog_size",
        ]

    @property
    def SELF_WRITEABLE_FIELDS(self):
        return super().SELF_WRITEABLE_FIELDS + [
            "sbs_sidebar_type",
            "sbs_chatter_position",
            "sbs_dialog_size",
        ]

    sbs_sidebar_type = fields.Selection(
        selection=[
            ("invisible", "Invisible"),
            ("small", "Small"),
            ("large", "Large"),
        ],
        string="Sidebar Type",
        default="large",
        required=True,
    )
    sbs_chatter_position = fields.Selection(
        selection=[
            ("side", "Side"),
            ("bottom", "Bottom"),
        ],
        string="Chatter Position",
        default="side",
        required=True,
    )
    sbs_dialog_size = fields.Selection(
        selection=[
            ("minimize", "Minimize"),
            ("maximize", "Maximize"),
        ],
        string="Dialog Size",
        default="minimize",
        required=True,
    )
