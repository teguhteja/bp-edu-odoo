#!/usr/bin/env bash
# Backup semua database Odoo + filestore ke folder backups/
# Usage:
#   ./scripts/backup.sh              → backup semua DB
#   ./scripts/backup.sh teguhteja    → backup satu DB saja
#
# Hasil: backups/YYYY-MM-DD_HH-MM/<db>.sql.gz + <db>_filestore.tar.gz

set -euo pipefail

# ── Konfigurasi ───────────────────────────────────────────────────────────────
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_DIR="$(dirname "$SCRIPT_DIR")"
BACKUP_DIR="$PROJECT_DIR/backups"
COMPOSE_FILE="$PROJECT_DIR/docker-compose.yml"

# Load .env jika ada
[ -f "$PROJECT_DIR/.env" ] && source "$PROJECT_DIR/.env"

PG_USER="${POSTGRES_USER:-odoo}"
PG_PASS="${POSTGRES_PASSWORD:-odoo}"
FILESTORE_VOL="bp-edu-odoo_odoo-filestore"

# DB yang dikecualikan dari backup
EXCLUDE_DBS="postgres template0 template1 azure_sys"

# Retensi backup (hari) — 0 = simpan selamanya
RETENTION_DAYS=7

# ── Fungsi ────────────────────────────────────────────────────────────────────
log()  { echo "[$(date '+%Y-%m-%d %H:%M:%S')] $*"; }
err()  { echo "[$(date '+%Y-%m-%d %H:%M:%S')] ERROR: $*" >&2; }

get_all_dbs() {
    docker compose -f "$COMPOSE_FILE" exec -T db \
        psql -U "$PG_USER" -t -c \
        "SELECT datname FROM pg_database WHERE datistemplate = false ORDER BY datname;" \
        2>/dev/null | tr -d ' ' | grep -v '^$'
}

backup_db() {
    local db="$1"
    local dest="$2"

    # Skip DB yang dikecualikan
    for excl in $EXCLUDE_DBS; do
        [ "$db" = "$excl" ] && return 0
    done

    log "  Backup database: $db"
    PGPASSWORD="$PG_PASS" docker compose -f "$COMPOSE_FILE" exec -T db \
        pg_dump -U "$PG_USER" --no-owner --no-acl "$db" \
        | gzip -9 > "$dest/${db}.sql.gz"

    local size
    size=$(du -sh "$dest/${db}.sql.gz" | cut -f1)
    log "    → ${db}.sql.gz ($size)"
}

backup_filestore() {
    local db="$1"
    local dest="$2"

    # Filestore ada di dalam container di /var/lib/odoo/.local/share/Odoo/filestore/<db>
    local container_fs="/var/lib/odoo/.local/share/Odoo/filestore"
    local check
    check=$(docker compose -f "$COMPOSE_FILE" exec -T web \
        sh -c "[ -d '$container_fs/$db' ] && echo ok || echo no" 2>/dev/null)

    if [ "$check" != "ok" ]; then
        log "    → filestore $db tidak ada, skip"
        return 0
    fi

    log "  Backup filestore: $db"
    docker compose -f "$COMPOSE_FILE" exec -T web \
        tar -czf - -C "$container_fs" "$db" > "$dest/${db}_filestore.tar.gz"

    local size
    size=$(du -sh "$dest/${db}_filestore.tar.gz" | cut -f1)
    log "    → ${db}_filestore.tar.gz ($size)"
}

cleanup_old_backups() {
    if [ "$RETENTION_DAYS" -le 0 ]; then
        return 0
    fi
    log "Membersihkan backup lebih dari $RETENTION_DAYS hari..."
    find "$BACKUP_DIR" -maxdepth 1 -type d -mtime +"$RETENTION_DAYS" | while read -r old; do
        log "  Hapus: $old"
        rm -rf "$old"
    done
}

# ── Main ──────────────────────────────────────────────────────────────────────
TIMESTAMP=$(date '+%Y-%m-%d_%H-%M')
DEST="$BACKUP_DIR/$TIMESTAMP"
mkdir -p "$DEST"

log "========================================"
log "Odoo Backup - $TIMESTAMP"
log "Tujuan: $DEST"
log "========================================"

# Tentukan daftar DB yang akan di-backup
if [ $# -ge 1 ]; then
    DBS=("$@")
    log "Mode: backup spesifik → ${DBS[*]}"
else
    mapfile -t DBS < <(get_all_dbs)
    log "Mode: backup semua DB (${#DBS[@]} database)"
fi

FAILED=0
for db in "${DBS[@]}"; do
    db=$(echo "$db" | tr -d '[:space:]')
    [ -z "$db" ] && continue

    # Skip DB yang dikecualikan
    skip=0
    for excl in $EXCLUDE_DBS; do
        [ "$db" = "$excl" ] && skip=1 && break
    done
    [ "$skip" -eq 1 ] && continue

    if ! backup_db "$db" "$DEST"; then
        err "Gagal backup database $db"
        FAILED=$((FAILED + 1))
    fi
    backup_filestore "$db" "$DEST"
done

# Buat manifest
MANIFEST="$DEST/manifest.txt"
{
    echo "Backup: $TIMESTAMP"
    echo "Host:   $(hostname)"
    echo "DBs:    ${DBS[*]}"
    echo ""
    echo "Files:"
    ls -lh "$DEST"/*.gz 2>/dev/null || echo "(tidak ada file)"
} > "$MANIFEST"

cleanup_old_backups

log "========================================"
if [ "$FAILED" -gt 0 ]; then
    err "$FAILED database gagal di-backup"
    log "Backup selesai dengan error. Lihat log di atas."
    exit 1
else
    log "Backup selesai. Semua berhasil."
    log "Total size: $(du -sh "$DEST" | cut -f1)"
fi
log "========================================"
