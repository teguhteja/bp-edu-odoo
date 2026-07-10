from odoo.tests.common import TransactionCase, tagged


@tagged('post_install', '-at_install')
class TestFlowBuilder(TransactionCase):

    def setUp(self):
        super().setUp()
        self.partner = self.env['res.partner'].create({'name': 'Flow Test Co'})
        self.product = self.env['product.product'].create({
            'name': 'Flow Test Product', 'type': 'consu', 'list_price': 100.0,
        })
        self.so = self.env['sale.order'].create({
            'partner_id': self.partner.id,
            'order_line': [(0, 0, {'product_id': self.product.id, 'product_uom_qty': 1})],
        })

    def test_anchor_node_present(self):
        graph = self.env['transaction.flow.builder'].get_flow_graph('sale.order', self.so.id)
        node_keys = {n['id'] for n in graph['nodes']}
        self.assertIn('sale.order,%s' % self.so.id, node_keys)
        anchor = next(n for n in graph['nodes'] if n['id'] == 'sale.order,%s' % self.so.id)
        self.assertEqual(anchor['model'], 'sale.order')
        self.assertEqual(anchor['res_id'], self.so.id)
        self.assertFalse(graph['truncated'])

    def test_so_neighbors_include_delivery(self):
        self.so.action_confirm()
        graph = self.env['transaction.flow.builder'].get_flow_graph('sale.order', self.so.id)
        models_in_graph = {n['model'] for n in graph['nodes']}
        self.assertIn('stock.picking', models_in_graph)
        node_ids = {n['id'] for n in graph['nodes']}
        for e in graph['edges']:
            self.assertIn(e['from'], node_ids)
            self.assertIn(e['to'], node_ids)

    def test_graph_connects_so_to_invoice(self):
        self.so.action_confirm()
        inv = self.so._create_invoices()
        inv.action_post()
        graph = self.env['transaction.flow.builder'].get_flow_graph('sale.order', self.so.id)
        ids = {n['id'] for n in graph['nodes']}
        self.assertIn('account.move,%s' % inv.id, ids)
        self.assertTrue(any(
            'sale.order,%s' % self.so.id in (e['from'], e['to']) and
            'account.move,%s' % inv.id in (e['from'], e['to'])
            for e in graph['edges']
        ))

    def test_node_cap_sets_truncated(self):
        graph = self.env['transaction.flow.builder'].get_flow_graph(
            'sale.order', self.so.id, max_nodes=1)
        self.assertTrue(graph['truncated'])
        self.assertLessEqual(len(graph['nodes']), 1)
