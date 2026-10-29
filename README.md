# Nidus Billing

**Complete multitenant billing for Costa Rica — operational invoices today, Hacienda e-invoice end-to-end.**

![Python 3.12+](https://img.shields.io/badge/python-3.12+-blue.svg)
![FastAPI](https://img.shields.io/badge/FastAPI-0.110+-009688.svg)
![PostgreSQL 17](https://img.shields.io/badge/PostgreSQL-17-336791.svg)
![Next.js 16](https://img.shields.io/badge/Next.js-16-black.svg)
![React 19](https://img.shields.io/badge/React-19-61DAFB.svg)
![TypeScript](https://img.shields.io/badge/TypeScript-5-3178C6.svg)
![Tailwind CSS](https://img.shields.io/badge/Tailwind-v4-38BDF8.svg)
![License](https://img.shields.io/badge/license-AGPL--3.0-blue.svg)

**Nidus Billing** is the first vertical product forked from [Nidus Core](https://github.com/Iskullgra09/nidus-core). It keeps the Core platform (IAM, tenants, RLS, Docker, FE shell) and builds a full billing system: parties, catalog, quotes, cash/credit invoices, PDF, email delivery, payments, fiscal org setup, and Costa Rica Hacienda (emit + receive + verify).

Platform capabilities stay aligned with Core via `upstream`. **Never** push billing domain back into `nidus-core`.

---

## Product vision

A tenant can manage customers and suppliers, sell with **contado** or **crédito** documents, number and collect payments, email the invoice to the customer, prove Hacienda linkage (clave / acceptance status), and later ingest supplier e-invoices (API + mailbox) to accept or reject them — all under RLS, scopes, audit, and EN/ES UI inside `modules/billing/`, wired into shell (Cmd+K, settings, dashboard).

Lightweight **catalog** (items/services + price) lives here. Stock/kardex belongs in a future `nidus-inventory` product — not in this repo.

---

## Product vs platform

| Repo | Role |
| :--- | :--- |
| **`nidus-core`** | Clone-ready platform (auth, IAM, tenancy, shell, observability) |
| **`nidus-billing`** (this repo) | Vertical product: full operational + fiscal billing |

Inherited FE modules: `identity` / `access` / `organization` / `shell`. Domain UI: `modules/billing/`.

Architecture decisions: `docs/architecture.md` (Core ADRs 001–059 = platform history; Billing ADRs = `B-xxx`, only when a concrete technical decision is made).

---

## Roadmap (Nidus Billing)

Phases are **product slices**, not Core’s old Phase 1–16 list. Status updates as each branch lands.

| Phase | Focus | Status |
| :---: | :--- | :--- |
| **B0** | Brand & side-by-side runtime | Done |
| **B1** | Parties & catalog | Done |
| **B2** | Operational docs (contado/crédito) + PDF | Planned |
| **B3** | Numbering, payments & balances | Planned |
| **B4** | Outbound email (send invoice) | Planned |
| **B5** | Org fiscal profile & Hacienda credentials | Planned |
| **B6** | Hacienda outbound (emit + verify) | Planned |
| **B7** | Hacienda inbound (receive / accept-reject) | Planned |
| **B8** | Inbound email mailbox (load supplier invoices) | Planned |
| **B9** | Hardening, UX polish, domain tests | Planned |

```text
B0 → B1 → B2 → B3 → B4
              ↘
               B5 → B6 → B7 → B8 → B9
```

Operational billing (B1–B4) can ship value before fiscal/Hacienda. Email send (B4) uses existing SMTP; Hacienda (B5–B7) and mailbox ingest (B8) build on that.

### B0 — Brand & side-by-side runtime

- Product named Nidus Billing; DB/roles/containers/ports distinct from Core.
- Docker DB+API healthy; FE login against Billing API.
- ADR B-001.

### B1 — Parties & catalog

**Backend:** customers + suppliers (proveedores); items/services (SKU, name, unit, price, tax hints); soft-delete; cursor pagination; scopes + RLS.  
**Frontend:** `modules/billing/` CRUD lists (URL-as-state), empty states, Cmd+K entries, EN/ES.  
**Out of scope:** stock, warehouses, kardex.

### B2 — Operational documents (contado / crédito) + PDF

**Backend:** quotes (optional); invoices with payment condition **contado** vs **crédito**; line items; operational status machine (draft → issued → … / void); PDF generation.  
**Frontend:** create/edit invoice UX, status badges, PDF download/preview.  
**Out of scope:** Hacienda XML, legal numbering series (B3/B6).

### B3 — Numbering, payments & balances

**Backend:** per-org document series / consecutive numbers; payments (full/partial); open balance; paid / partial / overdue / void.  
**Frontend:** payment capture, balance on invoice list/detail.  
**Out of scope:** full accounting ledger / journal entries.

### B4 — Outbound email (send invoice)

**Backend:** send issued invoice by email (PDF; later XML/clave when fiscal exists); delivery log per document; reuse Core SMTP settings.  
**Frontend:** “Send email” action, resend, delivery status.  
**Out of scope:** inbound mailbox (B8).

### B5 — Org fiscal profile & Hacienda credentials

**Backend:** CR fiscal fields per org (nombre, cédula/juridica, actividad económica, sucursal, etc.); encrypted store for `.p12` / API OAuth secrets; never commit secrets.  
**Frontend:** Organization → Fiscal / Hacienda settings UI.  
**Security:** app-role cannot read raw private keys in logs/audit metadata.  
**Out of scope:** live Hacienda calls (B6).

### B6 — Hacienda outbound (emit + verify)

**Backend:** build XML 4.4; sign; submit sandbox → prod; persist **clave numérica**, submission id, Hacienda response; status sync (aceptada / rechazada / procesando); **verify** action so the UI proves the document is linked to Hacienda; credit/debit notes as needed for corrections.  
**Frontend:** emit flow, Hacienda status badge, verify/detail panel, error surfacing.  
**Out of scope:** supplier reception (B7).

### B7 — Hacienda inbound (receive / accept-reject)

**Backend:** pull or receive supplier e-documents; map to supplier; accept/reject workflow against Hacienda; store XML + status.  
**Frontend:** inbox / bandeja, accept-reject actions, link to supplier record.  
**Out of scope:** email-based ingest (B8).

### B8 — Inbound email mailbox (load into the system)

**Goal:** invoices that arrive by email (or are forwarded to a dedicated org inbox) are parsed and loaded as inbound documents for review.

**Backend:** per-org inbound address or IMAP/webhook mailbox; parse attachments (XML preferred; PDF fallback metadata); dedupe by clave; create inbound draft linked to supplier when possible; notify tenant.  
**Frontend:** mailbox settings, “imported from email” badge, triage into B7 accept/reject.  
**Out of scope:** replacing Hacienda as source of truth — email is an ingest channel, verification still via Hacienda where applicable.

### B9 — Hardening, UX polish, domain tests

**Backend:** domain audit events; rate limits on emit/send/credential paths; pytest coverage for billing services & Hacienda adapter fakes.  
**Frontend:** dashboard widgets (open AR, recent emits, Hacienda failures); Cmd+K completeness; EN/ES polish; empty/error states.  
**Quality:** CI keeps backend + frontend gates; add billing-focused specs as modules land.

---

## Explicit non-goals (this product)

| Non-goal | Where it belongs |
| :--- | :--- |
| Stock / kardex / warehouses | Future `nidus-inventory` |
| Full accounting / asientos | Separate product or later expansion |
| Multi-country tax engines | Costa Rica first |
| Billing domain inside Core | Never — keep forks clean |

---

## Database Strategy (Dual DB + Dual Role)

Identifiers are **Billing-specific** so Core and Billing can run on the same machine:

| Database | Purpose | App user | Admin user |
| :--- | :--- | :--- | :--- |
| **`nidus_billing`** | Development & manual usage | `nidus_billing_app` (RLS) | `nidus_billing_admin` (migrations) |
| **`nidus_billing_test`** | pytest & CI only — truncated before each test | `nidus_billing_app` (RLS) | `nidus_billing_admin` (truncate/seed) |

**Never run pytest against `nidus_billing`.** The suite uses `TEST_APP_DATABASE_URL` / `TEST_DATABASE_URL`.

Containers: `nidus-billing-postgres` / `nidus-billing-api` (Compose project `nidus-billing`).

**Host ports (side-by-side with Core):** Postgres `5445`, API `8001`, FE `3001` (Core typically uses `5444` / `8000` / `3000`).

---

## Operational Command Center

Use these commands from the project root. Ensure your `.env` is present at the root.

### Deploy secrets checklist

Before any shared or production deploy:

- [ ] Copy `.env.example` → `.env` (never commit `.env`).
- [ ] Set a long random `SECRET_KEY` (JWT signing).
- [ ] Keep `ALGORITHM=HS256` unless you intentionally change the JWT stack.
- [ ] Use strong distinct `APP_PASSWORD` and `ADMIN_PASSWORD`.
- [ ] Set `FRONTEND_URL` to the real HTTPS origin (CORS + email links).
- [ ] Configure real SMTP credentials (or an approved relay) — required for B4+.
- [ ] Leave `RATE_LIMIT_ENABLED=true` in shared environments.
- [ ] Serve the frontend over HTTPS and keep session `Secure` (`NODE_ENV=production` or `COOKIE_SECURE=true`).
- [ ] Confirm `SEED_DEMO=false` outside local demo boxes.
- [ ] Hacienda credentials only via encrypted org settings (B5+) — never in git.

### Infrastructure (Docker)

Recommended flow: **DB + API in Docker**, frontend on the host with `pnpm`.

| Goal | Command |
| :--- | :--- |
| **Start DB + API** | `docker compose up -d --build` |
| **Start Only DB** (API via `uv` on host) | `docker compose up -d db` |
| **Stop Everything** | `docker compose stop` |
| **Full Wipe & Reset** | `docker compose down -v` |
| **View DB Logs** | `docker logs -f nidus-billing-postgres` |
| **View API Logs** | `docker logs -f nidus-billing-api` |
| **Rebuild API image** | `docker compose build api --no-cache` |
| **Seed demo data** | `docker compose exec api python seed.py` |
| **Wipe DB volume** | `docker compose down -v` then `up -d --build` |

API listens on `http://localhost:8001` by default (docs at `/docs`; override with `API_PORT`). Compose overrides `POSTGRES_SERVER=db` inside the API container; host `uv` workflows keep `POSTGRES_SERVER=localhost` from `.env`.

#### Demo accounts (after seed)

Password for **all** demo users: `password123`

| Email | Access |
| :--- | :--- |
| `owner@acme.dev` | Owner - Acme Corp |
| `admin@acme.dev` | Admin (+ `audit:read`) - Acme |
| `member@acme.dev` | Member - Acme |
| `viewer@acme.dev` | Viewer - Acme |
| `multi@nidus.dev` | Acme Owner + Nidus Labs Member (org picker) |
| `owner@nidus.dev` | Owner - Nidus Labs |
| `admin@nidus.dev` | Admin - Nidus Labs |
| `member@nidus.dev` | Member - Nidus Labs |
| `owner@beta.dev` | Owner - Beta Partners |
| `viewer@beta.dev` | Viewer - Beta Partners |

Pending invites: `invitee@acme.dev`, `contractor@nidus.dev`, `partner@beta.dev`.

Or set `SEED_DEMO=true` in `.env` so the API container seeds automatically on start.

### Backend Development (Python / uv)

From `backend/`:

| Goal | Command |
| :--- | :--- |
| **Install Deps** | `uv sync` |
| **Run Migrations (dev DB)** | `uv run alembic upgrade head` |
| **Run Migrations (test DB)** | `uv run python scripts/migrate_test_db.py` |
| **Create Migration** | `uv run alembic revision --autogenerate -m "description"` |
| **Run Seed Script** | `uv run seed.py` |
| **Run Seed Script on Docker** | `docker compose exec api python seed.py` |
| **Run API Locally** | `uv run fastapi dev app/main.py` |
| **Run Tests** | `uv run pytest` |

Point Cursor/VS Code at `backend/.venv/Scripts/python.exe` so imports resolve.

### Frontend Development (pnpm)

Run from `nidus-frontend/`:

| Goal | Command |
| :--- | :--- |
| **Install Deps** | `pnpm install` |
| **Dev Mode** | `pnpm dev -- --port 3001` |
| **Build Prod** | `pnpm build` |
| **Strict Typecheck** | `pnpm typecheck` |
| **Run Linter** | `pnpm lint` |
| **Add UI Component** | `pnpm dlx shadcn@latest add <component>` |
| **Clean cache** | `pnpm store prune` |

If port 3001 is already in use, another Billing FE is running — use it or kill that PID first. Core usually occupies `3000`.

### Maintenance & Cleanup

| Goal | Command |
| :--- | :--- |
| **Fix Line Endings** | `dos2unix infrastructure/db-init/*.sh` (If utility is installed) |
| **Prune Volumes** | `docker volume prune -f` |

---

## License

Copyright (c) 2026 Isaac Granados Quesada.

Nidus Billing is licensed under the **GNU Affero General Public License v3.0 (AGPL-3.0)** (same as Nidus Core).
See [`LICENSE`](LICENSE). If you run a modified version as a network service (SaaS), you must
offer the corresponding source to users of that service under the same license.

---

*Developed by Isaac Granados Quesada - Principal Engineer & Computer Architect.*
