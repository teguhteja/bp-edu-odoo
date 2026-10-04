from odoo import api, models, fields, _
from odoo.exceptions import UserError


class BpEduLabStockOpname(models.Model):
    _name = 'bp.edu.lab.stock.opname'
    _description = 'Stock Opname Lab'
    _inherit = ['mail.thread']
    _rec_name = 'kode'
    _order = 'tanggal desc, id desc'

    kode = fields.Char(string='Kode', readonly=True, copy=False, default='/')
    tanggal = fields.Date(string='Tanggal', required=True, default=fields.Date.context_today)
    user_id = fields.Many2one('res.users', string='Petugas', default=lambda self: self.env.user)
    referensi = fields.Char(string='Referensi')
    catatan = fields.Text(string='Catatan')
    state = fields.Selection([
        ('draft', 'Draft'),
        ('selesai', 'Selesai'),
    ], string='Status', default='draft', required=True, tracking=True, copy=False)
    line_ids = fields.One2many('bp.edu.lab.stock.opname.line', 'opname_id', string='Barang')

    @api.model_create_multi
    def create(self, vals_list):
        for vals in vals_list:
            if vals.get('kode', '/') == '/':
                vals['kode'] = self.env['ir.sequence'].next_by_code('bp.edu.lab.stock.opname') or '/'
        return super().create(vals_list)

    def unlink(self):
        if self.filtered(lambda o: o.state != 'draft'):
            raise UserError(_('Stock opname yang sudah divalidasi tidak bisa dihapus.'))
        return super().unlink()

    def action_validasi(self):
        """Timpa stok dengan hasil hitung fisik. Selisih = hitung - sebelum
        (StockOpnameController@store di lab-app)."""
        helper = self.env['bp.edu.lab.stock.helper']
        lokasi = helper._get_lokasi_stok()
        for rec in self:
            if rec.state != 'draft':
                raise UserError(_('Stock opname %s sudah divalidasi.', rec.kode))
            if not rec.line_ids:
                raise UserError(_('Tambahkan minimal satu barang.'))
            for line in rec.line_ids:
                sebelum = helper._qty_di_lokasi(line.product_id, lokasi)
                line.write({'qty_sebelum': sebelum, 'selisih': line.qty_hitung - sebelum})
                helper._set_qty(line.product_id, line.qty_hitung, lokasi)
            rec.state = 'selesai'
        return True


class BpEduLabStockOpnameLine(models.Model):
    _name = 'bp.edu.lab.stock.opname.line'
    _description = 'Baris Stock Opname Lab'

    opname_id = fields.Many2one('bp.edu.lab.stock.opname', required=True, ondelete='cascade')
    kode = fields.Char(related='opname_id.kode', string='Kode SO')
    tanggal = fields.Date(related='opname_id.tanggal', store=True, string='Tanggal')
    state = fields.Selection(related='opname_id.state')
    product_id = fields.Many2one('product.product', string='Barang', required=True,
                                 domain="[('is_storable', '=', True)]")
    uom_id = fields.Many2one(related='product_id.uom_id', string='Satuan')
    qty_sistem = fields.Float(string='Stok Sistem', compute='_compute_qty_sistem', digits='Product Unit')
    qty_sebelum = fields.Float(string='Stok Sebelum', readonly=True, digits='Product Unit')
    qty_hitung = fields.Float(string='Hasil Hitung', digits='Product Unit')
    selisih = fields.Float(string='Selisih', readonly=True, digits='Product Unit')
    stok_sekarang = fields.Float(related='product_id.qty_available', string='Stok Sekarang')

    @api.depends('product_id')
    def _compute_qty_sistem(self):
        helper = self.env['bp.edu.lab.stock.helper']
        lokasi = helper._get_lokasi_stok()
        for line in self:
            line.qty_sistem = helper._qty_di_lokasi(line.product_id, lokasi) if line.product_id else 0
