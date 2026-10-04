from odoo import api, models, _
from odoo.exceptions import UserError


class BpEduLabStockHelper(models.AbstractModel):
    """Utilitas stok bersama untuk perbaikan, stock opname, dan skrip impor lab-app."""
    _name = 'bp.edu.lab.stock.helper'
    _description = 'Utilitas Stok Laboratorium'

    @api.model
    def _get_lokasi_stok(self):
        warehouse = self.env['stock.warehouse'].search(
            [('company_id', '=', self.env.company.id)], limit=1)
        if not warehouse:
            raise UserError(_('Gudang (warehouse) untuk perusahaan ini belum ada.'))
        return warehouse.lot_stock_id

    @api.model
    def _get_lokasi_perbaikan(self):
        """Lokasi virtual "Perbaikan": barang yang sedang diperbaiki keluar dari stok tersedia
        (sama seperti lab-app yang mengurangi qty) dan kembali saat perbaikan selesai."""
        Location = self.env['stock.location'].sudo()
        lokasi = self.env.ref('bp_edu_lab_inventaris.stock_location_perbaikan', raise_if_not_found=False)
        if lokasi:
            return lokasi
        lokasi = Location.create({
            'name': _('Perbaikan Lab'),
            'usage': 'inventory',
            'company_id': False,
        })
        self.env['ir.model.data'].sudo().create({
            'module': 'bp_edu_lab_inventaris',
            'name': 'stock_location_perbaikan',
            'model': 'stock.location',
            'res_id': lokasi.id,
            'noupdate': True,
        })
        return lokasi

    @api.model
    def _qty_di_lokasi(self, product, lokasi):
        return product.with_context(location=lokasi.id).qty_available

    @api.model
    def _pindah_stok(self, product, qty, lokasi_asal, lokasi_tujuan, origin):
        """Buat dan selesaikan satu stock.move (riwayat tercatat di Moves Analysis)."""
        if qty <= 0:
            return self.env['stock.move']
        move = self.env['stock.move'].sudo().create({
            'product_id': product.id,
            'product_uom_qty': qty,
            'product_uom': product.uom_id.id,
            'location_id': lokasi_asal.id,
            'location_dest_id': lokasi_tujuan.id,
            'origin': origin,
        })
        move._action_confirm()
        move._action_assign()
        move.quantity = qty
        move.picked = True
        move._action_done()
        return move

    @api.model
    def _set_qty(self, product, qty, lokasi=None):
        """Timpa qty produk di lokasi stok (inventory adjustment), seperti Inventaris::updateQty."""
        lokasi = lokasi or self._get_lokasi_stok()
        quant = self.env['stock.quant'].sudo().with_context(inventory_mode=True).create({
            'product_id': product.id,
            'location_id': lokasi.id,
            'inventory_quantity': qty,
        })
        quant._apply_inventory()
        return quant
