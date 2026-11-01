from odoo import fields, models


class UmkmPengeluaran(models.Model):
    _name = 'umkm.pengeluaran'
    _description = 'Pengeluaran UMKM'
    _order = 'date desc, id desc'

    date = fields.Date(string='Tanggal', required=True, default=fields.Date.context_today)
    kategori = fields.Selection([
        ('bahan', 'Bahan (janur, bunga, dll)'),
        ('transport', 'Transport'),
        ('utilitas', 'Listrik / Air / Pulsa'),
        ('gaji', 'Upah / Gaji'),
        ('lain', 'Lain-lain'),
    ], string='Kategori', required=True, default='bahan')
    name = fields.Char(string='Keterangan')
    amount = fields.Monetary(string='Jumlah', required=True)
    company_id = fields.Many2one('res.company', required=True, default=lambda self: self.env.company)
    currency_id = fields.Many2one(related='company_id.currency_id')

    _amount_positive = models.Constraint('CHECK(amount > 0)', 'Jumlah pengeluaran harus lebih dari 0.')
