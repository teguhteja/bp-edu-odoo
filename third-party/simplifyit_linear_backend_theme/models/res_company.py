# Copyright 2026. Developed and maintained by Simplify It S.R.L. (https://simplifyit.com.bo)

from odoo import fields, models

PALETTE_SELECTION = [
    ('indigo', '🟣 Indigo (default)'),
    ('blue', '🔵 Blue'),
    ('teal', '🟢 Teal'),
    ('green', '🟢 Green'),
    ('purple', '🟣 Purple'),
    ('pink', '🌸 Pink'),
    ('orange', '🟠 Orange'),
    ('red', '🔴 Red'),
]


class ResCompany(models.Model):
    _inherit = 'res.company'

    slt_palette = fields.Selection(
        PALETTE_SELECTION,
        string='Backend Accent Color',
        default='indigo',
        required=True,
        help='Accent color used for buttons, active menu items and highlights '
             'in the backend theme. A matching variant is used automatically '
             'in dark mode.',
    )
