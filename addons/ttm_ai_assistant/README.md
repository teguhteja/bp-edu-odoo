# TTM AI Assistant — Odoo 19 CE

Modul Odoo yang mengintegrasikan AI langsung ke dalam **chatter** (pesan internal) Odoo.
Ketik `@ai [perintah]` di kolom pesan record mana pun, dan AI akan membalas di thread yang sama.

---

## Fitur

- **@ai trigger** — deteksi otomatis di semua chatter
- **Context-aware** — AI mengetahui data record yang sedang dibuka
- **Tool calling** — AI dapat membaca, mencari, dan mengubah data Odoo
- **Non-blocking** — berjalan di background thread, UI tidak terkunci
- **Multi-provider** — Groq (gratis), OpenRouter, OpenAI
- **Webhook** — endpoint HTTP untuk integrasi eksternal

---

## Cara Setup API Key Groq (GRATIS)

Groq menyediakan API gratis dengan rate limit yang cukup untuk development.

1. Buka **https://console.groq.com**
2. Klik **Sign Up** (bisa pakai Google/GitHub)
3. Masuk ke dashboard → klik **API Keys** di sidebar kiri
4. Klik **Create API Key** → beri nama (contoh: "odoo-dev")
5. **Salin key** yang dihasilkan (format: `gsk_xxxx...`) — hanya tampil sekali!
6. Masukkan key tersebut di Settings Odoo (lihat langkah instalasi)

> **Rate limit Groq gratis:** ~30 req/menit, 6000 token/menit untuk `llama-3.3-70b-versatile`.
> Cukup untuk penggunaan development dan tim kecil.

---

## Instalasi

### 1. Rebuild container (karena ada module baru)

```bash
cd /path/to/bp-edu-odoo
podman compose build web
podman compose up -d
```

### 2. Update module list di Odoo UI

1. Buka Odoo → **Settings → Technical → Update Apps List**
2. Atau via URL: `/web#action=base.action_module_update`

### 3. Install modul

1. **Apps** → hapus filter "Apps" → cari **"TTM AI Assistant"**
2. Klik **Install**

### 4. (Alternatif) Install via command line

```bash
# Tampilkan command — JANGAN jalankan saat container sedang aktif serve traffic
podman compose exec web odoo -c /etc/odoo/odoo.conf \
  --update=ttm_ai_assistant \
  --stop-after-init \
  -d <nama_database>
```

---

## Konfigurasi

Setelah install, buka **Settings** → scroll ke bagian **TTM AI Assistant**:

| Field | Nilai Default | Keterangan |
|-------|--------------|------------|
| AI Provider | Groq | Pilih Groq (gratis), OpenRouter, atau OpenAI |
| API Key | *(kosong)* | Masukkan API key dari provider |
| Nama Model | `llama-3.3-70b-versatile` | Kosongkan = pakai default provider |
| Max Tokens | 2048 | Panjang maksimum respons |
| Temperature | 0.7 | 0.0 deterministik, 1.0 kreatif |
| System Prompt | *(default)* | Instruksi karakter AI |

Klik **Save** setelah mengisi API Key.

---

## Cara Penggunaan

Buka **record mana pun** di Odoo (Sale Order, Invoice, Partner, dll) dan ketik di chatter:

### Contoh Perintah

```
@ai siapa nama customer ini?
```
> AI membaca field `partner_id` dari record aktif dan menjawab.

```
@ai ubah priority field menjadi high
```
> AI memanggil tool `update_field` untuk mengubah priority.

```
@ai tampilkan 5 invoice terbaru customer ini
```
> AI mencari `account.move` dengan domain `partner_id = <id customer>`.

```
@ai buatkan activity call untuk besok jam 10
```
> AI membuat record `mail.activity` dengan `activity_type_id` untuk Phone Call.

```
@ai ringkasan data record ini
```
> AI membaca semua field dan merangkum dalam bahasa natural.

```
@ai berapa total semua sale order yang sudah confirmed bulan ini?
```
> AI mencari sale orders dengan domain state dan date filter.

### Format Trigger

- **Wajib** dimulai dengan `@ai` (tidak case-sensitive: `@AI`, `@Ai` juga valid)
- Spasi setelah `@ai` wajib ada
- Bisa di mana saja dalam pesan (tidak harus di awal baris, tapi direkomendasikan)
- Pesan boleh mengandung HTML formatting dari editor Odoo

---

## AI Tools yang Tersedia

AI dapat menggunakan 5 tools berikut secara otomatis:

| Tool | Fungsi |
|------|--------|
| `get_current_record_info` | Baca data record aktif saat @ai dipanggil |
| `search_records` | Cari records dengan filter (domain) |
| `read_record` | Baca detail satu record by ID |
| `update_field` | Update nilai field record |
| `create_record` | Buat record baru |

AI memilih tool yang tepat secara otomatis berdasarkan perintah user.

---

## Webhook API

Endpoint untuk integrasi eksternal (harus login Odoo terlebih dahulu):

```http
POST /ttm_ai/ask
Content-Type: application/json

{
    "jsonrpc": "2.0",
    "method": "call",
    "params": {
        "command": "Siapa customer dengan piutang terbesar?",
        "model": "sale.order",
        "id": 42
    }
}
```

Response:
```json
{
    "result": {
        "response": "<div>🤖 AI Assistant: ...</div>",
        "status": "ok"
    }
}
```

---

## Troubleshooting

### AI tidak merespons
1. Cek **Settings → AI Assistant** — pastikan API Key terisi
2. Lihat log Odoo: `podman compose logs -f web | grep -i "AI\|ttm_ai"`
3. Buka **Settings → Technical → AI Agents** → Test Koneksi

### Error "API Key tidak valid"
- Groq: pastikan format `gsk_...` (bukan bearer token)
- OpenRouter: format `sk-or-v1-...`
- OpenAI: format `sk-...`

### AI lambat merespons
- Normal: AI memproses di background, balasan muncul 3–15 detik
- Groq biasanya paling cepat (sub-second inference)
- Jika > 60 detik, kemungkinan timeout — cek koneksi internet server

### Error "Model tidak ditemukan"
- Groq: lihat daftar model di https://console.groq.com/docs/models
- OpenRouter: lihat di https://openrouter.ai/models
- Hapus field Nama Model di settings untuk kembali ke default

---

## Struktur File

```
addons/ttm_ai_assistant/
├── __init__.py
├── __manifest__.py
├── models/
│   ├── __init__.py
│   ├── ai_agent.py          ← Core LLM + tool calling
│   ├── mail_message.py      ← Intercept @ai trigger
│   └── res_config_settings.py ← Settings integration
├── controllers/
│   ├── __init__.py
│   └── webhook.py           ← HTTP API endpoint
├── views/
│   ├── ai_assistant_views.xml       ← AI Agents CRUD views
│   └── res_config_settings_views.xml ← Settings section
├── data/
│   └── ir_config_parameter.xml      ← Default values
└── security/
    └── ir.model.access.csv
```

---

## Provider Comparison

| Provider | Harga | Speed | Model Terbaik | Batas |
|----------|-------|-------|---------------|-------|
| **Groq** | **Gratis** | ⚡ Sangat cepat | `llama-3.3-70b-versatile` | 30 req/menit |
| OpenRouter | Pay-per-token | ⚡ Cepat | `deepseek/deepseek-chat` | Tidak ada (berbayar) |
| OpenAI | Pay-per-token | Normal | `gpt-4o-mini` | Tidak ada (berbayar) |

**Rekomendasi untuk mulai:** Gunakan **Groq** dengan model `llama-3.3-70b-versatile`.
