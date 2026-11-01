{
    'name': 'UMKM Pengeluaran & Laba Rugi',
    'version': '19.0.1.0.0',
    'category': 'Sales/Point of Sale',
    'summary': 'Catat pengeluaran harian dan laporan laba/rugi bulanan dari penjualan POS',
    'depends': ['point_of_sale'],
    'data': [
        'security/ir.model.access.csv',
        'views/umkm_views.xml',
    ],
    'installable': True,
    'application': True,
    'author': 'IB Teguh Teja Murti',
    'license': 'LGPL-3',
}
