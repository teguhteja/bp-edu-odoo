#!/usr/bin/env bash
# Manajemen backup & restore database Odoo
#
# BACKUP
#   ./scripts/odoo-db.sh backup                    → backup semua DB
#   ./scripts/odoo-db.sh backup teguhteja          → backup satu DB
#   ./scripts/odoo-db.sh backup teguhteja company1 → backup beberapa DB
#
# RESTORE
#   ./scripts/odoo-db.sh restore                   → pilih dari daftar backup
#   ./scripts/odoo-db.sh restore 2026-07-13_14-15  → restore folder tertentu
#   ./scripts/odoo-db.sh restore 2026-07-13_14-15 teguhteja          → restore satu DB
#   ./scripts/odoo-db.sh restore 2026-07-13_14-15 teguhteja new_name → restore dengan nama baru
#
# LIST
#   ./scripts/odoo-db.sh list                      → tampilkan semua backup tersedia

set -euo pipefail

# ── Konfigurasi ───────────────────────────────────────────────────────────────
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_DIR="$(dirname "$SCRIPT_DIR")"
BACKUP_DIR="$PROJECT_DIR/backups"
COMPOSE_FILE="$PROJECT_DIR/docker-compose.yml"

[ -f "$PROJECT_DIR/.env" ] && source "$PROJECT_DIR/.env"

PG_USER="${POSTGRES_USER:-odoo}"
PG_PASS="${POSTGRES_PASSWORD:-odoo}"
EXCLUDE_DBS="postgres template0 template1 azure_sys"
RETENTION_DAYS=7
CONTAINER_FS="/var/lib/odoo/.local/share/Odoo/filestore"

# ── Helper ────────────────────────────────────────────────────────────────────
log()     { echo "[$(date '+%Y-%m-%d %H:%M:%S')] $*"; }
err()     { echo "[$(date '+%Y-%m-%d %H:%M:%S')] ERROR: $*" >&2; }
info()    { echo "[$(date '+%Y-%m-%d %H:%M:%S')] INFO:  $*"; }
success() { echo "[$(date '+%Y-%m-%d %H:%M:%S')] OK:    $*"; }
sep()     { echo "[$(date '+%Y-%m-%d %H:%M:%S')] $(printf '=%.0s' {1..44})"; }

is_excluded() {
    local db="$1"
    for excl in $EXCLUDE_DBS; do [ "$db" = "$excl" ] && return 0; done
    return 1
}

get_all_dbs() {
    docker compose -f "$COMPOSE_FILE" exec -T db \
        psql -U "$PG_USER" -t -c \
        "SELECT datname FROM pg_database WHERE datistemplate = false ORDER BY datname;" \
        2>/dev/null | tr -d ' ' | grep -v '^$'
}

db_exists() {
    docker compose -f "$COMPOSE_FILE" exec -T db \
        psql -U "$PG_USER" -t -c \
        "SELECT 1 FROM pg_database WHERE datname='$1';" \
        2>/dev/null | grep -q 1
}

# ══════════════════════════════════════════════════════════════════════════════
# BACKUP
# ══════════════════════════════════════════════════════════════════════════════

do_backup_db() {
    local db="$1" dest="$2"
    is_excluded "$db" && return 0
    log "  Database : $db"
    PGPASSWORD="$PG_PASS" docker compose -f "$COMPOSE_FILE" exec -T db \
        pg_dump -U "$PG_USER" --no-owner --no-acl "$db" \
        | gzip -9 > "$dest/${db}.sql.gz"
    success "    → ${db}.sql.gz ($(du -sh "$dest/${db}.sql.gz" | cut -f1))"
}

do_backup_filestore() {
    local db="$1" dest="$2"
    local check
    check=$(docker compose -f "$COMPOSE_FILE" exec -T web \
        sh -c "[ -d '$CONTAINER_FS/$db' ] && echo ok || echo no" 2>/dev/null)
    if [ "$check" != "ok" ]; then
        info "    → filestore $db kosong, skip"
        return 0
    fi
    log "  Filestore: $db"
    docker compose -f "$COMPOSE_FILE" exec -T web \
        tar -czf - -C "$CONTAINER_FS" "$db" > "$dest/${db}_filestore.tar.gz"
    success "    → ${db}_filestore.tar.gz ($(du -sh "$dest/${db}_filestore.tar.gz" | cut -f1))"
}

cleanup_old() {
    [ "$RETENTION_DAYS" -le 0 ] && return 0
    log "Membersihkan backup > $RETENTION_DAYS hari..."
    find "$BACKUP_DIR" -maxdepth 1 -type d -mtime +"$RETENTION_DAYS" | while read -r old; do
        info "  Hapus: $(basename "$old")"
        rm -rf "$old"
    done
}

cmd_backup() {
    local TIMESTAMP DEST
    TIMESTAMP=$(date '+%Y-%m-%d_%H-%M')
    DEST="$BACKUP_DIR/$TIMESTAMP"
    mkdir -p "$DEST"

    sep; log "BACKUP  →  $TIMESTAMP"; sep

    local DBS=()
    if [ $# -ge 1 ]; then
        DBS=("$@")
        log "Target: ${DBS[*]}"
    else
        mapfile -t DBS < <(get_all_dbs)
        log "Target: semua DB (${#DBS[@]} ditemukan)"
    fi

    local FAILED=0
    for db in "${DBS[@]}"; do
        db=$(echo "$db" | tr -d '[:space:]')
        [ -z "$db" ] && continue
        is_excluded "$db" && continue
        do_backup_db       "$db" "$DEST" || { err "Gagal backup DB $db"; FAILED=$((FAILED+1)); }
        do_backup_filestore "$db" "$DEST"
    done

    # Manifest
    {
        echo "timestamp : $TIMESTAMP"
        echo "host      : $(hostname)"
        echo "databases : ${DBS[*]}"
        echo ""
        ls -lh "$DEST"/*.gz 2>/dev/null || true
    } > "$DEST/manifest.txt"

    cleanup_old
    sep
    if [ "$FAILED" -gt 0 ]; then
        err "$FAILED DB gagal. Cek log di atas."; exit 1
    fi
    success "Selesai. Total: $(du -sh "$DEST" | cut -f1)  →  $DEST"
    sep
}

# ══════════════════════════════════════════════════════════════════════════════
# LIST
# ══════════════════════════════════════════════════════════════════════════════

cmd_list() {
    sep; log "DAFTAR BACKUP"; sep
    if [ ! -d "$BACKUP_DIR" ] || [ -z "$(ls -A "$BACKUP_DIR" 2>/dev/null)" ]; then
        info "Belum ada backup di $BACKUP_DIR"
        return 0
    fi
    local idx=1
    for dir in "$BACKUP_DIR"/*/; do
        [ -d "$dir" ] || continue
        local name size dbs
        name=$(basename "$dir")
        size=$(du -sh "$dir" 2>/dev/null | cut -f1)
        dbs=$(ls "$dir"/*.sql.gz 2>/dev/null | xargs -I{} basename {} .sql.gz | tr '\n' ' ')
        printf "  [%2d]  %-20s  %6s   DB: %s\n" "$idx" "$name" "$size" "${dbs:-–}"
        idx=$((idx+1))
    done
    sep
}

# ══════════════════════════════════════════════════════════════════════════════
# RESTORE
# ══════════════════════════════════════════════════════════════════════════════

do_restore_db() {
    local sql_file="$1" target_db="$2"

    # Terminasi koneksi aktif ke DB target
    docker compose -f "$COMPOSE_FILE" exec -T db \
        psql -U "$PG_USER" -c \
        "SELECT pg_terminate_backend(pid) FROM pg_stat_activity
         WHERE datname='$target_db' AND pid <> pg_backend_pid();" \
        2>/dev/null || true

    # Drop & buat ulang DB target
    if db_exists "$target_db"; then
        log "    Drop DB lama: $target_db"
        docker compose -f "$COMPOSE_FILE" exec -T db \
            psql -U "$PG_USER" -c "DROP DATABASE \"$target_db\";" 2>/dev/null
    fi
    docker compose -f "$COMPOSE_FILE" exec -T db \
        psql -U "$PG_USER" -c \
        "CREATE DATABASE \"$target_db\" OWNER \"$PG_USER\" ENCODING 'UTF8';" 2>/dev/null

    # Restore dump
    log "    Restore SQL → $target_db"
    PGPASSWORD="$PG_PASS" \
        zcat "$sql_file" | \
        docker compose -f "$COMPOSE_FILE" exec -T db \
        psql -U "$PG_USER" -d "$target_db" -q 2>/dev/null 1>/dev/null

    success "    → database $target_db berhasil di-restore"
}

do_restore_filestore() {
    local tar_file="$1" target_db="$2" original_db="$3"

    [ ! -f "$tar_file" ] && { info "    → tidak ada filestore backup, skip"; return 0; }

    log "    Restore filestore → $target_db"
    # Extract ke /tmp dalam container, lalu pindahkan ke lokasi filestore
    docker compose -f "$COMPOSE_FILE" exec -T web \
        sh -c "mkdir -p '$CONTAINER_FS/$target_db'" 2>/dev/null

    if [ "$original_db" = "$target_db" ]; then
        # Sama nama: extract langsung ke parent folder
        docker compose -f "$COMPOSE_FILE" exec -T web \
            sh -c "rm -rf '$CONTAINER_FS/$target_db'" 2>/dev/null
        cat "$tar_file" | docker compose -f "$COMPOSE_FILE" exec -T web \
            tar -xzf - -C "$CONTAINER_FS"
    else
        # Nama berbeda: extract dengan nama lama, lalu rename
        docker compose -f "$COMPOSE_FILE" exec -T web \
            sh -c "rm -rf '$CONTAINER_FS/$original_db' '$CONTAINER_FS/$target_db'" 2>/dev/null
        cat "$tar_file" | docker compose -f "$COMPOSE_FILE" exec -T web \
            tar -xzf - -C "$CONTAINER_FS"
        docker compose -f "$COMPOSE_FILE" exec -T web \
            sh -c "mv '$CONTAINER_FS/$original_db' '$CONTAINER_FS/$target_db'" 2>/dev/null
    fi

    success "    → filestore $target_db berhasil di-restore"
}

pick_backup_dir() {
    # Tampilkan daftar dan minta user pilih jika belum ada argumen
    cmd_list
    local dirs=()
    mapfile -t dirs < <(ls -d "$BACKUP_DIR"/*/ 2>/dev/null | sort -r)
    [ ${#dirs[@]} -eq 0 ] && { err "Tidak ada backup tersedia."; exit 1; }

    echo ""
    read -rp "Masukkan nama folder backup (contoh: 2026-07-13_14-15): " chosen
    echo "$BACKUP_DIR/$chosen"
}

cmd_restore() {
    sep; log "RESTORE"; sep

    # Argumen: [folder] [db_asal] [db_tujuan]
    local backup_folder="" src_db="" dst_db=""

    if [ $# -ge 1 ]; then
        backup_folder="$BACKUP_DIR/$1"
    else
        backup_folder=$(pick_backup_dir)
    fi

    [ ! -d "$backup_folder" ] && { err "Folder backup tidak ditemukan: $backup_folder"; exit 1; }
    log "Sumber backup: $backup_folder"

    # Daftar DB yang tersedia di folder backup
    local available_dbs=()
    for f in "$backup_folder"/*.sql.gz; do
        [ -f "$f" ] && available_dbs+=("$(basename "$f" .sql.gz)")
    done
    [ ${#available_dbs[@]} -eq 0 ] && { err "Tidak ada file .sql.gz di $backup_folder"; exit 1; }

    if [ $# -ge 2 ]; then
        src_db="$2"
        dst_db="${3:-$2}"
        # Restore satu DB spesifik
        local sql_file="$backup_folder/${src_db}.sql.gz"
        local fs_file="$backup_folder/${src_db}_filestore.tar.gz"
        [ ! -f "$sql_file" ] && { err "File tidak ditemukan: $sql_file"; exit 1; }

        log "Restore: $src_db → $dst_db"
        do_restore_db       "$sql_file" "$dst_db"
        do_restore_filestore "$fs_file" "$dst_db" "$src_db"
    else
        # Restore semua DB yang ada di folder
        log "Restore semua DB: ${available_dbs[*]}"
        echo ""
        echo "  PERINGATAN: Semua database berikut akan di-DROP dan di-restore:"
        for db in "${available_dbs[@]}"; do echo "    - $db"; done
        echo ""
        read -rp "  Lanjutkan? (ketik 'ya' untuk konfirmasi): " confirm
        [ "$confirm" != "ya" ] && { info "Dibatalkan."; exit 0; }

        local FAILED=0
        for db in "${available_dbs[@]}"; do
            log "Restore DB: $db"
            do_restore_db       "$backup_folder/${db}.sql.gz" "$db" \
                || { err "Gagal restore $db"; FAILED=$((FAILED+1)); continue; }
            do_restore_filestore "$backup_folder/${db}_filestore.tar.gz" "$db" "$db"
        done

        if [ "$FAILED" -gt 0 ]; then
            err "$FAILED DB gagal di-restore."; exit 1
        fi
    fi

    sep
    success "Restore selesai."
    info "Jalankan 'docker compose restart web' jika Odoo perlu reload registry."
    sep
}

# ══════════════════════════════════════════════════════════════════════════════
# ENTRY POINT
# ══════════════════════════════════════════════════════════════════════════════

COMMAND="${1:-help}"
shift || true

case "$COMMAND" in
    backup)  cmd_backup  "$@" ;;
    restore) cmd_restore "$@" ;;
    list)    cmd_list         ;;
    help|--help|-h)
        cat <<'HELP'
Penggunaan: ./scripts/odoo-db.sh <perintah> [argumen]

Perintah:
  backup                              Backup semua database
  backup <db1> [db2] ...              Backup database tertentu
  list                                Tampilkan semua backup tersedia
  restore                             Pilih backup interaktif, restore semua DB
  restore <folder>                    Restore semua DB dari folder tertentu
  restore <folder> <db>               Restore satu DB (nama tetap)
  restore <folder> <db> <nama_baru>   Restore satu DB dengan nama baru

Contoh:
  ./scripts/odoo-db.sh backup
  ./scripts/odoo-db.sh backup teguhteja
  ./scripts/odoo-db.sh list
  ./scripts/odoo-db.sh restore 2026-07-13_14-15
  ./scripts/odoo-db.sh restore 2026-07-13_14-15 teguhteja
  ./scripts/odoo-db.sh restore 2026-07-13_14-15 teguhteja teguhteja_recovery
HELP
        ;;
    *) err "Perintah tidak dikenal: $COMMAND. Gunakan 'help' untuk bantuan."; exit 1 ;;
esac
