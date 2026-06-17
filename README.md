# PrivGuard

**v2.0.0 — Web Dashboard** · [Changelog](CHANGELOG.md)

**Take back control of your personal information.**

PrivGuard is a local web dashboard that scans data broker websites, people-search engines, social platforms, and known data breach databases to find where your personal information is exposed. When it finds your data, it can auto-submit opt-out / removal requests using a real browser. Everything runs on your own machine — no cloud account, no subscription, no telemetry.

---

## Quick Start

```bash
pip install -e .
npm install --prefix web
playwright install chromium
privguard serve
```

Open http://localhost:3000 and enter your master password to unlock the vault.

---

## Table of Contents

1. [What PrivGuard Does](#what-privguard-does)
2. [Prerequisites](#prerequisites)
3. [Installation](#installation)
4. [First-Time Setup](#first-time-setup)
5. [Using the Dashboard](#using-the-dashboard)
6. [Password Breach Check](#password-breach-check)
7. [Getting a HIBP API Key](#getting-a-hibp-api-key)
8. [Updating the Broker Database](#updating-the-broker-database)
9. [Runtime Files](#runtime-files)
10. [Troubleshooting](#troubleshooting)
11. [Security Notes](#security-notes)

---

## What PrivGuard Does

PrivGuard scans five categories of exposure:

| Category | What it checks |
|---|---|
| **Data Brokers** | 76+ people-search and data broker websites (Whitepages, Spokeo, BeenVerified, ZoomInfo, etc.) |
| **Data Breaches** | Known breach databases via the Have I Been Pwned (HIBP) API |
| **Social Platforms** | Public profile visibility on Facebook, LinkedIn, Twitter/X, Instagram, TikTok, Reddit, YouTube, Pinterest |
| **Search Engines** | Whether your personal information appears in Google or Bing search results |
| **Ad Networks** | Opt-out status for NAI, DAA, Google Ads, and Facebook Off-Site Activity |

For each data broker where your information is found, PrivGuard can auto-submit the opt-out removal form using a real browser (Playwright). Sites that require manual steps (e.g. uploading a photo ID) show clear instructions inline. Everything stays on your machine.

---

## Prerequisites

- **Python 3.11 or newer** — `python --version`
- **Node.js 18 or newer** — `node --version`
- **npm** — included with Node.js
- **Git** — to clone the repository
- A **Have I Been Pwned API key** for breach scanning (optional but recommended — see [Getting a HIBP API Key](#getting-a-hibp-api-key))

---

## Installation

```bash
# 1. Clone the repository
git clone https://github.com/your-org/privguard.git
cd privguard

# 2. Install Python dependencies
pip install -e .

# 3. Install frontend dependencies
npm install --prefix web

# 4. Install the Chromium browser used for automated opt-outs
playwright install chromium
```

Start the app:

```bash
privguard serve
```

This starts the FastAPI backend on port 8000 and the Next.js dev server on port 3000, then opens http://localhost:3000 in your default browser.

---

## First-Time Setup

### Step 1 — Create a vault

PrivGuard stores all personal information in an AES-256 encrypted vault protected by a master password. On first launch, the login page will prompt you to create one.

**There is no password recovery** — if you forget your master password, you must delete the vault and start over.

### Step 2 — Add a profile

After unlocking, click **Add Profile** in the sidebar. Fill in:

- Display name (required)
- Full name, date of birth, city/state
- One or more email addresses
- One or more phone numbers

Click **Save Profile**. You can add profiles for family members too — each person's findings are tracked separately.

---

## Using the Dashboard

### Dashboard

The home screen shows a summary card for each profile with counts of exposed, submitted, manual-required, and cleared findings. Click **View →** to open a profile's detail page.

### Running a Scan

On any profile's detail page, click **Scan**. The scan runs in the background and streams live progress to the browser. When it finishes, you are taken directly to the results.

Scans check all five sources (brokers, HIBP, social, search engines, ad networks). Expect 10–20 minutes for a full broker scan — PrivGuard waits between requests to avoid being blocked.

### Viewing Results

Results are shown in five tabs:

| Tab | Contents |
|---|---|
| **All** | Every finding across all sources |
| **Brokers** | Data broker findings with opt-out links and status |
| **Social** | Social platform profile visibility findings |
| **Ad Networks** | Ad network opt-out status |
| **Breaches** | HIBP breach records enriched with logos and descriptions |

Each finding has a status badge:

| Status | Meaning |
|---|---|
| **Found** | Your data was found and no action has been taken |
| **Submitted** | Opt-out request auto-submitted via Playwright |
| **Pending Verification** | Opt-out submitted; awaiting confirmation email from the broker |
| **Manual Required** | Broker requires a step (e.g. photo ID) that cannot be automated |
| **Cleared** | You have confirmed the listing was removed |
| **Not Found** | Checked and not found |

Click **Clear** on any finding to mark it as cleared after you confirm removal.

### Submitting Opt-Outs

Click **Submit Opt-Outs** on a profile's detail page. PrivGuard opens Playwright in the background and submits removal requests to every broker where your status is `found`. Progress streams live to the browser.

Sites that require manual action show their instructions inline in the Brokers tab — expand the row to see the steps.

### Re-scanning

Data brokers re-add your information periodically (typically every 3–6 months). Re-scan and re-submit every few months to stay opted out.

---

## Password Breach Check

Click **Password Check** in the sidebar. Enter any password to check whether it has appeared in a known data breach.

Your password is hashed (SHA-1) entirely in your browser. Only the first 5 characters of the hash are sent to HIBP's Pwned Passwords API. The rest is matched locally — your full password never leaves your device. No API key required.

---

## Getting a HIBP API Key

Have I Been Pwned (HIBP) checks whether your email address appeared in a known data breach. Scanning via the API requires a key.

**Cost:** approximately **$3.50 USD per month**.

**How to get a key:**

1. Go to https://haveibeenpwned.com/API/Key
2. Enter your email address and complete the payment form
3. You will receive your API key by email within a few minutes
4. Enter the key when adding a profile in the dashboard

PrivGuard stores the key in your encrypted vault — it is never written to a plain-text file.

**Note:** HIBP requires a 6-second wait between API calls. The breach scan will be slow if you have many email addresses — this is normal.

---

## Updating the Broker Database

The broker list lives in [data/brokers.json](data/brokers.json). Edit it to add sites, remove sites, or change how submissions work.

### Entry schema

```json
{
  "id": "unique-site-id",
  "name": "Human Readable Site Name",
  "category": "data_broker",
  "opt_out_url": "https://example.com/opt-out",
  "submission_method": "playwright",
  "form_fields": {
    "fname": "{first_name}",
    "lname": "{last_name}",
    "state": "{state}",
    "email": "{primary_email}"
  },
  "requires_email_verification": true,
  "requires_id_verification": false,
  "manual_instructions": null
}
```

### Field reference

| Field | Type | Description |
|---|---|---|
| `id` | string | Unique identifier (lowercase, hyphens OK) |
| `name` | string | Display name shown in the dashboard |
| `category` | string | `data_broker`, `marketing_database`, `phone_lookup`, etc. |
| `opt_out_url` | string | URL of the opt-out or removal request page |
| `submission_method` | string | `"playwright"` for automated, `"post"` for HTTP POST, `"manual"` for manual-only |
| `form_fields` | object | Maps HTML form field names to profile placeholders |
| `requires_email_verification` | boolean | `true` if the site sends a confirmation email |
| `requires_id_verification` | boolean | `true` if the site requires a photo ID |
| `manual_instructions` | string or null | Instructions shown inline when `submission_method` is `"manual"` |

### Profile placeholders

| Placeholder | Value |
|---|---|
| `{first_name}` | First name |
| `{last_name}` | Last name |
| `{full_name}` | First and last joined with a space |
| `{city}` | City |
| `{state}` | Two-letter state abbreviation |
| `{zip}` | ZIP code |
| `{dob}` | Date of birth (YYYY-MM-DD) |
| `{primary_email}` | First email address in the profile |

---

## Runtime Files

PrivGuard stores all data under `~/.privguard/` (your home directory).

```
~/.privguard/
├── vault.enc          # Encrypted vault — all personal info (AES-256)
├── privguard.db       # SQLite database — scan results, statuses, URLs
└── screenshots/       # Browser screenshots from opt-out submissions
```

| File | Description |
|---|---|
| `vault.enc` | AES-256 encrypted. Contains all PII: names, emails, phones, DOB, address. Protected by your master password. |
| `privguard.db` | Plain SQLite. Contains broker names, opt-out URLs, submission statuses, and dates. No raw personal information — safe to inspect with any SQLite viewer. |
| `screenshots/` | PNG screenshots from Playwright submissions. Stored locally only. May contain your personal information as it appeared on a broker's site — do not share. |

---

## Troubleshooting

### "Playwright browser not found"

```bash
playwright install chromium
```

On Linux, also run:

```bash
playwright install-deps chromium
```

---

### "Invalid master password" / vault locked

PrivGuard cannot recover a forgotten master password — your password is the only key.

To start over (this permanently deletes all profiles and scan history):

```bash
rm ~/.privguard/vault.enc
rm ~/.privguard/privguard.db
```

Then restart `privguard serve` and create a new vault.

---

### HIBP scan is slow or returns 429

The HIBP API requires a 6-second delay between requests — PrivGuard enforces this automatically. If you still receive a 429, wait 10 minutes and scan again.

---

### Playwright opt-out failing for a specific site

Some broker sites change their forms without notice. To switch a site to manual mode:

1. Open `data/brokers.json`
2. Find the entry and change `"submission_method": "playwright"` to `"submission_method": "manual"`
3. Add instructions in `"manual_instructions"`

The change takes effect on the next scan.

---

## Security Notes

### What IS encrypted

- **`~/.privguard/vault.enc`** — AES-256, key derived via PBKDF2-HMAC-SHA256 (600,000 iterations). All PII lives here.

### What is NOT encrypted

- **`~/.privguard/privguard.db`** — Plain SQLite. Contains site names, URLs, statuses, and timestamps. No raw PII.

### What leaves your machine

| Action | Data sent | Destination |
|---|---|---|
| Broker opt-out submission | Name, address, and/or email as required by each broker | The broker's website |
| HIBP breach scan | Your email address(es) | `haveibeenpwned.com` |
| Password breach check | First 5 hex chars of SHA-1 hash | `api.pwnedpasswords.com` |
| Everything else | Nothing | — |

PrivGuard never sends data to Anthropic, GitHub, or any other third party. No telemetry, no analytics, no update check.
