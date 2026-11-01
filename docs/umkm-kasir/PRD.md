# PRD — Mesin Kasir UMKM Banten (Odoo 19)

| | |
|---|---|
| Produk | Kasir tablet untuk UMKM canang, pejati, banten |
| Tenant | `kasir1` → https://kasir1.teguhteja.com |
| Platform | Odoo 19 Community (multi-tenant `teguhteja.com`), app Android **Odoo** (`com.odoo.mobile`) |
| Pemilik produk | IB Teguh Teja Murti (tim IT) |
| Tanggal | 7 Oktober 2026 |

## 1. Latar belakang
UMKM banten saat ini mencatat order dan pengeluaran secara manual, sehingga di akhir bulan
tidak tahu pasti berapa pendapatan, pengeluaran, dan laba/rugi, serta produk mana yang paling laku.
Sebagian besar order datang lewat WhatsApp. Pengadaan tablet + printer dibiayai hibah.

## 2. Tujuan
1. Setiap order tercatat dan pelanggan menerima struk.
2. Setiap pengeluaran tercatat dalam < 30 detik.
3. Akhir bulan: laporan **Pendapatan, Pengeluaran, Laba/Rugi** dan **jumlah item terjual per produk**, tanpa hitung manual.
4. Order WhatsApp masuk ke sistem yang sama dengan kasir.
5. Ada buku petunjuk yang bisa dipakai pemilik tanpa bantuan IT.

## 3. Pengguna
- **Pemilik/kasir** (1–2 orang): non-teknis, memakai tablet setiap hari.
- **Admin IT**: setup awal, tambah produk/user, dukungan.

## 4. Ruang lingkup MVP

### F1 — Kasir (POS)
- Pilih produk (Canang, Pejati, Banten Saiban, dll.) dengan gambar & harga, ubah jumlah, diskon manual.
- Pembayaran Tunai (hitung kembalian) dan QRIS/Transfer.
- Cetak struk ke printer thermal Bluetooth 58 mm.
- Buka/tutup sesi harian dengan hitung kas.

**Acceptance:** transaksi 3 item selesai + struk tercetak < 1 menit; order tercatat di Point of Sale → Orders.

### F2 — Order dari WhatsApp (semi-manual)
- Pesan WA ke nomor toko masuk ke Odoo (modul `whatsmeow` + `whatsmeow_discuss`) dan tampil di **Discuss** serta riwayat kontak pelanggan.
- Kasir membuat **Quotation** (Penjualan) untuk pelanggan tersebut, termasuk tanggal ambil/antar di catatan.
- Saat pelanggan mengambil/membayar, kasir membuka POS → tombol **Quotation/Order** (`pos_sale`) → pilih order → bayar → cetak struk.
- Kasir bisa membalas pelanggan dari Discuss.

**Acceptance:** pesan WA baru muncul di Discuss < 10 detik; quotation bisa di-load dan dibayar di POS; pendapatan hanya terhitung sekali.

### F3 — Pengeluaran
- Form: Tanggal (default hari ini), Kategori (Bahan, Transport, Listrik/Air/Pulsa, Upah/Gaji, Lain-lain), Keterangan, Jumlah.
- Daftar pengeluaran bulan ini dengan total.

**Acceptance:** input satu pengeluaran ≤ 4 isian; jumlah ≤ 0 ditolak.

### F4 — Laporan
- **Laporan Laba/Rugi bulanan:** Pendapatan (order POS yang dibayar) − Pengeluaran = Laba/Rugi; tampil sebagai tabel, pivot, dan grafik.
- **Produk Terlaris:** jumlah item terjual dan nilai penjualan per produk per bulan.

**Acceptance:** angka laporan cocok dengan penjumlahan manual order POS dan pengeluaran pada bulan uji.

### F5 — Buku petunjuk
Panduan bergambar dalam Bahasa Indonesia: `PANDUAN.md` (aktivitas harian, order WA, pengeluaran, laporan akhir bulan, printer).

## 5. Di luar ruang lingkup (MVP)
- Stok bahan & HPP otomatis (biaya bahan dicatat sebagai pengeluaran).
- Akuntansi penuh (jurnal, neraca, pajak).
- Parsing otomatis teks order WA menjadi pesanan.
- Multi-cabang, program loyalitas, pembayaran online.

## 6. Solusi teknis

| Kebutuhan | Solusi |
|---|---|
| Kasir, struk, sesi | `point_of_sale` (core) |
| Order WA → POS | `sale_management` + `pos_sale` (core) |
| WhatsApp masuk | `whatsmeow`, `whatsmeow_discuss` (sudah ada di `third-party/`) + gateway whatsmeow self-hosted di VPS |
| Pengeluaran & laba/rugi | addon custom `umkm_pengeluaran` (`addons/umkm_pengeluaran/`) |
| Produk terlaris | laporan bawaan `report.pos.order`, dipintas dari menu Keuangan UMKM |
| Bahasa & mata uang | Bahasa Indonesia, IDR, zona waktu Asia/Makassar |

Rumus laporan: `Laba = Σ pos_order.amount_total (state paid/done/invoiced) − Σ umkm_pengeluaran.amount`, per bulan WITA.

## 7. Perangkat keras

| Komponen | Pilihan | Harga |
|---|---|---|
| Tablet | Samsung Galaxy Tab A11 4/64 WiFi | Rp 2.355.000 |
| (alternatif) | Samsung Galaxy Tab A11 4/64 LTE (SIM) | Rp 2.785.000 |
| Printer | BLUEPRINT ECO 58D USB + Bluetooth thermal 58 mm | Rp 350.000 |
| (upgrade) | BLUEPRINT ECO 80 USB-BT (struk 80 mm) | Rp 575.000 |
| Stand + kertas thermal | — | ± Rp 200.000 |
| **Total (WiFi + 58D)** | | **± Rp 2.905.000** |

Rekomendasi: varian WiFi cukup jika toko punya WiFi/hotspot; pilih LTE bila tablet dipakai berpindah tempat.

### Cetak struk
POS mencetak lewat dialog print → aplikasi **RawBT** (Android) meneruskan ke printer Bluetooth.
Jika app Odoo Android tidak membuka dialog print, POS dibuka di **Chrome** dan dipasang sebagai ikon layar utama (PWA).

## 8. Risiko

| Risiko | Mitigasi |
|---|---|
| Nomor WA diblokir (whatsmeow = protokol WhatsApp Web, bukan API resmi) | Nomor khusus toko, volume rendah, pacing & warm-up bawaan modul; fallback: WA tetap dipakai di HP |
| Print dari app Odoo Android gagal | Pakai Chrome PWA + RawBT |
| Internet putus | POS Odoo tetap bisa transaksi offline dan sinkron setelah online |
| Pengguna lupa catat pengeluaran | Daftar pengeluaran default "Bulan Ini"; cek di panduan akhir hari |

## 9. Rencana & jadwal
1. Hari 1: buat tenant `kasir1`, install addon, data produk & metode bayar.
2. Hari 2: deploy gateway whatsmeow, pairing nomor WA toko.
3. Hari 3: setup tablet (app Odoo, RawBT, printer), uji end-to-end.
4. Hari 4: pelatihan + serah terima buku petunjuk.

## 10. Metrik keberhasilan
- 100% order bulan pertama tercatat di POS.
- Laporan laba/rugi bulan pertama tersedia tanpa hitung manual.
- Pemilik bisa operasi harian tanpa bantuan IT setelah minggu pertama.
