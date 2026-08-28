# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.

{
    "name": "Display Save & Discard Buttons",
    "summary": "Enhances form views by displaying Save and Discard buttons instead of small icons.",
    "description": """
        This module improves the Odoo form view interface by replacing the small save/discard icons 
        with clearly visible and user-friendly Save and Discard buttons. 
        It enhances usability and provides a more intuitive user experience across all form views.
    """,
    "author": "CodeSphere Tech",
    "website": "https://www.codespheretech.in/",
    "category": 'Extra Tools',
    "version": "19.0.1.0.0",
    'sequence': 0,
    "currency": "USD",
    "price": "0",
    "depends": ['base', 'web'],
    "data": [],
    'assets': {
        'web.assets_backend':
            [
                'cst_save_discard/static/src/**/*',
            ],
    },
    'images': ['static/description/Banner.png'],
    "license": "LGPL-3",
    "installable": True,
    "application": False,
    "auto_install": False,
}
