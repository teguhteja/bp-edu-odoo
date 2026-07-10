{
    'name': 'BP Edu AI',
    'version': '19.0.1.0.0',
    'category': 'Education',
    'summary': 'Integrasi AI untuk generate RPS, SAP, dan Kontrak Kuliah',
    'depends': ['bp_edu_rps', 'bp_edu_curriculum', 'bp_edu_core', 'ttm_ai_assistant'],
    'data': [
        'security/ir.model.access.csv',
        'wizard/bp_edu_ai_wizard_views.xml',
        'views/bp_edu_rps_ai_inherit.xml',
        'views/bp_edu_sap_ai_inherit.xml',
        'views/bp_edu_kontrak_ai_inherit.xml',
        'views/bp_edu_mata_kuliah_ai_inherit.xml',
        'views/bp_edu_dokumen_master_ai_inherit.xml',
    ],
    'installable': True,
    'application': False,
    'license': 'LGPL-3',
}
