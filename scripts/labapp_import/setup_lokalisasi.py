"""Lokalisasi DB lab baru: Bahasa Indonesia, mata uang IDR, zona waktu WITA.

Dijalankan lewat odoo shell (variabel `env` tersedia), idempotent:

    odoo shell -d lab --no-http < scripts/labapp_import/setup_lokalisasi.py
"""
TZ = 'Asia/Makassar'
LANG = 'id_ID'

lang = env['res.lang'].with_context(active_test=False).search([('code', '=', LANG)], limit=1)
if not lang.active:
    env['base.language.install'].create({'lang_ids': [(6, 0, lang.ids)], 'overwrite': False}).lang_install()

idr = env.ref('base.IDR')
idr.active = True
if env.company.currency_id != idr:
    # aman selama belum ada jurnal/transaksi akuntansi
    env.company.currency_id = idr

env.ref('base.user_admin').write({'lang': LANG, 'tz': TZ})
env.company.partner_id.write({'lang': LANG, 'tz': TZ})
# default untuk partner/user baru (mis. akun portal mahasiswa dari "Buat Akses Portal")
env['ir.default'].set('res.partner', 'tz', TZ)
env['ir.default'].set('res.partner', 'lang', LANG)

env.cr.commit()
print('LOKALISASI', env.company.currency_id.name, env.ref('base.user_admin').lang, env.ref('base.user_admin').tz)
