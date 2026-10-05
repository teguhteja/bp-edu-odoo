"""Ambil screenshot dokumentasi lab-app dengan Playwright (Python, Chromium).

Jalankan terhadap DB salinan yang sudah disiapkan prepare_docs_db.py, BUKAN DB labapp asli,
karena skrip ini menjalankan aksi (presensi, ujian, proses perbaikan, validasi opname/penerimaan).

    $env:LABAPP_DOCS_URL = 'http://localhost:18071'
    $env:LABAPP_PASSWORD = '<password yang sama dengan prepare_docs_db.py>'
    python scripts/labapp_docs/screenshots.py [mhs|dsn|inv ...]
"""
import os
import sys
import tempfile
import xmlrpc.client
from pathlib import Path

from playwright.sync_api import sync_playwright

URL = os.environ.get('LABAPP_DOCS_URL', 'http://localhost:18071')
DB = os.environ.get('LABAPP_DOCS_DB', 'labapp_docs')
PASSWORD = os.environ['LABAPP_PASSWORD']
ADMIN = 'admin@lab.test'
MAHASISWA = 'demo.mahasiswa@lab.test'
OUT = Path(__file__).resolve().parents[2] / 'docs' / 'labapp' / 'img'
VIEWPORT = {'width': 1366, 'height': 768}
GAGAL = []


class Rpc:
    def __init__(self):
        common = xmlrpc.client.ServerProxy(f'{URL}/xmlrpc/2/common')
        self.uid = common.authenticate(DB, ADMIN, PASSWORD, {})
        self.obj = xmlrpc.client.ServerProxy(f'{URL}/xmlrpc/2/object', allow_none=True)

    def __call__(self, model, method, *args, **kw):
        return self.obj.execute_kw(DB, self.uid, PASSWORD, model, method, list(args), kw)

    def first(self, model, domain, order='id'):
        ids = self(model, 'search', domain, limit=1, order=order)
        return ids[0] if ids else False


def tunggu(page, ms=600):
    # backend Odoo memakai koneksi bus yang selalu terbuka, jadi networkidle bisa tidak pernah tercapai
    try:
        page.wait_for_load_state('networkidle', timeout=4000)
    except Exception:
        pass
    page.wait_for_timeout(ms)


def tandai(page, *selectors):
    """Beri bingkai merah pada elemen penting."""
    for sel in selectors:
        loc = page.locator(sel)
        if loc.count():
            loc.first.evaluate("el => { el.style.outline = '3px solid #e53935'; el.style.outlineOffset = '2px'; }")


def shot(page, nama, *highlight, full=False):
    try:
        if not highlight or '.o-dropdown--menu' not in highlight[0]:
            page.mouse.move(VIEWPORT['width'] - 5, VIEWPORT['height'] - 5)  # hindari tooltip hover
            page.wait_for_timeout(200)
        tandai(page, *highlight)
        page.screenshot(path=str(OUT / f'{nama}.png'), full_page=full)
        print('ok  ', nama)
    except Exception as e:  # lanjut ke gambar berikutnya
        GAGAL.append(nama)
        print('GAGAL', nama, e)


def buka(page, path, tunggu_sel='.o_action_manager .o_view_controller'):
    page.goto(URL + path)
    if tunggu_sel:
        page.wait_for_selector(tunggu_sel, timeout=20000)
    tunggu(page)


def login(page, login_name):
    page.goto(f'{URL}/web/login')
    page.fill('input[name=login]', login_name)
    page.fill('input[name=password]', PASSWORD)
    page.click('form.oe_login_form button[type=submit]')
    tunggu(page, 1000)


def act(xmlid, rec_id=None):
    return f'/odoo/action-{xmlid}' + (f'/{rec_id}' if rec_id else '')


# ----------------------------------------------------------------------------
# Mahasiswa (portal)
# ----------------------------------------------------------------------------
def mahasiswa(browser, rpc):
    praktikum_id = rpc.first('bp.edu.lab.praktikum', [('nama', '=', 'Pertemuan 3 - JavaScript Dasar')])
    token = rpc('bp.edu.lab.praktikum', 'read', [praktikum_id], ['token'])[0]['token']
    row = f".o_lab_row[data-praktikum='{praktikum_id}']"

    ctx = browser.new_context(viewport=VIEWPORT, locale='id-ID')
    page = ctx.new_page()

    page.goto(f'{URL}/web/login')
    tunggu(page)
    page.fill('input[name=login]', MAHASISWA)
    shot(page, 'mhs-01-login', 'input[name=login]', 'input[name=password]')
    page.fill('input[name=password]', PASSWORD)
    page.click('form.oe_login_form button[type=submit]')
    tunggu(page, 1000)

    page.goto(f'{URL}/my')
    tunggu(page)
    shot(page, 'mhs-02-portal-home', '#portal_praktikum_category a')

    page.goto(f'{URL}/my/praktikum')
    tunggu(page)
    shot(page, 'mhs-03-daftar-praktikum', full=True)

    page.fill(f'{row} input[name=token]', 'SALAH1')
    shot(page, 'mhs-04-isi-token', f'{row} .o_lab_form_presensi')
    page.click(f'{row} .o_lab_form_presensi button[type=submit]')
    tunggu(page)
    shot(page, 'mhs-05-token-salah', '.o_lab_pesan')

    page.fill(f'{row} input[name=token]', token)
    page.click(f'{row} .o_lab_form_presensi button[type=submit]')
    tunggu(page)
    shot(page, 'mhs-06-presensi-berhasil', '.o_lab_pesan', f'{row} .o_lab_hadir')

    berkas = Path(tempfile.gettempdir()) / 'Laporan_Praktikum_JavaScript.pdf'
    berkas.write_bytes(b'%PDF-1.4\n% contoh laporan praktikum\n%%EOF\n')
    page.set_input_files(f'{row} .o_lab_form_berkas input[type=file]', str(berkas))
    shot(page, 'mhs-07-pilih-berkas', f'{row} .o_lab_form_berkas')
    page.click(f'{row} .o_lab_form_berkas button[type=submit]')
    tunggu(page)
    shot(page, 'mhs-08-berkas-terupload', '.o_lab_pesan', f'{row} .o_lab_berkas_nama')

    shot(page, 'mhs-09-tombol-pretest', f'{row} a.o_lab_ujian_pra')
    page.click(f'{row} a.o_lab_ujian_pra')
    page.wait_for_selector("button:has-text('Start')", timeout=20000)
    tunggu(page)
    shot(page, 'mhs-10-mulai-ujian', "button:has-text('Start')")
    page.click("button:has-text('Start')")
    page.wait_for_selector('.js_question-wrapper', timeout=20000)
    tunggu(page, 1000)
    jawaban = {'tabel': '<table>, dengan baris <tr> dan sel <td>.', 'PHP': '.php',
               'CSS': 'Tampilan halaman web: warna, huruf, dan tata letak.'}
    for wrapper in page.locator('.js_question-wrapper').all():
        teks = wrapper.inner_text()
        isian = next((v for k, v in jawaban.items() if k in teks), 'Jawaban saya.')
        wrapper.locator('textarea, input[type=text]').first.fill(isian)
    shot(page, 'mhs-11-menjawab-soal', full=True)
    page.click("button[value='finish']:not(.disabled)")
    page.wait_for_selector(".modal button.btn-primary:has-text('Submit')", timeout=10000)
    tunggu(page, 400)
    shot(page, 'mhs-12-konfirmasi-submit', ".modal button.btn-primary:has-text('Submit')")
    page.click(".modal button.btn-primary:has-text('Submit')")
    page.wait_for_selector('.o_survey_finished', timeout=20000)
    tunggu(page)
    shot(page, 'mhs-13-ujian-selesai')

    page.goto(f'{URL}/my/praktikum')
    tunggu(page)
    shot(page, 'mhs-14-setelah-ujian', f'{row} a.o_lab_ujian_pra', '.o_lab_row:not([data-praktikum="%s"]) .o_lab_nilai span' % praktikum_id, full=True)

    page.goto(f'{URL}/my/security')
    tunggu(page)
    shot(page, 'mhs-15-ganti-password', 'input[name=new1]', full=True)
    ctx.close()


# ----------------------------------------------------------------------------
# Dosen / laboran (backend)
# ----------------------------------------------------------------------------
def dosen(browser, rpc):
    praktikum_id = rpc.first('bp.edu.lab.praktikum', [('nama', '=', 'Pertemuan 3 - JavaScript Dasar')])
    kelompok_id = rpc.first('bp.edu.lab.kelompok', [('praktikum_id', '=', praktikum_id)])
    mhs_tanpa_akun = rpc.first('bp.edu.mahasiswa', [('user_id', '=', False)])
    kelas_id = rpc.first('bp.edu.kelas', [])
    survey_id = rpc('bp.edu.lab.praktikum', 'read', [praktikum_id], ['pretest_id'])[0]['pretest_id'][0]
    admin_uid = rpc.first('res.users', [('login', '=', ADMIN)])

    ctx = browser.new_context(viewport=VIEWPORT, locale='id-ID')
    page = ctx.new_page()
    login(page, ADMIN)

    page.goto(f'{URL}/odoo')
    page.wait_for_selector('.o_navbar', timeout=20000)
    tunggu(page)
    page.click('.o_navbar_apps_menu button')
    page.wait_for_selector(".o-dropdown--menu .o_app, .o-dropdown--menu a:has-text('Laboratorium')", timeout=5000)
    page.wait_for_timeout(400)
    shot(page, 'dsn-01-menu-aplikasi', ".o-dropdown--menu a:has-text('Laboratorium')")
    page.keyboard.press('Escape')

    buka(page, f'/odoo/action-base.action_res_users/{admin_uid}')
    tab = page.locator(".o_notebook a.nav-link:has-text('Access Rights')")
    if tab.count():
        tab.first.click()
        tunggu(page)
    # baris "Laboratorium" (label + pilihan grup) di tab Access Rights
    page.evaluate("""() => {
        const label = [...document.querySelectorAll('.o_form_view label')]
            .find(l => l.textContent.trim() === 'Laboratorium');
        if (!label) return;
        const row = label.closest('.o_wrap_field') || label.parentElement;
        row.scrollIntoView({block: 'center'});
        row.style.outline = '3px solid #e53935';
        row.style.outlineOffset = '4px';
    }""")
    page.wait_for_timeout(400)
    shot(page, 'dsn-02-hak-akses-user')

    buka(page, act('bp_edu_lab.bp_edu_lab_praktikum_action'))
    shot(page, 'dsn-03-menu-laboratorium', '.o_main_navbar .o_menu_sections')
    page.click(".o_main_navbar .o_menu_sections button:has-text('Mahasiswa')")
    page.wait_for_selector('.o-dropdown--menu', timeout=5000)
    page.wait_for_timeout(400)
    shot(page, 'dsn-04-submenu-mahasiswa', '.o-dropdown--menu')
    page.keyboard.press('Escape')

    buka(page, act('bp_edu_lab.bp_edu_program_studi_action_lab'))
    shot(page, 'dsn-05-program-studi')
    buka(page, act('bp_edu_lab.bp_edu_mata_kuliah_action_lab'))
    shot(page, 'dsn-06-mata-kuliah')
    buka(page, act('bp_edu_lab.bp_edu_kelas_action', kelas_id))
    shot(page, 'dsn-07-kelas-form')
    buka(page, act('bp_edu_lab.bp_edu_mahasiswa_action'))
    shot(page, 'dsn-08-mahasiswa-list')
    buka(page, act('bp_edu_lab.bp_edu_mahasiswa_action', mhs_tanpa_akun))
    shot(page, 'dsn-09-mahasiswa-form', "button[name='action_buat_akses_portal']")

    buka(page, act('bp_edu_lab.survey_survey_action_lab'))
    shot(page, 'dsn-10-ujian-list')
    buka(page, act('bp_edu_lab.survey_survey_action_lab', survey_id))
    shot(page, 'dsn-11-ujian-form', "div[name='jenis_ujian']", "div[name='mata_kuliah_id']")
    buka(page, act('bp_edu_lab.survey_survey_action_lab', survey_id))  # buang bingkai merah sebelumnya
    page.locator(".o_field_widget[name=question_and_page_ids] .o_data_row td[name='title']").first.click()
    page.wait_for_selector('.o_dialog .o_form_view', timeout=10000)
    tunggu(page)
    page.click(".o_dialog .o_notebook a.nav-link:has-text('Kunci Jawaban')")
    page.wait_for_timeout(500)
    shot(page, 'dsn-12-kunci-jawaban', ".o_dialog .o_notebook a.nav-link:has-text('Kunci Jawaban')", ".o_dialog div[name='kunci_jawaban']")
    page.keyboard.press('Escape')
    page.wait_for_timeout(500)

    buka(page, act('bp_edu_lab.bp_edu_lab_praktikum_action'))
    shot(page, 'dsn-13-praktikum-list')
    page.click(".o_switch_view.o_calendar")
    page.wait_for_selector('.o_calendar_renderer', timeout=10000)
    tunggu(page, 1000)
    shot(page, 'dsn-14-praktikum-kalender')
    buka(page, act('bp_edu_lab.bp_edu_lab_praktikum_action') + '/new')
    shot(page, 'dsn-15-praktikum-baru', "div[name='mata_kuliah_id']", "div[name='tanggal']", "div[name='pretest_id']")
    page.goto('about:blank')
    buka(page, act('bp_edu_lab.bp_edu_lab_praktikum_action', praktikum_id))
    page.click("button[name='action_generate_token']")
    tunggu(page)
    shot(page, 'dsn-16-generate-token', "button[name='action_generate_token']", "div[name='token']", "div[name='token_expired_at']")
    page.click(".o_notebook a.nav-link:has-text('Bahan/Alat')")
    page.wait_for_timeout(500)
    shot(page, 'dsn-17-bahan-praktikum', ".o_notebook a.nav-link:has-text('Bahan/Alat')")

    buka(page, act('bp_edu_lab.bp_edu_lab_kelompok_action'))
    shot(page, 'dsn-18-kelompok-list')
    buka(page, act('bp_edu_lab.bp_edu_lab_kelompok_action', kelompok_id))
    shot(page, 'dsn-19-kelompok-form', "button[name='action_tambah_mahasiswa_kelas']", "button[name='action_selesai']")

    buka(page, act('bp_edu_lab.survey_user_input_action_lab'))
    shot(page, 'dsn-20-jawaban-list')
    page.locator('.o_data_row td.o_data_cell').first.click()
    page.wait_for_selector('.o_form_view', timeout=10000)
    tunggu(page)
    shot(page, 'dsn-21-jawaban-detail', full=True)

    buka(page, act('bp_edu_lab.bp_edu_lab_praktikum_action', praktikum_id))
    page.click(".o_form_statusbar button[name='action_buka_penilaian']")
    page.wait_for_selector('.o_list_view .o_data_row', timeout=10000)
    tunggu(page)
    cell = page.locator(".o_data_row:has(td:has-text('Contoh Mahasiswa')) td[name='nilai']")
    cell.click()
    page.wait_for_selector(".o_data_row .o_field_widget[name='nilai'] input", timeout=5000)
    page.fill(".o_data_row .o_field_widget[name='nilai'] input", '88')
    shot(page, 'dsn-22-isi-nilai', ".o_data_row .o_field_widget[name='nilai']", '.o_list_button_save')
    page.click('.o_list_button_save')
    tunggu(page)
    shot(page, 'dsn-23-penilaian', "th[data-name='nilai']", ".o_data_row:has(td:has-text('Contoh Mahasiswa')) button[name='action_lihat_jawaban']")

    buka(page, act('bp_edu_lab.bp_edu_lab_peserta_laporan_nilai_action'))
    shot(page, 'dsn-24-laporan-nilai')
    page.click('.o_switch_view.o_pivot')
    page.wait_for_selector('.o_pivot', timeout=10000)
    tunggu(page)
    shot(page, 'dsn-25-laporan-nilai-pivot')
    buka(page, act('bp_edu_lab.bp_edu_lab_peserta_laporan_absensi_action'))
    shot(page, 'dsn-26-laporan-absensi')
    ctx.close()


# ----------------------------------------------------------------------------
# Inventaris (laboran)
# ----------------------------------------------------------------------------
def inventaris(browser, rpc):
    tmpl_id = rpc.first('product.template', [('default_code', '=', 'INV-001')])
    perbaikan_id = rpc.first('bp.edu.lab.perbaikan', [('state', '=', 'draft')])
    opname_id = rpc.first('bp.edu.lab.stock.opname', [('state', '=', 'draft')])
    po_draft = rpc.first('purchase.order', [('state', '=', 'draft')])
    po_confirm = rpc.first('purchase.order', [('state', '=', 'purchase')], order='id desc')

    ctx = browser.new_context(viewport=VIEWPORT, locale='id-ID')
    page = ctx.new_page()
    login(page, ADMIN)

    buka(page, act('bp_edu_lab_inventaris.product_template_action_lab'))
    shot(page, 'inv-01-barang-list')
    buka(page, act('bp_edu_lab_inventaris.product_template_action_lab', tmpl_id))
    page.click(".o_notebook a.nav-link:has-text('Laboratorium')")
    page.wait_for_timeout(500)
    shot(page, 'inv-02-barang-form', ".o_notebook a.nav-link:has-text('Laboratorium')", "div[name='bp_min_stock']")
    buka(page, act('bp_edu_lab_inventaris.product_template_action_lab_menipis'))
    shot(page, 'inv-03-stok-menipis', '.o_searchview_facet')
    buka(page, act('bp_edu_lab_inventaris.product_category_action_lab'))
    shot(page, 'inv-04-kategori')

    buka(page, act('bp_edu_lab_inventaris.bp_edu_lab_perbaikan_action'))
    shot(page, 'inv-05-perbaikan-list')
    buka(page, act('bp_edu_lab_inventaris.bp_edu_lab_perbaikan_action', perbaikan_id))
    shot(page, 'inv-06-perbaikan-draft', "button[name='action_proses']")
    page.click("button[name='action_proses']")
    tunggu(page)
    shot(page, 'inv-07-perbaikan-proses', "button[name='action_selesai']", '.o_statusbar_status')
    page.click("button[name='action_selesai']")
    tunggu(page)
    shot(page, 'inv-08-perbaikan-selesai', '.o_statusbar_status', "div[name='tanggal_selesai']")

    buka(page, act('bp_edu_lab_inventaris.bp_edu_lab_stock_opname_action'))
    shot(page, 'inv-09-opname-list')
    buka(page, act('bp_edu_lab_inventaris.bp_edu_lab_stock_opname_action', opname_id))
    shot(page, 'inv-10-opname-draft', "button[name='action_validasi']", "th[data-name='qty_hitung']")
    page.click("button[name='action_validasi']")
    tunggu(page)
    shot(page, 'inv-11-opname-selesai', "th[data-name='selisih']")

    buka(page, act('bp_edu_lab_inventaris.res_partner_action_supplier_lab'))
    shot(page, 'inv-12-supplier')
    buka(page, act('purchase.purchase_form_action'))
    shot(page, 'inv-13-po-list')
    buka(page, act('purchase.purchase_form_action') + '/new')
    shot(page, 'inv-14-po-baru', "div[name='partner_id']", '.o_field_widget[name=order_line]')
    page.goto('about:blank')
    buka(page, act('purchase.purchase_form_action', po_draft))
    shot(page, 'inv-15-po-draft', "button[name='button_confirm']")
    buka(page, act('purchase.purchase_form_action', po_confirm))
    shot(page, 'inv-16-po-dikonfirmasi', "button[name='action_view_picking']")
    page.click("button[name='action_view_picking']")
    page.wait_for_selector("button[name='button_validate']", timeout=10000)
    tunggu(page)
    shot(page, 'inv-17-penerimaan', "button[name='button_validate']", "th[data-name='quantity']")
    page.click("button[name='button_validate']")
    tunggu(page, 1000)
    shot(page, 'inv-18-penerimaan-selesai', '.o_statusbar_status')
    buka(page, act('stock.action_picking_tree_incoming'))
    shot(page, 'inv-19-penerimaan-list')

    buka(page, act('bp_edu_lab_inventaris.bp_edu_lab_laporan_penggunaan_action'))
    shot(page, 'inv-20-laporan-penggunaan')
    buka(page, act('bp_edu_lab_inventaris.bp_edu_lab_laporan_pembelian_action'))
    shot(page, 'inv-21-laporan-pembelian')
    buka(page, act('bp_edu_lab_inventaris.bp_edu_lab_laporan_penyesuaian_action'))
    shot(page, 'inv-22-laporan-penyesuaian')
    ctx.close()


def main():
    bagian = sys.argv[1:] or ['mhs', 'dsn', 'inv']
    OUT.mkdir(parents=True, exist_ok=True)
    rpc = Rpc()
    with sync_playwright() as p:
        browser = p.chromium.launch()
        if 'mhs' in bagian:
            mahasiswa(browser, rpc)
        if 'dsn' in bagian:
            dosen(browser, rpc)
        if 'inv' in bagian:
            inventaris(browser, rpc)
        browser.close()
    if GAGAL:
        print('Gagal:', ', '.join(GAGAL))
        sys.exit(1)


if __name__ == '__main__':
    main()
