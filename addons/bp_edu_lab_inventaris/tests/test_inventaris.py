from odoo.exceptions import UserError
from odoo.tests import HttpCase, new_test_user, tagged
from odoo.tests.common import TransactionCase

from odoo.addons.bp_edu_lab.tests.common import LabDataMixin


class InventarisMixin(LabDataMixin):

    @classmethod
    def _setup_inventaris(cls):
        cls._setup_lab_data()
        env = cls.env
        cls.helper = env['bp.edu.lab.stock.helper']
        cls.lokasi = cls.helper._get_lokasi_stok()
        cls.kategori = env['product.category'].create({'name': 'Perangkat Keras Tes'})
        cls.laptop = env['product.product'].create({
            'name': 'Laptop Tes', 'default_code': 'INV-T01', 'type': 'consu', 'is_storable': True,
            'categ_id': cls.kategori.id, 'bp_inventaris_lab': True, 'bp_reusable': True, 'bp_min_stock': 5,
        })
        cls.kertas = env['product.product'].create({
            'name': 'Kertas Tes', 'default_code': 'INV-T02', 'type': 'consu', 'is_storable': True,
            'categ_id': cls.kategori.id, 'bp_inventaris_lab': True, 'bp_min_stock': 2,
        })
        cls.helper._set_qty(cls.laptop, 10, cls.lokasi)
        cls.helper._set_qty(cls.kertas, 1, cls.lokasi)
        cls.supplier = env['res.partner'].create({'name': 'CV Supplier Tes', 'supplier_rank': 1, 'is_company': True})

    def qty(self, product):
        return self.helper._qty_di_lokasi(product, self.lokasi)


@tagged('post_install', '-at_install')
class TestInventaris(InventarisMixin, TransactionCase):
    """Port dari lab-app tests/Feature/PerbaikanInventarisTest.php + alur PO/receiving/opname."""

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls._setup_inventaris()

    def _perbaikan(self, qty):
        return self.env['bp.edu.lab.perbaikan'].create({'product_id': self.laptop.id, 'qty': qty,
                                                       'keterangan': 'Layar retak'})

    def test_perbaikan_mengurangi_lalu_mengembalikan_stok(self):
        perbaikan = self._perbaikan(3)
        self.assertTrue(perbaikan.kode.startswith('RP-'))
        perbaikan.action_proses()
        self.assertEqual(perbaikan.state, 'proses')
        self.assertEqual(self.qty(self.laptop), 7)
        self.assertEqual(self.laptop.qty_available, 7, 'lokasi Perbaikan tidak dihitung sebagai stok tersedia')

        perbaikan.action_selesai()
        self.assertEqual(perbaikan.state, 'selesai')
        self.assertTrue(perbaikan.tanggal_selesai)
        self.assertEqual(self.qty(self.laptop), 10)
        self.assertEqual(len(perbaikan.move_ids), 2)

    def test_perbaikan_melebihi_stok_ditolak(self):
        perbaikan = self._perbaikan(11)
        with self.assertRaisesRegex(UserError, 'melebihi stok'):
            perbaikan.action_proses()
        self.assertEqual(self.qty(self.laptop), 10)

    def test_perbaikan_selesai_dua_kali_ditolak(self):
        perbaikan = self._perbaikan(1)
        perbaikan.action_proses()
        perbaikan.action_selesai()
        with self.assertRaisesRegex(UserError, 'sudah ditandai selesai'):
            perbaikan.action_selesai()
        self.assertEqual(self.qty(self.laptop), 10)

    def test_stok_menipis(self):
        self.assertFalse(self.laptop.bp_stok_menipis)
        self.assertTrue(self.kertas.bp_stok_menipis)
        Template = self.env['product.template']
        menipis = Template.search([('bp_stok_menipis', '=', True)])
        self.assertIn(self.kertas.product_tmpl_id, menipis)
        self.assertNotIn(self.laptop.product_tmpl_id, menipis)
        self.assertIn(self.laptop.product_tmpl_id, Template.search([('bp_stok_menipis', '=', False)]))
        # perbaikan bisa membuat stok menjadi menipis
        self._perbaikan(6).action_proses()
        self.laptop.invalidate_recordset()
        self.assertTrue(self.laptop.bp_stok_menipis)

    def test_po_dan_penerimaan_menambah_stok(self):
        po = self.env['purchase.order'].create({
            'partner_id': self.supplier.id,
            'order_line': [(0, 0, {'product_id': self.kertas.id, 'product_qty': 20, 'price_unit': 50000})],
        })
        self.assertTrue(po.name.startswith('PO-'), 'kode PO mengikuti format lab-app PO-YYMMDD-NNN')
        po.button_confirm()
        self.assertEqual(po.receipt_status, 'pending')
        picking = po.picking_ids
        picking.move_ids.quantity = 20
        picking.move_ids.picked = True
        picking.button_validate()
        self.assertEqual(picking.state, 'done')
        self.assertEqual(po.receipt_status, 'full')
        self.assertEqual(self.qty(self.kertas), 21)
        self.kertas.invalidate_recordset()
        self.assertFalse(self.kertas.bp_stok_menipis)

    def test_stock_opname_menimpa_stok(self):
        opname = self.env['bp.edu.lab.stock.opname'].create({
            'referensi': 'SO-REF-T',
            'line_ids': [(0, 0, {'product_id': self.laptop.id, 'qty_hitung': 8}),
                         (0, 0, {'product_id': self.kertas.id, 'qty_hitung': 4})],
        })
        self.assertTrue(opname.kode.startswith('SO-'))
        self.assertEqual(opname.line_ids[0].qty_sistem, 10)
        opname.action_validasi()
        self.assertEqual(opname.state, 'selesai')
        baris = {l.product_id: l for l in opname.line_ids}
        self.assertEqual((baris[self.laptop].qty_sebelum, baris[self.laptop].selisih), (10, -2))
        self.assertEqual((baris[self.kertas].qty_sebelum, baris[self.kertas].selisih), (1, 3))
        self.assertEqual(self.qty(self.laptop), 8)
        self.assertEqual(self.qty(self.kertas), 4)
        with self.assertRaisesRegex(UserError, 'sudah divalidasi'):
            opname.action_validasi()

    def test_hapus_kategori_berbarang(self):
        with self.assertRaisesRegex(UserError, 'masih digunakan oleh barang'):
            self.kategori.unlink()

    def test_laporan_penggunaan(self):
        self.praktikum.bahan_ids = [(0, 0, {'product_id': self.kertas.id, 'qty': 3})]
        self.env['bp.edu.lab.kelompok'].create({'nama': 'Kelompok 2', 'praktikum_id': self.praktikum.id})
        self.env.flush_all()
        baris = self.env['bp.edu.lab.laporan.penggunaan'].search([('praktikum_id', '=', self.praktikum.id)])
        self.assertEqual(len(baris), 1)
        self.assertEqual((baris.jumlah_kelompok, baris.total), (2, 6))
        self.assertEqual(baris.categ_id, self.kategori)


@tagged('post_install', '-at_install')
class TestTourInventaris(InventarisMixin, HttpCase):

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls._setup_inventaris()
        new_test_user(cls.env, login='laboran_inv', groups='bp_edu_lab.group_lab_admin', name='Laboran Inventaris')

    def test_tour_perbaikan(self):
        """E2E: laboran melihat barang lalu memproses perbaikan; stok berkurang."""
        self.start_tour('/odoo/action-bp_edu_lab_inventaris.bp_edu_lab_perbaikan_action',
                        'bp_edu_lab_inventaris_tour', login='laboran_inv')
        perbaikan = self.env['bp.edu.lab.perbaikan'].search([('product_id', '=', self.laptop.id)])
        self.assertEqual(perbaikan.state, 'proses')
        self.assertEqual(perbaikan.qty, 2)
        self.assertEqual(self.qty(self.laptop), 8)
