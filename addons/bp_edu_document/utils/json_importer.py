"""
JSON → Odoo importer untuk format JSON rps_bp.

Mendukung tiga tipe JSON:
  - RPS   : keys meta, cpl_prodi, cpmk, sub_cpmk, korelasi, korelasi_cpl,
            penilaian, detail, pustaka_utama, pustaka_pendukung,
            rancangan_tugas_proyek (opsional), rubrik_penilaian (opsional)
  - SAP   : keys meta, pertemuan
  - Kontrak : keys tahun_akademik, nama_mk, cpmk, materi_minggu_N, bobot_*

Setiap fungsi menerima `env` (Odoo Environment) dan `data` (parsed dict).

import_rps() melakukan UPSERT: RPS untuk mata_kuliah_id yang sama akan
di-update (write) bukan dibuat baru, supaya re-import JSON yang sudah
diperbarui dari rps_bp otomatis tercatat di riwayat perubahan
(bp.edu.field.history, lihat bp_edu_rps/models/bp_edu_history_tracking.py)
alih-alih menumpuk RPS duplikat.
"""
import logging
import re

_logger = logging.getLogger(__name__)

_CPMK_RANGE_RE = re.compile(
    r'^(?:CPMK-)?(\d+)\s*s[\.\s]*d[\.\s]*(?:CPMK-)?(\d+)$', re.IGNORECASE,
)

_M_COLS = [f'm{i}' for i in range(1, 13)]
_P_COLS = [f'p{i}' for i in range(1, 21)]
_C_COLS = [f'c{i}' for i in range(1, 11)]


# ─── Helpers ─────────────────────────────────────────────────────────────────

def _safe_int(val, default=0):
    try:
        return int(val)
    except (TypeError, ValueError):
        return default


def _parse_minggu(val, default=0):
    """
    detail[].minggu di rps_bp bisa berupa angka polos (5) atau format
    "N/16" (mis. "5/16", menandakan minggu ke-5 dari 16). Ambil bagian
    sebelum '/' bila ada.
    """
    if isinstance(val, str) and '/' in val:
        val = val.split('/', 1)[0]
    return _safe_int(val, default)


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


def _parse_cpmk_refs(cpmk_text, cpmk_map):
    """
    Parse referensi CPMK dari sub_cpmk['cpmk'], yang bisa berupa:
      - Satu kode        : "CPMK-1"
      - Daftar dipisah koma: "CPMK-3, CPMK-5"
      - Rentang           : "CPMK-1 s.d. CPMK-5" -> CPMK-1..CPMK-5

    Returns: list of matched bp.edu.cpmk ids (urutan sesuai kemunculan/rentang),
    hanya kode yang benar-benar ada di cpmk_map.
    """
    cpmk_text = (cpmk_text or '').strip()
    if not cpmk_text:
        return []

    range_match = _CPMK_RANGE_RE.match(cpmk_text)
    if range_match:
        start, end = int(range_match.group(1)), int(range_match.group(2))
        kodes = [f'CPMK-{i}' for i in range(start, end + 1)]
    else:
        kodes = [k.strip() for k in cpmk_text.split(',') if k.strip()]

    return [cpmk_map[k] for k in kodes if k in cpmk_map]


# ─── RPS Importer ────────────────────────────────────────────────────────────

def import_rps(env, data: dict) -> dict:
    """
    Import data JSON format RPS ke Odoo. Melakukan upsert: bila sudah ada RPS
    untuk mata_kuliah_id yang sama, di-update (write) supaya tercatat di
    riwayat perubahan; bila belum ada, dibuat baru.

    Returns:
        dict dengan 'mk_id', 'rps_id', dan 'created' (bool)
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
    # Field 'cpl' di JSON versi lama menyimpan level taksonomi Bloom (mis. "C2");
    # versi baru rps_bp merename-nya menjadi 'taksonomi' agar tidak rancu dengan
    # CPL (Capaian Pembelajaran Lulusan). Baca 'taksonomi' dulu, fallback ke 'cpl'
    # supaya JSON lama tetap terbaca.
    #
    # item['cpmk'] biasanya satu kode ("CPMK-1"), tapi baris ringkasan/akhir
    # kadang merujuk banyak sekaligus: daftar dipisah koma ("CPMK-3, CPMK-5")
    # atau rentang ("CPMK-1 s.d. CPMK-5"). cpmk_id (utama, wajib) diisi CPMK
    # pertama yang match; cpmk_ids menyimpan semuanya.
    for item in data.get('sub_cpmk', []):
        cpmk_ids_matched = _parse_cpmk_refs(item.get('cpmk', ''), cpmk_map)
        if not cpmk_ids_matched:
            _logger.warning(
                'Sub-CPMK %s: CPMK %r tidak ditemukan, dilewati.',
                item.get('kode'), item.get('cpmk', ''),
            )
            continue
        env['bp.edu.sub.cpmk'].create({
            'kode': item.get('kode', ''),
            'cpmk_id': cpmk_ids_matched[0],
            'cpmk_ids': [(6, 0, cpmk_ids_matched)],
            'cpmk_text': item.get('cpmk', ''),
            'deskripsi': item.get('deskripsi', ''),
            'minggu': item.get('minggu', ''),
            'level_bloom': item.get('taksonomi') or item.get('cpl', ''),
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

    # 6. RPS header — upsert
    dosen = _find_dosen(env, meta.get('dosen_pengampu', ''))
    ta = _active_tahun_akademik(env)

    Rps = env['bp.edu.rps']
    rps = Rps.search([('mata_kuliah_id', '=', mk.id)], limit=1)
    created = not bool(rps)

    # dosen_id wajib diisi (required=True). Nama pengampu kadang berupa nama
    # tim/kolektif (mis. "Tim Dosen Pembimbing Tugas Akhir") yang tidak match
    # satu dosen manapun -- jangan timpa assignment lama dengan kosong kalau
    # lookup gagal, cukup pertahankan yang sudah ada.
    dosen_id = dosen.id if dosen else (rps.dosen_id.id if rps else False)
    # Sama untuk tahun akademik: JSON tidak menyebut tahun akademik secara
    # eksplisit, kita andalkan record yang ditandai "aktif". Kalau tidak ada
    # satupun yang aktif, jangan timpa assignment lama dengan kosong.
    tahun_akademik_id = ta.id if ta else (rps.tahun_akademik_id.id if rps else False)

    rps_vals = {
        'mata_kuliah_id': mk.id,
        'dosen_id': dosen_id,
        'tahun_akademik_id': tahun_akademik_id,
        'tanggal_penyusunan': meta.get('tanggal_penyusunan') or False,
    }
    if rps:
        rps.write(rps_vals)  # write() -> tercatat di bp.edu.field.history
    else:
        rps = Rps.create(rps_vals)

    # 7. RPS Detail (16 minggu) — hapus lalu buat ulang, konsisten dengan CPMK/pustaka.
    # Perubahan baris detail sendiri tidak dilacak per-field (hanya field header
    # RPS yang dilacak), jadi ini aman dan lebih sederhana daripada upsert per-baris.
    rps.detail_ids.unlink()
    for item in data.get('detail', []):
        env['bp.edu.rps.detail'].create({
            'rps_id': rps.id,
            'minggu': _parse_minggu(item.get('minggu', 0)),
            'deskripsi': item.get('deskripsi', ''),
            'indikator': item.get('indikator', ''),
            'kriteria': item.get('kriteria', ''),
            'tatap_muka': item.get('tatap_muka', ''),
            'daring': item.get('daring', ''),
            'materi': item.get('materi', ''),
            'bobot': str(item.get('bobot', '')),
        })

    # 8. Matriks Korelasi CPMK-Minggu, Korelasi Sub-CPMK-CPL, Penilaian
    _import_matriks(env, rps, data)

    # 9. Rancangan Tugas Proyek & Rubrik Penilaian (opsional, tidak semua MK punya)
    _import_rancangan_tugas(env, rps, data.get('rancangan_tugas_proyek'))
    _import_rubrik_penilaian(env, rps, data.get('rubrik_penilaian'))

    # 10. Jejak riwayat yang mudah dibaca manusia (selain bp.edu.field.history
    # yang mencatat per-field, chatter memberi ringkasan satu baris per import).
    aksi = 'dibuat' if created else 'diperbarui'
    rps.message_post(body=f'RPS {aksi} dari import JSON rps_bp (kode_mk={kode_mk}).')

    _logger.info('Import RPS selesai: MK=%s, RPS id=%s, created=%s', kode_mk, rps.id, created)
    return {'mk_id': mk.id, 'rps_id': rps.id, 'created': created}


def _import_matriks(env, rps, data):
    """Ganti baris matriks korelasi/korelasi_cpl/penilaian dengan isi JSON terbaru."""
    rps.korelasi_ids.unlink()
    for seq, item in enumerate(data.get('korelasi', []), start=10):
        vals = {'rps_id': rps.id, 'sequence': seq, 'cpmk': item.get('cpmk', '')}
        vals.update({col: item.get(col, '') for col in _M_COLS})
        env['bp.edu.rps.korelasi'].create(vals)

    rps.korelasi_cpl_ids.unlink()
    for seq, item in enumerate(data.get('korelasi_cpl', []), start=10):
        vals = {
            'rps_id': rps.id,
            'sequence': seq,
            'sub': item.get('sub', ''),
            'bobot': str(item.get('bobot', '')),
            'minggu': str(item.get('minggu', '')),
        }
        vals.update({col: item.get(col, '') for col in _P_COLS})
        env['bp.edu.rps.korelasi.cpl'].create(vals)

    rps.penilaian_ids.unlink()
    for seq, item in enumerate(data.get('penilaian', []), start=10):
        vals = {
            'rps_id': rps.id,
            'sequence': seq,
            'jenis': item.get('jenis', ''),
            'bobot': str(item.get('bobot', '')),
        }
        vals.update({col: item.get(col, '') for col in _C_COLS})
        env['bp.edu.rps.penilaian'].create(vals)


def _join_lines(items):
    """list of str (JSON) -> Text satu item per baris (field Odoo)."""
    if not items:
        return ''
    return '\n'.join(str(i) for i in items)


def _import_rancangan_tugas(env, rps, rtp):
    """Import rancangan_tugas_proyek (opsional — tidak semua MK punya proyek)."""
    rps.rancangan_tugas_ids.unlink()
    if not rtp:
        return
    uraian = rtp.get('uraian_tugas', {}) or {}
    kriteria = rtp.get('kriteria_penilaian', {}) or {}

    def _kriteria(key):
        item = kriteria.get(key, {}) or {}
        return item.get('bobot', ''), item.get('deskripsi', '')

    prop_bobot, prop_desk = _kriteria('penyusunan_proposal')
    impl_bobot, impl_desk = _kriteria('pengimplementasian_proyek')
    lap_bobot, lap_desk = _kriteria('penyusunan_laporan')
    pres_bobot, pres_desk = _kriteria('presentasi')

    env['bp.edu.rps.rancangan.tugas'].create({
        'rps_id': rps.id,
        'tujuan': rtp.get('tujuan', ''),
        'kompetensi': _join_lines(rtp.get('kompetensi')),
        'objek_garapan': uraian.get('objek_garapan', ''),
        'langkah_kerja': _join_lines(uraian.get('langkah_kerja')),
        'topik': _join_lines(uraian.get('topik')),
        'metode_kerja': _join_lines(uraian.get('metode_kerja')),
        'luaran_tugas': _join_lines(uraian.get('luaran_tugas')),
        'kriteria_proposal_bobot': prop_bobot,
        'kriteria_proposal_deskripsi': prop_desk,
        'kriteria_implementasi_bobot': impl_bobot,
        'kriteria_implementasi_deskripsi': impl_desk,
        'kriteria_laporan_bobot': lap_bobot,
        'kriteria_laporan_deskripsi': lap_desk,
        'kriteria_presentasi_bobot': pres_bobot,
        'kriteria_presentasi_deskripsi': pres_desk,
    })


def _import_rubrik_penilaian(env, rps, rp):
    """Import rubrik_penilaian (opsional — tidak semua MK punya rubrik proyek)."""
    rps.rubrik_holistik_ids.unlink()
    rps.rubrik_deskriptif_ids.unlink()
    if not rp:
        return

    for item in rp.get('rubrik_holistik_proposal_laporan', []):
        env['bp.edu.rps.rubrik.holistik'].create({
            'rps_id': rps.id,
            'grade': item.get('grade', ''),
            'skor_min': _safe_int(item.get('skor_min', 0)),
            'skor_max': _safe_int(item.get('skor_max', 0)),
            'kriteria': item.get('kriteria', ''),
        })

    deskriptif = rp.get('rubrik_deskriptif_presentasi')
    if not deskriptif:
        return
    skala = deskriptif.get('skala_penilaian', {}) or {}

    def _band(key):
        band = skala.get(key, {}) or {}
        return _safe_int(band.get('min', 0)), _safe_int(band.get('max', 0))

    sk_min, sk_max = _band('sangat_kurang')
    k_min, k_max = _band('kurang')
    c_min, c_max = _band('cukup')
    b_min, b_max = _band('baik')
    sb_min, sb_max = _band('sangat_baik')

    env['bp.edu.rps.rubrik.deskriptif'].create({
        'rps_id': rps.id,
        'aspek_yang_dinilai': _join_lines(deskriptif.get('aspek_yang_dinilai')),
        'format_penilaian': deskriptif.get('format_penilaian', ''),
        'skala_sangat_kurang_min': sk_min,
        'skala_sangat_kurang_max': sk_max,
        'skala_kurang_min': k_min,
        'skala_kurang_max': k_max,
        'skala_cukup_min': c_min,
        'skala_cukup_max': c_max,
        'skala_baik_min': b_min,
        'skala_baik_max': b_max,
        'skala_sangat_baik_min': sb_min,
        'skala_sangat_baik_max': sb_max,
    })


# ─── SAP Importer ────────────────────────────────────────────────────────────

def import_sap(env, data: dict) -> dict:
    """
    Import data JSON format SAP ke Odoo. Melakukan upsert: bila sudah ada SAP
    untuk mata_kuliah_id yang sama, di-update (write) supaya tercatat di
    riwayat perubahan; bila belum ada, dibuat baru. Sama seperti import_rps().

    Returns:
        dict dengan 'mk_id', 'sap_id', dan 'created' (bool)
    """
    meta = data.get('meta', {})
    kode_mk = meta.get('kode_mk', '').strip()
    nama_mk = meta.get('nama_mk', '').strip()

    mk = _find_or_create_mk(env, kode_mk, nama_mk, meta)
    dosen = _find_dosen(env, meta.get('dosen_pengampu', ''))
    ta = _active_tahun_akademik(env)

    Sap = env['bp.edu.sap']
    sap = Sap.search([('mata_kuliah_id', '=', mk.id)], limit=1)
    created = not bool(sap)

    # Jangan timpa assignment lama dengan kosong kalau lookup gagal (lihat
    # catatan yang sama di import_rps()).
    dosen_id = dosen.id if dosen else (sap.dosen_id.id if sap else False)
    tahun_akademik_id = ta.id if ta else (sap.tahun_akademik_id.id if sap else False)

    sap_vals = {
        'mata_kuliah_id': mk.id,
        'dosen_id': dosen_id,
        'tahun_akademik_id': tahun_akademik_id,
    }
    if sap:
        sap.write(sap_vals)  # write() -> tercatat di bp.edu.field.history
    else:
        sap = Sap.create(sap_vals)

    sap.pertemuan_ids.unlink()
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

    aksi = 'dibuat' if created else 'diperbarui'
    sap.message_post(body=f'SAP {aksi} dari import JSON rps_bp (kode_mk={kode_mk}).')

    _logger.info('Import SAP selesai: MK=%s, SAP id=%s, created=%s', kode_mk, sap.id, created)
    return {'mk_id': mk.id, 'sap_id': sap.id, 'created': created}


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
