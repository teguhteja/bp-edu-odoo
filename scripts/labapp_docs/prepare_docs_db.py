# Menyiapkan DB salinan (mis. labapp_docs) untuk pengambilan screenshot dokumentasi.
# JANGAN dijalankan pada DB labapp asli: skrip ini menambah sesi praktikum, PO, perbaikan, dan opname contoh.
#
#   $env:LABAPP_DB = 'labapp_docs'; $env:LABAPP_PASSWORD = '<password sementara>'
#   .\labapp\odoo-labapp.ps1 shell labapp_docs/prepare_docs_db.py
import os
from datetime import timedelta

assert env.cr.dbname != 'labapp', 'Jalankan pada DB salinan, bukan labapp'
password = os.environ.get('LABAPP_PASSWORD')
assert password, 'Set LABAPP_PASSWORD'

Users = env['res.users']
admin = Users.search([('login', '=', 'admin@lab.test')])
demo = Users.search([('login', '=', 'demo.mahasiswa@lab.test')])
(admin | demo).write({'password': password, 'tz': 'Asia/Makassar'})

Praktikum = env['bp.edu.lab.praktikum']
hari_ini = Praktikum._hari_ini()
kelas = env['bp.edu.kelas'].search([('kode', '!=', False)], order='id', limit=1)
mk = Praktikum.search([], order='id', limit=1).mata_kuliah_id
pretest = env['survey.survey'].search([('jenis_ujian', '=', 'pra'), ('question_and_page_ids', '!=', False)], order='id', limit=1)
posttest = env['survey.survey'].search([('jenis_ujian', '=', 'post'), ('question_and_page_ids', '!=', False)], order='id', limit=1)

product = {p.default_code: p for p in env['product.product'].search([('bp_inventaris_lab', '=', True)])}

praktikum = Praktikum.search([('nama', '=', 'Pertemuan 3 - JavaScript Dasar')])
if not praktikum:
    praktikum = Praktikum.create({
        'nama': 'Pertemuan 3 - JavaScript Dasar',
        'ruang': 'Lab Komputer 1',
        'tanggal': hari_ini,
        'due_date': hari_ini + timedelta(days=7),
        'mata_kuliah_id': mk.id,
        'pretest_id': pretest.id,
        'posttest_id': posttest.id,
        'deskripsi': 'Variabel, fungsi, dan manipulasi DOM sederhana.',
        'bahan_ids': [
            (0, 0, {'product_id': product['INV-001'].id, 'qty': 1}),
            (0, 0, {'product_id': product['INV-003'].id, 'qty': 1}),
        ],
    })
    kelompok = env['bp.edu.lab.kelompok'].create({
        'nama': f'{kelas.kode} - Pertemuan 3 - JavaScript Dasar',
        'praktikum_id': praktikum.id,
        'kelas_id': kelas.id,
    })
    kelompok.action_tambah_mahasiswa_kelas()
praktikum.action_generate_token()

# Contoh nilai untuk sesi lama mahasiswa demo supaya kolom Nilai di portal terisi.
mhs_demo = demo._get_mahasiswa()
lama = env['bp.edu.lab.peserta'].search([('mahasiswa_id', '=', mhs_demo.id), ('praktikum_id', '!=', praktikum.id)])
lama.write({'presensi': True, 'nilai': 85})

# Inventaris: perbaikan draft, opname draft, PO draft, PO terkonfirmasi (penerimaan menunggu validasi).
if not env['bp.edu.lab.perbaikan'].search([('state', '=', 'draft')]):
    env['bp.edu.lab.perbaikan'].create({
        'product_id': product['INV-004'].id, 'qty': 1,
        'keterangan': 'Beberapa tombol tidak berfungsi.',
    })
if not env['bp.edu.lab.stock.opname'].search([('state', '=', 'draft')]):
    env['bp.edu.lab.stock.opname'].create({
        'referensi': 'Opname akhir bulan',
        'line_ids': [
            (0, 0, {'product_id': product['INV-007'].id, 'qty_hitung': 7}),
            (0, 0, {'product_id': product['INV-008'].id, 'qty_hitung': 5}),
        ],
    })
supplier = env['res.partner'].search([('supplier_rank', '>', 0)], order='id', limit=1)
PO = env['purchase.order']
if not PO.search([('state', '=', 'draft')]):
    PO.create({'partner_id': supplier.id, 'order_line': [
        (0, 0, {'product_id': product['INV-007'].id, 'product_qty': 20, 'price_unit': 55000}),
    ]})
    po2 = PO.create({'partner_id': supplier.id, 'order_line': [
        (0, 0, {'product_id': product['INV-003'].id, 'product_qty': 10, 'price_unit': 75000}),
    ]})
    po2.button_confirm()

env.cr.commit()
print('SIAP', praktikum.id, praktikum.token)
