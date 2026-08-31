from odoo import models, fields


class BpEduMataKuliahGdriveLink(models.Model):
    _name = 'bp.edu.mata.kuliah.gdrive.link'
    _description = 'Link Google Drive Buku Ajar'
    _order = 'sequence, id'

    sequence = fields.Integer(default=10)
    mata_kuliah_id = fields.Many2one(
        'bp.edu.mata.kuliah', string='Mata Kuliah',
        required=True, ondelete='cascade',
    )
    name = fields.Char(string='Judul', required=True)
    url = fields.Char(string='Link Google Drive', required=True)
