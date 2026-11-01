from odoo import fields
from odoo.tests import tagged
from odoo.addons.point_of_sale.tests.common import TestPoSCommon


@tagged('post_install', '-at_install')
class TestLabaRugi(TestPoSCommon):

    def test_laba_rugi_bulanan(self):
        self.config = self.basic_config
        product = self.create_product('Canang Sari', self.categ_basic, 10.0, 0)
        self.open_new_session()
        orders = self._create_orders([
            {'pos_order_lines_ui_args': [(product, 5)], 'uuid': 'umkm-1'},
            {'pos_order_lines_ui_args': [(product, 2)], 'uuid': 'umkm-2'},
        ])
        pendapatan = sum(o.amount_total for o in orders.values())
        self.assertTrue(pendapatan)

        Pengeluaran = self.env['umkm.pengeluaran']
        Pengeluaran.create({'kategori': 'bahan', 'name': 'janur', 'amount': 15.0})
        Pengeluaran.create({'kategori': 'transport', 'amount': 5.0})

        self.env.flush_all()
        today = fields.Date.context_today(Pengeluaran.with_context(tz='Asia/Makassar'))
        row = self.env['umkm.laba.rugi'].search([
            ('date', '=', today.replace(day=1)), ('company_id', '=', self.env.company.id),
        ])
        self.assertEqual(len(row), 1)
        self.assertAlmostEqual(row.pendapatan, pendapatan)
        self.assertAlmostEqual(row.pengeluaran, 20.0)
        self.assertAlmostEqual(row.laba, pendapatan - 20.0)
