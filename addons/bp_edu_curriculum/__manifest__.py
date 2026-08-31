{
    'name': 'BP Edu Curriculum',
    'version': '19.0.1.2.0',
    'category': 'Education',
    'summary': 'Kurikulum: mata kuliah, CPL, CPMK, Sub-CPMK, dan pustaka referensi',
    'depends': ['bp_edu_core', 'mail'],
    'data': [
        'security/ir.model.access.csv',
        'security/bp_edu_curriculum_rules.xml',
        'views/bp_edu_cpl_views.xml',
        'views/bp_edu_mata_kuliah_views.xml',
        'views/menu.xml',
    ],
    'installable': True,
    'application': False,
    'license': 'LGPL-3',
}
