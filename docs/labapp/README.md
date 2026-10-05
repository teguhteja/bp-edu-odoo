# Panduan Aplikasi Laboratorium (Lab-app di Odoo)

Aplikasi **Laboratorium** mengelola kegiatan praktikum dan inventaris laboratorium prodi:
presensi mahasiswa dengan token, pretest/posttest, pengumpulan berkas laporan, penilaian, serta
stok barang, perbaikan, stock opname, dan pengadaan barang.

Panduan dibagi tiga, sesuai siapa yang memakainya:

| Panduan | Untuk | Isi |
|---|---|---|
| [Panduan Mahasiswa](panduan-mahasiswa.md) | Mahasiswa | Login, presensi dengan token, upload berkas, mengerjakan pretest/posttest, melihat nilai |
| [Panduan Dosen / Laboran](panduan-dosen.md) | Dosen, laboran, admin lab | Data mahasiswa & kelas, membuat soal ujian, sesi praktikum & token, kelompok, penilaian, laporan |
| [Panduan Inventaris](panduan-inventaris.md) | Laboran, admin lab | Barang & stok menipis, perbaikan, stock opname, purchase order, penerimaan barang, laporan |

Versi Word (`.docx`) dari tiap panduan ada di folder yang sama dan bisa dibagikan langsung.

---

## Peran dan Hak Akses

| Peran | Siapa | Bisa apa |
|---|---|---|
| **Lab: Admin / Laboran** | Laboran, dosen pengampu praktikum, admin lab | Semua menu Laboratorium: membuat/mengubah data, generate token, membuat soal, menilai, inventaris, pengadaan |
| **Lab: Manager (baca saja)** | Kaprodi, pimpinan | Melihat semua data dan laporan, tanpa bisa mengubah |
| **Mahasiswa** (akun portal) | Mahasiswa | Hanya halaman **Praktikum** di portal: presensi, upload berkas, ujian, nilai miliknya sendiri |

Cara admin memberi peran ada di [Panduan Dosen bagian 1](panduan-dosen.md#1-peran-dan-hak-akses).

## Login

1. Buka alamat Odoo yang diberikan admin kampus.
2. Isi **Email** dan **Password**, lalu klik **Log in**.
   - Dosen/laboran masuk ke halaman aplikasi Odoo dan memilih menu **Laboratorium**.
   - Mahasiswa masuk ke halaman portal **My Account** dan memilih kartu **Praktikum**.

Akun mahasiswa dibuat oleh laboran dari data mahasiswa (tombol **Buat Akses Portal**). Login
mahasiswa = email mahasiswa yang tercatat di data mahasiswa.

## Catatan Umum

- Semua aturan tanggal (batas pretest/posttest, "hari ini") memakai zona waktu **WITA
  (Asia/Makassar)**.
- Token presensi terdiri dari **6 karakter** (huruf/angka), berlaku **4 jam** sejak dibuat.
- Tampilan bawaan Odoo (tombol seperti *New*, *Save*, *Confirm Order*) memakai bahasa Inggris;
  menu dan isian khusus laboratorium memakai bahasa Indonesia.
- Screenshot dalam panduan diambil dari data contoh; nama, tanggal, dan angka di sistem Anda bisa
  berbeda.
