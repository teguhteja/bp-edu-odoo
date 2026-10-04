"""Verifikasi hasil impor: bandingkan data lab-app (JSONL) dengan record Odoo di DB labapp.

    .\\labapp\\odoo-labapp.ps1 shell labapp_import/verify_import.py

Keluar dengan pesan "SEMUA COCOK" atau daftar selisih.
"""
import json
import os
import pathlib

DATA_DIR = pathlib.Path(os.environ.get('LABAPP_DATA_DIR', '/mnt/scripts/labapp_import/data'))
MODULE = 'labapp_import'
masalah = []


def rows(table):
    path = DATA_DIR / f'{table}.jsonl'
    return [json.loads(l) for l in path.read_text(encoding='utf-8').splitlines() if l.strip()] if path.exists() else []


def ref(table, key):
    return env.ref(f'{MODULE}.{table}_{key}', raise_if_not_found=False)


def cek(label, harapan, hasil):
    status = 'OK ' if harapan == hasil else 'BEDA'
    print(f'[{status}] {label:38} lab-app={harapan!s:>8}  odoo={hasil!s:>8}')
    if harapan != hasil:
        masalah.append(label)


# Jumlah record per tabel (tiap baris lab-app harus punya pasangan di Odoo)
TABEL = ['prodi', 'kelas', 'mata_kuliah', 'mahasiswa', 'users', 'category_inventaris', 'inventaris',
         'supplier', 'purchase_order', 'recieving', 'stock_opname', 'inventaris_perbaikan', 'test',
         'test_detail', 'praktikum', 'praktikum_detail', 'kelompok', 'kelompok_detail']
for tabel in TABEL:
    data = rows(tabel)
    pk = next(iter(data[0])) if data else None
    keys = [r.get(f'{tabel}_id', r.get('id', r.get('perbaikan_id'))) for r in data]
    ada = sum(1 for k in keys if ref(tabel, k))
    cek(f'jumlah {tabel}', len(data), ada)

# Stok tiap barang = inventaris.qty
helper = env['bp.edu.lab.stock.helper']
lokasi = helper._get_lokasi_stok()
for r in rows('inventaris'):
    tmpl = ref('inventaris', r['inventaris_id'])
    qty = helper._qty_di_lokasi(tmpl.product_variant_id, lokasi) if tmpl else None
    cek(f'stok {r["inventaris_code"]}', float(r['qty']), qty)

# Nilai & presensi peserta
beda_nilai = 0
for r in rows('kelompok_detail'):
    peserta = ref('kelompok_detail', r['kelompok_detail_id'])
    nilai = float(r['nilai']) if r.get('nilai') not in (None, '') else 0.0
    if not peserta or peserta.nilai != nilai or peserta.presensi != bool(r.get('presensi')):
        beda_nilai += 1
cek('peserta dengan nilai/presensi berbeda', 0, beda_nilai)

# Status PO & penerimaan
for r in rows('purchase_order'):
    po = ref('purchase_order', r['purchase_order_id'])
    harapan = {1: 'pending', 2: 'full'}.get(r.get('status'), 'cancel')
    hasil = 'cancel' if po and po.state == 'cancel' else (po.receipt_status if po else None)
    cek(f'status {r["purchase_order_code"]}', harapan, hasil)

# Kelompok selesai, token praktikum, tautan akun mahasiswa
cek('kelompok selesai', sum(1 for r in rows('kelompok') if r.get('done')),
    env['bp.edu.lab.kelompok'].search_count([('state', '=', 'selesai')]))
for r in rows('praktikum'):
    p = ref('praktikum', r['praktikum_id'])
    cek(f'token praktikum {r["praktikum_id"]}', r.get('token') or False, p.token if p else None)
for r in rows('users'):
    if r.get('mahasiswa_id'):
        m = ref('mahasiswa', r['mahasiswa_id'])
        cek(f'akun {r["email"]} -> mahasiswa', r['mahasiswa_id'] and True, bool(m and m.user_id == ref('users', r['id'])))
cek('perbaikan status proses', sum(1 for r in rows('inventaris_perbaikan') if r.get('status') == 'proses'),
    env['bp.edu.lab.perbaikan'].search_count([('state', '=', 'proses')]))

print('\nSEMUA COCOK' if not masalah else f'\n{len(masalah)} SELISIH: {", ".join(masalah)}')
