from odoo import api, models, fields, _
from odoo.exceptions import UserError


class ProductTemplate(models.Model):
    _inherit = 'product.template'

    bp_inventaris_lab = fields.Boolean(string='Inventaris Lab', index=True,
                                       help='Barang yang dikelola laboratorium.')
    bp_reusable = fields.Boolean(string='Dapat Dipakai Ulang',
                                 help='Centang untuk alat (reusable); kosongkan untuk bahan habis pakai.')
    bp_min_stock = fields.Float(string='Stok Minimum', digits='Product Unit')
    bp_expiry_date = fields.Date(string='Tanggal Kedaluwarsa')
    bp_stok_menipis = fields.Boolean(string='Stok Menipis', compute='_compute_bp_stok_menipis',
                                     search='_search_bp_stok_menipis')
    bp_perbaikan_ids = fields.One2many('bp.edu.lab.perbaikan', 'product_tmpl_id', string='Riwayat Perbaikan')

    @api.depends('qty_available', 'bp_min_stock')
    def _compute_bp_stok_menipis(self):
        for rec in self:
            rec.bp_stok_menipis = rec.bp_min_stock > 0 and rec.qty_available <= rec.bp_min_stock

    def _search_bp_stok_menipis(self, operator, value):
        if operator not in ('=', '!=') or not isinstance(value, bool):
            raise UserError(_('Operasi pencarian tidak didukung.'))
        kandidat = self.search([('bp_min_stock', '>', 0), ('is_storable', '=', True)])
        menipis = kandidat.filtered('bp_stok_menipis')
        positif = (operator == '=') == value
        return [('id', 'in' if positif else 'not in', menipis.ids)]


class ProductCategory(models.Model):
    _inherit = 'product.category'

    def unlink(self):
        if self.env['product.template'].with_context(active_test=False).search_count(
                [('categ_id', 'in', self.ids)]):
            raise UserError(_('Kategori masih digunakan oleh barang, tidak bisa dihapus.'))
        return super().unlink()
