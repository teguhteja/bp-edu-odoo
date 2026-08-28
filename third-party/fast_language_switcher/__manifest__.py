# -*- coding: utf-8 -*-
{
    'name': 'Fast Language Switcher',
    'version': '17.0.1.1.0',
    'category': 'Technical',
    'summary': 'Quick language switcher in the top bar with a configurable keyboard shortcut',
    'description': """
Fast Language Switcher
======================
Adds a language flag icon to the main navigation bar systray.

Features:
- Flag icon in the navbar showing the current language.
- Dropdown with all installed languages (flag + name). Click to switch instantly.
- macOS-style overlay triggered by a keyboard shortcut (default Ctrl+L).
  Each press cycles to the next language; auto-applies after 1.5 s of inactivity.
- Configurable shortcut in Settings > General Settings > Language Switcher.
    """,
    'author': 'Zura Mukbaniani',
    'depends': ['web', 'base_setup'],
    'data': [
        'views/res_config_settings_views.xml',
    ],
    'images': ['static/description/banner.png'],
    'assets': {
        'web.assets_backend': [
            'fast_language_switcher/static/src/shortcut_input_field/shortcut_input_field.js',
            'fast_language_switcher/static/src/shortcut_input_field/shortcut_input_field.xml',
            'fast_language_switcher/static/src/shortcut_input_field/shortcut_input_field.scss',
            'fast_language_switcher/static/src/language_switcher/language_switcher.js',
            'fast_language_switcher/static/src/language_switcher/language_switcher.xml',
            'fast_language_switcher/static/src/language_switcher/language_switcher.scss',
            'fast_language_switcher/static/src/language_switcher_dialog/language_switcher_dialog.js',
            'fast_language_switcher/static/src/language_switcher_dialog/language_switcher_dialog.xml',
            'fast_language_switcher/static/src/language_switcher_dialog/language_switcher_dialog.scss',
        ],
    },
    'installable': True,
    'auto_install': False,
    'application': False,
    'license': 'LGPL-3',
}
