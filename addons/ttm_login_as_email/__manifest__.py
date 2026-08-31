{
    'name': 'TTM Login as Email',
    'version': '19.0.1.0.0',
    'category': 'Technical',
    'summary': 'Login memakai alamat email selain username, tanpa mengubah field login',
    'description': """
Mengizinkan pengguna masuk memakai alamat email mereka, di samping username
(field `login`) yang sudah ada. Field `login` TIDAK diubah — email hanya
dipakai sebagai jalur pencarian tambahan saat autentikasi.

Cara kerja
----------
Odoo mencari user saat login lewat satu titik: `res.users._get_login_domain()`,
yang dipanggil di `_login()` sebagai `search(domain, order=..., limit=1)`.
Modul ini menyisip di titik tersebut dan MENERJEMAHKAN email menjadi nilai
`login` milik user yang bersangkutan, lalu meneruskannya ke `super()`.

Menerjemahkan (bukan mengganti domain dengan `id = X`) itu disengaja: modul
lain ikut menempel di hook yang sama — `website`, misalnya, menambahkan
`& website_domain()` supaya user hanya bisa login di website miliknya. Dengan
pendekatan terjemahan, batasan-batasan itu tetap berlaku.

Karena penyisipan terjadi sebelum pencocokan password, seluruh mekanisme
bawaan Odoo tetap utuh dan tidak perlu disalin ulang: rate limiting
(`_assert_can_auth`), pengecekan password (`_check_credentials`), 2FA, TOTP,
OAuth, LDAP, sampai `reset_password` di auth_signup (yang memakai hook yang
sama, jadi reset password lewat email ikut berfungsi).

Aturan pencocokan
-----------------
- Input tanpa "@" dianggap username -> tidak ada query tambahan sama sekali.
- Kalau ada user dengan `login` persis sama dengan yang diketik, user itulah
  yang menang. Email tidak pernah bisa membajak sebuah username.
- Email dicocokkan case-insensitive, dan hanya diterima kalau tepat SATU user
  aktif memakainya. Nol atau lebih dari satu -> login gagal seperti biasa.
  Ini penting karena `email` di res.users tidak unik dan bisa diubah sendiri
  oleh pengguna.

Tampilan
--------
Label pada form login diubah menjadi "Email Address or Username" (beserta
placeholder-nya). Diterapkan dengan priority 99 supaya tetap menang terhadap
tema backend yang juga menimpa label tersebut.
    """,
    'author': 'IB Teguh TM',
    'depends': ['web'],
    'data': [
        'views/login_templates.xml',
    ],
    'installable': True,
    'application': False,
    'license': 'LGPL-3',
}
