# BP Edu Odoo

Proyek Odoo Education - Sistem Manajemen Pembelajaran berbasis Odoo ERP.

## Prerequisites

- Docker & Docker Compose
- Git
- Python 3.11+ (untuk development lokal)

## Quick Start

### 1. Clone Repository

```bash
git clone git@github.com:teguhteja/bp-edu-odoo.git
cd bp-edu-odoo
```

### 2. Setup Environment

```bash
# Copy environment file
cp .env.example .env

# Edit .env sesuai kebutuhan
# Default ports:
# - Odoo: 18069
# - PostgreSQL: 15432
# - Nginx Proxy Manager: 81
# - Adminer: 18070
```

### 3. Start Docker

```bash
docker compose up -d
```

### 4. Akses Odoo

- **Odoo Web**: http://localhost:18069
- **Adminer** (DB Management): http://localhost:18070
- **Nginx Proxy Manager**: http://localhost:81

## Default Credentials

### Odoo
- Database: `teguhteja-odoo-dev`
- Email: `admin`
- Password: `admin`

### Nginx Proxy Manager
- URL: http://localhost:81
- Email: `admin@example.com`
- Password: `changeme`

## Struktur Project

```
bp-edu-odoo/
├── addons/              # Custom Odoo addons
├── third-party/         # Third-party addons
├── config/              # Configuration files
│   ├── nginx.conf       # Nginx configuration
│   └── odoo.conf        # Odoo configuration
├── Dockerfile           # Odoo image build
├── docker-compose.yml   # Docker services
├── CLAUDE.md            # AI Development guidelines
└── .env.example         # Environment template
```

## Development

### Custom Addons

Tempatkan custom addons di direktori `addons/`.

### Third-party Addons

Tempatkan third-party addons di direktori `third-party/`.

### Update Odoo Version

Edit `Dockerfile` untuk menggunakan versi Odoo yang berbeda.

## License

Proprietary - All rights reserved
