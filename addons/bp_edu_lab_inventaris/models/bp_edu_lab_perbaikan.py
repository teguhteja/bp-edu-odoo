from odoo import api, models, fields, _
from odoo.exceptions import UserError


class BpEduLabPerbaikan(models.Model):
    _name = 'bp.edu.lab.perbaikan'
    _description = 'Perbaikan Inventaris Lab'
    _inherit = ['mail.thread']
    _rec_name = 'kode'
    _order = 'tanggal desc, id desc'

    kode = fields.Char(string='Kode', readonly=True, copy=False, default='/')
    product_id = fields.Many2one('product.product', string='Barang', required=True,
                                 domain="[('is_storable', '=', True)]", tracking=True)
    product_tmpl_id = fields.Many2one(related='product_id.product_tmpl_id', store=True)
    uom_id = fields.Many2one(related='product_id.uom_id', string='Satuan')
    tanggal = fields.Date(string='Tanggal Perbaikan', required=True, default=fields.Date.context_today)
    qty = fields.Float(string='Jumlah Rusak', required=True, default=1, digits='Product Unit')
    keterangan = fields.Text(string='Keterangan')
    state = fields.Selection([
        ('draft', 'Draft'),
        ('proses', 'Proses'),
        ('selesai', 'Selesai'),
    ], string='Status', default='draft', required=True, tracking=True, copy=False)
    tanggal_selesai = fields.Date(string='Tanggal Selesai', readonly=True, copy=False)
    move_ids = fields.Many2many('stock.move', string='Pergerakan Stok', readonly=True, copy=False)

    _qty_positif = models.Constraint('CHECK(qty >= 1)', 'Jumlah rusak minimal 1.')

    @api.model_create_multi
    def create(self, vals_list):
        for vals in vals_list:
            if vals.get('kode', '/') == '/':
                vals['kode'] = self.env['ir.sequence'].next_by_code('bp.edu.lab.perbaikan') or '/'
        return super().create(vals_list)

    def unlink(self):
        if self.filtered(lambda p: p.state != 'draft'):
            raise UserError(_('Hanya perbaikan berstatus draft yang bisa dihapus.'))
        return super().unlink()

    def action_proses(self):
        """Barang rusak keluar dari stok tersedia ke lokasi Perbaikan (PerbaikanController@store)."""
        helper = self.env['bp.edu.lab.stock.helper']
        lokasi_stok = helper._get_lokasi_stok()
        lokasi_perbaikan = helper._get_lokasi_perbaikan()
        for rec in self:
            if rec.state != 'draft':
                raise UserError(_('Perbaikan %s sudah diproses.', rec.kode))
            tersedia = helper._qty_di_lokasi(rec.product_id, lokasi_stok)
            if rec.qty > tersedia:
                raise UserError(_('Jumlah rusak (%(qty)s) melebihi stok tersedia (%(stok)s).',
                                  qty=rec.qty, stok=tersedia))
            move = helper._pindah_stok(rec.product_id, rec.qty, lokasi_stok, lokasi_perbaikan, rec.kode)
            rec.write({'state': 'proses', 'move_ids': [(4, move.id)]})
        return True

    def action_selesai(self):
        """Perbaikan selesai: barang kembali ke stok (PerbaikanController@selesai)."""
        helper = self.env['bp.edu.lab.stock.helper']
        lokasi_stok = helper._get_lokasi_stok()
        lokasi_perbaikan = helper._get_lokasi_perbaikan()
        for rec in self:
            if rec.state == 'selesai':
                raise UserError(_('Perbaikan ini sudah ditandai selesai.'))
            if rec.state != 'proses':
                raise UserError(_('Perbaikan harus diproses terlebih dahulu.'))
            move = helper._pindah_stok(rec.product_id, rec.qty, lokasi_perbaikan, lokasi_stok, rec.kode)
            rec.write({
                'state': 'selesai',
                'tanggal_selesai': fields.Date.context_today(rec),
                'move_ids': [(4, move.id)],
            })
        return True
