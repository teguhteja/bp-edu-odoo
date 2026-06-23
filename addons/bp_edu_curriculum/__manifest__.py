{
    'name': 'BP Edu Curriculum',
    'version': '19.0.1.0.0',
    'category': 'Education',
    'summary': 'Kurikulum: mata kuliah, CPL, CPMK, Sub-CPMK, dan pustaka referensi',
    'depends': ['bp_edu_core'],
    'data': [
        'security/ir.model.access.csv',
        'views/bp_edu_cpl_views.xml',
        'views/bp_edu_mata_kuliah_views.xml',
        'views/menu.xml',
    ],
    'installable': True,
    'application': False,
    'license': 'LGPL-3',
}
