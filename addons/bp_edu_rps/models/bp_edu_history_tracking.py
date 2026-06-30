"""
Extend bp.edu.rps, bp.edu.sap, bp.edu.kontrak.kuliah dengan:
  - write() override untuk mencatat setiap perubahan field
  - history_count computed field untuk smart button
  - action_view_history untuk membuka daftar riwayat
"""
from odoo import models, fields


# ── Helper ────────────────────────────────────────────────────────────────────

def _display_value(record, field_name):
    """Kembalikan nilai field dalam bentuk string yang mudah dibaca manusia."""
    field = record._fields[field_name]
    value = record[field_name]

    if field.type == 'many2one':
        return value.display_name if value else ''

    if field.type == 'selection':
        if isinstance(field.selection, list):
            sel = dict(field.selection)
        else:
            sel = dict(field._description_selection(record.env))
        return sel.get(value, str(value)) if value is not False else ''

    if field.type == 'boolean':
        return 'Ya' if value else 'Tidak'

    if field.type in ('date', 'datetime'):
        return str(value) if value else ''

    if field.type in ('integer', 'float'):
        return str(value) if value is not False else ''

    return str(value) if value else ''


def _track_and_write(records, vals, tracked_fields):
    """
    Snapshot nilai lama → write → bandingkan → buat history records.
    Dipanggil oleh write() di setiap model.
    """
    fields_in_vals = [f for f in tracked_fields if f in vals]

    # Snapshot nilai lama per record sebelum write
    snapshots = {}
    if fields_in_vals:
        for rec in records:
            snapshots[rec.id] = {f: _display_value(rec, f) for f in fields_in_vals}

    result = super(type(records), records).write(vals)

    # Catat perubahan
    if snapshots:
        history_vals = []
        for rec in records:
            for f in fields_in_vals:
                old_val = snapshots[rec.id][f]
                new_val = _display_value(rec, f)
                if old_val != new_val:
                    history_vals.append({
                        'model_name': records._name,
                        'res_id': rec.id,
                        'res_name': rec.display_name,
                        'field_name': f,
                        'field_label': records._fields[f].string,
                        'old_value': old_val or '(kosong)',
                        'new_value': new_val or '(kosong)',
                        'changed_by': records.env.user.id,
                    })
        if history_vals:
            records.env['bp.edu.field.history'].sudo().create(history_vals)

    return result


def _history_count(records):
    History = records.env['bp.edu.field.history']
    for rec in records:
        rec.history_count = History.search_count([
            ('model_name', '=', records._name),
            ('res_id', '=', rec.id),
        ])


def _action_view_history(record):
    record.ensure_one()
    return {
        'type': 'ir.actions.act_window',
        'name': 'Riwayat Perubahan',
        'res_model': 'bp.edu.field.history',
        'view_mode': 'list,form',
        'domain': [
            ('model_name', '=', record._name),
            ('res_id', '=', record.id),
        ],
        'context': {'search_default_group_date': 1},
    }


# ── RPS ───────────────────────────────────────────────────────────────────────

_RPS_TRACKED = [
    'mata_kuliah_id', 'dosen_id', 'tahun_akademik_id',
    'tanggal_penyusunan', 'state',
]


class BpEduRpsTracking(models.Model):
    _inherit = 'bp.edu.rps'

    history_count = fields.Integer(
        string='Riwayat', compute='_compute_history_count_rps',
    )

    def _compute_history_count_rps(self):
        _history_count(self)

    def action_view_history(self):
        return _action_view_history(self)

    def write(self, vals):
        return _track_and_write(self, vals, _RPS_TRACKED)


# ── SAP ───────────────────────────────────────────────────────────────────────

_SAP_TRACKED = [
    'mata_kuliah_id', 'dosen_id', 'tahun_akademik_id', 'rps_id',
]


class BpEduSapTracking(models.Model):
    _inherit = 'bp.edu.sap'

    history_count = fields.Integer(
        string='Riwayat', compute='_compute_history_count_sap',
    )

    def _compute_history_count_sap(self):
        _history_count(self)

    def action_view_history(self):
        return _action_view_history(self)

    def write(self, vals):
        return _track_and_write(self, vals, _SAP_TRACKED)


# ── Kontrak Kuliah ────────────────────────────────────────────────────────────

_KONTRAK_TRACKED = [
    'mata_kuliah_id', 'dosen_id', 'tahun_akademik_id',
    'periode', 'kelas', 'hari_jam', 'jenis_mk', 'prasyarat',
    'bobot_diskusi', 'bobot_proyek', 'bobot_tugas',
    'bobot_kuis', 'bobot_uts', 'bobot_uas',
    'jumlah_kuis_mingguan', 'jumlah_tugas_terstruktur', 'jumlah_proyek',
    'wakil_mahasiswa', 'nim_wakil',
]


class BpEduKontrakTracking(models.Model):
    _inherit = 'bp.edu.kontrak.kuliah'

    history_count = fields.Integer(
        string='Riwayat', compute='_compute_history_count_kontrak',
    )

    def _compute_history_count_kontrak(self):
        _history_count(self)

    def action_view_history(self):
        return _action_view_history(self)

    def write(self, vals):
        return _track_and_write(self, vals, _KONTRAK_TRACKED)
