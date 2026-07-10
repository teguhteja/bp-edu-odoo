"""
Wizard Generate dengan AI — dialog interaktif untuk memanggil AI
dari form RPS, SAP, Kontrak Kuliah, atau Mata Kuliah.
"""
import logging

from odoo import models, fields, api

_logger = logging.getLogger(__name__)

CONTOH_PROMPT = {
    'bp.edu.rps': (
        'Contoh: "Buatkan detail 16 minggu RPS berdasarkan CPMK yang ada. '
        'Pertemuan 8 untuk UTS dan pertemuan 16 untuk UAS."'
    ),
    'bp.edu.sap': (
        'Contoh: "Generate SAP pertemuan 1 sampai 8 berdasarkan RPS yang terhubung.'
        ' Isi kegiatan pendahuluan, penyajian, dan penutup."'
    ),
    'bp.edu.kontrak.kuliah': (
        'Contoh: "Isi materi per minggu berdasarkan CPMK mata kuliah ini."'
    ),
    'bp.edu.mata.kuliah': (
        'Contoh: "Tambahkan CPMK baru: mahasiswa mampu menganalisis algoritma sorting '
        'dengan kompleksitas waktu O(n log n)."'
    ),
    'bp.edu.dokumen.master': (
        'Contoh: "Ringkas bagian ketentuan cuti akademik menjadi poin-poin." atau '
        '"Perbaiki tata bahasa pada bagian pendahuluan."'
    ),
}


class BpEduAiWizard(models.TransientModel):
    _name = 'bp.edu.ai.wizard'
    _description = 'Generate dengan AI'

    res_model = fields.Char(string='Model', required=True)
    res_id = fields.Integer(string='Record ID', required=True)
    res_name = fields.Char(string='Record', compute='_compute_res_name')

    prompt = fields.Text(
        string='Instruksi untuk AI',
        required=True,
        help='Jelaskan apa yang ingin Anda generate atau ubah.',
    )
    placeholder_hint = fields.Char(compute='_compute_placeholder_hint')

    state = fields.Selection([
        ('input', 'Input'),
        ('processing', 'Memproses...'),
        ('done', 'Selesai'),
        ('error', 'Error'),
    ], default='input')

    result_html = fields.Html(string='Hasil AI', readonly=True)

    @api.depends('res_model', 'res_id')
    def _compute_res_name(self):
        for rec in self:
            try:
                record = self.env[rec.res_model].browse(rec.res_id)
                rec.res_name = record.display_name if record.exists() else f'#{rec.res_id}'
            except Exception:
                rec.res_name = f'#{rec.res_id}'

    @api.depends('res_model')
    def _compute_placeholder_hint(self):
        for rec in self:
            rec.placeholder_hint = CONTOH_PROMPT.get(rec.res_model, 'Ketik instruksi untuk AI...')

    def action_generate(self):
        self.ensure_one()
        self.state = 'processing'

        try:
            # Cari agent aktif dengan prioritas tertinggi
            agent = self.env['ai.agent'].sudo().search([('active', '=', True)], limit=1)
            if not agent:
                # Fallback ke config_parameter
                result = self.env['ai.agent'].sudo().call_from_settings(
                    self.prompt, self.res_model, self.res_id
                )
            else:
                result = agent.process_message(self.prompt, self.res_model, self.res_id)

            self.write({'result_html': result, 'state': 'done'})
            _logger.info('BP Edu AI wizard selesai: model=%s id=%s', self.res_model, self.res_id)

        except Exception as e:
            _logger.exception('BP Edu AI wizard error')
            self.write({
                'result_html': f'<p><b>Error:</b> {e}</p>',
                'state': 'error',
            })

        return {
            'type': 'ir.actions.act_window',
            'res_model': self._name,
            'res_id': self.id,
            'view_mode': 'form',
            'target': 'new',
        }

    def action_post_to_chatter(self):
        """Post hasil AI ke chatter record asal."""
        self.ensure_one()
        if not self.result_html or not self.res_model or not self.res_id:
            return
        try:
            record = self.env[self.res_model].browse(self.res_id)
            if record.exists() and hasattr(record, 'message_post'):
                record.message_post(
                    body=self.result_html,
                    message_type='comment',
                    subtype_xmlid='mail.mt_comment',
                )
        except Exception:
            _logger.exception('Gagal post ke chatter dari wizard')

    def action_reset(self):
        self.write({'state': 'input', 'result_html': False, 'prompt': ''})
        return {
            'type': 'ir.actions.act_window',
            'res_model': self._name,
            'res_id': self.id,
            'view_mode': 'form',
            'target': 'new',
        }
