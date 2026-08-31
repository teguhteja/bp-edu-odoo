"""
Extend mail.message dengan:
  - bp_edu_tracking_summary: tampilan ringkas field yang berubah pada satu
    message (dari tracking_value_ids), dipakai list/form riwayat perubahan
    RPS/SAP/Kontrak Kuliah.
  - action_view_snapshot_before: rekonstruksi & tampilkan kondisi record
    (field yang dilacak) tepat sebelum message ini terjadi, lewat
    bp.edu.history.snapshot.wizard.

Hanya berpengaruh pada message yang membawa tracking_value_ids (perubahan
field) -- message lain (chatter biasa, log, dsb) tidak terpengaruh sama
sekali karena field-field baru di sini kosong/tidak dipakai untuk itu.
"""
import html

from markupsafe import Markup

from odoo import models, fields

from .bp_edu_field_history import TRACKED_FIELDS_BY_MODEL


def _tracking_value_text(env, tv, new=False):
    """
    Representasi teks satu sisi (lama/baru) dari mail.tracking.value.

    Odoo sudah menyimpan old_value_char/new_value_char sebagai teks yang
    SIAP TAMPIL untuk many2one (nama record) maupun selection (label, bukan
    key mentah) -- diverifikasi langsung dari data mail.tracking.value asli,
    bukan diasumsikan. Cuma date/datetime/integer/float yang perlu dibaca
    dari kolom bertipe lain lalu diformat sendiri.
    """
    ftype = tv.field_id.ttype
    p = 'new_value_' if new else 'old_value_'

    if ftype == 'date':
        val = tv[p + 'datetime']
        return str(val.date()) if val else ''

    if ftype == 'datetime':
        val = tv[p + 'datetime']
        return str(val) if val else ''

    if ftype == 'integer':
        val = tv[p + 'integer']
        return str(val) if val is not False else ''

    if ftype in ('float', 'monetary'):
        val = tv[p + 'float']
        return str(val) if val is not False else ''

    # many2one, selection, char, text, html, boolean, ... -> sudah teks siap tampil
    return tv[p + 'char'] or tv[p + 'text'] or ''


class MailMessageHistory(models.Model):
    _inherit = 'mail.message'

    bp_edu_tracking_summary = fields.Html(
        string='Perubahan', compute='_compute_bp_edu_tracking_summary',
    )
    bp_edu_tracking_fields_changed = fields.Char(
        string='Field Berubah', compute='_compute_bp_edu_tracking_summary',
    )

    def _compute_bp_edu_tracking_summary(self):
        for msg in self:
            if not msg.tracking_value_ids:
                msg.bp_edu_tracking_summary = False
                msg.bp_edu_tracking_fields_changed = False
                continue
            rows = []
            for tv in msg.tracking_value_ids:
                label = tv.field_id.field_description
                old = _tracking_value_text(msg.env, tv, new=False)
                new = _tracking_value_text(msg.env, tv, new=True)
                rows.append((label, old, new))
            msg.bp_edu_tracking_summary = msg._bp_edu_render_tracking_table(rows)
            msg.bp_edu_tracking_fields_changed = ', '.join(r[0] for r in rows)

    def _bp_edu_render_tracking_table(self, rows):
        parts = ['<table class="table table-sm mb-0">',
                 '<tr><th>Field</th><th>Nilai Lama</th><th>Nilai Baru</th></tr>']
        for label, old, new in rows:
            parts.append(
                f'<tr><td><strong>{html.escape(label)}</strong></td>'
                f'<td>{html.escape(old or "(kosong)")}</td>'
                f'<td>{html.escape(new or "(kosong)")}</td></tr>'
            )
        parts.append('</table>')
        return Markup(''.join(parts))

    # ── Rekonstruksi kondisi sebelum ────────────────────────────────────────

    def _bp_edu_reconstruct_before(self, field_name):
        """Nilai teks field_name tepat sebelum message ini, sama logikanya
        dengan versi lama (bp_edu_field_history): cari perubahan field ini
        yang paling akhir sebelum/pada message ini; kalau itu message ini
        sendiri pakai old_value, kalau message lain yang sudah lebih dulu
        selesai pakai new_value; kalau belum pernah berubah sampai sini,
        pakai old_value dari perubahan pertama setelahnya; kalau field ini
        tidak pernah tercatat berubah sama sekali, pakai nilai record saat ini.
        """
        self.ensure_one()
        Message = self.env['mail.message'].sudo()
        candidates = Message.search([
            ('model', '=', self.model),
            ('res_id', '=', self.res_id),
            ('tracking_value_ids.field_id.name', '=', field_name),
        ], order='date asc, id asc')

        def tv_for(msg):
            return msg.tracking_value_ids.filtered(lambda t: t.field_id.name == field_name)[:1]

        before = candidates.filtered(lambda m: (m.date, m.id) <= (self.date, self.id))
        if before:
            latest = before[-1]
            tv = tv_for(latest)
            if tv:
                return _tracking_value_text(self.env, tv, new=(latest.id != self.id))

        after = candidates - before
        if after:
            tv = tv_for(after[0])
            if tv:
                return _tracking_value_text(self.env, tv, new=False)

        record = self.env[self.model].browse(self.res_id) if self.model in self.env else None
        if record and record.exists() and field_name in record._fields:
            value = record[field_name]
            field = record._fields[field_name]
            if field.type == 'many2one':
                return value.display_name if value else ''
            if field.type in ('many2many', 'one2many'):
                return ', '.join(value.mapped('display_name')) if value else ''
            if field.type == 'selection':
                sel = dict(field.selection) if isinstance(field.selection, list) else dict(field._description_selection(self.env))
                return sel.get(value, value) if value else ''
            return str(value) if value not in (False, None) else ''
        return ''

    def action_view_snapshot_before(self):
        self.ensure_one()
        tracked = TRACKED_FIELDS_BY_MODEL.get(self.model, [])
        changed_field_names = self.tracking_value_ids.mapped('field_id.name')

        record = self.env[self.model].browse(self.res_id) if self.model in self.env else None
        rows = []
        for f in tracked:
            if record is None or f not in record._fields:
                continue
            label = record._fields[f].string
            value = self._bp_edu_reconstruct_before(f) or '(kosong)'
            rows.append((label, value, f in changed_field_names))

        snapshot_html = self._bp_edu_render_snapshot(rows)

        wizard = self.env['bp.edu.history.snapshot.wizard'].create({
            'model_name': self.model,
            'res_name': record.display_name if record and record.exists() else f'{self.model} #{self.res_id}',
            'changed_at': self.date,
            'changed_by': self.author_id.name or '',
            'snapshot_html': snapshot_html,
        })
        return {
            'type': 'ir.actions.act_window',
            'res_model': 'bp.edu.history.snapshot.wizard',
            'res_id': wizard.id,
            'view_mode': 'form',
            'target': 'new',
        }

    @staticmethod
    def _bp_edu_render_snapshot(rows):
        parts = ['<table class="table table-sm mb-0">']
        for label, value, is_changed in rows:
            style = ' style="background-color:#fff3cd;"' if is_changed else ''
            parts.append(
                f'<tr{style}><td style="width:35%;"><strong>{html.escape(label)}</strong></td>'
                f'<td>{html.escape(value)}</td></tr>'
            )
        parts.append('</table>')
        return Markup(''.join(parts))
