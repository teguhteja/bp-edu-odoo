from odoo import models, fields, tools


class BpEduLabLaporanPenggunaan(models.Model):
    """Laporan penggunaan bahan: qty per kelompok x jumlah kelompok pada praktikum
    (LaporanController laporan-penggunaan di lab-app)."""
    _name = 'bp.edu.lab.laporan.penggunaan'
    _description = 'Laporan Penggunaan Bahan Praktikum'
    _auto = False
    _order = 'tanggal desc, praktikum_id'

    praktikum_id = fields.Many2one('bp.edu.lab.praktikum', string='Praktikum', readonly=True)
    tanggal = fields.Date(string='Tanggal', readonly=True)
    product_id = fields.Many2one('product.product', string='Barang', readonly=True)
    categ_id = fields.Many2one('product.category', string='Kategori', readonly=True)
    qty_per_kelompok = fields.Float(string='Qty per Kelompok', readonly=True)
    jumlah_kelompok = fields.Integer(string='Jumlah Kelompok', readonly=True)
    total = fields.Float(string='Total Pemakaian', readonly=True)
    stok_sekarang = fields.Float(related='product_id.qty_available', string='Stok Sekarang')

    def init(self):
        tools.drop_view_if_exists(self.env.cr, self._table)
        self.env.cr.execute(f"""
            CREATE OR REPLACE VIEW {self._table} AS (
                SELECT b.id AS id,
                       b.praktikum_id AS praktikum_id,
                       p.tanggal AS tanggal,
                       b.product_id AS product_id,
                       pt.categ_id AS categ_id,
                       b.qty AS qty_per_kelompok,
                       COALESCE(k.jumlah, 0) AS jumlah_kelompok,
                       b.qty * COALESCE(k.jumlah, 0) AS total
                  FROM bp_edu_lab_praktikum_bahan b
                  JOIN bp_edu_lab_praktikum p ON p.id = b.praktikum_id
                  JOIN product_product pp ON pp.id = b.product_id
                  JOIN product_template pt ON pt.id = pp.product_tmpl_id
             LEFT JOIN (SELECT praktikum_id, COUNT(*) AS jumlah
                          FROM bp_edu_lab_kelompok
                      GROUP BY praktikum_id) k ON k.praktikum_id = b.praktikum_id
            )
        """)
