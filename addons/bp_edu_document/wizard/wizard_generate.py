"""
Wizard Generate DOCX — generate RPS, SAP (ZIP 16 file), atau Kontrak Kuliah dari template.
"""
import base64
import io
import logging
import zipfile

from odoo import models, fields, api
from odoo.exceptions import UserError

_logger = logging.getLogger(__name__)


class BpEduWizardGenerate(models.TransientModel):
    _name = 'bp.edu.wizard.generate'
    _description = 'Wizard Generate DOCX'

    document_type = fields.Selection([
        ('rps', 'RPS'),
        ('sap', 'SAP'),
        ('kontrak', 'Kontrak Kuliah'),
    ], string='Jenis Dokumen', required=True)

    template_id = fields.Many2one(
        'bp.edu.docx.template',
        string='Template',
        required=True,
        domain="[('document_type', '=', document_type)]",
    )

    # Source record — hanya satu yang diisi tergantung document_type
    rps_id = fields.Many2one('bp.edu.rps', string='RPS')
    sap_id = fields.Many2one('bp.edu.sap', string='SAP')
    kontrak_id = fields.Many2one('bp.edu.kontrak.kuliah', string='Kontrak Kuliah')

    result_attachment_id = fields.Many2one('ir.attachment', string='File Hasil', readonly=True)
    result_filename = fields.Char(string='Nama File', readonly=True)
    state = fields.Selection([('draft', 'Draft'), ('done', 'Selesai')], default='draft')

    # ─── Context builders ────────────────────────────────────────────────────

    def _build_rps_context(self):
        rps = self.rps_id
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
                {'kode': c.kode, 'tipe': c.tipe, 'deskripsi': c.deskripsi}
                for c in mk.cpl_ids.sorted('kode')
            ],
            'cpmk': [
                {'kode': c.kode, 'cpl': c.cpl_text or '', 'deskripsi': c.deskripsi}
                for c in mk.cpmk_ids.sorted('kode')
            ],
            'sub_cpmk': [
                {
                    'kode': s.kode,
                    'deskripsi': s.deskripsi,
                    'cpmk': s.cpmk_id.kode,
                    'minggu': s.minggu or '',
                    'cpl': s.level_bloom or '',
                }
                for s in mk.cpmk_ids.mapped('sub_cpmk_ids').sorted('kode')
            ],
            'detail': [
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
        ctx['meta'] = dict(ctx)
        return ctx

    def _build_sap_context_per_pertemuan(self, pertemuan):
        """SAP: satu context per pertemuan, digabung dengan meta MK."""
        sap = self.sap_id
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

    def _build_kontrak_context(self):
        kontrak = self.kontrak_id
        mk = kontrak.mata_kuliah_id
        dosen = kontrak.dosen_id
        ta = kontrak.tahun_akademik_id

        ctx = {
            'tahun_akademik': ta.nama if ta else '',
            'periode': kontrak.periode or '',
            'nama_mk': mk.nama if mk else '',
            'semester': str(mk.semester) if mk else '',
            'sks_total': str(mk.sks_total) if mk else '',
            'jenis_mk': kontrak.jenis_mk or '',
            'kelas': kontrak.kelas or '',
            'prasyarat': kontrak.prasyarat or '-',
            'hari_jam': kontrak.hari_jam or '',
            'dosen_pengampu': dosen.nama if dosen else '',
            'nuptk': (dosen.nuptk or '') if dosen else '',
            'cpmk': [
                {'kode': c.kode, 'deskripsi': c.deskripsi}
                for c in kontrak.cpmk_ids.sorted('kode')
            ],
            'jumlah_kuis_mingguan': str(kontrak.jumlah_kuis_mingguan),
            'jumlah_tugas_terstruktur': str(kontrak.jumlah_tugas_terstruktur),
            'jumlah_proyek': str(kontrak.jumlah_proyek),
            'bobot_diskusi': str(kontrak.bobot_diskusi),
            'bobot_proyek': str(kontrak.bobot_proyek),
            'bobot_tugas': str(kontrak.bobot_tugas),
            'bobot_kuis': str(kontrak.bobot_kuis),
            'bobot_uts': str(kontrak.bobot_uts),
            'bobot_uas': str(kontrak.bobot_uas),
            'wakil_mahasiswa': kontrak.wakil_mahasiswa or '',
            'nim_wakil': kontrak.nim_wakil or '',
        }
        # materi_minggu_1 … materi_minggu_16 (flat keys)
        for m in kontrak.materi_ids.sorted('minggu'):
            ctx[f'materi_minggu_{m.minggu}'] = m.materi or ''

        ctx['meta'] = dict(ctx)
        return ctx

    def _get_images(self, dosen):
        images = {}
        if dosen and dosen.tanda_tangan:
            images['dosen_sign'] = base64.b64decode(dosen.tanda_tangan)
        return images

    # ─── Generate ────────────────────────────────────────────────────────────

    def action_generate(self):
        self.ensure_one()
        from ..utils import docx_renderer

        template_bytes = base64.b64decode(self.template_id.template_file)

        if self.document_type == 'rps':
            if not self.rps_id:
                raise UserError('Pilih RPS terlebih dahulu.')
            ctx = self._build_rps_context()
            images = self._get_images(self.rps_id.dosen_id)
            docx_bytes = docx_renderer.render(template_bytes, ctx, images)
            kode = self.rps_id.kode_mk or 'RPS'
            filename = f'RPS_{kode}.docx'
            mimetype = 'application/vnd.openxmlformats-officedocument.wordprocessingml.document'
            attachment = self._create_attachment(filename, docx_bytes, mimetype)
            mk = self.rps_id.mata_kuliah_id

        elif self.document_type == 'sap':
            if not self.sap_id:
                raise UserError('Pilih SAP terlebih dahulu.')
            pertemuan_list = self.sap_id.pertemuan_ids.sorted('no')
            if not pertemuan_list:
                raise UserError('SAP belum memiliki pertemuan. Generate pertemuan kosong terlebih dahulu.')
            images = self._get_images(self.sap_id.dosen_id)
            kode = self.sap_id.kode_mk or 'SAP'
            # Generate ZIP berisi 16 DOCX
            zip_buf = io.BytesIO()
            with zipfile.ZipFile(zip_buf, 'w', zipfile.ZIP_DEFLATED) as zf:
                for p in pertemuan_list:
                    ctx = self._build_sap_context_per_pertemuan(p)
                    docx_bytes = docx_renderer.render(template_bytes, ctx, images)
                    zf.writestr(f'SAP_{kode}_{p.no:02d}.docx', docx_bytes)
            filename = f'SAP_{kode}.zip'
            mimetype = 'application/zip'
            attachment = self._create_attachment(filename, zip_buf.getvalue(), mimetype)
            mk = self.sap_id.mata_kuliah_id

        elif self.document_type == 'kontrak':
            if not self.kontrak_id:
                raise UserError('Pilih Kontrak Kuliah terlebih dahulu.')
            ctx = self._build_kontrak_context()
            images = self._get_images(self.kontrak_id.dosen_id)
            docx_bytes = docx_renderer.render(template_bytes, ctx, images)
            mk_nama = self.kontrak_id.mata_kuliah_id.kode or 'KONTRAK'
            filename = f'Kontrak_{mk_nama}.docx'
            mimetype = 'application/vnd.openxmlformats-officedocument.wordprocessingml.document'
            attachment = self._create_attachment(filename, docx_bytes, mimetype)
            mk = self.kontrak_id.mata_kuliah_id

        else:
            raise UserError('Jenis dokumen tidak valid.')

        # Log
        self.env['bp.edu.generate.log'].create({
            'name': filename,
            'document_type': self.document_type,
            'mata_kuliah_id': mk.id if mk else False,
            'template_id': self.template_id.id,
            'attachment_id': attachment.id,
        })

        self.write({'result_attachment_id': attachment.id, 'result_filename': filename, 'state': 'done'})

        # Tetap buka wizard dengan tombol download
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

    def _create_attachment(self, filename: str, content: bytes, mimetype: str):
        return self.env['ir.attachment'].create({
            'name': filename,
            'datas': base64.b64encode(content).decode(),
            'mimetype': mimetype,
            'res_model': self._name,
            'res_id': self.id,
        })
