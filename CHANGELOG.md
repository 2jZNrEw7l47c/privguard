# Changelog

All notable changes to PrivGuard are documented here.
Versioning follows [Semantic Versioning](https://semver.org/).

---

## [1.0.0] — 2026-06-17

Initial release. CLI-based tool for scanning personal data exposure and submitting opt-out requests.

### Features

**Vault**
- AES-256 encrypted local vault (`~/.privguard/vault.enc`)
- Master password via PBKDF2-HMAC-SHA256 (600,000 iterations), never stored on disk
- Unlimited user profiles per vault — each with unlimited emails, phone numbers, addresses, and aliases
- Atomic vault writes (crash-safe)

**Scanning**
- 44 US data broker sites scanned via HTTP HEAD
- Have I Been Pwned (HIBP) API v3 breach check across all email addresses
- Social platform public profile visibility check (Facebook, LinkedIn, Twitter/X) via Playwright
- Search engine removal guidance (Google "Results About You", Bing Content Removal)
- Interrupted scans resume from last completed site
- `--force` flag to re-scan already-checked sites

**Opt-out submission**
- Playwright headless Chromium for automated form fill and submit
- HTTP POST for simpler broker forms
- Manual instructions for sites requiring ID verification
- Timestamped browser screenshots saved to `~/.privguard/screenshots/`
- Email verification sites flagged as `pending_verification`
- Re-submission protection (skips already-submitted sites unless `--force`)

**Reports**
- Color-coded Excel reports via openpyxl (5 sheets)
- Sheets: Summary, Data Brokers, Breaches (HIBP), Social Platforms, Search Engine Removals
- Exposure Risk Score: LOW / MEDIUM / HIGH

**CLI**
- `privguard init` — first-time vault and database setup
- `privguard user add/list/remove` — manage profiles
- `privguard scan [--user] [--source] [--force]` — scan for exposures
- `privguard submit [--user] [--force]` — submit opt-out requests
- `privguard report [--user] [--output]` — generate Excel report

**Test suite**
- 149 tests, all passing
- Full TDD coverage across vault, db, scanner, submitter, reporter

---

## Upcoming

### [2.0.0] — planned

- Web dashboard replacing CLI (Next.js + FastAPI)
- ~200 data brokers (expanded from 44)
- 8 social platforms (expanded from 3)
- Ad network opt-outs (NAI, DAA, Google Ads, Facebook)
- Pwned Passwords checker (free, client-side, no API key)
- HIBP breach catalogue enrichment (logos, descriptions)
- Live scan progress via Server-Sent Events

### [2.1.0] — planned

- DeHashed dark web scanning (paid API)
- Email / username enumeration across 120+ platforms (holehe)
