# Perbandingan Addon Accounting Pihak Ketiga (`third-party/`)

Dokumen ini membandingkan grup-grup addon accounting yang ada di `third-party/`
(hasil ekstrak beberapa zip bundle) untuk membantu memutuskan mana yang dipakai,
terutama karena ada **2 konflik nyata** antar grup (lihat bagian "Konflik" di bawah).

## Ringkasan Grup

| Grup | Entry Point | Jumlah Modul | Vendor | Fokus |
|---|---|---|---|---|
| **ERP Heritage (`eh_account_*`)** | `eh_account_suite` | ~52 modul | ERP Heritage | Suite akuntansi IFRS/IAS lengkap (enterprise-grade) |
| **OdooMates (`om_account_*` + `om_*`)** | `om_account_accountant` | 7 modul | Odoo Mates / Walnut | Suite akuntansi ringkas ala Odoo Enterprise Community-port |
| **Base Accounting Kit** | `base_accounting_kit` | 1 modul (+ `dynamic_accounts_report`) | Cybrosys | Kit akuntansi all-in-one (Asset, Budget, Follow-up, PDC, dll dalam 1 modul) |
| **Payroll — OM** | `om_hr_payroll` + `om_hr_payroll_account` | 2 modul | Odoo Mates | Payroll generik |
| **Payroll — Community** | `hr_payroll_community` + `hr_payroll_account_community` | 2 modul | (lain) | Payroll generik (alternatif) |
| **Lain-lain (standalone)** | — | 17 modul | Beragam | Utility, tidak konflik dengan grup manapun |

---

## 1. Grup ERP Heritage (`eh_account_*`) — 52 modul

Entry point: **`eh_account_suite`** ("Odoo 19 Community Accounting Pro") — install satu ini, otomatis menarik semua di bawah.

Base wajib: **`eh_account_base`** ("Accounting Suite Base") — shared reporting engine, audit log, cache. Semua modul `eh_account_*` lain bergantung ke ini.

| Modul | Fungsi |
|---|---|
| `eh_account_setup` | Checklist onboarding setup akuntansi (26 task, 7 kategori) |
| `eh_account_dynamic_reports` | Laporan keuangan dinamis (P&L, Balance Sheet) berbasis SQL, cepat untuk ledger besar |
| `eh_account_dynamic_reports_pro` | Upgrade: jadwal laporan otomatis ke email/chat, compose laporan custom |
| `eh_account_dynamic_reports_budget` | Kolom budget-vs-actual di laporan dinamis |
| `eh_account_dashboard` | Dashboard KPI keuangan per company (cash, AR/AP aging, revenue) |
| `eh_account_reconcile_pro` | Bank reconciliation dengan 5-signal suggestion engine |
| `eh_account_bank_statement_import` | Import rekening bank: CSV, OFX, QIF, CAMT.053, MT940 |
| `eh_account_batch_payment` | Batch payment (gabung banyak pembayaran jadi satu batch, ekspor CSV bank) |
| `eh_account_collections` | Workbench collections (kanban) untuk piutang jatuh tempo |
| `eh_account_credit_limit` | Batas kredit customer, blokir invoice saat melebihi limit |
| `eh_account_recurring_invoices` | Invoice berulang otomatis (cron harian) |
| `eh_account_pdc` | Post Dated Cheque (cek mundur) — issued & received |
| `eh_account_portal_extra` | Portal customer: download statement PDF, saldo real-time |
| `eh_account_ap_automation` | Vendor bill automation — 3-way match PO vs goods-receipt vs invoice |
| `eh_account_approval` | Approval workflow multi-step untuk vendor bill & journal entry |
| `eh_account_assets_pro` | Fixed asset + IFRS 16 lease accounting, depresiasi otomatis |
| `eh_account_close_workflow` | Checklist tutup buku bulanan/tahunan dengan sign-off chain |
| `eh_account_year_end` | Tutup tahun fiskal, hitung laba bersih otomatis |
| `eh_account_fx_revaluation` | IAS 21 revaluasi FX periode akhir |
| `eh_account_intercompany` | Mirror invoice antar-company otomatis |
| `eh_account_intercompany_so_po` | Extend inter-company ke SO/PO |
| `eh_account_consolidation` | Konsolidasi laporan grup multi-entitas |
| `eh_account_budget_pro` | Budget multi-versi dengan PO encumbrance |
| `eh_account_einvoice_peppol` | E-invoicing Peppol BIS Billing 3.0 (UBL 2.1) |
| `eh_account_l10n_au_bas` | Laporan BAS Australia (pajak) |
| `eh_account_sepa_ct` / `eh_account_sepa_dd` | SEPA Credit Transfer / Direct Debit (XML ISO 20022) |
| `eh_account_ai_agent` / `_ai_budget` / `_ai_collections` | AI helper deterministik (anomaly detection, komentar variance budget, next-action collections) — tanpa API key |
| `eh_account_ecl` | IFRS 9 Expected Credit Loss |
| `eh_account_fair_value` | IFRS 13 Fair Value Measurement |
| `eh_account_deferred_tax` | IAS 12 Deferred Tax |
| `eh_account_provisions` | IAS 37 Provisions & Contingencies |
| `eh_account_revenue` / `_revenue_recurring` | IFRS 15 Revenue Recognition |
| `eh_account_borrowing_costs` | IAS 23 Borrowing Costs |
| `eh_account_grants` | IAS 20 Government Grants |
| `eh_account_inventory_nrv` | IAS 2 Inventory NRV write-down |
| `eh_account_investment_property` | IAS 40 Investment Property |
| `eh_account_held_for_sale` | IFRS 5 Held for Sale & Discontinued Operations |
| `eh_account_business_combination` | IFRS 3 / IAS 28 Business Combinations |
| `eh_account_events` | IAS 8 / IAS 10 Accounting Changes & Events |
| `eh_account_eps` | IAS 33 Earnings Per Share |
| `eh_account_share_based_payment` | IFRS 2 Share-based Payments |
| `eh_account_employee_benefits` | IAS 19 Employee Benefits |
| `eh_account_costing` | Standard costing & CVP |
| `eh_account_statements` | IAS 1 Primary Statements |
| `eh_account_disclosures` | Catatan laporan keuangan (IAS 24/IFRS 7/8/12) |
| `eh_account_audit_pack` | Audit trail hash chain + integrity scan |

**Terkait AI**: `eh_ai` (engine chat AI generik) dan `eh_ai_account` (tool AI khusus akuntansi) — **terpisah dari `eh_account_suite`**, tidak wajib.

> Grup ini SANGAT lengkap (fokus kepatuhan IFRS/IAS internasional) — cocok kalau butuh akuntansi standar internasional/multi-entitas yang detail.

---

## 2. Grup OdooMates (`om_account_*`) — 7 modul

Entry point: **`om_account_accountant`** ("Odoo 19 Accounting Community")

| Modul | Fungsi |
|---|---|
| `accounting_pdf_reports` | Laporan keuangan PDF dasar |
| `om_account_asset` | Manajemen aset & depresiasi |
| `om_account_budget` | Manajemen budget |
| `om_fiscal_year` | Fiscal year & lock date |
| `om_recurring_payments` | Pembayaran berulang |
| `om_account_daily_reports` | Cash Book, Day Book, Bank Book |
| `om_account_followup` | Customer follow-up management ⚠️ **konflik**, lihat bawah |

> Grup ini lebih ringkas/sederhana — cocok kalau cuma butuh fitur akuntansi dasar Odoo Enterprise yang di-community-kan, tanpa kompleksitas IFRS/IAS.

---

## 3. Base Accounting Kit — 1 modul besar

`base_accounting_kit` ("Odoo 19 Full Accounting Kit for Community") — satu modul all-in-one: Asset Management, Budget (via `base_account_budget`), PDC, Follow-up ⚠️ **konflik**, Multi Invoice, Cash Flow Report, dll — semua digabung jadi satu.

`dynamic_accounts_report` bergantung ke modul ini (laporan dinamis versi Cybrosys).

---

## 4. Payroll — 2 pilihan

| | OM Payroll | Community Payroll |
|---|---|---|
| Core | `om_hr_payroll` | `hr_payroll_community` |
| + Accounting | `om_hr_payroll_account` | `hr_payroll_account_community` |
| Depends | `mail`, `hr_holidays` | `hr_holidays` |

⚠️ **Konflik**: keduanya bikin record `decimal.precision` bernama "Payroll" — unique constraint bentrok kalau dua-duanya diinstall.

---

## ⚠️ Konflik yang Ditemukan

### A. Payroll
`hr_payroll_community` vs `om_hr_payroll` — sama-sama insert `decimal.precision(name='Payroll')`.
**Pilih salah satu**, tidak bisa dua-duanya.

### B. Customer Follow-up
`base_accounting_kit` (model `followup.line`, parent `account.followup`) vs
`om_account_followup` (model `followup.line` juga!, tapi parent `followup.followup`) —
**nama model persis sama** (`followup.line` → tabel `followup_line`) tapi field relasi ke parent beda.
Ini bentrok level skema ORM, bukan cuma data.

**Konsekuensi**: `base_accounting_kit` tidak bisa hidup berdampingan dengan `om_account_followup`
(dan otomatis `om_account_accountant`, karena itu dependency-nya).

---

## Rekomendasi Kombinasi

| Skenario | Pilihan |
|---|---|
| **A. Butuh kepatuhan IFRS/IAS lengkap** (perusahaan multi-negara/multi-entitas, audit ketat) | `eh_account_suite` (semua `eh_account_*`) + salah satu Payroll |
| **B. Cukup fitur akuntansi dasar ala Enterprise** (lebih ringan) | `om_account_accountant` (grup OM) + salah satu Payroll — **jangan install `base_accounting_kit`** |
| **C. Sudah pakai kit dari Cybrosys** | `base_accounting_kit` + `dynamic_accounts_report` — **jangan install `om_account_accountant`/`om_account_followup`** |

`eh_account_*` (ERP Heritage) tidak bentrok dengan `om_account_*` atau `base_accounting_kit`
secara model (nama model beda semua) — jadi **A bisa digabung dengan B atau C** kalau mau reporting
dasar dari OM/Cybrosys tetap dipakai bersamaan dengan IFRS engine dari ERP Heritage. Yang **tidak bisa**
digabung adalah **B dengan C** (follow-up bentrok), dan **kedua payroll sekaligus**.

---

## Modul Standalone (Tidak Terlibat Konflik)

| Modul | Fungsi |
|---|---|
| `account_reconcile_oca` + `account_statement_base` | OCA reconcile & bank statement base |
| `codeerts_transaction_flow_visualizer` | Peta visual alur dokumen Sales→Purchase→MRP→Accounting |
| `document_management_system` / `enhanced_document_management` | Manajemen dokumen |
| `helpdesk_mgmt` | Helpdesk/tiket |
| `onlyoffice_odoo` | Edit office file (Word/Excel/PPT) langsung di Odoo Documents |
| `sentry` | Kirim error Odoo ke Sentry |
| `ss_enterprise_theme` | Tema backend ala Enterprise (navbar putih, app icon) |
| `web_digital_sign` | Tanda tangan digital via touchscreen |
| `web_save_discard_button` | Tombol Save/Discard tambahan |
| `eh_edi_core` | Fondasi EDI (vault kredensial, EN16931 mapper) — dipakai `eh_account_einvoice_peppol` |

---

*Dibuat otomatis dari isi `__manifest__.py` masing-masing modul di `third-party/` per 2026-07-09.*
