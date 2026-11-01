from odoo import fields, models, tools


class UmkmLabaRugi(models.Model):
    _name = 'umkm.laba.rugi'
    _description = 'Laporan Laba Rugi Bulanan'
    _auto = False
    _order = 'date desc'

    date = fields.Date(string='Bulan', readonly=True)
    company_id = fields.Many2one('res.company', readonly=True)
    currency_id = fields.Many2one(related='company_id.currency_id')
    pendapatan = fields.Monetary(readonly=True)
    pengeluaran = fields.Monetary(readonly=True)
    laba = fields.Monetary(string='Laba / Rugi', readonly=True)

    def init(self):
        tools.drop_view_if_exists(self.env.cr, self._table)
        # ponytail: month boundary fixed to Asia/Makassar (WITA, Bali); use company/user tz if tenants span zones
        self.env.cr.execute(f"""
            CREATE VIEW {self._table} AS (
                SELECT row_number() OVER () AS id, bulan AS date, company_id,
                       SUM(pendapatan) AS pendapatan,
                       SUM(pengeluaran) AS pengeluaran,
                       SUM(pendapatan) - SUM(pengeluaran) AS laba
                FROM (
                    SELECT date_trunc('month', date_order AT TIME ZONE 'UTC' AT TIME ZONE 'Asia/Makassar')::date AS bulan,
                           company_id, amount_total AS pendapatan, 0 AS pengeluaran
                      FROM pos_order
                     WHERE state IN ('paid', 'done')
                    UNION ALL
                    SELECT date_trunc('month', date)::date, company_id, 0, amount
                      FROM umkm_pengeluaran
                ) t
                GROUP BY bulan, company_id
            )
        """)
