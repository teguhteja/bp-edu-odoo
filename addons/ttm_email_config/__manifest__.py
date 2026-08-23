{
    'name': 'TTM Email Config',
    'version': '19.0.1.0.0',
    'category': 'Administration',
    'author': 'IB Teguh TM',
    'summary': 'Copy outgoing mail server settings from main DB when installed on a tenant',
    'depends': ['base', 'mail'],
    'data': [
        'security/ir.model.access.csv',
        'data/ir_config_parameter.xml',
    ],
    'post_init_hook': 'post_init_hook',
    'installable': True,
    'application': False,
    'license': 'LGPL-3',
}
