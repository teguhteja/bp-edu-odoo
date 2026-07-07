{
    'name': 'BP Edu Core',
    'version': '19.0.1.0.0',
    'category': 'Education',
    'summary': 'Foundation: master data dosen, program studi, dan tahun akademik',
    'depends': ['base', 'web', 'mail'],
    'data': [
        'security/groups.xml',
        'security/ir.model.access.csv',
        'views/bp_edu_dosen_views.xml',
        'views/bp_edu_program_studi_views.xml',
        'views/bp_edu_tahun_akademik_views.xml',
        'views/bp_edu_dokumen_master_views.xml',
        'views/menu.xml',
    ],
    'external_dependencies': {
        'python': ['docx', 'PyPDF2'],
    },
    'installable': True,
    'application': True,
    'license': 'LGPL-3',
}
