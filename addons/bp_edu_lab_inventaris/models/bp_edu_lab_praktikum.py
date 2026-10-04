from odoo import models, fields


class BpEduLabPraktikum(models.Model):
    _inherit = 'bp.edu.lab.praktikum'

    bahan_ids = fields.One2many('bp.edu.lab.praktikum.bahan', 'praktikum_id', string='Bahan/Alat')


class BpEduLabPraktikumBahan(models.Model):
    """Bahan/alat yang dipakai per kelompok pada satu sesi praktikum (praktikum_detail).
    Seperti lab-app, stok tidak dipotong otomatis; pemakaian dilaporkan di Laporan Penggunaan."""
    _name = 'bp.edu.lab.praktikum.bahan'
    _description = 'Bahan Praktikum'

    praktikum_id = fields.Many2one('bp.edu.lab.praktikum', required=True, ondelete='cascade')
    product_id = fields.Many2one('product.product', string='Barang', required=True,
                                 domain="[('bp_inventaris_lab', '=', True)]")
    uom_id = fields.Many2one(related='product_id.uom_id', string='Satuan')
    qty = fields.Float(string='Jumlah per Kelompok', default=1, digits='Product Unit')
