{
    'name': 'BP Edu AI',
    'version': '19.0.1.4.2',
    'category': 'Education',
    'summary': 'Integrasi AI untuk generate RPS, SAP, dan Kontrak Kuliah',
    'depends': ['bp_edu_rps', 'bp_edu_curriculum', 'bp_edu_core', 'bp_edu_document', 'ttm_ai_assistant'],
    'data': [
        'security/ir.model.access.csv',
        'wizard/bp_edu_ai_wizard_views.xml',
        'wizard/bp_edu_upload_wizard_views.xml',
    ],
    'installable': True,
    'application': False,
    'license': 'LGPL-3',
}
