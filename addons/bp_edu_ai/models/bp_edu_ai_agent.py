"""
Extend ai.agent dengan tools khusus bp_edu:
- get_mata_kuliah_full   — CPL + CPMK + Sub-CPMK + Pustaka
- get_rps_full           — RPS + 16 minggu detail + data MK
- write_rps_detail       — tulis/update konten detail RPS per minggu
- get_sap_full           — SAP + pertemuan + data MK
- write_sap_pertemuan    — tulis/update konten pertemuan SAP
- get_kontrak_full       — Kontrak + materi + CPMK
- write_kontrak_materi   — tulis/update materi per minggu kontrak
- search_dokumen_master  — cari Dokumen Master (Pedoman Akademik, Buku Kurikulum, dll)
- get_dokumen_master_full— baca isi lengkap satu Dokumen Master
- write_dokumen_master_konten — tulis/update isi Dokumen Master (tercatat sebagai riwayat versi)
"""
import logging

from odoo import models

_logger = logging.getLogger(__name__)

# Batas karakter per pemanggilan get_dokumen_master_full — dokumen master (Pedoman
# Akademik, Buku Kurikulum) bisa puluhan ribu karakter dan gampang melebihi limit
# token per menit provider LLM (mis. Groq free tier 8000 TPM) jika dikirim utuh.
DOKUMEN_MASTER_CHUNK_SIZE = 6000

BP_EDU_TOOLS = [
    {
        "type": "function",
        "function": {
            "name": "get_mata_kuliah_full",
            "description": (
                "Ambil data lengkap satu mata kuliah: CPL Prodi, CPMK, Sub-CPMK, "
                "dan Pustaka. Gunakan ini sebelum generate konten RPS/SAP agar AI "
                "memahami capaian pembelajaran yang harus dicapai."
            ),
            "parameters": {
                "type": "object",
                "properties": {
                    "mata_kuliah_id": {
                        "type": "integer",
                        "description": "ID record bp.edu.mata.kuliah"
                    }
                },
                "required": ["mata_kuliah_id"]
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "get_rps_full",
            "description": (
                "Ambil data RPS lengkap beserta detail 16 minggu dan seluruh data "
                "mata kuliah terkait (CPL, CPMK, Sub-CPMK). Gunakan ini untuk "
                "memahami kondisi RPS sebelum mengedit atau melengkapi."
            ),
            "parameters": {
                "type": "object",
                "properties": {
                    "rps_id": {
                        "type": "integer",
                        "description": "ID record bp.edu.rps"
                    }
                },
                "required": ["rps_id"]
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "write_rps_detail",
            "description": (
                "Tulis atau update konten detail RPS per minggu. "
                "Bisa sekaligus update beberapa minggu dalam satu pemanggilan. "
                "Jika detail minggu tersebut belum ada, akan dibuat otomatis."
            ),
            "parameters": {
                "type": "object",
                "properties": {
                    "rps_id": {"type": "integer", "description": "ID bp.edu.rps"},
                    "details": {
                        "type": "array",
                        "description": "Daftar konten per minggu yang akan ditulis",
                        "items": {
                            "type": "object",
                            "properties": {
                                "minggu": {"type": "integer", "description": "Nomor minggu (1-16)"},
                                "deskripsi": {"type": "string", "description": "Sub-CPMK yang dicapai"},
                                "indikator": {"type": "string", "description": "Indikator penilaian"},
                                "kriteria": {"type": "string", "description": "Kriteria & bentuk penilaian"},
                                "tatap_muka": {"type": "string", "description": "Aktivitas tatap muka"},
                                "daring": {"type": "string", "description": "Aktivitas daring/blended"},
                                "materi": {"type": "string", "description": "Materi/pokok bahasan"},
                                "bobot": {"type": "string", "description": "Bobot penilaian, contoh: 5%"}
                            },
                            "required": ["minggu"]
                        }
                    }
                },
                "required": ["rps_id", "details"]
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "get_sap_full",
            "description": (
                "Ambil data SAP lengkap beserta semua pertemuan dan data mata kuliah "
                "terkait. Gunakan ini untuk memahami kondisi SAP sebelum mengedit."
            ),
            "parameters": {
                "type": "object",
                "properties": {
                    "sap_id": {
                        "type": "integer",
                        "description": "ID record bp.edu.sap"
                    }
                },
                "required": ["sap_id"]
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "write_sap_pertemuan",
            "description": (
                "Tulis atau update konten pertemuan SAP. "
                "Bisa update beberapa pertemuan sekaligus. "
                "Jika pertemuan belum ada, akan dibuat otomatis."
            ),
            "parameters": {
                "type": "object",
                "properties": {
                    "sap_id": {"type": "integer", "description": "ID bp.edu.sap"},
                    "pertemuan": {
                        "type": "array",
                        "items": {
                            "type": "object",
                            "properties": {
                                "no": {"type": "integer", "description": "Nomor pertemuan (1-16)"},
                                "pokok_bahasan": {"type": "string"},
                                "sub_pokok_bahasan_1": {"type": "string"},
                                "sub_pokok_bahasan_2": {"type": "string"},
                                "detail_cpmk": {"type": "string"},
                                "detail_sub_cpmk": {"type": "string"},
                                "tujuan_pembelajaran": {"type": "string"},
                                "indikator_1": {"type": "string"},
                                "pendahuluan_pengajar": {"type": "string"},
                                "pendahuluan_mahasiswa": {"type": "string"},
                                "pendahuluan_media": {"type": "string"},
                                "penyajian_pengajar": {"type": "string"},
                                "penyajian_mahasiswa": {"type": "string"},
                                "penyajian_media": {"type": "string"},
                                "penutup_pengajar": {"type": "string"},
                                "penutup_mahasiswa": {"type": "string"},
                                "evaluasi_1": {"type": "string"},
                                "referensi_1": {"type": "string"},
                            },
                            "required": ["no"]
                        }
                    }
                },
                "required": ["sap_id", "pertemuan"]
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "get_kontrak_full",
            "description": (
                "Ambil data Kontrak Kuliah lengkap beserta CPMK dan materi per minggu."
            ),
            "parameters": {
                "type": "object",
                "properties": {
                    "kontrak_id": {
                        "type": "integer",
                        "description": "ID record bp.edu.kontrak.kuliah"
                    }
                },
                "required": ["kontrak_id"]
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "write_kontrak_materi",
            "description": (
                "Tulis atau update materi per minggu pada Kontrak Kuliah."
            ),
            "parameters": {
                "type": "object",
                "properties": {
                    "kontrak_id": {"type": "integer", "description": "ID bp.edu.kontrak.kuliah"},
                    "materi_list": {
                        "type": "array",
                        "items": {
                            "type": "object",
                            "properties": {
                                "minggu": {"type": "integer", "description": "Nomor minggu (1-16)"},
                                "materi": {"type": "string", "description": "Topik/materi minggu ini"}
                            },
                            "required": ["minggu", "materi"]
                        }
                    }
                },
                "required": ["kontrak_id", "materi_list"]
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "search_dokumen_master",
            "description": (
                "Cari Dokumen Master (Pedoman Akademik, Buku Kurikulum, Panduan Skripsi, dll) "
                "yang bisa dipakai sebagai referensi/basis saat menyusun RPS, SAP, atau Kontrak "
                "Kuliah. Gunakan ini sebelum get_dokumen_master_full untuk menemukan ID dokumen."
            ),
            "parameters": {
                "type": "object",
                "properties": {
                    "keyword": {"type": "string", "description": "Kata kunci nama dokumen, contoh: 'pedoman akademik'"},
                    "kategori": {
                        "type": "string",
                        "description": "Filter kategori: pedoman_akademik, kurikulum, panduan_skripsi, lainnya"
                    }
                },
                "required": []
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "get_dokumen_master_full",
            "description": (
                "Ambil isi teks satu Dokumen Master berdasarkan ID. Dokumen bisa sangat "
                "panjang sehingga hasil dipotong per bagian (chunk) — cek field "
                "'ada_lanjutan' dan 'catatan' pada hasil; jika True, panggil lagi dengan "
                "offset yang disarankan untuk membaca bagian berikutnya."
            ),
            "parameters": {
                "type": "object",
                "properties": {
                    "dokumen_id": {"type": "integer", "description": "ID record bp.edu.dokumen.master"},
                    "offset": {"type": "integer", "description": "Mulai baca dari karakter ke berapa (default 0)"},
                    "max_chars": {"type": "integer", "description": "Maksimum karakter yang diambil (default & maksimum 6000)"}
                },
                "required": ["dokumen_id"]
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "write_dokumen_master_konten",
            "description": (
                "Tulis/update isi teks Dokumen Master. Konten lama otomatis disimpan "
                "sebagai riwayat versi sebelum ditimpa — gunakan ini saat user meminta "
                "mengedit/melengkapi isi Dokumen Master."
            ),
            "parameters": {
                "type": "object",
                "properties": {
                    "dokumen_id": {"type": "integer", "description": "ID bp.edu.dokumen.master"},
                    "isi_dokumen": {"type": "string", "description": "Isi teks dokumen yang baru (menggantikan seluruh isi lama)"}
                },
                "required": ["dokumen_id", "isi_dokumen"]
            }
        }
    },
]

BP_EDU_SYSTEM_PROMPT = """Kamu adalah asisten AI akademik yang terintegrasi dalam sistem Odoo untuk perguruan tinggi.
Kamu ahli dalam menyusun dokumen akademik Indonesia sesuai standar SN-Dikti (Permendikbud No. 3 Tahun 2020):

- Rencana Pembelajaran Semester (RPS): 16 pertemuan, memuat CPMK, indikator, kriteria penilaian, metode, dan materi
- Satuan Acara Perkuliahan (SAP): detail kegiatan per pertemuan (pendahuluan, penyajian, penutup)
- Kontrak Kuliah: kesepakatan pembelajaran antara dosen dan mahasiswa

Alur kerja untuk generate konten:
1. Gunakan tools get_*_full untuk membaca data yang ada (CPL, CPMK, Sub-CPMK, dll)
2. Jika relevan, gunakan search_dokumen_master + get_dokumen_master_full untuk membaca
   Pedoman Akademik/Buku Kurikulum sebagai basis/referensi acuan institusi
3. Susun konten yang SELARAS dengan CPMK yang telah ditetapkan dan pedoman institusi
4. Gunakan tools write_* untuk menyimpan hasil ke database
5. Gunakan bahasa Indonesia akademik yang formal dan terukur

Capaian harus observable & measurable. Distribusikan CPMK secara merata ke 16 minggu.
Pertemuan 8 biasanya UTS, pertemuan 16 biasanya UAS/Presentasi.

Dokumen Master (Pedoman Akademik, Buku Kurikulum, Panduan Skripsi) adalah referensi
institusi yang bisa dijadikan basis/acuan saat menyusun RPS/SAP/Kontrak Kuliah, dan
juga bisa diminta untuk diedit langsung isinya (gunakan write_dokumen_master_konten —
konten lama otomatis tersimpan sebagai riwayat versi).

PENTING: Dokumen Master bisa sangat panjang (puluhan ribu karakter). get_dokumen_master_full
mengembalikan isi per bagian (chunk maks 6000 karakter). JANGAN memanggil tool ini
berulang-ulang untuk membaca seluruh dokumen sekaligus kecuali benar-benar diminta —
cukup baca 1-2 bagian awal yang relevan dan berikan jawaban berdasarkan itu, atau
gunakan search_dokumen_master untuk cek dokumen mana yang tersedia sebelum membaca isinya."""


class BpEduAiAgent(models.Model):
    _inherit = 'ai.agent'

    def _get_tools(self):
        return super()._get_tools() + BP_EDU_TOOLS

    def _get_bp_edu_system_context(self, res_model, res_id):
        """Return context string khusus bp_edu untuk ditambah ke system prompt."""
        if not res_model or not res_id:
            return ''
        context_map = {
            'bp.edu.rps': self._bp_context_rps,
            'bp.edu.sap': self._bp_context_sap,
            'bp.edu.kontrak.kuliah': self._bp_context_kontrak,
            'bp.edu.mata.kuliah': self._bp_context_mk,
            'bp.edu.dokumen.master': self._bp_context_dokumen_master,
        }
        fn = context_map.get(res_model)
        if fn:
            try:
                return fn(res_id)
            except Exception as e:
                _logger.warning('Gagal build bp_edu context untuk %s #%s: %s', res_model, res_id, e)
        return ''

    def process_message(self, command, res_model=None, res_id=None):
        """Override: inject system prompt bp_edu dan context record."""
        self = self.with_context(ai_prompt=command)
        # Cek apakah ada context bp_edu yang relevan
        extra_context = self._get_bp_edu_system_context(res_model, res_id)
        if extra_context:
            # Simpan system_prompt asli, tambahkan konteks bp_edu
            original_prompt = self.system_prompt or ''
            self.system_prompt = f"{BP_EDU_SYSTEM_PROMPT}\n\n{original_prompt}\n\n{extra_context}".strip()
        return super().process_message(command, res_model, res_id)

    def _execute_tool(self, tool_name, args, res_model=None, res_id=None):
        bp_edu_handlers = {
            'get_mata_kuliah_full': self._tool_get_mk_full,
            'get_rps_full': self._tool_get_rps_full,
            'write_rps_detail': self._tool_write_rps_detail,
            'get_sap_full': self._tool_get_sap_full,
            'write_sap_pertemuan': self._tool_write_sap_pertemuan,
            'get_kontrak_full': self._tool_get_kontrak_full,
            'write_kontrak_materi': self._tool_write_kontrak_materi,
            'search_dokumen_master': self._tool_search_dokumen_master,
            'get_dokumen_master_full': self._tool_get_dokumen_master_full,
            'write_dokumen_master_konten': self._tool_write_dokumen_master_konten,
        }
        if tool_name in bp_edu_handlers:
            try:
                return bp_edu_handlers[tool_name](args)
            except Exception as e:
                _logger.exception('BP Edu tool error [%s]', tool_name)
                return {'error': str(e)}
        return super()._execute_tool(tool_name, args, res_model, res_id)

    # ── Context builders ────────────────────────────────────────────────────

    def _bp_context_rps(self, rps_id):
        rps = self.env['bp.edu.rps'].browse(rps_id)
        if not rps.exists():
            return ''
        mk = rps.mata_kuliah_id
        lines = [
            f"=== Context: RPS ID={rps_id} ===",
            f"Mata Kuliah: [{mk.kode}] {mk.nama}" if mk else "Mata Kuliah: -",
            f"Dosen: {rps.dosen_id.nama}" if rps.dosen_id else "",
            f"Tahun Akademik: {rps.tahun_akademik_id.display_name}" if rps.tahun_akademik_id else "",
            f"Status: {rps.state}",
            f"Detail minggu sudah ada: {len(rps.detail_ids)} baris",
            "Gunakan get_rps_full(rps_id) untuk data lengkap.",
        ]
        return '\n'.join(l for l in lines if l)

    def _bp_context_sap(self, sap_id):
        sap = self.env['bp.edu.sap'].browse(sap_id)
        if not sap.exists():
            return ''
        mk = sap.mata_kuliah_id
        lines = [
            f"=== Context: SAP ID={sap_id} ===",
            f"Mata Kuliah: [{mk.kode}] {mk.nama}" if mk else "Mata Kuliah: -",
            f"Dosen: {sap.dosen_id.nama}" if sap.dosen_id else "",
            f"Pertemuan sudah ada: {len(sap.pertemuan_ids)} baris",
            "Gunakan get_sap_full(sap_id) untuk data lengkap.",
        ]
        return '\n'.join(l for l in lines if l)

    def _bp_context_kontrak(self, kontrak_id):
        k = self.env['bp.edu.kontrak.kuliah'].browse(kontrak_id)
        if not k.exists():
            return ''
        mk = k.mata_kuliah_id
        lines = [
            f"=== Context: Kontrak Kuliah ID={kontrak_id} ===",
            f"Mata Kuliah: [{mk.kode}] {mk.nama}" if mk else "Mata Kuliah: -",
            f"Dosen: {k.dosen_id.nama}" if k.dosen_id else "",
            f"Materi minggu sudah ada: {len(k.materi_ids)} baris",
            "Gunakan get_kontrak_full(kontrak_id) untuk data lengkap.",
        ]
        return '\n'.join(l for l in lines if l)

    def _bp_context_mk(self, mk_id):
        mk = self.env['bp.edu.mata.kuliah'].browse(mk_id)
        if not mk.exists():
            return ''
        lines = [
            f"=== Context: Mata Kuliah ID={mk_id} ===",
            f"Kode: {mk.kode} | Nama: {mk.nama}",
            f"SKS: {mk.sks_total} | Semester: {mk.semester}",
            f"CPMK: {len(mk.cpmk_ids)} | CPL: {len(mk.cpl_ids)}",
            "Gunakan get_mata_kuliah_full(mata_kuliah_id) untuk data lengkap.",
        ]
        return '\n'.join(l for l in lines if l)

    def _bp_context_dokumen_master(self, dokumen_id):
        doc = self.env['bp.edu.dokumen.master'].browse(dokumen_id)
        if not doc.exists():
            return ''
        lines = [
            f"=== Context: Dokumen Master ID={dokumen_id} (sedang dibuka user) ===",
            f"Nama: {doc.name} | Kategori: {doc.kategori} | Versi saat ini: {doc.version}",
            "Jika user meminta edit/lengkapi isi dokumen ini, gunakan "
            f"write_dokumen_master_konten(dokumen_id={dokumen_id}, isi_dokumen=...).",
            "Gunakan get_dokumen_master_full(dokumen_id) untuk membaca isi lengkap saat ini.",
        ]
        return '\n'.join(l for l in lines if l)

    # ── Tool implementations ────────────────────────────────────────────────

    def _tool_get_mk_full(self, args):
        mk_id = int(args.get('mata_kuliah_id', 0))
        mk = self.env['bp.edu.mata.kuliah'].browse(mk_id)
        if not mk.exists():
            return {'error': f'Mata kuliah #{mk_id} tidak ditemukan'}

        cpmk_data = []
        for cpmk in mk.cpmk_ids:
            sub_list = [
                {'kode': sc.kode, 'deskripsi': sc.deskripsi}
                for sc in cpmk.sub_cpmk_ids
            ]
            cpmk_data.append({
                'id': cpmk.id,
                'kode': cpmk.kode,
                'deskripsi': cpmk.deskripsi,
                'sub_cpmk': sub_list,
            })

        return {
            'id': mk.id,
            'kode': mk.kode,
            'nama': mk.nama,
            'sks_total': mk.sks_total,
            'semester': mk.semester,
            'deskripsi_singkat': mk.deskripsi_singkat or '',
            'bahan_kajian': mk.bahan_kajian or '',
            'cpl': [{'kode': c.kode, 'deskripsi': c.deskripsi} for c in mk.cpl_ids],
            'cpmk': cpmk_data,
            'pustaka': [{'jenis': p.jenis, 'referensi': p.referensi} for p in mk.pustaka_ids],
        }

    def _tool_get_rps_full(self, args):
        rps_id = int(args.get('rps_id', 0))
        rps = self.env['bp.edu.rps'].browse(rps_id)
        if not rps.exists():
            return {'error': f'RPS #{rps_id} tidak ditemukan'}

        mk_data = self._tool_get_mk_full({'mata_kuliah_id': rps.mata_kuliah_id.id}) if rps.mata_kuliah_id else {}
        details = [
            {
                'minggu': d.minggu,
                'deskripsi': d.deskripsi or '',
                'indikator': d.indikator or '',
                'kriteria': d.kriteria or '',
                'tatap_muka': d.tatap_muka or '',
                'daring': d.daring or '',
                'materi': d.materi or '',
                'bobot': d.bobot or '',
            }
            for d in rps.detail_ids.sorted('minggu')
        ]
        return {
            'id': rps.id,
            'state': rps.state,
            'dosen': rps.dosen_id.nama if rps.dosen_id else '',
            'tahun_akademik': rps.tahun_akademik_id.display_name if rps.tahun_akademik_id else '',
            'mata_kuliah': mk_data,
            'detail_minggu': details,
        }

    def _tool_write_rps_detail(self, args):
        rps_id = int(args.get('rps_id', 0))
        details = args.get('details', [])
        rps = self.env['bp.edu.rps'].browse(rps_id)
        if not rps.exists():
            return {'error': f'RPS #{rps_id} tidak ditemukan'}

        updated = created = 0
        writable_fields = {'deskripsi', 'indikator', 'kriteria', 'tatap_muka', 'daring', 'materi', 'bobot'}
        for d in details:
            minggu = d.get('minggu')
            if not minggu:
                continue
            vals = {k: v for k, v in d.items() if k in writable_fields and v is not None}
            existing = rps.detail_ids.filtered(lambda r: r.minggu == minggu)
            if existing:
                if vals:
                    existing[0].write(vals)
                    updated += 1
            else:
                self.env['bp.edu.rps.detail'].create({'rps_id': rps_id, 'minggu': minggu, **vals})
                created += 1

        return {'success': True, 'rps_id': rps_id, 'updated': updated, 'created': created}

    def _tool_get_sap_full(self, args):
        sap_id = int(args.get('sap_id', 0))
        sap = self.env['bp.edu.sap'].browse(sap_id)
        if not sap.exists():
            return {'error': f'SAP #{sap_id} tidak ditemukan'}

        mk_data = self._tool_get_mk_full({'mata_kuliah_id': sap.mata_kuliah_id.id}) if sap.mata_kuliah_id else {}
        pertemuan = [
            {
                'no': p.no,
                'pokok_bahasan': p.pokok_bahasan or '',
                'detail_cpmk': p.detail_cpmk or '',
                'detail_sub_cpmk': p.detail_sub_cpmk or '',
                'tujuan_pembelajaran': p.tujuan_pembelajaran or '',
                'pendahuluan_pengajar': p.pendahuluan_pengajar or '',
                'penyajian_pengajar': p.penyajian_pengajar or '',
                'penutup_pengajar': p.penutup_pengajar or '',
            }
            for p in sap.pertemuan_ids.sorted('no')
        ]
        return {
            'id': sap.id,
            'dosen': sap.dosen_id.nama if sap.dosen_id else '',
            'tahun_akademik': sap.tahun_akademik_id.display_name if sap.tahun_akademik_id else '',
            'mata_kuliah': mk_data,
            'pertemuan': pertemuan,
        }

    def _tool_write_sap_pertemuan(self, args):
        sap_id = int(args.get('sap_id', 0))
        pertemuan_list = args.get('pertemuan', [])
        sap = self.env['bp.edu.sap'].browse(sap_id)
        if not sap.exists():
            return {'error': f'SAP #{sap_id} tidak ditemukan'}

        SAP_FIELDS = {
            'pokok_bahasan', 'sub_pokok_bahasan_1', 'sub_pokok_bahasan_2',
            'detail_cpmk', 'detail_sub_cpmk', 'tujuan_pembelajaran',
            'indikator_1', 'indikator_2',
            'pendahuluan_pengajar', 'pendahuluan_mahasiswa', 'pendahuluan_media',
            'penyajian_pengajar', 'penyajian_mahasiswa', 'penyajian_media',
            'penutup_pengajar', 'penutup_mahasiswa', 'penutup_media',
            'evaluasi_1', 'evaluasi_2', 'referensi_1', 'referensi_2',
        }
        updated = created = 0
        for p in pertemuan_list:
            no = p.get('no')
            if not no:
                continue
            vals = {k: v for k, v in p.items() if k in SAP_FIELDS and v is not None}
            existing = sap.pertemuan_ids.filtered(lambda r: r.no == no)
            if existing:
                if vals:
                    existing[0].write(vals)
                    updated += 1
            else:
                self.env['bp.edu.sap.pertemuan'].create({'sap_id': sap_id, 'no': no, **vals})
                created += 1

        return {'success': True, 'sap_id': sap_id, 'updated': updated, 'created': created}

    def _tool_get_kontrak_full(self, args):
        kontrak_id = int(args.get('kontrak_id', 0))
        k = self.env['bp.edu.kontrak.kuliah'].browse(kontrak_id)
        if not k.exists():
            return {'error': f'Kontrak #{kontrak_id} tidak ditemukan'}

        mk_data = self._tool_get_mk_full({'mata_kuliah_id': k.mata_kuliah_id.id}) if k.mata_kuliah_id else {}
        cpmk = [{'kode': c.kode, 'deskripsi': c.deskripsi} for c in k.cpmk_ids]
        materi = [{'minggu': m.minggu, 'materi': m.materi or ''} for m in k.materi_ids.sorted('minggu')]

        return {
            'id': k.id,
            'dosen': k.dosen_id.nama if k.dosen_id else '',
            'tahun_akademik': k.tahun_akademik_id.display_name if k.tahun_akademik_id else '',
            'mata_kuliah': mk_data,
            'bobot': {
                'diskusi': k.bobot_diskusi, 'proyek': k.bobot_proyek,
                'tugas': k.bobot_tugas, 'kuis': k.bobot_kuis,
                'uts': k.bobot_uts, 'uas': k.bobot_uas,
            },
            'cpmk': cpmk,
            'materi': materi,
        }

    def _tool_write_kontrak_materi(self, args):
        kontrak_id = int(args.get('kontrak_id', 0))
        materi_list = args.get('materi_list', [])
        k = self.env['bp.edu.kontrak.kuliah'].browse(kontrak_id)
        if not k.exists():
            return {'error': f'Kontrak #{kontrak_id} tidak ditemukan'}

        updated = created = 0
        for m in materi_list:
            minggu = m.get('minggu')
            materi = m.get('materi', '')
            if not minggu:
                continue
            existing = k.materi_ids.filtered(lambda r: r.minggu == minggu)
            if existing:
                existing[0].write({'materi': materi})
                updated += 1
            else:
                self.env['bp.edu.kontrak.materi'].create(
                    {'kontrak_id': kontrak_id, 'minggu': minggu, 'materi': materi}
                )
                created += 1

        return {'success': True, 'kontrak_id': kontrak_id, 'updated': updated, 'created': created}

    def _tool_search_dokumen_master(self, args):
        domain = [('active', '=', True)]
        keyword = (args.get('keyword') or '').strip()
        if keyword:
            domain.append(('name', 'ilike', keyword))
        kategori = (args.get('kategori') or '').strip()
        if kategori:
            domain.append(('kategori', '=', kategori))
        docs = self.env['bp.edu.dokumen.master'].search(domain, limit=20)
        return {
            'count': len(docs),
            'documents': [
                {'id': d.id, 'name': d.name, 'kategori': d.kategori, 'version': d.version}
                for d in docs
            ],
        }

    def _tool_get_dokumen_master_full(self, args):
        dokumen_id = int(args.get('dokumen_id', 0))
        doc = self.env['bp.edu.dokumen.master'].browse(dokumen_id)
        if not doc.exists():
            return {'error': f'Dokumen Master #{dokumen_id} tidak ditemukan'}

        isi = doc.isi_dokumen or ''
        offset = max(int(args.get('offset', 0) or 0), 0)
        max_chars = min(int(args.get('max_chars', 0) or DOKUMEN_MASTER_CHUNK_SIZE), DOKUMEN_MASTER_CHUNK_SIZE)
        chunk = isi[offset:offset + max_chars]
        has_more = (offset + max_chars) < len(isi)

        return {
            'id': doc.id,
            'name': doc.name,
            'kategori': doc.kategori,
            'version': doc.version,
            'panjang_total_karakter': len(isi),
            'offset': offset,
            'isi_dokumen': chunk,
            'ada_lanjutan': has_more,
            'catatan': (
                f'Isi dipotong ({len(chunk)} dari {len(isi)} karakter). '
                f'Panggil lagi dengan offset={offset + max_chars} untuk baca lanjutannya.'
            ) if has_more else None,
        }

    def _tool_write_dokumen_master_konten(self, args):
        dokumen_id = int(args.get('dokumen_id', 0))
        isi_dokumen = args.get('isi_dokumen', '')
        doc = self.env['bp.edu.dokumen.master'].browse(dokumen_id)
        if not doc.exists():
            return {'error': f'Dokumen Master #{dokumen_id} tidak ditemukan'}
        doc._write_content(isi_dokumen, source='ai', prompt=self.env.context.get('ai_prompt'))
        return {'success': True, 'dokumen_id': dokumen_id, 'version_baru': doc.version}
