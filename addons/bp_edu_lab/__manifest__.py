{
    'name': 'BP Edu Laboratorium',
    'version': '19.0.1.0.0',
    'category': 'Education',
    'summary': 'Praktikum lab: kelas, mahasiswa, sesi praktikum, token presensi, '
               'kelompok, pretest/posttest (survey), penilaian, dan portal mahasiswa',
    'author': 'IB Teguh TM',
    'depends': ['bp_edu_curriculum', 'survey', 'portal', 'mail'],
    'data': [
        'security/groups.xml',
        'security/ir.model.access.csv',
        'views/bp_edu_kelas_views.xml',
        'views/bp_edu_mahasiswa_views.xml',
        'views/bp_edu_lab_praktikum_views.xml',
        'views/bp_edu_lab_kelompok_views.xml',
        'views/bp_edu_lab_peserta_views.xml',
        'views/bp_edu_master_ext_views.xml',
        'views/survey_views.xml',
        'views/portal_templates.xml',
        'views/menu.xml',
    ],
    'assets': {
        'web.assets_tests': [
            'bp_edu_lab/static/tests/tours/*.js',
        ],
    },
    'installable': True,
    'application': True,
    'license': 'LGPL-3',
}
