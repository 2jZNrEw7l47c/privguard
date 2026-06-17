# PrivGuard Web — Design Spec
**Date:** 2026-06-17
**Status:** Approved

---

## Overview

Replace the PrivGuard CLI and Excel reports with a local web dashboard. A FastAPI backend wraps the existing Python logic (vault, scanner, submitter, db) and exposes it as a REST/SSE API. A Next.js frontend provides the browser UI. Everything runs on localhost — no network exposure, no cloud, no installer.

---

## Goals

- Replace `privguard` CLI commands with a browser dashboard at `localhost:3000`
- Keep all existing Python logic unchanged (vault.py, submitter.py, db.py)
- Expand `brokers.json` from 44 to ~200 entries (marketing databases, phone lookup, mugshot/arrest sites)
- Add five more social platforms to scanner.py (Instagram, TikTok, Reddit, YouTube, Pinterest)
- Add ad network opt-out as a new scan source in scanner.py (NAI, DAA)
- Show live scan progress in the browser via Server-Sent Events
- Replace Excel reports with filterable in-browser tables
- Single command to start everything: `privguard serve`

---

## Non-Goals

- No network exposure (localhost only — no LAN sharing)
- No downloadable reports (dashboard replaces Excel entirely)
- No mobile-optimised layout
- No dark/light mode toggle (dark theme only)
- No cloud sync or remote access
- No user-level permissions (single master password controls everything)

---

## Architecture

```
online_security/
├── privguard/           # mostly unchanged — see Data Sources section for scanner.py additions
│   ├── vault.py         # UNCHANGED
│   ├── scanner.py       # MODIFIED: add social platforms + ad_networks source
│   ├── submitter.py     # UNCHANGED
│   ├── db.py            # UNCHANGED
│   └── __init__.py
├── api/                 # NEW — FastAPI application
│   ├── __init__.py
│   ├── app.py           # FastAPI instance, router registration, static mount
│   ├── auth.py          # Session management (unlock / lock)
│   ├── jobs.py          # Background task registry and SSE queue
│   └── routes/
│       ├── users.py     # User profile CRUD
│       ├── scan.py      # Scan endpoints
│       ├── submit.py    # Submission endpoints
│       └── findings.py  # Findings and breaches read endpoints
├── web/                 # NEW — Next.js application
│   ├── app/
│   │   ├── page.tsx                        # Login page (redirects to /dashboard if session active)
│   │   ├── dashboard/page.tsx              # All-profiles overview
│   │   ├── users/[name]/page.tsx           # User detail (tabbed: brokers, breaches, social, search)
│   │   ├── users/[name]/scan/page.tsx      # Live scan progress
│   │   ├── users/new/page.tsx              # Add profile form
│   │   └── tools/password-check/page.tsx  # Pwned Passwords checker (client-only, no API key)
│   ├── components/
│   │   ├── StatCards.tsx
│   │   ├── FindingsTable.tsx
│   │   ├── BreachList.tsx
│   │   ├── ScanProgress.tsx
│   │   ├── StatusBadge.tsx
│   │   └── PasswordChecker.tsx             # client component: SHA-1 hash → HIBP range check
│   ├── lib/
│   │   └── api.ts                          # Typed fetch wrappers for FastAPI
│   └── package.json
├── data/
│   └── brokers.json     # EXPANDED: ~44 → ~200 entries (see Data Sources section)
├── pyproject.toml       # adds fastapi, uvicorn to deps
└── README.md            # updated for web UI
```

---

## Data Sources (Expanded)

### brokers.json — expanded to ~200 entries

New categories added beyond the original 44 people-search sites:

| Category | Examples | Submission method |
|----------|----------|-------------------|
| Marketing / lead-gen databases | ZoomInfo, Clearbit, Apollo.io, Bombora, FullContact, Epsilon, Neustar, Acxiom, Oracle BlueKai | `manual` (require business email or verification) |
| Data aggregators / resellers | LexisNexis, CoreLogic, DataLogix, Versium, Equifax IXI, TransUnion TLO | `manual` |
| Phone lookup sites | Spy Dialer, NumLookup, USPhoneBook, 411.com, WhoCalledMe, AnyWho | `playwright` or `manual` |
| Address / property lookup | Addresses.com, PublicRecordsNow, USSearch, CheckPeople | `playwright` or `manual` |
| Mugshot / arrest record sites | MugshotLook, arrests.org, StateRecords.org, CourtCaseFinder, JustMugshots, BustedMugshots, MugshotZone, Mugshots.com | `manual` (ID verification required) |

All existing 44 entries are preserved. Only the JSON file changes — no code modifications to scanner.py or submitter.py.

### scanner.py — new and expanded sources

**Expanded social platforms** (`_SOCIAL_SITES` list):

Added to the existing Facebook, LinkedIn, Twitter/X entries:
- Instagram — `https://www.instagram.com/{name_slug}/`
- TikTok — `https://www.tiktok.com/@{name_slug}`
- Reddit — `https://www.reddit.com/search/?q={full_name}&type=user`
- YouTube — `https://www.youtube.com/results?search_query={full_name}`
- Pinterest — `https://www.pinterest.com/search/users/?q={full_name}`

All use the same Playwright page-content check already in `_scan_social`. No structural code changes.

**Ad network opt-outs** — new source `"ad_networks"`:

New `_scan_ad_networks()` function added to scanner.py, called when `source in (None, "ad_networks")`. Checks two opt-out endpoints via HTTP HEAD (same pattern as broker scanning):

| Site | ID | Opt-out URL | Method |
|------|----|-------------|--------|
| NAI (Network Advertising Initiative) | `nai_optout` | `https://optout.networkadvertising.org/` | `manual` |
| DAA (Digital Advertising Alliance) | `daa_optout` | `https://optout.aboutads.info/` | `manual` |
| Google Ad Personalization | `google_ads` | `https://adssettings.google.com/` | `manual` |
| Facebook Off-Facebook Activity | `facebook_offsite` | `https://www.facebook.com/off_facebook_activity/` | `manual` |

All four are `manual` — the sites require browser interaction or account login. They are stored with `status="manual_required"` and step-by-step `manual_instructions`. The `--source ad_networks` CLI/API flag selects only this source.

The `scan_user()` function in scanner.py gains one new branch:
```python
if source is None or source == "ad_networks":
    _scan_ad_networks(profile, force=force, db_path=db_path)
```

### HIBP Free Tier Features

Two HIBP features require no API key and are added at zero cost.

**1. Pwned Passwords checker**

Uses the [k-anonymity range API](https://haveibeenpwned.com/API/v3#PwnedPasswords): `GET https://api.pwnedpasswords.com/range/{first5}`. The full password is never sent anywhere — the browser hashes it with SHA-1, sends only the first 5 hex characters, and checks whether the remaining suffix appears in the response list.

This is implemented entirely in the browser (Next.js client component) — no FastAPI route needed, no backend changes. The flow:

```
User types password in browser
  → browser: SHA1(password) = "5BAA61E4C9B93F3F0682250B6CF8331B7EE68FD8"
  → browser fetch: GET https://api.pwnedpasswords.com/range/5BAA6
  → HIBP returns list of suffix:count pairs
  → browser checks if "1E4C9B93F3F0682250B6CF8331B7EE68FD8" is in list
  → shows: "⚠ Found in 3,861,493 breaches — change this password"
     or:   "✓ Not found in any known breach"
```

New page: `/tools/password-check` — text input, check button, result shown inline. Users can check multiple passwords in sequence; nothing is stored. A short explanation of k-anonymity ("your password never leaves your browser") is shown below the input.

**2. Public breach metadata enrichment**

`GET https://haveibeenpwned.com/api/v3/breaches` (no auth) returns the full list of all known breaches with metadata: logo URL, description, domain, pwn count, data classes. No personal data involved — this is a public catalogue.

Called once at dashboard load and cached in memory. Used to enrich the Breaches (HIBP) tab: each breach row gains the service's logo/favicon and a short description pulled from the public catalogue. No API key required.

This is a FastAPI-level cache (fetched server-side on startup, refreshed daily):

```python
# api/app.py — on startup
@app.on_event("startup")
async def _load_breach_catalogue():
    resp = requests.get("https://haveibeenpwned.com/api/v3/breaches", timeout=10)
    app.state.breach_catalogue = {b["Name"]: b for b in resp.json()}
```

The `/api/users/{name}/breaches` endpoint merges catalogue metadata into each breach record before returning it to the frontend.

---

## Backend: FastAPI (`api/`)

### Session / Auth

Master password is POSTed to `/api/auth/unlock`. FastAPI calls `privguard.vault.load_vault(password)` — if decryption succeeds the vault dict is stored in a server-side in-memory dict keyed by a random session token. The token is returned as an `httpOnly` cookie. All other endpoints extract the token from the cookie and look up the vault from memory.

Session lifetime: until server restart or `POST /api/auth/lock`. The password is never stored — only the already-decrypted vault dict lives in memory.

### API Routes

| Method | Path | Description |
|--------|------|-------------|
| `POST` | `/api/auth/unlock` | Accept master password, decrypt vault, set session cookie |
| `POST` | `/api/auth/lock` | Clear session (logout) |
| `GET` | `/api/users` | List profiles from in-memory vault |
| `POST` | `/api/users` | Add new profile, re-encrypt and save vault |
| `DELETE` | `/api/users/{name}` | Remove profile, re-encrypt and save vault |
| `POST` | `/api/users/{name}/scan` | Start background scan task, return `job_id`. Optional body: `{"source": "brokers"\|"hibp"\|"social"\|"search_engines"\|"ad_networks"}` |
| `POST` | `/api/users/{name}/submit` | Start background submission task, return `job_id` |
| `GET` | `/api/users/{name}/findings` | Return findings from SQLite |
| `GET` | `/api/users/{name}/breaches` | Return breaches from SQLite |
| `PATCH` | `/api/findings/{id}/status` | Manually update a finding status |
| `GET` | `/api/jobs/{job_id}/stream` | SSE stream — live progress events for a running job |

### Background Jobs and SSE

`POST /api/users/{name}/scan` launches an `asyncio` background task that runs the existing `scanner.scan_user()` function. A per-job `asyncio.Queue` is created before the task starts. The scanner publishes structured progress events to the queue:

```json
{"type": "progress", "broker": "Whitepages", "status": "found", "count": 3, "total": 44}
{"type": "done", "total_found": 18}
```

`GET /api/jobs/{job_id}/stream` opens an SSE connection and reads from that queue, forwarding each event to the browser. The browser can disconnect and reconnect — SQLite holds durable state, so reconnecting after a page refresh picks up the latest status even if the SSE stream is gone.

### Static File Serving (Production)

`api/app.py` mounts the Next.js `out/` directory (static export) under `/`. In production a single `uvicorn api.app:app --port 8000` serves everything on one port. In development, Next.js dev server runs on `:3000` with API proxied to `:8000`.

---

## Frontend: Next.js (`web/`)

**Tech:** Next.js 14+ (App Router), TypeScript, Tailwind CSS, SWR for data fetching.

### Pages

**Login (`/`)**
- Single password input, submit button
- POSTs to `/api/auth/unlock`
- On success redirects to `/dashboard`
- On failure shows inline error

**Dashboard (`/dashboard`)**
- One summary card per profile: name, exposure count, risk score, last scanned
- "Scan all" and "Submit all" buttons at the top
- Clicking a profile card navigates to `/users/[name]`

**User Detail (`/users/[name]`)**
- Header: display name, emails, city/state
- Five stat cards: Found · Submitted · Pending · Manual · Breaches
- Risk score banner (HIGH / MEDIUM / LOW)
- Tabbed table:
  - **Data Brokers** — site name, colour-coded status badge, opt-out URL, submission date, per-row Submit / View steps button
  - **Breaches (HIBP)** — email, breach name, date, exposed data types, HIBP link
  - **Social Platforms** — platform, profile URL, public fields exposed
  - **Search Engines** — engine, status, removal URL, date submitted
  - **Ad Networks** — network name, status, opt-out URL, manual instructions link
- "Run Scan" and "Submit Removals" buttons in header

**Scan Progress (`/users/[name]/scan`)**
- Live log: one line per site checked, grouped by source (brokers, social, ad networks, search engines)
- Progress bar: `N / ~200 brokers checked` (broker count only; other sources shown as separate counters)
- Auto-redirects back to user detail page when scan completes

**Add Profile (`/users/new`)**
- Form fields matching the vault schema: display name, full name, DOB, emails (multi-entry), phones (multi-entry), address, HIBP API key
- POSTs to `/api/users`
- On success redirects to `/dashboard`

**Password Checker (`/tools/password-check`)**
- Single password input field (masked), "Check Password" button
- Entirely client-side — no network call to FastAPI, no data stored
- On submit: hashes input with SHA-1 via Web Crypto API, fetches `https://api.pwnedpasswords.com/range/{first5}`, checks response for matching suffix
- Shows result: breach count if found (red warning), or "not found in any known breach" (green)
- Brief explainer under the input: "Your password is hashed locally and never sent anywhere. Only the first 5 characters of the hash are transmitted."
- Linked from the sidebar under a "Tools" section

### Status Colours

| Status | Colour |
|--------|--------|
| `found` | Red `#e85555` |
| `submitted` / `cleared` | Green `#44aa44` |
| `pending_verification` | Yellow `#ddcc00` |
| `manual_required` | Orange `#ff8800` |
| `not_found` | Grey `#666` |

---

## Starting the App

```bash
privguard serve
```

This command (added to `pyproject.toml` entry points) does:
1. Runs `uvicorn api.app:app --port 8000` in a subprocess
2. In development: runs `npm run dev` in `web/` on port 3000, opens `http://localhost:3000` in the default browser
3. In production (after `npm run build` + `next export`): skips Next.js dev server — FastAPI serves the static build on port 8000, opens `http://localhost:8000`

In development, `web/next.config.ts` includes an API rewrite so the browser's `/api/*` calls are proxied to `http://localhost:8000/api/*`:

```ts
// web/next.config.ts
const nextConfig = {
  async rewrites() {
    return [{ source: '/api/:path*', destination: 'http://localhost:8000/api/:path*' }]
  },
}
```

---

## Auth Flow (Detail)

```
Browser                  FastAPI                   Python (privguard)
  |                         |                              |
  | POST /api/auth/unlock   |                              |
  | {password: "..."}  ---> |                              |
  |                         | vault.load_vault(password)-> |
  |                         |                   <vault dict|
  |                         | sessions[token] = vault_dict |
  |                         | Set-Cookie: session=token    |
  | <--- 200 OK ------------|                              |
  |                         |                              |
  | GET /api/users          |                              |
  | Cookie: session=token-->|                              |
  |                         | vault = sessions[token]      |
  |                         | return vault["users"]        |
  | <--- [profile list] ----|                              |
```

---

## Dependencies (additions to pyproject.toml)

```
fastapi>=0.110
uvicorn[standard]>=0.29
python-multipart>=0.0.9    # form parsing
```

The existing `privguard` CLI entry point in `pyproject.toml` (`privguard.main:cli`) is replaced with `api.serve:main`, which is the function that starts uvicorn and optionally the Next.js dev server. The command name stays `privguard serve`.

New `package.json` in `web/`:
```
next@14
react@18
react-dom@18
typescript
tailwindcss
swr
```

---

## What Is Removed

- `privguard/main.py` — CLI entry point replaced by `privguard serve`
- `privguard/reporter.py` — Excel generation replaced by in-browser tables
- `tests/test_reporter.py` — reporter tests removed with the module

All other existing Python modules and tests are kept unchanged.

---

## Out of Scope

- Scheduled / automatic re-scans (user triggers manually from dashboard)
- Email inbox monitoring
- Proxy rotation
- International brokers
- PDF or Excel export
- LAN / multi-device access
