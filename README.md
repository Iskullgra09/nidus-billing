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
| **B2** | Operational docs (contado/crédito) + PDF | Done |
| **B3** | Numbering, payments & balances | Done |
| **B4** | Outbound email (send invoice) | Done |
| **B5** | Org fiscal profile & Hacienda credentials | Done |
| **B6** | Hacienda outbound (emit + verify), CRC/USD whitelist, tax codes for XML | Done (mock emit; live XAdES gated) |
| **B6.1** | XAdES signer + sandbox live path; USD rate on FE; CABYS UI mínimo | Done (mock default; live gated) |
| **B7** | Hacienda inbound (receive / accept-reject) | Planned |
| **B8** | Inbound email mailbox (load supplier invoices) | Planned |
| **B9** | Hardening, UX polish, quotes→invoice, domain tests | Planned |
| **B10** | FX / BCCR rates + multi-currency AR reports | Planned |
| **B11** | Party enrichment (multi contact / address) | Planned |

```text
B0 → B1 → B2 → B3 → B4 → B5 → B6 → B6.1 → B7 → B8 → B9
                                                    ↘→ B10 FX (BCCR / reports)
                                                    ↘→ B11 parties
Add-ons (post-core): AP/OC, inventory, payroll, subscriptions, treasury
```

Operational billing (B1–B4) ships value before fiscal/Hacienda. B5 stores issuer identity and encrypted credentials. B6–B8 are the Hacienda critical path (B6.1 closes outbound before inbound). B9–B11 harden product quality after emit/receive work.

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

**Backend:** `POST /invoices/{id}/send-email` attaches PDF; `invoice_email_delivery` log (`sent` / `failed` / `mocked` when SMTP unset); reuses SMTP settings; audit `invoice_email.send`.  
**Frontend:** Send email on issued/partial/paid; delivery history on invoice detail; optional override recipient.  
**Out of scope:** inbound mailbox (B8); XML/clave (B6).

### B5 — Org fiscal profile & Hacienda credentials

**Backend:** CR fiscal fields per org (nombre, cédula/juridica, actividad económica, sucursal, etc.); encrypted store for `.p12` / API OAuth secrets; never commit secrets. Scopes `billing:fiscal:read|write` on Admin/Owner.  
**Frontend:** Organization → Fiscal / Hacienda settings UI.  
**Security:** app-role cannot read raw private keys in logs/audit metadata. Local/dev may fall back to a hash of `SECRET_KEY`; **production must set `CREDENTIALS_ENCRYPTION_KEY`**.  
**Existing orgs:** re-run `uv run seed.py` (or edit Admin role scopes) so Admin picks up `billing:fiscal:*`; then re-login.  
**Out of scope:** live Hacienda calls (B6); currency whitelist / FX (B6 / B10).

### B6 — Hacienda outbound (emit + verify)

**Backend:** `invoice_fiscal` beside the operational invoice; FE XML **4.4**; mock XAdES + mock MH client when `HACIENDA_LIVE=false`; persist **clave** (50 digits), consecutive, XML, MH status; **verify** polls/mock-accepts. Live submit gated by flag + B5 credentials (ATV pin → IdP password).  
**Currency:** whitelist **CRC | USD** (no FX engine yet).  
**Tax:** line `tax_code` (+ `cabys_code` column) for XML; `%` still for operational totals.  
**Frontend:** emit/verify actions, Hacienda badge + detail panel, currency selector.  
**ADR:** B-008 (dual operational + fiscal status); B-009 (test ladder + B6.1 scope).  
**Done when:** mock emit/verify end-to-end; clave persisted; UI surfaces fiscal status.  
**Not done here:** real XAdES, sandbox MH calls, USD `TipoCambio` on FE, CABYS picker UI.

### B6.1 — Close outbound (signer, sandbox, USD rate, CABYS mínimo)

**Goal:** safe path to real MH **sandbox** without jumping to B7/B8 or full B10.

1. **XAdES-EPES** via `signxml` + org `.p12` when present; mock marker when no cert (`HACIENDA_LIVE=false` default). Live emit refuses mock sign / missing `.p12`.
2. **Test ladder:** local mock (default) → MH sandbox with ATV test credentials + test `.p12` → production only with real org + `HACIENDA_LIVE`. Policy digest env (`HACIENDA_XADES_POLICY_*`) is placeholder until MH PDF digest is set.
3. **USD on FE:** invoice `exchange_rate` (+ `exchange_rate_date`) required for USD emit; XML `TipoCambio` filled. Manual entry only — **not** BCCR sync (**B10**).
4. **CABYS mínimo:** line `cabys_code` required at emit; optional item default copied onto lines; invoice/item forms expose the field. Rich CABYS catalog sync waits (B9 / later).
5. **Out of scope:** supplier reception (**B7**), inbound mailbox (**B8**), NC/ND full flows, BCCR multi-currency AR (**B10**).

**Shipped:** `signxml` XAdES + mock fallback; invoice FX fields + `TipoCambio`; CABYS on lines/items + emit gates; migration `d2e3f4a5b6c7`; demo seed CRC/USD FE-ready; unit + API tests.  
**Done when:** mock CI green; XAdES with test `.p12`; USD/CABYS block incomplete emit; UI captures rate + CABYS. ✅

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
**Frontend:** dashboard widgets (open AR, recent emits, Hacienda failures); Cmd+K completeness; EN/ES polish; empty/error states; richer invoice document UX (full-page route, print CSS); **quotes → invoice**; sparse in-app guidance on hard concepts (statuses, contado/crédito, issue vs void).  
**Quality:** CI keeps backend + frontend gates; add billing-focused specs as modules land.

### B10 — FX / tipo de cambio

**Backend:** BCCR (or configured) rates, rate date on documents, conversion helpers; multi-currency AR reporting.  
**Frontend:** rate display, reports that mix CRC and USD without lying about balances.  
**Boundary:** B6.1 may store a **document** exchange rate for FE XML when USD; B10 owns automatic BCCR sync and reporting that mixes CRC/USD without lying about balances.

### B11 — Party enrichment

**Backend:** multi phone / multi address on customers and suppliers (billing vs shipping) when fiscal or logistics need it.  
**Frontend:** party detail editors beyond a single phone/email.  
**Out of scope:** expanding party schema during B1–B5 (flat contact fields stay until this phase).

### Creation & ingest channels (how invoices enter the system)

| Channel | When | Notes |
| :--- | :--- | :--- |
| **Manual UI** | B2 now | Draft with ≥1 line → edit lines while draft → issue. Lines are not a separate document; they belong to the invoice. |
| **Outbound email** | B4 | Send issued PDF (later XML/clave). |
| **Hacienda XML emit** | B6 | Fiscal layer beside operational invoice. |
| **Hacienda inbound** | B7 | Supplier e-docs → accept/reject (not sales AR). |
| **Email mailbox ingest** | B8 | XML/PDF attachments → inbound drafts for triage. |

### UX convention (billing lists)

List tables share one interaction model: **row click → View**, menu = View / Edit / domain actions, Edit also reachable from View.

**Modular piece:** `DataTable` (`shared/components/layout/data-table.tsx`) exposes optional `onRowClick`. Each billing table (customers, suppliers, items, invoices) wires that callback + its own View dialog. The click behavior is shared; the “what you see” is domain-specific — not one mega-table component.

### Operational invoice statuses (B2/B3 — not Hacienda yet)

These are **commercial / AR** states on `invoice.status`. They are **not** Hacienda aceptada/rechazada (that arrives with `invoice_fiscal` in B6+).

| Status | Meaning | Typical next actions |
| :--- | :--- | :--- |
| **draft** | Editable; no commercial number yet | Edit, Issue, Delete |
| **issued** | Number assigned (`INV-######`); open balance = total | Pay, Void (if no payments), PDF |
| **partial** | Some payments applied; balance &gt; 0 | Pay more, PDF (void blocked if amount_paid &gt; 0) |
| **paid** | amount_paid covers total; balance 0 | PDF only (no more pay/void) |
| **void** | Cancelled commercially | PDF / view only |

**Overdue** is a **derived flag** (`is_overdue`), not a stored status: issued/partial + `due_date` &lt; today + balance &gt; 0.

**Actions today:**
- **View / row click** — read-only document detail (same data).
- **Edit** — draft only; form shaped like the invoice.
- **Issue** — draft → issued; allocates series number; freezes lines.
- **Register payment** — reduces balance; moves issued → partial → paid.
- **Void** — issued (and unpaid) → void; clears open balance for AR UI. Does **not** talk to Hacienda yet.
- **PDF** — renders current snapshot (works for any status with data).

**Invoice vs “transaction”:** in this product, the sales document is `invoice` (AR). Cash movement is `invoice_payment` (not a second invoice type). Full journal / GL “transactions” are out of scope until accounting add-ons. Hacienda emit/annul is a **parallel fiscal lifecycle** (B6), not a replacement of these operational states.

### Backlog notes (not yet a numbered phase)

Promoted: CRC|USD + tax codes → **B6**; dual operational+fiscal → **B6** (ADR B-008); XAdES + sandbox + USD rate on FE + CABYS UI mínimo → **B6.1** (ADR B-009); BCCR FX/reports → **B10**; party multi-contact → **B11**; richer invoice UX / quotes→invoice → **B9**.

Still parked (no phase yet):

- **Accounting ledger / journal:** explicit non-goal until add-ons; balances stay AR cash application (B3).
- **Import sales drafts from XML/file:** prefer aligning with B6/B8 parsers rather than a one-off upload helper.
- **Rich CABYS catalog sync** (search/sync MH codes beyond line field + item default): after B6.1 mínimo; not B7.
- **NC/ND emit workflows:** after outbound FE is solid (post B6.1).

---

## Product packaging: core vs add-ons

**Core (roadmap B0–B11):** customers/suppliers/catalog, **sales** invoices (AR), payments & balances, PDF/email, Costa Rica Hacienda emit/receive/mailbox, CRC|USD whitelist, FX later, party enrichment.

**Add-ons (post-core, not in the critical path):** purchase orders, supplier bills (AP), inventory/kardex, payroll (planillas), subscriptions, bank transfers/treasury. These get their own tables, scopes, and nav — never a boolean on `invoice`.

See ADR B-005 in `docs/architecture.md`.

## Explicit non-goals (this product)

| Non-goal | Where it belongs |
| :--- | :--- |
| Stock / kardex / warehouses | Future `nidus-inventory` / add-on |
| Full accounting / asientos | Separate product or later expansion |
| Purchase orders / AP payments | Post-B9 add-on (inbound FE is B7–B8 only) |
| Payroll / subscriptions / treasury | Post-B9 add-ons |
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
