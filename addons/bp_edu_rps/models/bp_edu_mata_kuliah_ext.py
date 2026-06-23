from odoo import models, fields, api


class BpEduMataKuliahRpsExt(models.Model):
    """Extend Mata Kuliah dengan count fields untuk RPS, SAP, dan Kontrak."""
    _inherit = 'bp.edu.mata.kuliah'

    rps_count = fields.Integer(string='Jumlah RPS', compute='_compute_doc_counts')
    sap_count = fields.Integer(string='Jumlah SAP', compute='_compute_doc_counts')
    kontrak_count = fields.Integer(string='Jumlah Kontrak', compute='_compute_doc_counts')

    def _compute_doc_counts(self):
        RPS = self.env['bp.edu.rps']
        SAP = self.env['bp.edu.sap']
        Kontrak = self.env['bp.edu.kontrak.kuliah']
        for rec in self:
            rec.rps_count = RPS.search_count([('mata_kuliah_id', '=', rec.id)])
            rec.sap_count = SAP.search_count([('mata_kuliah_id', '=', rec.id)])
            rec.kontrak_count = Kontrak.search_count([('mata_kuliah_id', '=', rec.id)])

    def action_view_rps(self):
        return {
            'type': 'ir.actions.act_window',
            'name': f'RPS – {self.nama}',
            'res_model': 'bp.edu.rps',
            'view_mode': 'list,form',
            'domain': [('mata_kuliah_id', '=', self.id)],
            'context': {'default_mata_kuliah_id': self.id},
        }

    def action_view_sap(self):
        return {
            'type': 'ir.actions.act_window',
            'name': f'SAP – {self.nama}',
            'res_model': 'bp.edu.sap',
            'view_mode': 'list,form',
            'domain': [('mata_kuliah_id', '=', self.id)],
            'context': {'default_mata_kuliah_id': self.id},
        }

    def action_view_kontrak(self):
        return {
            'type': 'ir.actions.act_window',
            'name': f'Kontrak Kuliah – {self.nama}',
            'res_model': 'bp.edu.kontrak.kuliah',
            'view_mode': 'list,form',
            'domain': [('mata_kuliah_id', '=', self.id)],
            'context': {'default_mata_kuliah_id': self.id},
        }
