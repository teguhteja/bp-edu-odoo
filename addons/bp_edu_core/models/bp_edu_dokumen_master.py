"""
Dokumen Master — dokumen institusi (Pedoman Akademik, Buku Kurikulum, dsb.)
yang diupload sebagai referensi/basis dalam pembuatan RPS, SAP, Kontrak Kuliah,
dan dokumen akademik lainnya. Perubahan isi (manual, ekstraksi file, atau AI)
dicatat sebagai riwayat versi.
"""
import base64
import io
import logging

from odoo import models, fields, api

_logger = logging.getLogger(__name__)


class BpEduDokumenMaster(models.Model):
    _name = 'bp.edu.dokumen.master'
    _description = 'Dokumen Master'
    _inherit = ['mail.thread', 'mail.activity.mixin']
    _order = 'name'

    name = fields.Char(string='Nama Dokumen', required=True, tracking=True,
                        help='Contoh: Pedoman Akademik 2024, Buku Kurikulum S1 Informatika')
    kategori = fields.Selection([
        ('pedoman_akademik', 'Pedoman Akademik'),
        ('kurikulum', 'Buku Kurikulum'),
        ('panduan_skripsi', 'Panduan Skripsi/Tugas Akhir'),
        ('lainnya', 'Lainnya'),
    ], string='Kategori', required=True, default='lainnya', tracking=True)
    prodi_id = fields.Many2one('bp.edu.program.studi', string='Program Studi')
    file = fields.Binary(string='File Dokumen', attachment=True)
    filename = fields.Char(string='Nama File')
    isi_dokumen = fields.Text(string='Isi Dokumen (Teks)',
                               help='Teks dokumen yang digunakan AI sebagai referensi. '
                                    'Diisi otomatis via ekstraksi file atau manual.')
    version = fields.Integer(string='Versi', default=1, readonly=True)
    active = fields.Boolean(default=True)
    history_ids = fields.One2many(
        'bp.edu.dokumen.master.history', 'dokumen_id', string='Riwayat Perubahan'
    )
    history_count = fields.Integer(compute='_compute_history_count')

    @api.depends('history_ids')
    def _compute_history_count(self):
        for rec in self:
            rec.history_count = len(rec.history_ids)

    def action_extract_content(self):
        """Ekstrak teks dari file yang diupload (.docx, .pdf, .txt)."""
        for rec in self:
            if not rec.file:
                raise ValueError('Belum ada file yang diupload.')
            raw = base64.b64decode(rec.file)
            fname = (rec.filename or '').lower()
            if fname.endswith('.docx'):
                text = rec._extract_docx(raw)
            elif fname.endswith('.pdf'):
                text = rec._extract_pdf(raw)
            elif fname.endswith('.txt'):
                text = raw.decode('utf-8', errors='ignore')
            else:
                raise ValueError(
                    'Format file tidak didukung untuk ekstraksi otomatis '
                    '(gunakan .docx, .pdf, atau .txt). Isi manual di field Isi Dokumen.'
                )
            rec._write_content(text, source='extract')

    @staticmethod
    def _extract_docx(raw):
        import docx
        doc = docx.Document(io.BytesIO(raw))
        return '\n'.join(p.text for p in doc.paragraphs if p.text.strip())

    @staticmethod
    def _extract_pdf(raw):
        from PyPDF2 import PdfReader
        reader = PdfReader(io.BytesIO(raw))
        return '\n'.join((page.extract_text() or '') for page in reader.pages)

    def _write_content(self, new_content, source='manual', prompt=False):
        """Simpan konten baru dan catat konten lama sebagai riwayat versi."""
        self.ensure_one()
        old_content = self.isi_dokumen or ''
        new_content = new_content or ''
        if old_content == new_content:
            return
        self.env['bp.edu.dokumen.master.history'].sudo().create({
            'dokumen_id': self.id,
            'version': self.version,
            'isi_sebelum': old_content,
            'isi_sesudah': new_content,
            'prompt': prompt or False,
            'source': source,
        })
        self.write({
            'isi_dokumen': new_content,
            'version': self.version + 1,
        })

    def action_view_history(self):
        self.ensure_one()
        return {
            'type': 'ir.actions.act_window',
            'name': 'Riwayat Perubahan',
            'res_model': 'bp.edu.dokumen.master.history',
            'view_mode': 'list,form',
            'domain': [('dokumen_id', '=', self.id)],
            'context': {'default_dokumen_id': self.id},
        }


class BpEduDokumenMasterHistory(models.Model):
    _name = 'bp.edu.dokumen.master.history'
    _description = 'Riwayat Perubahan Dokumen Master'
    _order = 'create_date desc'

    dokumen_id = fields.Many2one(
        'bp.edu.dokumen.master', string='Dokumen',
        required=True, ondelete='cascade',
    )
    version = fields.Integer(string='Versi Sebelum Perubahan')
    isi_sebelum = fields.Text(string='Isi Sebelum')
    isi_sesudah = fields.Text(string='Isi Sesudah')
    prompt = fields.Text(string='Prompt AI (jika ada)')
    source = fields.Selection([
        ('manual', 'Manual'),
        ('ai', 'AI'),
        ('extract', 'Ekstrak File'),
    ], string='Sumber Perubahan', default='manual', required=True)
    edited_by = fields.Many2one(
        'res.users', string='Diubah Oleh',
        default=lambda self: self.env.uid, readonly=True,
    )
