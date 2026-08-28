# -*- coding: utf-8 -*-
from odoo import fields, models


class ResConfigSettings(models.TransientModel):
    _inherit = 'res.config.settings'

    fast_language_switcher_shortcut = fields.Char(
        string='Language Switcher Shortcut',
        default='ctrl+l',
        config_parameter='fast_language_switcher.shortcut',
        help=(
            'Keyboard shortcut to open the language switcher overlay.\n'
            'Supported modifiers: ctrl, alt, shift, meta\n'
            'Examples: ctrl+l  |  ctrl+shift+l  |  alt+l'
        ),
    )
