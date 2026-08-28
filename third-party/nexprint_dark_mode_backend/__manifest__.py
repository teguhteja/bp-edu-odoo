{
    'name': 'NEXprint Dark Mode Backend',
    'version': '1.0',
    'summary': 'Modern Dark Mode theme for Odoo Backend',
    'description': 'A high-quality free module by NEXprint. Modern Dark Mode theme for Odoo Backend.',
    'category': 'Theme/Backend',
    'author': 'Servicios NEXprint - Ing Mary Del Villar Saez',
    'website': 'https://www.gruponexprint.com',
    'license': 'LGPL-3',
    'depends': ['web'],
    'data': [],
    'assets': {
        'web.assets_backend': [
            'nexprint_dark_mode_backend/static/src/scss/style.scss',
        ],
        'web.assets_frontend': [
            'nexprint_dark_mode_backend/static/src/scss/frontend.scss',
        ]
    },
    'images': ['static/description/banner.png'],
    'installable': True,
    'application': False,
}
