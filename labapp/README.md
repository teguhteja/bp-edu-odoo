# Lab-app di Odoo 19 (bp_edu_lab + bp_edu_lab_inventaris)

Pengganti aplikasi Laravel `claude-projects/lab-app` di atas Odoo 19 CE.

| Addon | Isi |
|---|---|
| `bp_edu_lab` | kelas, mahasiswa (akun portal tertaut via email), sesi praktikum + token presensi 4 jam, kelompok/peserta, pretest/posttest memakai **survey** (jendela waktu + satu jawaban per mahasiswa), penilaian manual, portal `/my/praktikum`, laporan nilai & absensi |
| `bp_edu_lab_inventaris` | barang lab di **product/stock**, PO & penerimaan memakai **purchase_stock**, stock opname (SO-YYMMDD-NNN), perbaikan (stok dipindah ke lokasi "Perbaikan Lab"), bahan praktikum, laporan penggunaan/pembelian/penyesuaian, stok menipis |

Tidak ada addon OCA yang dibutuhkan; semua celah diisi addon core (survey, portal, purchase, stock) + modul di atas.

Peran: `Lab: Admin / Laboran` (penuh), `Lab: Manager (baca saja)`, mahasiswa = user portal.

## Menjalankan (PowerShell, dari root worktree)

```powershell
podman build -t localhost/bp-edu-odoo-labapp:latest -f labapp/Dockerfile.test labapp   # sekali
.\labapp\odoo-labapp.ps1 run -i bp_edu_lab,bp_edu_lab_inventaris   # buat/instal DB labapp
.\labapp\odoo-labapp.ps1 serve                                      # http://localhost:18070
.\labapp\odoo-labapp.ps1 test                                       # 53 tes + 3 tour di DB labapp_test
```

Container `bp-edu-odoo_labapp` memakai DB server `bp-edu-odoo_db_1` (network `odoo_app`) tetapi
addons dari worktree ini, jadi container web utama tidak tersentuh.

## Impor data lab-app

```powershell
podman start lab-app_db_1
bash -c "podman exec -i lab-app_db_1 sh -s < scripts/labapp_import/export_mysql.sh > scripts/labapp_import/data/dump.txt"
python scripts/labapp_import/split_dump.py scripts/labapp_import/data/dump.txt
$env:LABAPP_PASSWORD = '...'   # opsional; tanpa ini password acak dicetak
.\labapp\odoo-labapp.ps1 shell labapp_import/import_labapp.py
.\labapp\odoo-labapp.ps1 shell labapp_import/verify_import.py   # harus "SEMUA COCOK"
```

Impor idempotent (external id `labapp_import.<tabel>_<id>`). Catatan pemetaan:

- Password bcrypt Laravel tidak bisa dipindah; akun impor diberi password baru.
- Stock opname lama dicatat sebagai riwayat; stok akhir disamakan persis dengan `inventaris.qty`.
- Peserta tanpa `kelompok_id` ditampung di kelompok "Umum - <praktikum>".
- Tabel `presensi`, `penilaian`, `activity_log` di lab-app tidak dipakai, sehingga tidak diimpor.
