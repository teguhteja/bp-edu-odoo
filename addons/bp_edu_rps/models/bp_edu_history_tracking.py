"""
Extend bp.edu.rps, bp.edu.sap, bp.edu.kontrak.kuliah dengan riwayat perubahan.

bp.edu.rps pakai sistem SNAPSHOT PENUH: setiap kali record disimpan dengan
field header ATAU salah satu baris child (detail_ids/korelasi_ids/dst)
berubah, sistem otomatis membuat SATU salinan penuh record itu sebagaimana
kondisinya SEBELUM perubahan -- termasuk seluruh baris di semua tab (copy()
Odoo menyalin one2many anak secara default) -- disimpan sebagai record
bp.edu.rps juga (supaya bisa dibuka lewat form aslinya, bp_edu_rps_form_view,
apa adanya), ditandai is_history_snapshot=True + active=False (disembunyikan
dari list biasa lewat mekanisme active bawaan Odoo, tidak perlu ubah domain
pencarian di tempat lain) + snapshot_of_id + snapshot_date + snapshot_by_id.

bp.edu.sap dan bp.edu.kontrak.kuliah masih pakai riwayat per-field lewat
chatter (tracking=True + mail.thread, lihat bp_edu_mail_message_history.py)
-- hanya mencakup field header, belum baris child seperti pertemuan_ids
atau materi_ids.
"""
from odoo import models, fields

from .bp_edu_field_history import TRACKED_FIELDS_BY_MODEL


def _mail_history_count(records):
    MailMessage = records.env['mail.message']
    for rec in records:
        rec.history_count = MailMessage.search_count([
            ('model', '=', records._name),
            ('res_id', '=', rec.id),
            ('tracking_value_ids', '!=', False),
        ])


def _mail_action_view_history(record):
    record.ensure_one()
    return {
        'type': 'ir.actions.act_window',
        'name': 'Riwayat Perubahan',
        'res_model': 'mail.message',
        'view_mode': 'list,form',
        'views': [
            (record.env.ref('bp_edu_rps.bp_edu_history_message_list_view').id, 'list'),
            (record.env.ref('bp_edu_rps.bp_edu_history_message_form_view').id, 'form'),
        ],
        'domain': [
            ('model', '=', record._name),
            ('res_id', '=', record.id),
            ('tracking_value_ids', '!=', False),
        ],
    }


# ── RPS: snapshot penuh ──────────────────────────────────────────────────────

# One2many tab notebook yang perlu disalin manual ke snapshot -- field-field
# ini punya copy=False (default Odoo untuk one2many, supaya "Duplicate" RPS
# biasa tidak diam-diam menggandakan ratusan baris anak), jadi rec.copy()
# TIDAK menyalinnya otomatis. Disalin sendiri lewat _copy_o2m_children().
_RPS_SNAPSHOT_O2M_FIELDS = [
    'detail_ids', 'korelasi_ids', 'korelasi_cpl_ids', 'penilaian_ids',
    'rancangan_tugas_ids', 'rubrik_holistik_ids', 'rubrik_deskriptif_ids',
]

# Field yang memicu snapshot kalau berubah: field header yang dilacak +
# semua one2many tab notebook (isi tabel, bukan cuma field RPS itu sendiri).
_RPS_SNAPSHOT_FIELDS = TRACKED_FIELDS_BY_MODEL['bp.edu.rps'] + _RPS_SNAPSHOT_O2M_FIELDS


def _copy_o2m_children(source, target, o2m_field_names):
    """Salin manual baris one2many dari `source` ke `target` (record model
    sama), karena field-field ini copy=False secara default di Odoo."""
    for field_name in o2m_field_names:
        field = source._fields[field_name]
        inverse = field.inverse_name
        ChildModel = source.env[field.comodel_name]
        for child in source[field_name]:
            vals = child.copy_data()[0]
            vals[inverse] = target.id
            ChildModel.create(vals)


class BpEduRpsTracking(models.Model):
    _inherit = 'bp.edu.rps'

    is_history_snapshot = fields.Boolean(
        string='Snapshot Riwayat', default=False, copy=False, index=True,
    )
    snapshot_of_id = fields.Many2one(
        'bp.edu.rps', string='Snapshot dari', ondelete='cascade', copy=False, index=True,
    )
    snapshot_date = fields.Datetime(string='Waktu Snapshot', copy=False)
    snapshot_by_id = fields.Many2one('res.users', string='Snapshot oleh', copy=False)
    # Field standar Odoo -- snapshot disimpan active=False supaya otomatis
    # tersembunyi dari list/search RPS biasa tanpa perlu ubah domain di
    # tempat lain (mis. json_importer.py, list/kanban/report).
    active = fields.Boolean(default=True)

    history_count = fields.Integer(
        string='Riwayat', compute='_compute_history_count_rps',
    )

    def _compute_history_count_rps(self):
        Rps = self.with_context(active_test=False)
        for rec in self:
            rec.history_count = 0 if rec.is_history_snapshot else Rps.search_count([
                ('snapshot_of_id', '=', rec.id),
            ])

    def _compute_display_name(self):
        super()._compute_display_name()
        for rec in self:
            if rec.is_history_snapshot:
                when = rec.snapshot_date.strftime('%d %b %Y %H:%M') if rec.snapshot_date else ''
                rec.display_name = f'[Riwayat {when}] {rec.display_name}'

    def action_view_history(self):
        self.ensure_one()
        return {
            'type': 'ir.actions.act_window',
            'name': 'Riwayat Perubahan',
            'res_model': 'bp.edu.rps',
            'view_mode': 'list,form',
            'views': [
                (self.env.ref('bp_edu_rps.bp_edu_rps_list_view').id, 'list'),
                (self.env.ref('bp_edu_rps.bp_edu_rps_form_view').id, 'form'),
            ],
            'domain': [('snapshot_of_id', '=', self.id)],
            'context': {'active_test': False},
        }

    def write(self, vals):
        for rec in self:
            if not rec.is_history_snapshot and any(f in vals for f in _RPS_SNAPSHOT_FIELDS):
                snapshot = rec.copy({
                    'is_history_snapshot': True,
                    'snapshot_of_id': rec.id,
                    'snapshot_date': fields.Datetime.now(),
                    'snapshot_by_id': rec.env.uid,
                    'active': False,
                })
                _copy_o2m_children(rec, snapshot, _RPS_SNAPSHOT_O2M_FIELDS)
        return super().write(vals)

    def action_open_live_rps(self):
        """Dari form snapshot, buka RPS aslinya yang masih aktif/berjalan."""
        self.ensure_one()
        target = self.snapshot_of_id
        if not target:
            return
        return {
            'type': 'ir.actions.act_window',
            'res_model': 'bp.edu.rps',
            'res_id': target.id,
            'view_mode': 'form',
            'views': [(self.env.ref('bp_edu_rps.bp_edu_rps_form_view').id, 'form')],
        }


# ── SAP ───────────────────────────────────────────────────────────────────────

_SAP_TRACKED = TRACKED_FIELDS_BY_MODEL['bp.edu.sap']


class BpEduSapTracking(models.Model):
    _inherit = 'bp.edu.sap'

    history_count = fields.Integer(
        string='Riwayat', compute='_compute_history_count_sap',
    )

    def _compute_history_count_sap(self):
        _mail_history_count(self)

    def action_view_history(self):
        return _mail_action_view_history(self)


# ── Kontrak Kuliah ────────────────────────────────────────────────────────────

_KONTRAK_TRACKED = TRACKED_FIELDS_BY_MODEL['bp.edu.kontrak.kuliah']


class BpEduKontrakTracking(models.Model):
    _inherit = 'bp.edu.kontrak.kuliah'

    history_count = fields.Integer(
        string='Riwayat', compute='_compute_history_count_kontrak',
    )

    def _compute_history_count_kontrak(self):
        _mail_history_count(self)

    def action_view_history(self):
        return _mail_action_view_history(self)
