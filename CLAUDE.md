# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

CaritaHub AAC is an **Odoo 17** business application for community care management. It consists of ~97 custom modules in `caritahub/` and ~26 third-party modules in `third-party/`. The application manages members/clients, volunteers, activities, events, healthcare assessments, AI-powered features, and integrations with external services.

## Running the Application

This is an Odoo addon repository — it is loaded by an Odoo server instance, not run standalone. The Odoo server configuration (`.conf`) is gitignored and managed externally.

```bash
# Install dependencies
pip install -r requirements.txt
pip install -r requirements-ai.txt   # only if working on AI modules

# Typical Odoo commands (adjust paths to your local setup)
odoo -c /path/to/odoo.conf -u <module_name> -d <database>   # upgrade a module
odoo -c /path/to/odoo.conf -i <module_name> -d <database>   # install a module
odoo -c /path/to/odoo.conf --test-enable -u <module_name>   # run module tests
```

There is no project-level build, lint, or test command. Testing and linting follow standard Odoo conventions.

## Architecture

### Module Structure

Every custom module in `caritahub/` follows this layout:

```
caritahub/<module_name>/
├── __init__.py          # imports controllers, models, wizard, report
├── __manifest__.py      # metadata, dependencies, data files, assets
├── models/              # ORM model classes
├── views/               # XML view definitions (forms, lists, kanban, reports)
├── controllers/         # HTTP routes and API endpoints
├── data/                # XML seed/demo data
├── security/            # ir.model.access.csv (ACL rules)
├── static/              # CSS, JS, XML (QWeb) templates
├── wizard/              # Transient model wizards
└── report/              # PDF report templates
```

A blank module template is available at `templates/modules/caritahub_base/`.

### Key Modules & Dependency Chain

```
caritahub_base (auto_install, foundation)
  └─> caritahub_hr
      └─> caritahub_member (clients, events, workshops, volunteers)
          └─> caritahub_volunteer
              └─> caritahub_aac (activities & community — the main app)
```

- **caritahub_base** — shared tools (`tools/`), styles, user management, base models. Auto-installs.
- **caritahub_member** — core member/client management, events, workshops, push notifications.
- **caritahub_volunteer** — volunteer records and coordination.
- **caritahub_aac** — activities and community features (the primary application module).
- **caritahub_api / caritahub_api_gateway** — REST API layer with JWT authentication for mobile/web apps.
- **caritahub_ai_base** — AI configuration, prompts, and base AI infrastructure (LangChain, OpenAI, Google Cloud).

### API Layer

API controllers live in `caritahub_api/controllers/` and related API modules. Key patterns:

- JWT authentication: access tokens (60 min), refresh tokens (30 days), public tokens (5 min). See `cth_jwt_token.py`.
- Response helpers: `valid_response()` and `invalid_response()` from `caritahub_api/models/common.py`.
- Serializers in `cth_serializers.py` handle data formatting for API responses.

### Shared Utilities

`caritahub_base/tools/` contains reusable helpers:
- `validator.py` — email, NRIC, phone, postal code validation
- `date_time.py` — period calculations, date utilities
- `notification.py` — notification management
- `google_cloud_translate.py` / `translation.py` — multi-language support
- `qr.py` — QR code generation
- `nrc.py` — NRIC (National Registration Certificate) utilities

## Naming Conventions

These conventions were established during the Odoo 15 → 17 migration:

| Element         | Convention                     | Example                          |
|-----------------|--------------------------------|----------------------------------|
| Module name     | `caritahub_` prefix            | `caritahub_member`               |
| Python class    | `Cth` prefix                   | `CthUser`, `CthClient`          |
| Database table  | `cth.` or `cth_` prefix        | `cth.user`, `cth.client`        |
| View XML ID     | `cth.` / `cth_` prefix         | `cth.user_form_view`            |
| View file       | `_views.xml` suffix            | `cth_user_views.xml`            |
| Model file      | Match model name               | `cth_user.py`, `cth_program.py` |

Split models and views into separate files per entity (e.g., `cth_user.py` + `cth_user_views.xml`).

## Odoo 17 Specifics

Key differences from earlier Odoo versions (reference: `guidelines/Guide on migration odoo15 to odoo17.md`):

- **No `states` attribute** on fields — use `readonly`/`invisible` conditions in views instead.
- **No `attrs` in views** — use `attribute='condition'` format directly (e.g., `invisible="field == 'value'"`).
- **`name_get` is deprecated** — use `_compute_display_name` instead.
- **`_read_group` signature** — `fields` parameter renamed to `aggregates`.
- **New ORM methods**: `search_fetch()` and `fetch()`.
- **`fields_get`** — `fields` parameter renamed to `allfields`.
- **Email sending** — use `template_id.send_email(res_id, ...)` instead of `generate_email`.
- **Field tracking** — use `tracking=True` instead of `track_visibility="onchange"`.
- Avoid circular dependencies at module, view, and field levels. Use class inheritance to break cycles.

## External Integrations

The application integrates with: Google Cloud (Translate, TTS, Storage), Firebase (push notifications), AWS S3 (file storage), Twilio (SMS), FHIR (healthcare data standard), ElevenLabs (voice), OpenAI/LangChain (AI features), and various government/partner systems (PALM, Bright, VDMS/Feiyue, HSAR).

## Current Work: Dashboard Enhancement — Activity Insights

We are building new dashboard modules to add analytics blocks to the AAC admin portal. The first module is **Activity Insights** under the Activities menu.

### Spec & Planning Docs

- `docs/SPEC-activity-insights-module.md` — Full build spec for Claude Code (block definitions, XML refs, field mappings, colour palette, verification checklist)
- `docs/dashboard-data-suggestions.md` — Master suggestions doc covering all planned dashboard categories (section 2.1 is the approved Activity Insights spec)

### Module: `caritahub_aac_activity_insights`

**Location:** `caritahub/caritahub_aac_activity_insights/`
**Menu:** Activities > Activity Insights (sequence 99, end of top menus)
**Dependencies:** `caritahub_base`, `caritahub_aac`, `caritahub_dashboard`

The module is implemented with 12 dashboard blocks (4 tiles + 8 charts). Sequences use 10-unit gaps for easy insertion.

**4 Tiles (sequences 10-40, top row):**
| Seq | Name | Filter | Colour |
|-----|------|--------|--------|
| 10 | Total Attended | state = done | `#1CB27C` (green) |
| 20 | Unique Participants | count_distinct members, state = done | `#3A73D7` (blue) |
| 30 | No-Show Rate | state = No-Show | `#ED564D` (red) |
| 40 | Cancellations | state = cancel | `#FFA151` (orange) |

**8 Charts (sequences 50-120):**
| Seq | Name | Type | Group By |
|-----|------|------|----------|
| 50 | Top Activities | Bar | event (activity name) |
| 60 | Activity Fill Rate % | Bar | activity name, measures `fill_rate` |
| 70 | Attendance Trend | Line | register_date by month |
| 80 | No-Show Trend | Line | register_date by month |
| 90 | AAP Domain Distribution | Doughnut | aap_domain |
| 100 | Delivery Mode Split | Doughnut | event_mode (on cth.aac.activities) |
| 110 | New vs Returning Attendees | Doughnut | is_first_registration |
| 120 | Peak Attendance Hours | Bar | hour_of_day |

**Computed fields (added by this module via `_inherit`):**
- `is_first_registration` (Boolean, stored) on `cth.aac.activities.registration` — True if no earlier done registration exists for the same member
- `hour_of_day` (Integer, stored) on `cth.aac.activities.registration` — extracted from slot's `start_time` float field
- `fill_rate` (Float, stored) on `cth.aac.activities` — (registered / total slot vacancies) x 100, recomputed on registration create/write/unlink

**Tile icons:** SVG images in `static/src/img/` served via a Python model override (`models/cth_dashboard_block.py`) that extends `get_tile_vals` to inject `icon_image_top` paths by block name.

**Unified filters:** JS patch (`static/src/js/activity_insights_dashboard.js`) moves Period filter next to Centre filter at the top, hides the "Breakdown by period" section, and renames the title to "Activity Insights".

**Blocks NOT included (already on existing Dashboard):**
- Clients vs Non-clients — duplicate of "Member Attendances"

### Dashboard Block System

All dashboard blocks are records of `cth.dashboard.block` (defined in `caritahub_dashboard/models/cth_dashboard_block.py`). Key patterns:

- Each block references a `client_action` (ir.actions.client) — this determines which dashboard page it appears on
- The `caritahub_dashboard` tag reuses the same OWL component for rendering
- Tile icons are mapped by block `name` to PNG paths in `get_tile_vals()` via `image_top_map`
- Supported types: `tile`, `graph` (bar, line, pie, doughnut, stacked_bar, radar, 2_doughnuts), `table`, `kpi`, `kpi_2`
- Caching: 60-minute cache via `cth.kpi.dashboard.cache`
- Period & centre filters apply when `date_field` and `centre_field` are set on the block

### Registration Model State Values

The `state` field on `cth.aac.activities.registration` has these exact values (case-sensitive):
- `wait` — Waiting
- `unconfirm` — Pending
- `confirm` — Confirmed
- `No-Show` — No-Show (**capital N-S**)
- `done` — Attended
- `cancel` — Cancelled

### CaritaHub Brand Colours

| Colour | Hex | Usage |
|--------|-----|-------|
| Navy Blue | `#153276` | Primary brand, dark backgrounds |
| Dark Navy | `#25317E` | Chart accents |
| Blue Denim | `#3A73D7` | Primary chart colour, tiles |
| Medium Blue | `#3DA5F4` | Secondary blue |
| Green | `#1CB27C` | Success, positive metrics |
| Orange | `#FFA151` | Warnings, cancellations |
| Red | `#ED564D` | Alerts, no-shows |
| Indigo | `#6771DC` | Domain/category charts |
| Slate | `#64748B` | Neutral elements |

## Repository Layout

- `caritahub/` — all custom Odoo modules (~97)
- `third-party/` — external/OCA Odoo modules (~26, includes queue_job, auditlog, fs_storage, server_environment)
- `guidelines/` — migration guides and coding standards
- `templates/` — blank module template for scaffolding new modules
- `database/test/` — test database dumps
- `docs/` — dashboard specs and planning documents
