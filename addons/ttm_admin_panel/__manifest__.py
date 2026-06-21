{
    'name': 'TTM Admin Panel',
    'version': '19.0.1.0.0',
    'category': 'Administration',
    'summary': 'Manage Odoo tenants: create new databases and subdomains automatically',
    'depends': ['base', 'web'],
    'data': [
        'security/ir.model.access.csv',
        'data/ir_config_parameter.xml',
        'views/ttm_tenant_views.xml',
        'views/menu.xml',
    ],
    'installable': True,
    'application': True,
    'license': 'LGPL-3',
}
