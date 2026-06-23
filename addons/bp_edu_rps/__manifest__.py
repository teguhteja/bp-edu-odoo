{
    'name': 'BP Edu RPS',
    'version': '19.0.1.0.0',
    'category': 'Education',
    'summary': 'Rencana Pembelajaran Semester, SAP, dan Kontrak Kuliah',
    'depends': ['bp_edu_curriculum'],
    'data': [
        'security/ir.model.access.csv',
        'views/bp_edu_rps_views.xml',
        'views/bp_edu_sap_views.xml',
        'views/bp_edu_kontrak_kuliah_views.xml',
        'views/bp_edu_mata_kuliah_inherit_views.xml',
        'views/menu.xml',
    ],
    'installable': True,
    'application': False,
    'license': 'LGPL-3',
}
