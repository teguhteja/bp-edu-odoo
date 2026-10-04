{
    'name': 'BP Edu Laboratorium - Inventaris',
    'version': '19.0.1.0.0',
    'category': 'Education',
    'summary': 'Inventaris lab di atas Purchase & Inventory: barang, supplier, PO, penerimaan, '
               'stock opname, perbaikan, bahan praktikum, stok menipis, dan laporan',
    'author': 'IB Teguh TM',
    'depends': ['bp_edu_lab', 'purchase_stock', 'stock'],
    'data': [
        'security/ir.model.access.csv',
        'data/ir_sequence_data.xml',
        'views/product_views.xml',
        'views/bp_edu_lab_perbaikan_views.xml',
        'views/bp_edu_lab_stock_opname_views.xml',
        'views/bp_edu_lab_praktikum_views.xml',
        'views/bp_edu_lab_laporan_views.xml',
        'views/menu.xml',
    ],
    'assets': {
        'web.assets_tests': [
            'bp_edu_lab_inventaris/static/tests/tours/*.js',
        ],
    },
    'installable': True,
    'application': False,
    'license': 'LGPL-3',
}
