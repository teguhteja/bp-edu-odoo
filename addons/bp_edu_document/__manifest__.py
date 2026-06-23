{
    'name': 'BP Edu Document',
    'version': '19.0.1.0.0',
    'category': 'Education',
    'summary': 'Generate DOCX (RPS, SAP, Kontrak Kuliah) dan import/export JSON',
    'depends': ['bp_edu_rps'],
    'data': [
        'security/ir.model.access.csv',
        'views/bp_edu_docx_template_views.xml',
        'views/bp_edu_generate_log_views.xml',
        'views/wizard_generate_views.xml',
        'views/wizard_import_json_views.xml',
        'views/bp_edu_rps_buttons_inherit.xml',
        'views/menu.xml',
    ],
    'external_dependencies': {
        'python': ['docx', 'PIL'],
    },
    'installable': True,
    'application': False,
    'license': 'LGPL-3',
}
