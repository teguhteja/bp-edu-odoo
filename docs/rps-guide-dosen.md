# Panduan RPS: Melihat, Mengedit via Upload Dokumen, dan Menambah Buku Ajar

Panduan ini untuk dosen dan kaprodi yang menggunakan modul RPS (Rencana
Pembelajaran Semester). Mencakup 3 hal: cara melihat RPS, cara mengedit RPS
lewat upload dokumen `.docx`, dan cara menambah buku ajar lewat DMS/Google
Drive.

Beberapa menu terkait (CPL Prodi, Template DOCX, History Generate, Import
JSON) khusus untuk Kaprodi dan tidak dibahas di sini.

---

## 1. Melihat RPS

Buka menu **Pendidikan > Perencanaan > RPS**.

### Daftar RPS

Kolom yang tampil di daftar:

| Kolom | Keterangan |
|---|---|
| Kode MK | Kode mata kuliah |
| Nama MK | Nama mata kuliah |
| Prodi | Program studi |
| Semester | Semester mata kuliah |
| Dosen Koordinator | Dosen penanggung jawab RPS |
| Tahun Akademik | Tahun akademik RPS berlaku |
| State | Badge status: **Draft** (abu-abu) atau **Final** (hijau) |

Gunakan kotak pencarian **"Cari RPS"** untuk mencari, filter **Draft** /
**Final** untuk menyaring status, atau kelompokkan hasil (Group By)
berdasarkan **Program Studi**, **Tahun Akademik**, **Dosen Koordinator**,
atau **Semester**.

### Membuka Satu RPS

Klik salah satu baris untuk membuka form RPS. Tombol-tombol yang tersedia di
header:

| Tombol | Fungsi |
|---|---|
| Finalisasi | Mengubah status RPS dari Draft ke Final |
| Reset ke Draft | Mengembalikan RPS Final ke Draft agar bisa diedit lagi |
| Generate 16 Baris Minggu | Membuat 16 baris kosong di tabel Detail Perkuliahan (hanya muncul selama tabel masih kosong) |
| Generate DOCX | Mengunduh RPS sebagai file Word — lihat [bagian 2](#2-mengedit-rps-dengan-upload-dokumen-docx) |
| Upload Dokumen | Mengunggah kembali file Word yang sudah diedit — lihat [bagian 2](#2-mengedit-rps-dengan-upload-dokumen-docx) |

Di samping status bar (Draft / Final) ada tombol **"Riwayat"** (ikon jam),
menampilkan jumlah versi lama yang tersimpan.

### Tab-Tab pada Form RPS

| Tab | Isi |
|---|---|
| Detail Perkuliahan (16 Minggu) | Rencana pertemuan minggu 1–16 |
| Korelasi CPMK-Minggu | Matriks keterkaitan CPMK dengan minggu perkuliahan |
| Korelasi Sub-CPMK-CPL | Matriks keterkaitan Sub-CPMK dengan CPL |
| Matriks Penilaian | Komponen dan bobot penilaian |
| Rancangan Tugas Proyek | Rincian tugas/proyek mahasiswa |
| Rubrik Penilaian | Berisi dua sub-bagian: **Rubrik Holistik Proposal/Laporan** dan **Rubrik Deskriptif Presentasi** |

### Melihat Riwayat Perubahan

Klik tombol **"Riwayat"** untuk membuka daftar **"Riwayat Perubahan"** — ini
adalah salinan lengkap RPS pada kondisi sebelumnya, dibuat otomatis oleh
sistem setiap kali ada perubahan tercatat (bukan hanya field header, tapi
juga isi seluruh tabel).

Membuka salah satu baris riwayat akan menampilkan banner:

> *"Ini adalah snapshot riwayat — kondisi RPS ini [tanggal], sebelum
> perubahan oleh [user]. Data di bawah ini apa adanya saat itu dan tidak
> bisa diedit atau disimpan."*

Data di layar ini tidak bisa diubah. Klik tombol **"Buka RPS Saat Ini"**
untuk kembali ke RPS yang aktif/berjalan.

### Kapan RPS Bisa Diedit

Jika status RPS **Final** (atau sedang melihat halaman Riwayat), sebagian
besar field menjadi tidak bisa diedit. Klik **"Reset ke Draft"** terlebih
dahulu di RPS yang aktif sebelum mengubah isinya.

---

## 2. Mengedit RPS dengan Upload Dokumen (.docx)

Alurnya dua tahap: **unduh dulu dari sistem, edit di Word, lalu upload
kembali**. Jangan membuat file Word baru dari nol untuk cara ini.

### Langkah 1 — Unduh Dokumen RPS

1. Di form RPS, klik tombol **"Generate DOCX"**.
2. Pada wizard yang terbuka, Jenis Dokumen dan RPS sudah otomatis terisi.
   Pilih **Template**, lalu klik **Generate**.
3. Setelah berhasil, akan muncul pesan **"Berhasil! File ... siap
   diunduh."**. Klik **Unduh File**.

Jika ada beberapa pilihan Template, tanyakan ke Kaprodi template mana yang
berlaku untuk prodi.

### Langkah 2 — Edit di Microsoft Word

⚠️ **Penting**: file yang akan diupload harus file hasil unduhan Langkah 1
di atas, bukan dokumen baru. Isi boleh diubah bebas, **tapi jangan mengubah
struktur baris/kolom pada tabel Detail Perkuliahan 16 Minggu** (jangan
menambah, menghapus, atau menggabung baris/kolom). Sistem membaca tabel ini
berdasarkan posisi kolom dan mencari tanda "Sub-CPMK" di judul tabel — kalau
strukturnya berubah, upload akan gagal dengan pesan:

> `Tabel "Detail Perkuliahan 16 Minggu" (kolom Sub-CPMK) tidak ditemukan...`

### Langkah 3 — Upload Kembali

1. Di form RPS, klik tombol **"Upload Dokumen"**.
2. Pilih file `.docx` yang sudah diedit.
3. Pilih mode dengan mencentang atau mengosongkan **"Proses dengan AI"**:

   | Mode | Yang Diganti | Kecepatan | Butuh AI Agent/API Key | Catatan |
   |---|---|---|---|---|
   | Tanpa AI (kosong) | Hanya tabel Detail Perkuliahan 16 Minggu | Cepat | Tidak | Risiko rendah |
   | Dengan AI (dicentang) | **Seluruh data RPS** (CPMK, Sub-CPMK, Pustaka, matriks korelasi, dll) | Lebih lambat | Ya | Lihat peringatan di bawah |

### Langkah 4 — Cek File

Klik **"Cek File"**. Hasilnya ditampilkan di kotak "Hasil Cek": ✅ berarti
berhasil dan siap diterapkan, ❌ berarti gagal, ⚠️ berarti terbaca tapi
datanya kurang lengkap.

Jika memakai mode AI dan pengecekan berhasil, akan muncul peringatan:

> *"⚠️ PERHATIAN: Menerapkan hasil ini akan MENGGANTI SELURUH data RPS
> (CPMK, Sub-CPMK, Pustaka, matriks korelasi, dan detail mingguan) sesuai
> isi di atas. Bagian yang bernilai 0 di atas akan DIKOSONGKAN."*

### Langkah 5 — Terapkan

- Klik **"Terapkan Perubahan"** (hanya aktif jika pengecekan berhasil).
  Akan muncul dialog konfirmasi: *"Yakin ingin menerapkan perubahan ini?
  Data RPS yang ada akan diganti."*
- Atau klik **"Coba File Lain"** untuk mengunggah ulang file yang berbeda.

### Langkah 6 — Selesai

Setelah diterapkan, muncul ringkasan "Hasil Update". Klik **"Buka RPS"**
untuk kembali ke RPS. File yang diupload otomatis tersimpan sebagai
lampiran pada percakapan (chatter) RPS, sebagai jejak riwayat.

### Ringkasan Peringatan

⚠️ Sebelum mengunggah, pastikan:

1. File adalah hasil unduhan sistem ini sendiri, dan struktur tabel
   mingguan tidak diubah.
2. Mode "Dengan AI" mengganti **seluruh** data RPS, termasuk mengosongkan
   bagian yang terbaca kosong — bukan hanya menambah/mengganti sebagian.
3. Mode "Dengan AI" butuh AI Agent/API key yang sudah aktif. Jika belum
   dikonfigurasi, akan muncul pesan *"AI belum dikonfigurasi..."* —
   hubungi admin, jangan mencoba mengatur sendiri lewat menu Settings.

---

## 3. Menambah Buku Ajar via DMS (Link Google Drive)

### Kenapa Tidak Bisa Upload File Langsung

Upload file langsung ke server DMS sengaja dimatikan untuk menghemat
storage. Jika dicoba, akan muncul pesan (dalam Bahasa Inggris):

> *"Sorry, we can't upload your ebook to the server. Please put it in
> Google Drive instead."*

Solusinya: simpan file buku ajar di Google Drive, lalu tempelkan link-nya
di sistem — ada dua cara.

### Cara 1 (Direkomendasikan) — Lewat Form Mata Kuliah

1. Buka menu **Pendidikan > Kurikulum > Mata Kuliah**, lalu buka mata
   kuliah yang dituju.
2. Buka tab **"Link Google Drive"** (terletak setelah tab "Pustaka").
3. Klik baris kosong di tabel, isi kolom **Judul** dan **Link Google
   Drive** (tempel link share dari Google Drive).

Tab ini menampilkan catatan:

> *"Upload file langsung ke server dimatikan untuk menghemat storage.
> Simpan buku ajar di Google Drive lalu tempel link-nya di sini."*

Form Mata Kuliah juga punya tombol **"Buku Ajar"** yang membuka folder DMS
milik mata kuliah tersebut, untuk melihat-lihat berkas yang sudah ada.
Folder ini dibuat otomatis dengan struktur `Buku Ajar / [Nama Prodi] /
[Kode] Nama Mata Kuliah`.

### Cara 2 (Alternatif) — Lewat Menu Documents

Menu ini masih berlabel Bahasa Inggris (berbeda dari sisa antarmuka yang
berbahasa Indonesia).

1. Buka menu **Documents > Files** atau **Documents > Directories**.
2. Buat atau buka satu berkas (file) DMS.
3. Field upload biasa ("Content") sudah diganti dengan field **"Link
   Google Drive"**. Tempel link di sana.
4. Tombol **"Buka di Google Drive"** akan membuka link tersebut di tab
   baru. Jika link berformat `.../file/d/<id>/...`, pratinjau (preview)
   file akan otomatis muncul di bawah field.

### Cara 1 vs Cara 2

| | Kapan Dipakai | Catatan |
|---|---|---|
| Cara 1 — Form Mata Kuliah | Buku ajar terkait langsung ke satu mata kuliah | Lebih cepat, semua dari satu layar |
| Cara 2 — Menu Documents | Perlu mengatur folder/struktur lebih bebas | Ada pratinjau otomatis untuk link file Google Drive |

### Hak Akses

Dosen bisa menambah dan mengubah link/berkas di area "Buku Ajar", tapi
**tidak bisa menghapus** — izin hapus hanya untuk Kaprodi/admin. Jika perlu
menghapus, minta bantuan Kaprodi.

### Cara Mendapatkan Link Share dari Google Drive

1. Buka Google Drive, klik kanan file yang dimaksud.
2. Pilih **"Get link"** / **"Dapatkan link"**.
3. Pastikan aksesnya diset ke **"Anyone with the link"** (siapa saja yang
   punya link) supaya dosen lain atau kaprodi bisa membukanya.
4. Salin link, lalu tempelkan di sistem sesuai Cara 1 atau Cara 2 di atas.

---

*Panduan ini disusun manual berdasarkan tampilan aplikasi per 2026-08-31.
Jika menu/tombol berubah di versi berikutnya, mohon informasikan agar
dokumen ini diperbarui.*
