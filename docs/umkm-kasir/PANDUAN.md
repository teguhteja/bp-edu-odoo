# Buku Petunjuk Kasir Banten

Alamat: **https://kasir1.teguhteja.com** — login dengan email & password yang diberikan tim IT.

> Screenshot akan ditambahkan setelah tablet terpasang.

## A. Persiapan tablet (sekali saja, dibantu IT)
1. Install **Odoo** dari Play Store, isi alamat `https://kasir1.teguhteja.com`, login.
2. Install **RawBT** dari Play Store.
3. Nyalakan printer BLUEPRINT ECO 58D, buka *Pengaturan → Bluetooth* di tablet, pasangkan printer (PIN biasanya `0000` atau `1234`).
4. Buka RawBT → *Settings → Connection method: Bluetooth* → pilih printer → *Test print*.
5. Jika tombol cetak di app Odoo tidak berfungsi: buka Chrome → `kasir1.teguhteja.com/pos/ui` → menu ⋮ → **Tambahkan ke layar utama**. Pakai ikon itu untuk kasir.

## B. Setiap pagi — buka kasir
1. Buka menu **Point of Sale** → tombol **Buka Sesi**.
2. Isi uang kas awal di laci → **Buka Sesi**.

## C. Melayani pembeli langsung
1. Ketuk produk (mis. *Canang Sari*). Ketuk lagi untuk menambah jumlah, atau ketik angka di keypad.
2. Ketuk **Pembayaran** → pilih **Tunai** atau **QRIS**.
3. Untuk tunai, ketik uang yang diterima → kembalian muncul otomatis.
4. Ketuk **Validasi** → **Cetak Struk** → di layar print pilih **RawBT**.
5. Ketuk **Order Baru** untuk pembeli berikutnya.

## D. Order dari WhatsApp
1. Pesan WA pelanggan muncul di menu **Discuss** (ikon chat). Balas pelanggan langsung dari situ.
2. Catat pesanan: menu **Penjualan → Quotation → Baru**.
   - Pelanggan: pilih / buat kontak (nama + nomor WA).
   - Tambah produk & jumlah.
   - Tulis tanggal ambil/antar di catatan → **Simpan**.
3. Saat pelanggan mengambil & membayar: di POS ketuk **⋮ / Quotation/Order** → pilih order pelanggan → **Bayar** (bagian C langkah 2–4).

> Pendapatan baru dihitung setelah order dibayar di POS.

## E. Mencatat pengeluaran
1. Menu **Keuangan UMKM → Pengeluaran** → **Baru**.
2. Isi **Kategori** (Bahan, Transport, Listrik/Air/Pulsa, Upah/Gaji, Lain-lain), **Keterangan** (mis. *janur 5 ikat*), **Jumlah** → tekan Enter / **Simpan**.
3. Tanggal otomatis hari ini; ubah bila mencatat pengeluaran kemarin.

Tips: catat setiap kali belanja, atau kumpulkan nota dan catat sebelum tutup toko.

## F. Setiap malam — tutup kasir
1. Di POS: menu ☰ → **Tutup Sesi**.
2. Hitung uang di laci, isi jumlahnya → **Tutup Sesi**.
3. Pastikan pengeluaran hari ini sudah dicatat (bagian E).

## G. Akhir bulan — laporan
- **Keuangan UMKM → Laporan Laba / Rugi**: satu baris per bulan berisi **Pendapatan**, **Pengeluaran**, **Laba / Rugi** (merah = rugi). Ketuk ikon grafik untuk melihat tren.
- **Keuangan UMKM → Produk Terlaris**: jumlah item terjual per produk per bulan. Urutkan kolom *Jumlah* untuk melihat produk paling laku.
- **Keuangan UMKM → Pengeluaran** → filter *Kategori*: melihat pengeluaran terbesar.

## H. Masalah umum
| Masalah | Solusi |
|---|---|
| Struk tidak keluar | Printer menyala & kertas ada? Bluetooth tablet aktif? Coba *Test print* di RawBT. |
| Internet mati | Tetap bisa jualan di POS; data terkirim otomatis saat internet kembali. Jangan tutup aplikasi. |
| Pesan WA tidak masuk ke Odoo | Hubungi IT (sesi WhatsApp perlu dipindai ulang). Sementara balas lewat app WhatsApp. |
| Salah input pengeluaran | Buka Pengeluaran, ketuk baris tersebut, ubah atau hapus. |
| Salah transaksi POS | Buat **Refund** dari menu ☰ → Orders, lalu ulangi transaksi. |

Kontak IT: IB Teguh Teja Murti.
