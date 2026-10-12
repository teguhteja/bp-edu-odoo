"""
Wizard Mass Generate DOCX — generate banyak RPS atau SAP sekaligus menjadi satu ZIP.
"""
import base64
import io
import logging
import zipfile

from odoo import models, fields, api
from odoo.exceptions import UserError

_logger = logging.getLogger(__name__)

_M_COLS = [f'm{i}' for i in range(1, 13)]
_P_COLS = [f'p{i}' for i in range(1, 21)]
_C_COLS = [f'c{i}' for i in range(1, 11)]


def _split_lines(text):
    if not text:
        return []
    return [line.strip() for line in text.split('\n') if line.strip()]


class BpEduWizardMassGenerate(models.TransientModel):
    _name = 'bp.edu.wizard.mass.generate'
    _description = 'Wizard Mass Generate DOCX'

    document_type = fields.Selection([
        ('rps', 'RPS'),
        ('sap', 'SAP'),
    ], string='Jenis Dokumen', required=True)

    template_id = fields.Many2one(
        'bp.edu.docx.template',
        string='Template',
        required=True,
        domain="[('document_type', '=', document_type)]",
    )

    rps_ids = fields.Many2many('bp.edu.rps', string='RPS yang Dipilih')
    sap_ids = fields.Many2many('bp.edu.sap', string='SAP yang Dipilih')

    record_count = fields.Integer(string='Jumlah Record', compute='_compute_record_count')
    result_attachment_id = fields.Many2one('ir.attachment', string='File Hasil', readonly=True)
    result_filename = fields.Char(string='Nama File', readonly=True)
    generate_warning = fields.Text(string='Peringatan', readonly=True)
    state = fields.Selection([('draft', 'Draft'), ('done', 'Selesai')], default='draft')

    @api.model
    def default_get(self, fields_list):
        res = super().default_get(fields_list)
        active_model = self.env.context.get('active_model')
        active_ids = self.env.context.get('active_ids', [])
        if active_model == 'bp.edu.rps':
            res['document_type'] = 'rps'
            res['rps_ids'] = [(6, 0, active_ids)]
        elif active_model == 'bp.edu.sap':
            res['document_type'] = 'sap'
            res['sap_ids'] = [(6, 0, active_ids)]
        return res

    @api.depends('rps_ids', 'sap_ids', 'document_type')
    def _compute_record_count(self):
        for rec in self:
            if rec.document_type == 'rps':
                rec.record_count = len(rec.rps_ids)
            else:
                rec.record_count = len(rec.sap_ids)

    def action_generate(self):
        self.ensure_one()
        from ..utils import docx_renderer

        template_bytes = base64.b64decode(self.template_id.template_file)
        warnings = []

        if self.document_type == 'rps':
            if not self.rps_ids:
                raise UserError('Tidak ada RPS yang dipilih.')
            zip_buf = io.BytesIO()
            with zipfile.ZipFile(zip_buf, 'w', zipfile.ZIP_DEFLATED) as zf:
                for rps in self.rps_ids.sorted('kode_mk'):
                    ctx = self._build_rps_context(rps)
                    images = self._get_images(rps.dosen_id)
                    docx_bytes = docx_renderer.render(template_bytes, ctx, images)
                    missing = docx_renderer.get_missing_required_arrays()
                    if missing:
                        warnings.append(f'{rps.kode_mk}: {", ".join(sorted(missing))}')
                    kode = rps.kode_mk or f'RPS_{rps.id}'
                    zf.writestr(f'RPS_{kode}.docx', docx_bytes)
            filename = 'RPS_Batch.zip'
            mimetype = 'application/zip'
            attachment = self._create_attachment(filename, zip_buf.getvalue(), mimetype)

        elif self.document_type == 'sap':
            if not self.sap_ids:
                raise UserError('Tidak ada SAP yang dipilih.')
            zip_buf = io.BytesIO()
            with zipfile.ZipFile(zip_buf, 'w', zipfile.ZIP_DEFLATED) as zf:
                for sap in self.sap_ids.sorted('kode_mk'):
                    pertemuan_list = sap.pertemuan_ids.sorted('no')
                    if not pertemuan_list:
                        warnings.append(f'{sap.kode_mk}: belum ada pertemuan, dilewati.')
                        continue
                    kode = sap.kode_mk or f'SAP_{sap.id}'
                    images = self._get_images(sap.dosen_id)
                    folder = f'SAP_{kode}'
                    for p in pertemuan_list:
                        ctx = self._build_sap_context_per_pertemuan(sap, p)
                        docx_bytes = docx_renderer.render(template_bytes, ctx, images)
                        zf.writestr(f'{folder}/SAP_{kode}_{p.no:02d}.docx', docx_bytes)
            filename = 'SAP_Batch.zip'
            mimetype = 'application/zip'
            attachment = self._create_attachment(filename, zip_buf.getvalue(), mimetype)

        else:
            raise UserError('Jenis dokumen tidak valid.')

        self.write({
            'result_attachment_id': attachment.id,
            'result_filename': filename,
            'generate_warning': '\n'.join(warnings) if warnings else False,
            'state': 'done',
        })
        return {
            'type': 'ir.actions.act_window',
            'res_model': self._name,
            'res_id': self.id,
            'view_mode': 'form',
            'target': 'new',
        }

    def action_download(self):
        self.ensure_one()
        if not self.result_attachment_id:
            raise UserError('Belum ada file yang di-generate.')
        return {
            'type': 'ir.actions.act_url',
            'url': f'/web/content/{self.result_attachment_id.id}?download=true',
            'target': 'new',
        }

    def _create_attachment(self, filename, content, mimetype):
        return self.env['ir.attachment'].create({
            'name': filename,
            'datas': base64.b64encode(content).decode(),
            'mimetype': mimetype,
            'res_model': self._name,
            'res_id': self.id,
        })

    def _get_images(self, dosen):
        images = {}
        if dosen and dosen.tanda_tangan:
            images['dosen_sign'] = base64.b64decode(dosen.tanda_tangan)
        return images

    def _build_rps_context(self, rps):
        mk = rps.mata_kuliah_id
        dosen = rps.dosen_id
        ctx = {
            'kode_mk': mk.kode or '',
            'nama_mk': mk.nama or '',
            'sks_total': mk.sks_total,
            'sks_teori': mk.sks_teori,
            'sks_praktik': mk.sks_praktik,
            'semester': mk.semester,
            'status': mk.status or '',
            'kategori': mk.kategori or '',
            'tanggal_penyusunan': str(rps.tanggal_penyusunan) if rps.tanggal_penyusunan else '',
            'dosen_pengampu': dosen.nama if dosen else '',
            'nuptk': (dosen.nuptk or '') if dosen else '',
            'pangkat_golongan': (dosen.pangkat_golongan or '-') if dosen else '-',
            'pangkat': (dosen.pangkat_golongan or '-') if dosen else '-',
            'jabatan': (dosen.jabatan or '') if dosen else '',
            'deskripsi_singkat': mk.deskripsi_singkat or '',
            'bahan_kajian': mk.bahan_kajian or '',
            'matakuliah_syarat': mk.matakuliah_syarat or '-',
            'cpl_prodi': [
                {
                    'kode': c.kode, 'tipe': c.tipe, 'deskripsi': c.deskripsi,
                    'nomor': f'CPL {i}', 'label': f'CPL {i} ({c.kode})',
                }
                for i, c in enumerate(mk.cpl_ids.sorted('kode'), start=1)
            ],
            'cpmk': [
                {'kode': c.kode, 'cpl': c.cpl_text or '', 'deskripsi': c.deskripsi}
                for c in mk.cpmk_ids.sorted('kode')
            ],
            'sub_cpmk': [
                {
                    'kode': s.kode, 'deskripsi': s.deskripsi,
                    'cpmk': s.cpmk_text or s.cpmk_id.kode,
                    'minggu': s.minggu or '', 'cpl': s.level_bloom or '',
                    'taksonomi': s.level_bloom or '',
                }
                for s in mk.cpmk_ids.mapped('sub_cpmk_ids').sorted('kode')
            ],
            'korelasi': [
                {'cpmk': k.cpmk or '', **{col: k[col] or '' for col in _M_COLS}}
                for k in rps.korelasi_ids.sorted('sequence')
            ],
            'korelasi_cpl': [
                {'sub': k.sub or '', 'bobot': k.bobot or '', 'minggu': k.minggu or '',
                 **{col: k[col] or '' for col in _P_COLS}}
                for k in rps.korelasi_cpl_ids.sorted('sequence')
            ],
            'penilaian': [
                {'jenis': p.jenis or '', 'bobot': p.bobot or '',
                 **{col: p[col] or '' for col in _C_COLS}}
                for p in rps.penilaian_ids.sorted('sequence')
            ],
            'detail': [
                {
                    'minggu': d.minggu, 'deskripsi': d.deskripsi or '',
                    'indikator': d.indikator or '', 'kriteria': d.kriteria or '',
                    'tatap_muka': d.tatap_muka or '', 'daring': d.daring or '',
                    'materi': d.materi or '', 'bobot': d.bobot or '',
                }
                for d in rps.detail_ids.sorted('minggu')
            ],
            'pustaka_utama': [
                {'kode': p.kode, 'jenis': p.jenis, 'referensi': p.referensi}
                for p in mk.pustaka_ids.filtered(lambda p: p.jenis == 'Utama')
            ],
            'pustaka_pendukung': [
                {'kode': p.kode, 'jenis': p.jenis, 'referensi': p.referensi}
                for p in mk.pustaka_ids.filtered(lambda p: p.jenis == 'Pendukung')
            ],
        }
        rt = rps.rancangan_tugas_ids[:1]
        if rt:
            ctx['rancangan_tugas_proyek'] = {
                'tujuan': rt.tujuan or '',
                'kompetensi': _split_lines(rt.kompetensi),
                'uraian_tugas': {
                    'objek_garapan': rt.objek_garapan or '',
                    'langkah_kerja': _split_lines(rt.langkah_kerja),
                    'topik': _split_lines(rt.topik),
                    'metode_kerja': _split_lines(rt.metode_kerja),
                    'luaran_tugas': _split_lines(rt.luaran_tugas),
                },
                'kriteria_penilaian': {
                    'penyusunan_proposal': {'bobot': rt.kriteria_proposal_bobot or '', 'deskripsi': rt.kriteria_proposal_deskripsi or ''},
                    'pengimplementasian_proyek': {'bobot': rt.kriteria_implementasi_bobot or '', 'deskripsi': rt.kriteria_implementasi_deskripsi or ''},
                    'penyusunan_laporan': {'bobot': rt.kriteria_laporan_bobot or '', 'deskripsi': rt.kriteria_laporan_deskripsi or ''},
                    'presentasi': {'bobot': rt.kriteria_presentasi_bobot or '', 'deskripsi': rt.kriteria_presentasi_deskripsi or ''},
                },
            }
        rd = rps.rubrik_deskriptif_ids[:1]
        if rps.rubrik_holistik_ids or rd:
            ctx['rubrik_penilaian'] = {
                'rubrik_holistik_proposal_laporan': [
                    {'grade': r.grade or '', 'skor_min': r.skor_min, 'skor_max': r.skor_max, 'kriteria': r.kriteria or ''}
                    for r in rps.rubrik_holistik_ids.sorted('skor_min')
                ],
            }
            if rd:
                ctx['rubrik_penilaian']['rubrik_deskriptif_presentasi'] = {
                    'aspek_yang_dinilai': _split_lines(rd.aspek_yang_dinilai),
                    'skala_penilaian': {
                        'sangat_kurang': {'min': rd.skala_sangat_kurang_min, 'max': rd.skala_sangat_kurang_max},
                        'kurang': {'min': rd.skala_kurang_min, 'max': rd.skala_kurang_max},
                        'cukup': {'min': rd.skala_cukup_min, 'max': rd.skala_cukup_max},
                        'baik': {'min': rd.skala_baik_min, 'max': rd.skala_baik_max},
                        'sangat_baik': {'min': rd.skala_sangat_baik_min, 'max': rd.skala_sangat_baik_max},
                    },
                    'format_penilaian': rd.format_penilaian or '',
                }
        ctx['meta'] = dict(ctx)
        return ctx

    def _build_sap_context_per_pertemuan(self, sap, pertemuan):
        mk = sap.mata_kuliah_id
        dosen = sap.dosen_id
        meta = {
            'kode_mk': mk.kode or '',
            'nama_mk': mk.nama or '',
            'sks_total': mk.sks_total,
            'dosen_pengampu': dosen.nama if dosen else '',
            'nuptk': (dosen.nuptk or '') if dosen else '',
        }
        pertemuan_data = {
            'no': pertemuan.no,
            'waktu_pertemuan': pertemuan.waktu_pertemuan or '',
            'detail_cpmk': pertemuan.detail_cpmk or '',
            'detail_sub_cpmk': pertemuan.detail_sub_cpmk or '',
            'indikator_1': pertemuan.indikator_1 or '',
            'indikator_2': pertemuan.indikator_2 or '',
            'tujuan_pembelajaran': pertemuan.tujuan_pembelajaran or '',
            'pokok_bahasan': pertemuan.pokok_bahasan or '',
            'sub_pokok_bahasan_1': pertemuan.sub_pokok_bahasan_1 or '',
            'sub_pokok_bahasan_2': pertemuan.sub_pokok_bahasan_2 or '',
            'kegiatan': {
                'pendahuluan': {
                    'pengajar': pertemuan.pendahuluan_pengajar or '',
                    'mahasiswa': pertemuan.pendahuluan_mahasiswa or '',
                    'media': pertemuan.pendahuluan_media or '',
                },
                'penyajian': {
                    'pengajar': pertemuan.penyajian_pengajar or '',
                    'mahasiswa': pertemuan.penyajian_mahasiswa or '',
                    'media': pertemuan.penyajian_media or '',
                },
                'penutup': {
                    'pengajar': pertemuan.penutup_pengajar or '',
                    'mahasiswa': pertemuan.penutup_mahasiswa or '',
                    'media': pertemuan.penutup_media or '',
                },
            },
            'evaluasi_1': pertemuan.evaluasi_1 or '',
            'evaluasi_2': pertemuan.evaluasi_2 or '',
            'referensi_1': pertemuan.referensi_1 or '',
            'referensi_2': pertemuan.referensi_2 or '',
        }
        ctx = {**meta, **pertemuan_data}
        ctx['meta'] = meta
        return ctx
