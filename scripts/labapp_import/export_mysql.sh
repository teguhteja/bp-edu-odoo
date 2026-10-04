#!/bin/sh
# Ekspor tabel lab-app (MySQL) ke JSON Lines, satu baris JSON per record (read-only).
# Dijalankan DI DALAM container MySQL lab-app, output ditulis ke stdout dengan penanda
# "### <tabel>" sebelum setiap tabel:
#   podman exec -i lab-app_db_1 sh -s < scripts/labapp_import/export_mysql.sh > dump.txt
# lalu dipecah oleh split_dump.py menjadi data/<tabel>.jsonl.
TABLES="prodi kelas mahasiswa mata_kuliah users category_inventaris inventaris supplier
purchase_order purchase_order_detail recieving recieving_detail stock_opname
stock_opname_detail inventaris_perbaikan test test_detail test_answer praktikum
praktikum_detail kelompok kelompok_detail"

q() {
    MYSQL_PWD="$MYSQL_PASSWORD" mysql -u"$MYSQL_USER" "$MYSQL_DATABASE" -N -B --raw -e "$1"
}

for t in $TABLES; do
    cols=$(q "SELECT GROUP_CONCAT(CONCAT('''', column_name, ''',\`', column_name, '\`') ORDER BY ordinal_position SEPARATOR ',') FROM information_schema.columns WHERE table_schema = DATABASE() AND table_name = '$t'")
    echo "### $t"
    q "SELECT JSON_OBJECT($cols) FROM \`$t\`"
done
