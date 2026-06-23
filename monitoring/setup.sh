#!/bin/bash
# ══════════════════════════════════════════════════════════════
#  CaritaHub Monitoring Stack – Setup Script
#  Jalankan sekali di VPS setelah clone repo.
# ══════════════════════════════════════════════════════════════
set -e

cd "$(dirname "$0")"

GREEN='\033[0;32m'; YELLOW='\033[1;33m'; RED='\033[0;31m'; NC='\033[0m'
info()    { echo -e "${GREEN}[✔]${NC} $1"; }
warn()    { echo -e "${YELLOW}[!]${NC} $1"; }
error()   { echo -e "${RED}[✘]${NC} $1"; exit 1; }
section() { echo -e "\n${GREEN}━━━ $1 ━━━${NC}"; }

echo ""
echo "╔══════════════════════════════════════════════════════╗"
echo "║       CaritaHub Monitoring Stack – Setup             ║"
echo "╚══════════════════════════════════════════════════════╝"

# ── 1. Buat .env ──────────────────────────────────────────────
section "Konfigurasi .env"

if [ ! -f .env ]; then
    cp .env.example .env
    info "File .env dibuat dari .env.example"

    # Auto-generate secret key
    if command -v python3 &>/dev/null; then
        SECRET=$(python3 -c "import secrets; print(secrets.token_hex(50))")
    else
        SECRET=$(openssl rand -hex 50)
    fi
    sed -i "s|CHANGE_THIS_TO_A_RANDOM_100_CHAR_STRING|${SECRET}|" .env

    # Auto-generate DB password
    DB_PASS=$(openssl rand -hex 16)
    sed -i "s|CHANGE_THIS_DB_PASSWORD|${DB_PASS}|" .env

    info "Secret key dan DB password di-generate otomatis"
    warn "Edit .env untuk set ODOO_NETWORK dan GLITCHTIP_DOMAIN"
    echo ""
    echo "    Isi wajib diperiksa di .env:"
    echo "      - ODOO_NETWORK : nama Docker network Odoo kamu"
    echo "      - GLITCHTIP_DOMAIN : URL publik GlitchTip (misal https://sentry.domain.com)"
    echo "      - GLITCHTIP_FROM_EMAIL : email pengirim notifikasi"
    echo ""
else
    info "File .env sudah ada, melewati pembuatan"
fi

# Muat .env
set -a; source .env; set +a

# ── 2. Deteksi Odoo network ───────────────────────────────────
section "Deteksi Docker network Odoo"

ODOO_NET="${ODOO_NETWORK:-bp-edu-odoo_default}"
if docker network inspect "$ODOO_NET" &>/dev/null; then
    info "Network '${ODOO_NET}' ditemukan ✔"
else
    warn "Network '${ODOO_NET}' tidak ditemukan!"
    echo ""
    echo "    Docker networks yang ada:"
    docker network ls --format "  - {{.Name}}" | grep -v "^  - bridge$\|^  - host$\|^  - none$"
    echo ""
    warn "Update ODOO_NETWORK di .env lalu jalankan ulang script ini."
    exit 1
fi

# ── 3. Buat Dozzle users.yml ──────────────────────────────────
section "Setup autentikasi Dozzle"

if [ ! -f dozzle-users.yml ]; then
    echo "Masukkan password untuk akun admin Dozzle:"
    read -rs DOZZLE_PASS
    echo ""

    # Generate password hash dengan Dozzle
    HASH=$(docker run --rm amir20/dozzle:latest generate \
        --name "Admin" \
        --email "admin@localhost" \
        --password "${DOZZLE_PASS}" 2>/dev/null | grep "password:" | awk '{print $2}')

    cat > dozzle-users.yml <<EOF
users:
  admin:
    name: Admin
    email: admin@localhost
    password: "${HASH}"
EOF
    info "File dozzle-users.yml dibuat"
else
    info "File dozzle-users.yml sudah ada"
fi

# ── 4. Start dependency services ─────────────────────────────
section "Menjalankan database & cache"

docker compose up -d glitchtip-postgres glitchtip-redis mailpit dozzle
echo "Menunggu database siap..."
sleep 12
info "Services database sudah siap"

# ── 5. Migrasi database GlitchTip ────────────────────────────
section "Migrasi database GlitchTip"

docker compose run --rm glitchtip-migrate
info "Migrasi database selesai"

# ── 6. Jalankan semua services ────────────────────────────────
section "Menjalankan semua services"

docker compose up -d
sleep 5
info "Semua services berjalan"

# ── 7. Buat superuser GlitchTip ──────────────────────────────
section "Buat akun superuser GlitchTip"

echo ""
echo "  Silakan buat akun admin untuk GlitchTip:"
docker compose exec glitchtip-web ./manage.py createsuperuser

# ── 8. Summary ───────────────────────────────────────────────
VPS_IP=$(hostname -I | awk '{print $1}')

echo ""
echo "╔══════════════════════════════════════════════════════╗"
echo "║               Setup Selesai! ✔                       ║"
echo "╠══════════════════════════════════════════════════════╣"
echo -e "║  GlitchTip  → http://${VPS_IP}:${GLITCHTIP_PORT:-8100}        "
echo -e "║  Mailpit    → http://${VPS_IP}:${MAILPIT_UI_PORT:-8025}        "
echo -e "║  Dozzle     → http://${VPS_IP}:${DOZZLE_PORT:-9999}        "
echo "╠══════════════════════════════════════════════════════╣"
echo "║  Langkah selanjutnya:                                ║"
echo "║  1. Buka GlitchTip, buat organisasi & project       ║"
echo "║  2. Copy DSN → paste ke Odoo Settings > Sentry      ║"
echo "║  3. Set Odoo SMTP: host=mailpit port=1025            ║"
echo "║     (atau VPS_IP:1025 jika dari luar Docker)         ║"
echo "╚══════════════════════════════════════════════════════╝"
