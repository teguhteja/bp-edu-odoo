"""
Extend bp.edu.rps, bp.edu.sap, bp.edu.kontrak.kuliah with action_generate_docx.
Defined here (not in bp_edu_rps) so the reference to bp.edu.wizard.generate
only exists when bp_edu_document is installed.
"""
from odoo import models

_WIZARD = 'bp.edu.wizard.generate'
_ACTION = {
    'type': 'ir.actions.act_window',
    'name': 'Generate DOCX',
    'res_model': _WIZARD,
    'view_mode': 'form',
    'target': 'new',
}


class BpEduRpsGenerateExt(models.Model):
    _inherit = 'bp.edu.rps'

    def action_generate_docx(self):
        self.ensure_one()
        return {**_ACTION, 'context': {
            'default_document_type': 'rps',
            'default_rps_id': self.id,
        }}


class BpEduSapGenerateExt(models.Model):
    _inherit = 'bp.edu.sap'

    def action_generate_docx(self):
        self.ensure_one()
        return {**_ACTION, 'context': {
            'default_document_type': 'sap',
            'default_sap_id': self.id,
        }}


class BpEduKontrakGenerateExt(models.Model):
    _inherit = 'bp.edu.kontrak.kuliah'

    def action_generate_docx(self):
        self.ensure_one()
        return {**_ACTION, 'context': {
            'default_document_type': 'kontrak',
            'default_kontrak_id': self.id,
        }}
