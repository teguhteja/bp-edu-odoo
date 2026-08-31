"""
Wizard Upload Dokumen RPS — dosen mengunggah kembali file .docx (hasil edit
dari file yang sebelumnya di-download), sistem mengecek apakah bisa dibaca,
lalu menggantikan data RPS yang ada.

Dua mode:
  - Tanpa AI: baca tabel Detail Perkuliahan 16 Minggu berdasarkan posisi
    kolom. Cepat, tidak butuh API key, tapi hanya mengganti detail_ids.
  - Dengan AI: kirim seluruh isi dokumen ke LLM, minta JSON lengkap sesuai
    skema rps_bp, lalu diterapkan lewat import_rps() (sama seperti wizard
    Import JSON) -- MENGGANTI SELURUH data RPS (CPMK, Sub-CPMK, Pustaka,
    matriks korelasi, dan detail mingguan) sesuai apa yang terbaca AI.
"""
import base64
import json
import logging

from odoo import models, fields
from odoo.exceptions import UserError

from ..utils import docx_upload_parser as parser

_logger = logging.getLogger(__name__)


class BpEduUploadRpsWizard(models.TransientModel):
    _name = 'bp.edu.upload.rps.wizard'
    _description = 'Upload Dokumen RPS'

    rps_id = fields.Many2one('bp.edu.rps', string='RPS', required=True)

    docx_file = fields.Binary(string='File RPS (.docx)', required=True, attachment=False)
    docx_filename = fields.Char(string='Nama File')
    use_ai = fields.Boolean(
        string='Proses dengan AI',
        help='Tanpa AI: hanya mengganti tabel Detail Perkuliahan 16 Minggu, '
             'berdasarkan posisi kolom (cepat, tanpa API key).\n'
             'Dengan AI: membaca seluruh isi dokumen (CPMK, Sub-CPMK, Pustaka, '
             'matriks korelasi, dll) dan MENGGANTI SELURUH data RPS ini sesuai '
             'apa yang berhasil dibaca AI dari dokumen.',
    )

    state = fields.Selection([
        ('upload', 'Upload'),
        ('checked', 'Hasil Cek'),
        ('done', 'Selesai'),
    ], default='upload')
    check_ok = fields.Boolean(readonly=True)
    check_result = fields.Text(string='Hasil Cek', readonly=True)
    result_summary = fields.Text(string='Hasil Update', readonly=True)

    # Cache hasil parse dari action_check(), dipakai lagi oleh action_apply()
    # supaya tidak parse ulang / panggil AI dua kali.
    detail_cache_json = fields.Text(readonly=True)
    ai_json_cache = fields.Text(readonly=True)

    # ─── Cek ─────────────────────────────────────────────────────────────

    def action_check(self):
        self.ensure_one()
        doc, err = parser.load_docx(self.docx_file, self.docx_filename)
        if err:
            self.write({
                'state': 'checked', 'check_ok': False, 'check_result': err,
                'detail_cache_json': False, 'ai_json_cache': False,
            })
            return self._reopen()

        if self.use_ai:
            self._check_ai(doc)
        else:
            self._check_deterministic(doc)
        return self._reopen()

    def _check_deterministic(self, doc):
        result = parser.extract_detail_table(doc)
        lines = []
        if result['ok']:
            lines.append('✅ Tabel Detail Perkuliahan 16 Minggu terbaca lengkap (16/16 minggu).')
            lines.append('')
            lines.append('Cuplikan isi yang akan diterapkan:')
            for w in range(1, 17):
                deskripsi = result['weeks'][w]['deskripsi'][:60]
                lines.append(f'  Minggu {w}: {deskripsi}')
        else:
            lines.append('❌ Dokumen belum bisa diproses:')
            for e in result['errors']:
                lines.append(f'  - {e}')
            for w in result['warnings']:
                lines.append(f'  - {w}')
            if result['weeks']:
                lines.append('')
                lines.append(f"({len(result['weeks'])} dari 16 minggu berhasil terbaca)")

        self.write({
            'state': 'checked',
            'check_ok': result['ok'],
            'check_result': '\n'.join(lines),
            'detail_cache_json': json.dumps(result['weeks']) if result['ok'] else False,
            'ai_json_cache': False,
        })

    def _check_ai(self, doc):
        data, err = parser.extract_full_json_via_ai(self.env, doc)
        if err:
            self.write({
                'state': 'checked', 'check_ok': False,
                'check_result': f'❌ AI gagal memproses dokumen:\n{err}',
                'detail_cache_json': False, 'ai_json_cache': False,
            })
            return

        ok, counts, weeks_found = parser.summarize_ai_json(data)
        lines = ['✅ AI berhasil membaca dokumen ini:' if ok else '⚠️ AI membaca dokumen, tapi datanya kurang lengkap:']
        for label, count in counts.items():
            lines.append(f'  - {label}: {count}')
        missing = [w for w in range(1, 17) if w not in weeks_found]
        if missing:
            lines.append('')
            lines.append('Minggu yang tidak terbaca: ' + ', '.join(str(w) for w in missing) + '.')
        lines.append('')
        if ok:
            lines.append(
                '⚠️ PERHATIAN: Menerapkan hasil ini akan MENGGANTI SELURUH data RPS '
                '(CPMK, Sub-CPMK, Pustaka, matriks korelasi, dan detail mingguan) '
                'sesuai isi di atas. Bagian yang bernilai 0 di atas akan DIKOSONGKAN.'
            )
        else:
            lines.append(
                'Data yang terbaca terlalu sedikit untuk dianggap dokumen RPS yang valid '
                '(minimal 10/16 minggu, 1 CPL, dan 1 CPMK). Tidak bisa diterapkan.'
            )

        self.write({
            'state': 'checked',
            'check_ok': ok,
            'check_result': '\n'.join(lines),
            'ai_json_cache': json.dumps(data) if ok else False,
            'detail_cache_json': False,
        })

    # ─── Terapkan ────────────────────────────────────────────────────────

    def action_apply(self):
        self.ensure_one()
        if not self.check_ok:
            raise UserError('Dokumen ini belum lolos pengecekan, tidak bisa diterapkan.')

        rps = self.rps_id
        if self.use_ai:
            if not self.ai_json_cache:
                raise UserError('Hasil cek AI tidak ditemukan, silakan cek ulang.')
            data = json.loads(self.ai_json_cache)
            mk = rps.mata_kuliah_id
            data.setdefault('meta', {})
            data['meta']['kode_mk'] = mk.kode
            data['meta']['nama_mk'] = mk.nama

            from odoo.addons.bp_edu_document.utils.json_importer import import_rps
            try:
                import_rps(self.env, data)
            except Exception as e:
                _logger.exception('Upload RPS (AI): import_rps gagal')
                raise UserError(f'Gagal menerapkan hasil AI: {e}')

            summary = 'RPS diperbarui dari upload dokumen (diproses dengan AI).'
        else:
            if not self.detail_cache_json:
                raise UserError('Hasil cek tabel mingguan tidak ditemukan, silakan cek ulang.')
            weeks = json.loads(self.detail_cache_json)
            rps.detail_ids.unlink()
            for w in sorted(weeks, key=int):
                item = weeks[w]
                self.env['bp.edu.rps.detail'].create({
                    'rps_id': rps.id,
                    'minggu': int(item['minggu']),
                    'deskripsi': item['deskripsi'],
                    'indikator': item['indikator'],
                    'kriteria': item['kriteria'],
                    'tatap_muka': item['tatap_muka'],
                    'daring': item['daring'],
                    'materi': item['materi'],
                    'bobot': item['bobot'],
                })
            summary = 'Tabel Detail Perkuliahan 16 Minggu diperbarui dari upload dokumen.'

        rps.message_post(
            body=summary,
            attachments=[(self.docx_filename, base64.b64decode(self.docx_file))],
        )
        self.write({'state': 'done', 'result_summary': summary})
        return self._reopen()

    def action_reset(self):
        self.write({
            'state': 'upload', 'check_ok': False, 'check_result': False,
            'result_summary': False, 'detail_cache_json': False, 'ai_json_cache': False,
        })
        return self._reopen()

    def action_open_rps(self):
        self.ensure_one()
        return {
            'type': 'ir.actions.act_window',
            'res_model': 'bp.edu.rps',
            'res_id': self.rps_id.id,
            'view_mode': 'form',
        }

    def _reopen(self):
        return {
            'type': 'ir.actions.act_window',
            'res_model': self._name,
            'res_id': self.id,
            'view_mode': 'form',
            'target': 'new',
            'context': {'dialog_size': 'large'},
        }
