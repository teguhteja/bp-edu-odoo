"""Impor data lab-app (hasil export_mysql.sh + split_dump.py) ke DB Odoo "labapp".

Dijalankan lewat odoo shell (variabel `env` sudah tersedia):

    .\\labapp\\odoo-labapp.ps1 shell < scripts/labapp_import/import_labapp.py

Skrip ini idempotent: setiap record lab-app dipetakan ke external id
``labapp_import.<tabel>_<id>``. Record yang sudah ada diperbarui (data master) atau
dilewati (transaksi stok: PO, penerimaan, perbaikan) sehingga stok tidak terhitung ganda.
Langkah terakhir menyamakan stok Odoo dengan kolom ``inventaris.qty`` di MySQL.

Password Laravel (bcrypt) tidak bisa dipindahkan. Semua akun hasil impor diberi password
dari env ``LABAPP_PASSWORD`` atau password acak yang dicetak di akhir.
"""
import json
import os
import pathlib
import secrets
from datetime import datetime

DATA_DIR = pathlib.Path(os.environ.get('LABAPP_DATA_DIR', '/mnt/scripts/labapp_import/data'))
MODULE = 'labapp_import'
PASSWORD = os.environ.get('LABAPP_PASSWORD') or secrets.token_urlsafe(9)

IMD = env['ir.model.data'].sudo()
report = {}


def rows(table):
    path = DATA_DIR / f'{table}.jsonl'
    if not path.exists():
        print(f'[peringatan] {path} tidak ada, dilewati')
        return []
    return [json.loads(line) for line in path.read_text(encoding='utf-8').splitlines() if line.strip()]


def ref(table, key):
    if key in (None, '', 0):
        return None
    return env.ref(f'{MODULE}.{table}_{key}', raise_if_not_found=False)


def bind(table, key, record):
    IMD.create({'module': MODULE, 'name': f'{table}_{key}', 'model': record._name,
                'res_id': record.id, 'noupdate': True})


def upsert(table, key, model, vals):
    """Buat atau perbarui record master; mengembalikan (record, dibuat_baru)."""
    record = ref(table, key)
    if record:
        record.write(vals)
        return record, False
    record = env[model].sudo().create(vals)
    bind(table, key, record)
    return record, True


def count(name, created):
    stat = report.setdefault(name, [0, 0])
    stat[0 if created else 1] += 1


def to_date(value):
    return value[:10] if value else False


def to_dt(value):
    # Laravel menyimpan timestamp dalam UTC (config/app.php timezone = UTC)
    return value[:19] if value else False


def num(value, default=0.0):
    try:
        return float(value)
    except (TypeError, ValueError):
        return default


# ---------------------------------------------------------------------------
# 1. Akademik: prodi, kelas, mata kuliah, mahasiswa
# ---------------------------------------------------------------------------
for r in rows('prodi'):
    nama = r['prodi_name']
    kode = ''.join(w[0] for w in nama.split() if w[:1].isalpha()).upper() or f'P{r["prodi_id"]}'
    if not ref('prodi', r['prodi_id']):
        existing = env['bp.edu.program.studi'].sudo().search(['|', ('nama', '=', nama), ('kode', '=', kode)], limit=1)
        if existing:
            bind('prodi', r['prodi_id'], existing)
    rec, new = upsert('prodi', r['prodi_id'], 'bp.edu.program.studi', {
        'nama': nama,
        'kode': ref('prodi', r['prodi_id']).kode if ref('prodi', r['prodi_id']) else kode,
        'jenjang': 's1',
        'gedung': r.get('gedung'),
        'alamat': r.get('street'),
        'telepon': str(r['phone']) if r.get('phone') else False,
        'deskripsi': r.get('desc'),
    })
    count('prodi', new)

for r in rows('kelas'):
    rec, new = upsert('kelas', r['kelas_id'], 'bp.edu.kelas', {
        'nama': r['kelas_name'],
        'kode': r['kelas_code'],
        'angkatan': r.get('angkatan') or 0,
        'prodi_id': ref('prodi', r['prodi_id']).id,
        'deskripsi': r.get('desc'),
    })
    count('kelas', new)

for r in rows('mata_kuliah'):
    if r.get('deleted_at'):
        print(f'[info] mata kuliah {r["mata_kuliah_code"]} soft-deleted di lab-app, dilewati')
        continue
    if not ref('mata_kuliah', r['mata_kuliah_id']):
        existing = env['bp.edu.mata.kuliah'].sudo().search([('kode', '=', r['mata_kuliah_code'])], limit=1)
        if existing:
            bind('mata_kuliah', r['mata_kuliah_id'], existing)
    prodi = env['bp.edu.program.studi'].sudo().search([], limit=2)
    rec, new = upsert('mata_kuliah', r['mata_kuliah_id'], 'bp.edu.mata.kuliah', {
        'kode': r['mata_kuliah_code'],
        'nama': r['mata_kuliah_name'],
        'semester': int(num(r.get('semester'), 1)),
        'dosen_pengampu': r.get('dosen'),
        'deskripsi_singkat': r.get('desc'),
        # lab-app tidak menyimpan prodi untuk mata kuliah; isi bila hanya ada satu prodi
        'prodi_id': prodi.id if len(prodi) == 1 else False,
    })
    count('mata_kuliah', new)

for r in rows('mahasiswa'):
    gender = r.get('mahasiswa_gender')
    rec, new = upsert('mahasiswa', r['mahasiswa_id'], 'bp.edu.mahasiswa', {
        'nim': r['mahasiswa_nim'],
        'nama': r['mahasiswa_name'],
        'email': r['mahasiswa_email'],
        'telepon': None if r.get('mahasiswa_phone') in (None, '-') else r['mahasiswa_phone'],
        'alamat': None if r.get('mahasiswa_street') in (None, '-') else r['mahasiswa_street'],
        'tanggal_lahir': to_date(r.get('mahasiswa_dob')),
        'gender': gender if gender in ('laki', 'perempuan') else False,
        'prodi_id': ref('prodi', r['prodi_id']).id,
        'kelas_id': ref('kelas', r['kelas_id']).id if ref('kelas', r['kelas_id']) else False,
        'tahun': r.get('tahun') or 0,
        'deskripsi': r.get('desc'),
    })
    foto = r.get('mahasiswa_photo')
    foto_path = DATA_DIR / 'files' / 'mahasiswa' / (foto or '')
    if foto and foto != 'default.png' and foto_path.is_file():
        import base64
        rec.foto = base64.b64encode(foto_path.read_bytes())
    count('mahasiswa', new)

# ---------------------------------------------------------------------------
# 2. Akun pengguna: admin -> user internal + group lab admin, user -> portal
# ---------------------------------------------------------------------------
group_admin = env.ref('bp_edu_lab.group_lab_admin')
group_manager = env.ref('bp_edu_lab.group_lab_manager')
group_internal = env.ref('base.group_user')
group_portal = env.ref('base.group_portal')
Users = env['res.users'].sudo().with_context(no_reset_password=True, active_test=False)
for r in rows('users'):
    login = r['email'].strip().lower()
    tipe = r.get('type') or 0
    groups = {1: [group_internal, group_admin], 2: [group_internal, group_manager]}.get(tipe, [group_portal])
    user = ref('users', r['id'])
    if not user:
        user = Users.search([('login', '=', login)], limit=1)
        if user:
            bind('users', r['id'], user)
    new = not user
    if new:
        user = Users.create({
            'name': r['name'],
            'login': login,
            'email': login,
            'password': PASSWORD,
            'group_ids': [(6, 0, [g.id for g in groups])],
        })
        bind('users', r['id'], user)
    elif tipe in (1, 2):
        user.write({'group_ids': [(4, g.id) for g in groups]})
    mahasiswa = ref('mahasiswa', r.get('mahasiswa_id'))
    if mahasiswa and mahasiswa.user_id != user:
        # Tautan eksplisit users.mahasiswa_id di lab-app (tidak selalu sama emailnya)
        env['bp.edu.mahasiswa'].sudo().search([('user_id', '=', user.id)]).user_id = False
        mahasiswa.user_id = user
    count('users', new)

# ---------------------------------------------------------------------------
# 3. Inventaris: kategori, barang, supplier
# ---------------------------------------------------------------------------
UOM_MAP = {'unit': 'uom.product_uom_unit', 'pcs': 'uom.product_uom_unit'}
uom_unit = env.ref('uom.product_uom_unit')


def get_uom(nama):
    nama = (nama or 'unit').strip()
    if nama.lower() in UOM_MAP:
        return env.ref(UOM_MAP[nama.lower()])
    uom = env['uom.uom'].sudo().search([('name', '=ilike', nama)], limit=1)
    if not uom:
        uom = env['uom.uom'].sudo().create({'name': nama, 'relative_factor': 1.0, 'relative_uom_id': uom_unit.id})
    return uom


parent_categ = env.ref('product.product_category_all', raise_if_not_found=False)
for r in rows('category_inventaris'):
    rec, new = upsert('category_inventaris', r['category_inventaris_id'], 'product.category', {
        'name': r['category_inventaris_name'],
        'parent_id': parent_categ.id if parent_categ else False,
    })
    count('kategori', new)

for r in rows('inventaris'):
    categ = ref('category_inventaris', r.get('category_inventaris_id'))
    uom = get_uom(r.get('satuan'))
    vals = {
        'name': r['inventaris_name'],
        'default_code': r['inventaris_code'],
        'type': 'consu',
        'is_storable': True,
        'bp_inventaris_lab': True,
        'bp_reusable': bool(r.get('reuseable')),
        'bp_min_stock': num(r.get('min_stock')),
        'bp_expiry_date': to_date(r.get('expiry')),
        'purchase_ok': True,
        'sale_ok': False,
    }
    if categ:
        vals['categ_id'] = categ.id
    tmpl = ref('inventaris', r['inventaris_id'])
    if not tmpl:
        vals.update({'uom_id': uom.id})
    rec, new = upsert('inventaris', r['inventaris_id'], 'product.template', vals)
    count('inventaris', new)


def product_of(inventaris_id):
    tmpl = ref('inventaris', inventaris_id)
    return tmpl.product_variant_id if tmpl else None


for r in rows('supplier'):
    rec, new = upsert('supplier', r['supplier_id'], 'res.partner', {
        'name': r['supplier_name'],
        'is_company': True,
        'supplier_rank': 1,
        'phone': r.get('supplier_phone'),
        'email': r.get('supplier_email'),
        'street': r.get('supplier_street'),
        'comment': r.get('desc'),
        'active': not r.get('deleted_at'),
    })
    if r.get('supplier_pic') and not rec.child_ids.filtered(lambda c: c.name == r['supplier_pic']):
        env['res.partner'].sudo().create({'name': r['supplier_pic'], 'parent_id': rec.id, 'type': 'contact',
                                          'function': 'PIC'})
    count('supplier', new)

# ---------------------------------------------------------------------------
# 4. Purchase order, penerimaan, stock opname, perbaikan
# ---------------------------------------------------------------------------
helper = env['bp.edu.lab.stock.helper'].sudo()
lokasi_stok = helper._get_lokasi_stok()
po_lines = {}
for r in rows('purchase_order_detail'):
    po_lines.setdefault(r['purchase_order_id'], []).append(r)
recv_lines = {}
for r in rows('recieving_detail'):
    recv_lines.setdefault(r['recieving_id'], []).append(r)
receipts_by_po = {}
receipts = rows('recieving')
for r in receipts:
    if r.get('purchase_order_id'):
        receipts_by_po.setdefault(r['purchase_order_id'], []).append(r)

PO = env['purchase.order'].sudo()
for r in rows('purchase_order'):
    if ref('purchase_order', r['purchase_order_id']):
        count('purchase_order', False)
        continue
    partner = ref('supplier', r['supplier_id'])
    po = PO.create({
        'name': r['purchase_order_code'],
        'partner_id': partner.id,
        'partner_ref': r.get('refrensi'),
        'date_order': r['purchase_order_date'] + ' 00:00:00',
        'note': r.get('note'),
        'order_line': [(0, 0, {
            'product_id': product_of(line['inventaris_id']).id,
            'product_qty': line['purchase_order_qty'],
            'price_unit': 0.0,
            'date_planned': r['purchase_order_date'] + ' 00:00:00',
        }) for line in po_lines.get(r['purchase_order_id'], [])],
    })
    bind('purchase_order', r['purchase_order_id'], po)
    status = r.get('status') or 1
    if status in (1, 2):
        po.button_confirm()
    else:
        po.button_cancel()
    count('purchase_order', True)

for r in receipts:
    if ref('recieving', r['recieving_id']):
        count('recieving', False)
        continue
    lines = recv_lines.get(r['recieving_id'], [])
    po = ref('purchase_order', r.get('purchase_order_id'))
    picking = po.picking_ids.filtered(lambda p: p.state not in ('done', 'cancel'))[:1] if po else None
    if not picking:
        picking_type = env['stock.picking.type'].sudo().search(
            [('code', '=', 'incoming'), ('company_id', '=', env.company.id)], limit=1)
        partner = ref('supplier', r.get('supplier_id'))
        src = picking_type.default_location_src_id or env.ref('stock.stock_location_suppliers')
        dest = picking_type.default_location_dest_id or lokasi_stok
        picking = env['stock.picking'].sudo().create({
            'picking_type_id': picking_type.id,
            'partner_id': partner.id if partner else False,
            'location_id': src.id,
            'location_dest_id': dest.id,
            'origin': r.get('purchase_order_code') or r.get('refrensi'),
            'move_ids': [(0, 0, {
                'product_id': product_of(line['inventaris_id']).id,
                'product_uom_qty': line['recieving_qty'],
                'product_uom': product_of(line['inventaris_id']).uom_id.id,
                'location_id': src.id,
                'location_dest_id': dest.id,
            }) for line in lines],
        })
        picking.action_confirm()
    qty_by_product = {}
    for line in lines:
        qty_by_product[product_of(line['inventaris_id']).id] = qty_by_product.get(
            product_of(line['inventaris_id']).id, 0) + line['recieving_qty']
    for move in picking.move_ids:
        move.quantity = qty_by_product.get(move.product_id.id, 0)
        move.picked = True
    picking.with_context(skip_backorder=True, picking_ids_not_to_backorder=picking.ids).button_validate()
    picking.write({'name': r['recieving_code'], 'note': r.get('note'),
                   'date_done': r['recieving_date'] + ' 00:00:00'})
    picking.move_ids.write({'date': r['recieving_date'] + ' 00:00:00'})
    bind('recieving', r['recieving_id'], picking)
    count('recieving', True)

so_lines = {}
for r in rows('stock_opname_detail'):
    so_lines.setdefault(r['stock_opname_id'], []).append(r)
for r in rows('stock_opname'):
    if ref('stock_opname', r['stock_opname_id']):
        count('stock_opname', False)
        continue
    # Dicatat sebagai riwayat (status selesai, angka asli lab-app). Efek stoknya sudah
    # tercermin pada inventaris.qty yang disamakan di langkah terakhir.
    catatan = '\n'.join(filter(None, [r.get('note'), r.get('desc')]))
    opname = env['bp.edu.lab.stock.opname'].sudo().create({
        'kode': r['stock_opname_code'],
        'tanggal': r['stock_opname_date'],
        'referensi': r.get('refrensi'),
        'catatan': catatan,
        'state': 'selesai',
        'user_id': (ref('users', r.get('user_id')) or env.user).id,
        'line_ids': [(0, 0, {
            'product_id': product_of(line['inventaris_id']).id,
            'qty_sebelum': line.get('before_qty') or 0,
            'qty_hitung': line.get('so_qty') or 0,
            'selisih': line.get('final_qty') or 0,
        }) for line in so_lines.get(r['stock_opname_id'], [])],
    })
    bind('stock_opname', r['stock_opname_id'], opname)
    count('stock_opname', True)

for r in rows('inventaris_perbaikan'):
    if ref('inventaris_perbaikan', r['perbaikan_id']):
        count('perbaikan', False)
        continue
    product = product_of(r['inventaris_id'])
    qty = r['qty_rusak'] or 1
    tersedia = helper._qty_di_lokasi(product, lokasi_stok)
    if tersedia < qty:
        helper._set_qty(product, qty, lokasi_stok)  # dirapikan lagi di langkah terakhir
    perbaikan = env['bp.edu.lab.perbaikan'].sudo().create({
        'product_id': product.id,
        'tanggal': to_date(r.get('tanggal_perbaikan')) or to_date(r.get('created_at')),
        'qty': qty,
        'keterangan': r.get('keterangan'),
    })
    perbaikan.action_proses()
    if r.get('status') == 'selesai':
        perbaikan.action_selesai()
        perbaikan.tanggal_selesai = to_date(r.get('tanggal_selesai'))
    bind('inventaris_perbaikan', r['perbaikan_id'], perbaikan)
    count('perbaikan', True)

# ---------------------------------------------------------------------------
# 5. Ujian (test -> survey)
# ---------------------------------------------------------------------------
soal_by_test = {}
for r in rows('test_detail'):
    soal_by_test.setdefault(r['test_id'], []).append(r)
for r in rows('test'):
    survey, new = upsert('test', r['test_id'], 'survey.survey', {
        'title': r['test_name'],
        'jenis_ujian': 'pra' if r.get('type') == 'pra' else 'post',
        'mata_kuliah_id': ref('mata_kuliah', r.get('mata_kuliah_id')).id if ref('mata_kuliah', r.get('mata_kuliah_id')) else False,
        'description': r.get('desc') if r.get('desc') not in (None, '-') else False,
        'active': not r.get('archived'),
        **env['survey.survey']._get_lab_default_vals(),
    })
    for seq, q in enumerate(soal_by_test.get(r['test_id'], []), start=1):
        upsert('test_detail', q['test_detail_id'], 'survey.question', {
            'survey_id': survey.id,
            'title': q['test_detail_soal'],
            'question_type': 'text_box',
            'kunci_jawaban': q.get('test_detail_jawaban'),
            'sequence': seq,
        })
    count('test', new)

# ---------------------------------------------------------------------------
# 6. Praktikum, bahan, kelompok, peserta
# ---------------------------------------------------------------------------
for r in rows('praktikum'):
    pre, post = ref('test', r.get('test_id')), ref('test', r.get('post_test_id'))
    rec, new = upsert('praktikum', r['praktikum_id'], 'bp.edu.lab.praktikum', {
        'nama': r['praktikum_name'],
        'ruang': r.get('praktikum_room'),
        'tanggal': to_date(r.get('praktikum_date')),
        'due_date': to_date(r.get('due_date')),
        'mata_kuliah_id': ref('mata_kuliah', r['mata_kuliah_id']).id,
        'pretest_id': pre.id if pre else False,
        'posttest_id': post.id if post else False,
        'deskripsi': r.get('desc'),
        'token': r.get('token') or False,
        'token_expired_at': to_dt(r.get('token_expired_at')),
    })
    count('praktikum', new)

for r in rows('praktikum_detail'):
    rec, new = upsert('praktikum_detail', r['praktikum_detail_id'], 'bp.edu.lab.praktikum.bahan', {
        'praktikum_id': ref('praktikum', r['praktikum_id']).id,
        'product_id': product_of(r['inventaris_id']).id,
        'qty': r.get('praktikum_qty') or 0,
    })
    count('praktikum_bahan', new)

Kelompok = env['bp.edu.lab.kelompok'].sudo()
for r in rows('kelompok'):
    vals = {
        'nama': r['kelompok_name'],
        'praktikum_id': ref('praktikum', r['praktikum_id']).id,
        'kelas_id': ref('kelas', r.get('kelas_id')).id if ref('kelas', r.get('kelas_id')) else False,
        'deskripsi': r.get('desc'),
    }
    kelompok = ref('kelompok', r['kelompok_id'])
    if kelompok:
        kelompok.action_draft()
        kelompok.write(vals)
        new = False
    else:
        kelompok = Kelompok.create(vals)
        bind('kelompok', r['kelompok_id'], kelompok)
        new = True
    kelompok.write({'prodi_id': ref('prodi', r.get('prodi_id')).id if ref('prodi', r.get('prodi_id')) else kelompok.prodi_id.id,
                    'angkatan': r.get('angkatan') or kelompok.angkatan})
    count('kelompok', new)

Peserta = env['bp.edu.lab.peserta'].sudo()
for r in rows('kelompok_detail'):
    praktikum = ref('praktikum', r['praktikum_id'])
    mahasiswa = ref('mahasiswa', r['mahasiswa_id'])
    if not praktikum or not mahasiswa:
        print(f'[peringatan] kelompok_detail {r["kelompok_detail_id"]}: praktikum/mahasiswa tidak ada, dilewati')
        continue
    kelompok = ref('kelompok', r.get('kelompok_id'))
    if not kelompok:
        # Baris lama tanpa kelompok_id: tampung di kelompok "Umum" per praktikum
        kelompok = Kelompok.search([('praktikum_id', '=', praktikum.id), ('nama', '=', f'Umum - {praktikum.nama}')], limit=1) \
            or Kelompok.create({'nama': f'Umum - {praktikum.nama}', 'praktikum_id': praktikum.id,
                                'kelas_id': mahasiswa.kelas_id.id})
    if kelompok.state == 'selesai':
        kelompok.action_draft()
    rec, new = upsert('kelompok_detail', r['kelompok_detail_id'], 'bp.edu.lab.peserta', {
        'kelompok_id': kelompok.id,
        'mahasiswa_id': mahasiswa.id,
        'presensi': bool(r.get('presensi')),
        'nilai': num(r.get('nilai')),
    })
    count('peserta', new)

for r in rows('kelompok'):
    if r.get('done'):
        ref('kelompok', r['kelompok_id']).action_selesai()

# ---------------------------------------------------------------------------
# 7. Jawaban ujian (test_answer -> survey.user_input)
# ---------------------------------------------------------------------------
UserInput = env['survey.user_input'].sudo()
for r in rows('test_answer'):
    praktikum = ref('praktikum', r['praktikum_id'])
    mahasiswa = ref('mahasiswa', r['mahasiswa_id'])
    question = ref('test_detail', r['test_detail_id'])
    if not (praktikum and mahasiswa and question):
        continue
    jenis = r.get('jenis') or question.survey_id.jenis_ujian
    answer = UserInput.search([('praktikum_id', '=', praktikum.id), ('mahasiswa_id', '=', mahasiswa.id),
                               ('jenis_ujian', '=', jenis), ('survey_id', '=', question.survey_id.id)], limit=1)
    if not answer:
        answer = UserInput.create({
            'survey_id': question.survey_id.id,
            'partner_id': mahasiswa.user_id.partner_id.id if mahasiswa.user_id else False,
            'email': mahasiswa.email,
            'nickname': mahasiswa.nama,
            'praktikum_id': praktikum.id,
            'mahasiswa_id': mahasiswa.id,
            'jenis_ujian': jenis,
            'state': 'done',
        })
    line = answer.user_input_line_ids.filtered(lambda l: l.question_id == question)
    vals = {'value_text_box': r.get('jawaban') or '', 'answer_type': 'text_box', 'skipped': not r.get('jawaban')}
    if line:
        line.write(vals)
    else:
        answer.write({'user_input_line_ids': [(0, 0, dict(vals, question_id=question.id))]})
    count('test_answer', True)

# ---------------------------------------------------------------------------
# 8. Samakan stok dengan inventaris.qty di lab-app
# ---------------------------------------------------------------------------
for r in rows('inventaris'):
    product = product_of(r['inventaris_id'])
    target = num(r.get('qty'))
    if helper._qty_di_lokasi(product, lokasi_stok) != target:
        helper._set_qty(product, target, lokasi_stok)
report['stok_disamakan'] = [len(rows('inventaris')), 0]

env.cr.commit()

print('\n=== Ringkasan impor lab-app (baru, diperbarui/dilewati) ===')
for name, (baru, lama) in report.items():
    print(f'{name:18} {baru:4} {lama:4}')
if not os.environ.get('LABAPP_PASSWORD') and report.get('users', [0])[0]:
    print(f'\nPassword akun hasil impor yang BARU dibuat: {PASSWORD}')
    print('(set env LABAPP_PASSWORD sebelum impor untuk memakai password sendiri)')
