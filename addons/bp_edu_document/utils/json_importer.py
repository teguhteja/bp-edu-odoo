"""
JSON → Odoo importer untuk format JSON rps_bp.

Mendukung tiga tipe JSON:
  - RPS   : keys meta, cpl_prodi, cpmk, sub_cpmk, detail, pustaka_utama, pustaka_pendukung
  - SAP   : keys meta, pertemuan
  - Kontrak : keys tahun_akademik, nama_mk, cpmk, materi_minggu_N, bobot_*

Setiap fungsi menerima `env` (Odoo Environment) dan `data` (parsed dict).
"""
import logging

_logger = logging.getLogger(__name__)


# ─── Helpers ─────────────────────────────────────────────────────────────────

def _safe_int(val, default=0):
    try:
        return int(val)
    except (TypeError, ValueError):
        return default


def _find_or_create_mk(env, kode, nama, meta):
    MK = env['bp.edu.mata.kuliah']
    mk = MK.search([('kode', '=', kode)], limit=1)
    if not mk:
        mk = MK.create({
            'kode': kode,
            'nama': nama,
            'sks_teori': _safe_int(meta.get('sks_teori', 2)),
            'sks_praktik': _safe_int(meta.get('sks_praktik', 0)),
            'semester': _safe_int(meta.get('semester', 1)),
            'status': meta.get('status', 'Wajib'),
            'kategori': meta.get('kategori', ''),
            'deskripsi_singkat': meta.get('deskripsi_singkat', ''),
            'bahan_kajian': meta.get('bahan_kajian', ''),
            'matakuliah_syarat': meta.get('matakuliah_syarat', '-'),
        })
    return mk


def _upsert_cpl(env, cpl_prodi_list):
    """Upsert CPL records. Returns {kode: id} map."""
    CPL = env['bp.edu.cpl']
    cpl_map = {}
    for item in cpl_prodi_list:
        kode = item.get('kode', '').strip()
        if not kode:
            continue
        cpl = CPL.search([('kode', '=', kode)], limit=1)
        if cpl:
            cpl.write({
                'tipe': item.get('tipe', cpl.tipe),
                'deskripsi': item.get('deskripsi', cpl.deskripsi),
            })
        else:
            cpl = CPL.create({
                'kode': kode,
                'tipe': item.get('tipe', 'Pengetahuan'),
                'deskripsi': item.get('deskripsi', ''),
            })
        cpl_map[kode] = cpl.id
    return cpl_map


def _find_dosen(env, nama_str):
    if not nama_str:
        return env['bp.edu.dosen'].browse()
    # Coba exact match dulu, fallback ilike
    dosen = env['bp.edu.dosen'].search([('nama', '=', nama_str)], limit=1)
    if not dosen:
        dosen = env['bp.edu.dosen'].search([('nama', 'ilike', nama_str.split(',')[0].strip())], limit=1)
    return dosen


def _active_tahun_akademik(env):
    return env['bp.edu.tahun.akademik'].search([('aktif', '=', True)], limit=1)


# ─── RPS Importer ────────────────────────────────────────────────────────────

def import_rps(env, data: dict) -> dict:
    """
    Import data JSON format RPS ke Odoo.

    Returns:
        dict dengan 'mk_id' dan 'rps_id'
    """
    meta = data.get('meta', {})
    kode_mk = meta.get('kode_mk', '').strip()
    nama_mk = meta.get('nama_mk', '').strip()

    if not kode_mk or not nama_mk:
        raise ValueError('JSON tidak valid: meta.kode_mk dan meta.nama_mk wajib ada.')

    # 1. Mata Kuliah
    meta_with_desc = dict(meta)
    meta_with_desc['deskripsi_singkat'] = data.get('deskripsi_singkat', '')
    meta_with_desc['bahan_kajian'] = data.get('bahan_kajian', '')
    meta_with_desc['matakuliah_syarat'] = data.get('matakuliah_syarat', '-')
    mk = _find_or_create_mk(env, kode_mk, nama_mk, meta_with_desc)

    # Update deskripsi jika MK sudah ada
    mk.write({
        'deskripsi_singkat': data.get('deskripsi_singkat', mk.deskripsi_singkat or ''),
        'bahan_kajian': data.get('bahan_kajian', mk.bahan_kajian or ''),
        'matakuliah_syarat': data.get('matakuliah_syarat', mk.matakuliah_syarat or '-'),
    })

    # 2. CPL Prodi
    cpl_map = _upsert_cpl(env, data.get('cpl_prodi', []))
    if cpl_map:
        mk.write({'cpl_ids': [(6, 0, list(cpl_map.values()))]})

    # 3. CPMK (hapus existing lalu buat ulang)
    mk.cpmk_ids.mapped('sub_cpmk_ids').unlink()
    mk.cpmk_ids.unlink()

    cpmk_map = {}
    for item in data.get('cpmk', []):
        kode = item.get('kode', '').strip()
        cpl_text = item.get('cpl', '')
        cpl_kodes = [k.strip() for k in cpl_text.split(',') if k.strip()]
        cpl_ids = [cpl_map[k] for k in cpl_kodes if k in cpl_map]
        cpmk = env['bp.edu.cpmk'].create({
            'kode': kode,
            'mata_kuliah_id': mk.id,
            'deskripsi': item.get('deskripsi', ''),
            'cpl_text': cpl_text,
            'cpl_ids': [(6, 0, cpl_ids)],
        })
        cpmk_map[kode] = cpmk.id

    # 4. Sub-CPMK
    for item in data.get('sub_cpmk', []):
        cpmk_kode = item.get('cpmk', '').strip()
        if cpmk_kode not in cpmk_map:
            _logger.warning('Sub-CPMK %s: CPMK %s tidak ditemukan, dilewati.', item.get('kode'), cpmk_kode)
            continue
        env['bp.edu.sub.cpmk'].create({
            'kode': item.get('kode', ''),
            'cpmk_id': cpmk_map[cpmk_kode],
            'deskripsi': item.get('deskripsi', ''),
            'minggu': item.get('minggu', ''),
            'level_bloom': item.get('cpl', ''),
        })

    # 5. Pustaka (hapus existing lalu buat ulang)
    mk.pustaka_ids.unlink()
    for item in data.get('pustaka_utama', []):
        env['bp.edu.pustaka'].create({
            'kode': item.get('kode', ''),
            'mata_kuliah_id': mk.id,
            'jenis': 'Utama',
            'referensi': item.get('referensi', ''),
        })
    for item in data.get('pustaka_pendukung', []):
        env['bp.edu.pustaka'].create({
            'kode': item.get('kode', ''),
            'mata_kuliah_id': mk.id,
            'jenis': 'Pendukung',
            'referensi': item.get('referensi', ''),
        })

    # 6. RPS header
    dosen = _find_dosen(env, meta.get('dosen_pengampu', ''))
    ta = _active_tahun_akademik(env)
    rps = env['bp.edu.rps'].create({
        'mata_kuliah_id': mk.id,
        'dosen_id': dosen.id if dosen else False,
        'tahun_akademik_id': ta.id if ta else False,
        'tanggal_penyusunan': meta.get('tanggal_penyusunan') or False,
    })

    # 7. RPS Detail (16 minggu)
    for item in data.get('detail', []):
        env['bp.edu.rps.detail'].create({
            'rps_id': rps.id,
            'minggu': _safe_int(item.get('minggu', 0)),
            'deskripsi': item.get('deskripsi', ''),
            'indikator': item.get('indikator', ''),
            'kriteria': item.get('kriteria', ''),
            'tatap_muka': item.get('tatap_muka', ''),
            'daring': item.get('daring', ''),
            'materi': item.get('materi', ''),
            'bobot': str(item.get('bobot', '')),
        })

    _logger.info('Import RPS selesai: MK=%s, RPS id=%s', kode_mk, rps.id)
    return {'mk_id': mk.id, 'rps_id': rps.id}


# ─── SAP Importer ────────────────────────────────────────────────────────────

def import_sap(env, data: dict) -> dict:
    """Import data JSON format SAP ke Odoo. Returns dict dengan 'sap_id'."""
    meta = data.get('meta', {})
    kode_mk = meta.get('kode_mk', '').strip()
    nama_mk = meta.get('nama_mk', '').strip()

    mk = _find_or_create_mk(env, kode_mk, nama_mk, meta)
    dosen = _find_dosen(env, meta.get('dosen_pengampu', ''))
    ta = _active_tahun_akademik(env)

    sap = env['bp.edu.sap'].create({
        'mata_kuliah_id': mk.id,
        'dosen_id': dosen.id if dosen else False,
        'tahun_akademik_id': ta.id if ta else False,
    })

    for item in data.get('pertemuan', []):
        kegiatan = item.get('kegiatan', {})
        pendahuluan = kegiatan.get('pendahuluan', {})
        penyajian = kegiatan.get('penyajian', {})
        penutup = kegiatan.get('penutup', {})

        env['bp.edu.sap.pertemuan'].create({
            'sap_id': sap.id,
            'no': _safe_int(item.get('no', 0)),
            'waktu_pertemuan': item.get('waktu_pertemuan', ''),
            'detail_cpmk': item.get('detail_cpmk', ''),
            'detail_sub_cpmk': item.get('detail_sub_cpmk', ''),
            'indikator_1': item.get('indikator_1', ''),
            'indikator_2': item.get('indikator_2', ''),
            'tujuan_pembelajaran': item.get('tujuan_pembelajaran', ''),
            'pokok_bahasan': item.get('pokok_bahasan', ''),
            'sub_pokok_bahasan_1': item.get('sub_pokok_bahasan_1', ''),
            'sub_pokok_bahasan_2': item.get('sub_pokok_bahasan_2', ''),
            'pendahuluan_pengajar': pendahuluan.get('pengajar', ''),
            'pendahuluan_mahasiswa': pendahuluan.get('mahasiswa', ''),
            'pendahuluan_media': pendahuluan.get('media', ''),
            'penyajian_pengajar': penyajian.get('pengajar', ''),
            'penyajian_mahasiswa': penyajian.get('mahasiswa', ''),
            'penyajian_media': penyajian.get('media', ''),
            'penutup_pengajar': penutup.get('pengajar', ''),
            'penutup_mahasiswa': penutup.get('mahasiswa', ''),
            'penutup_media': penutup.get('media', ''),
            'evaluasi_1': item.get('evaluasi_1', ''),
            'evaluasi_2': item.get('evaluasi_2', ''),
            'referensi_1': item.get('referensi_1', ''),
            'referensi_2': item.get('referensi_2', ''),
        })

    _logger.info('Import SAP selesai: MK=%s, SAP id=%s', kode_mk, sap.id)
    return {'mk_id': mk.id, 'sap_id': sap.id}


# ─── Kontrak Kuliah Importer ─────────────────────────────────────────────────

def import_kontrak(env, data: dict) -> dict:
    """Import data JSON format Kontrak Kuliah ke Odoo. Returns dict dengan 'kontrak_id'."""
    nama_mk = data.get('nama_mk', '').strip()
    mk = env['bp.edu.mata.kuliah'].search([('nama', 'ilike', nama_mk)], limit=1)
    if not mk:
        # Buat MK minimal jika tidak ditemukan
        mk = env['bp.edu.mata.kuliah'].create({
            'kode': f'TMP_{nama_mk[:6].upper().replace(" ", "")}',
            'nama': nama_mk,
            'sks_teori': _safe_int(data.get('sks_total', 2)),
            'kategori': data.get('jenis_mk', ''),
        })

    dosen = _find_dosen(env, data.get('dosen_pengampu', ''))
    ta = _active_tahun_akademik(env)

    # CPMK dari kontrak (kode + deskripsi saja)
    cpmk_ids = []
    for item in data.get('cpmk', []):
        kode = item.get('kode', '').strip()
        cpmk = env['bp.edu.cpmk'].search([
            ('kode', '=', kode), ('mata_kuliah_id', '=', mk.id)
        ], limit=1)
        if not cpmk:
            cpmk = env['bp.edu.cpmk'].create({
                'kode': kode,
                'mata_kuliah_id': mk.id,
                'deskripsi': item.get('deskripsi', ''),
            })
        cpmk_ids.append(cpmk.id)

    kontrak = env['bp.edu.kontrak.kuliah'].create({
        'mata_kuliah_id': mk.id,
        'dosen_id': dosen.id if dosen else False,
        'tahun_akademik_id': ta.id if ta else False,
        'periode': data.get('periode', ''),
        'kelas': data.get('kelas', 'A'),
        'hari_jam': data.get('hari_jam', ''),
        'jenis_mk': data.get('jenis_mk', ''),
        'prasyarat': data.get('prasyarat', '-'),
        'bobot_diskusi': _safe_int(data.get('bobot_diskusi', 10)),
        'bobot_proyek': _safe_int(data.get('bobot_proyek', 20)),
        'bobot_tugas': _safe_int(data.get('bobot_tugas', 10)),
        'bobot_kuis': _safe_int(data.get('bobot_kuis', 10)),
        'bobot_uts': _safe_int(data.get('bobot_uts', 20)),
        'bobot_uas': _safe_int(data.get('bobot_uas', 30)),
        'jumlah_kuis_mingguan': _safe_int(data.get('jumlah_kuis_mingguan', 1)),
        'jumlah_tugas_terstruktur': _safe_int(data.get('jumlah_tugas_terstruktur', 8)),
        'jumlah_proyek': _safe_int(data.get('jumlah_proyek', 1)),
        'wakil_mahasiswa': data.get('wakil_mahasiswa', ''),
        'nim_wakil': data.get('nim_wakil', ''),
        'cpmk_ids': [(6, 0, cpmk_ids)],
    })

    # Materi per minggu (materi_minggu_1 … materi_minggu_16)
    for i in range(1, 17):
        materi_text = data.get(f'materi_minggu_{i}', '')
        if materi_text:
            env['bp.edu.kontrak.materi'].create({
                'kontrak_id': kontrak.id,
                'minggu': i,
                'materi': materi_text,
            })

    _logger.info('Import Kontrak selesai: MK=%s, Kontrak id=%s', nama_mk, kontrak.id)
    return {'mk_id': mk.id, 'kontrak_id': kontrak.id}


# ─── Auto-detect dan dispatch ────────────────────────────────────────────────

def detect_type(data: dict) -> str:
    """Deteksi tipe JSON: 'rps', 'sap', atau 'kontrak'."""
    if 'detail' in data and 'meta' in data:
        return 'rps'
    if 'pertemuan' in data and 'meta' in data:
        return 'sap'
    if 'bobot_uts' in data or 'bobot_uas' in data:
        return 'kontrak'
    return 'unknown'


def import_json(env, data: dict) -> dict:
    """
    Auto-detect tipe JSON dan jalankan importer yang sesuai.

    Returns:
        dict berisi tipe ('type') dan ID record yang dibuat.
    """
    doc_type = detect_type(data)
    if doc_type == 'rps':
        result = import_rps(env, data)
        result['type'] = 'rps'
    elif doc_type == 'sap':
        result = import_sap(env, data)
        result['type'] = 'sap'
    elif doc_type == 'kontrak':
        result = import_kontrak(env, data)
        result['type'] = 'kontrak'
    else:
        raise ValueError(
            'Format JSON tidak dikenali. '
            'Pastikan JSON mengandung field "detail" (RPS), "pertemuan" (SAP), '
            'atau "bobot_uts/bobot_uas" (Kontrak Kuliah).'
        )
    return result
