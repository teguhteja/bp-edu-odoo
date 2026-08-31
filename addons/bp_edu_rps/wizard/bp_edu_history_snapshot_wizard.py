"""
Wizard read-only untuk menampilkan "kondisi record sebelum satu perubahan
tertentu" -- direkonstruksi dari mail.tracking.value (chatter). Bukan
record bisnis, tidak bisa disimpan/diedit -- murni tampilan historis.
"""
from odoo import models, fields


class BpEduHistorySnapshotWizard(models.TransientModel):
    _name = 'bp.edu.history.snapshot.wizard'
    _description = 'Kondisi Sebelum Perubahan (Riwayat)'

    model_name = fields.Char(string='Model', readonly=True)
    res_name = fields.Char(string='Record', readonly=True)
    changed_at = fields.Datetime(string='Waktu Perubahan', readonly=True)
    changed_by = fields.Char(string='Diubah oleh', readonly=True)
    snapshot_html = fields.Html(string='Kondisi Sebelum Perubahan', readonly=True)
