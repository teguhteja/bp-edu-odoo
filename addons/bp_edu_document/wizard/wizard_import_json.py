"""
Wizard Import JSON — upload file JSON rps_bp dan simpan ke model Odoo.
Auto-detect tipe: RPS, SAP, atau Kontrak Kuliah.
"""
import base64
import json
import logging

from odoo import models, fields
from odoo.exceptions import UserError

_logger = logging.getLogger(__name__)


class BpEduWizardImportJson(models.TransientModel):
    _name = 'bp.edu.wizard.import.json'
    _description = 'Wizard Import JSON'

    json_file = fields.Binary(string='File JSON', required=True, attachment=False)
    json_filename = fields.Char(string='Nama File')

    # Preview setelah parse
    detected_type = fields.Char(string='Tipe Terdeteksi', readonly=True)
    detected_mk = fields.Char(string='Mata Kuliah', readonly=True)
    state = fields.Selection([
        ('upload', 'Upload'),
        ('preview', 'Preview'),
        ('done', 'Selesai'),
    ], default='upload')

    # Hasil import
    result_summary = fields.Text(string='Hasil Import', readonly=True)
    rps_id = fields.Many2one('bp.edu.rps', string='RPS Dibuat', readonly=True)
    sap_id = fields.Many2one('bp.edu.sap', string='SAP Dibuat', readonly=True)
    kontrak_id = fields.Many2one('bp.edu.kontrak.kuliah', string='Kontrak Dibuat', readonly=True)

    def action_preview(self):
        """Parse JSON dan tampilkan preview sebelum import."""
        self.ensure_one()
        if not self.json_file:
            raise UserError('Upload file JSON terlebih dahulu.')

        try:
            content = base64.b64decode(self.json_file).decode('utf-8')
            data = json.loads(content)
        except Exception as e:
            raise UserError(f'File JSON tidak valid: {e}')

        from ..utils.json_importer import detect_type
        doc_type = detect_type(data)

        type_label = {'rps': 'RPS', 'sap': 'SAP', 'kontrak': 'Kontrak Kuliah'}.get(doc_type, 'Tidak Dikenali')

        # Deteksi nama MK
        meta = data.get('meta', {})
        nama_mk = (
            meta.get('nama_mk') or data.get('nama_mk') or '?'
        )
        kode_mk = meta.get('kode_mk', '')
        mk_label = f'[{kode_mk}] {nama_mk}' if kode_mk else nama_mk

        self.write({
            'detected_type': type_label,
            'detected_mk': mk_label,
            'state': 'preview',
        })
        return {
            'type': 'ir.actions.act_window',
            'res_model': self._name,
            'res_id': self.id,
            'view_mode': 'form',
            'target': 'new',
        }

    def action_import(self):
        """Jalankan import ke Odoo models."""
        self.ensure_one()
        try:
            content = base64.b64decode(self.json_file).decode('utf-8')
            data = json.loads(content)
        except Exception as e:
            raise UserError(f'File JSON tidak valid: {e}')

        from ..utils.json_importer import import_json
        try:
            result = import_json(self.env, data)
        except ValueError as e:
            raise UserError(str(e))
        except Exception as e:
            _logger.exception('Import JSON gagal')
            raise UserError(f'Import gagal: {e}')

        doc_type = result.get('type', '')
        summary_parts = [f'Tipe: {doc_type.upper()}']

        write_vals = {'state': 'done'}

        if doc_type == 'rps':
            rps = self.env['bp.edu.rps'].browse(result['rps_id'])
            mk = self.env['bp.edu.mata.kuliah'].browse(result['mk_id'])
            summary_parts += [
                f'Mata Kuliah: {mk.display_name}',
                f'RPS ID: {rps.id}',
                f'Detail: {len(rps.detail_ids)} minggu',
            ]
            write_vals['rps_id'] = rps.id
        elif doc_type == 'sap':
            sap = self.env['bp.edu.sap'].browse(result['sap_id'])
            mk = self.env['bp.edu.mata.kuliah'].browse(result['mk_id'])
            summary_parts += [
                f'Mata Kuliah: {mk.display_name}',
                f'SAP ID: {sap.id}',
                f'Pertemuan: {len(sap.pertemuan_ids)}',
            ]
            write_vals['sap_id'] = sap.id
        elif doc_type == 'kontrak':
            kontrak = self.env['bp.edu.kontrak.kuliah'].browse(result['kontrak_id'])
            mk = self.env['bp.edu.mata.kuliah'].browse(result['mk_id'])
            summary_parts += [
                f'Mata Kuliah: {mk.display_name}',
                f'Kontrak ID: {kontrak.id}',
            ]
            write_vals['kontrak_id'] = kontrak.id

        write_vals['result_summary'] = '\n'.join(summary_parts)
        self.write(write_vals)

        return {
            'type': 'ir.actions.act_window',
            'res_model': self._name,
            'res_id': self.id,
            'view_mode': 'form',
            'target': 'new',
        }

    def action_open_result(self):
        """Buka record hasil import."""
        self.ensure_one()
        if self.rps_id:
            return {
                'type': 'ir.actions.act_window',
                'res_model': 'bp.edu.rps',
                'res_id': self.rps_id.id,
                'view_mode': 'form',
            }
        if self.sap_id:
            return {
                'type': 'ir.actions.act_window',
                'res_model': 'bp.edu.sap',
                'res_id': self.sap_id.id,
                'view_mode': 'form',
            }
        if self.kontrak_id:
            return {
                'type': 'ir.actions.act_window',
                'res_model': 'bp.edu.kontrak.kuliah',
                'res_id': self.kontrak_id.id,
                'view_mode': 'form',
            }
