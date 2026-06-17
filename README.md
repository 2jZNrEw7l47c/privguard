# PrivGuard

**v1.0.0 — CLI edition** · [Changelog](CHANGELOG.md)

**Take back control of your personal information.**

PrivGuard is a command-line tool that automatically searches data broker websites, people-search engines, social platforms, and known data breach databases to find where your personal information is exposed. When it finds your data on a broker site, it can auto-submit opt-out / removal requests on your behalf using a real browser. After scanning, it generates a clear Excel report showing every exposure, what was found, and what actions were taken — all stored locally on your computer with no cloud accounts required.

---

## Table of Contents

1. [What PrivGuard Does](#what-privguard-does)
2. [Prerequisites](#prerequisites)
3. [Installation](#installation)
4. [First-Time Setup](#first-time-setup)
5. [Running a Scan](#running-a-scan)
6. [Submitting Removal Requests](#submitting-removal-requests)
7. [Generating a Report](#generating-a-report)
8. [Getting a HIBP API Key](#getting-a-hibp-api-key)
9. [Updating the Broker Database](#updating-the-broker-database)
10. [Runtime Files](#runtime-files)
11. [Troubleshooting](#troubleshooting)
12. [Security Notes](#security-notes)

---

## What PrivGuard Does

PrivGuard scans four categories of exposure:

| Category | What it checks |
|---|---|
| **Data Brokers** | 40+ people-search and data broker websites (Whitepages, Spokeo, BeenVerified, etc.) |
| **Data Breaches** | Known breach databases via the Have I Been Pwned (HIBP) API |
| **Social Platforms** | Public profile visibility on Facebook, LinkedIn, Twitter/X, and others |
| **Search Engines** | Whether your personal information appears in Google or Bing search results |

For each data broker where your information is found, PrivGuard attempts to auto-submit the opt-out removal form using a real browser (Playwright). If the site requires manual steps (like uploading a photo ID), it will tell you exactly what to do. Everything stays on your machine — no cloud, no subscription.

---

## Prerequisites

Before installing PrivGuard, make sure you have:

- **Python 3.11 or newer** — check with `python --version`
- **pip** — usually included with Python
- **Git** — to clone the repository
- **Playwright Chromium** — installed after setup (instructions below)
- A **Have I Been Pwned API key** for breach scanning (optional but strongly recommended — see [Getting a HIBP API Key](#getting-a-hibp-api-key))

---

## Installation

Open a terminal and run these commands one at a time:

```bash
# 1. Clone the repository
git clone https://github.com/your-org/privguard.git
cd privguard

# 2. Install PrivGuard and its Python dependencies
pip install -e .

# 3. Install the Chromium browser used for automated opt-outs
playwright install chromium
```

You can verify the installation worked:

```bash
privguard --help
```

You should see:

```
Usage: privguard [OPTIONS] COMMAND [ARGS]...

  PrivGuard — personal PII protection tool.

Options:
  --help  Show this message and exit.

Commands:
  init    First-time setup (create vault and database).
  user    Manage user profiles.
  scan    Scan for personal data exposures.
  submit  Submit opt-out removal requests.
  report  Generate an Excel exposure report.
```

---

## First-Time Setup

PrivGuard protects all your personal information with a master password. You set this once during `init`. **There is no password recovery** — if you forget it, you must start over.

### Step 1 — Initialise the vault

```bash
privguard init
```

Example terminal interaction:

```
Welcome to PrivGuard.

Choose a master password. This encrypts all personal information stored locally.
You will be asked for it every time you run a scan or generate a report.

Master password: ••••••••••••••
Confirm password: ••••••••••••••

Vault created at /Users/alice/.privguard/vault.enc
Database created at /Users/alice/.privguard/privguard.db

Setup complete. Next, add a user profile with: privguard user add
```

### Step 2 — Add a user profile

```bash
privguard user add
```

Example terminal interaction:

```
Master password: ••••••••••••••

Display name (e.g. "John Smith"): Alice Johnson

--- Personal information (used to search broker sites) ---
First name: Alice
Last name: Johnson
Date of birth (YYYY-MM-DD): 1985-03-22
City: Portland
State (2-letter abbreviation): OR
Zip code: 97201

--- Email addresses (press Enter with no input to finish) ---
Email 1: alice@gmail.com
Email 2: alice@work.com
Email 3:

--- Phone numbers (press Enter with no input to finish) ---
Phone 1: 503-555-0142
Phone 2:

Profile "Alice Johnson" saved.

You can add another profile with: privguard user add
Run a scan with: privguard scan --user "Alice Johnson"
```

You can add multiple people (family members, etc.) — each scan and report is kept separate.

---

## Running a Scan

A scan checks all configured sources for your personal information.

### Scan all sources for all users

```bash
privguard scan
```

### Scan a specific user

```bash
privguard scan --user "Alice Johnson"
```

### Scan only one source type

```bash
# Data brokers only
privguard scan --user "Alice Johnson" --source brokers

# HIBP breach database only
privguard scan --user "Alice Johnson" --source hibp

# Social platforms only
privguard scan --user "Alice Johnson" --source social

# Search engines only
privguard scan --user "Alice Johnson" --source search_engines
```

Example output during a broker scan:

```
Master password: ••••••••••••••

Scanning data brokers for Alice Johnson...

[1/44]  Whitepages .............. FOUND
[2/44]  Spokeo .................. not found
[3/44]  BeenVerified ............ FOUND
[4/44]  PeopleFinder ............ FOUND
[5/44]  Intelius ................ not found
...
[44/44] TruthFinder ............. FOUND

Scan complete.
  Exposures found:   18
  Not found:         26
  Run "privguard submit" to auto-submit opt-out requests.
```

Scans for large broker lists can take 10–20 minutes because PrivGuard waits between requests to avoid being blocked.

---

## Submitting Removal Requests

After a scan, use `submit` to send opt-out requests to all sites where your information was found.

```bash
privguard submit --user "Alice Johnson"
```

### What "auto-submit" means

For most broker sites, PrivGuard opens a real browser (invisibly, in the background), fills in your opt-out form, and submits it automatically. You do not need to do anything.

Some sites require extra steps that cannot be automated — for example, uploading a photo ID or clicking a link in a confirmation email. For these sites, PrivGuard will print clear manual instructions:

```
[MANUAL REQUIRED] Intelius
  Go to: https://intelius.com/opt-out/submit/
  Select "Individual" and search for your name.
  Check the box next to your listing and click "Remove This Record".
  You will receive a confirmation email within 72 hours.
```

### Re-submitting after a period of time

Data brokers re-add your information periodically (often every 3–6 months). Re-run `privguard scan` and `privguard submit` every few months to stay opted out.

---

## Generating a Report

```bash
privguard report --user "Alice Johnson"
```

This creates an Excel file in the current directory named:

```
PrivGuard_Report_Alice_Johnson_2026-06-15.xlsx
```

You can specify a different output folder:

```bash
privguard report --user "Alice Johnson" --output ~/Desktop/
```

### What each sheet contains

| Sheet | Contents |
|---|---|
| **Summary** | High-level counts: total sites checked, exposures found, auto-submitted, pending, manual actions needed, breaches found, and an overall Exposure Risk Score (LOW / MEDIUM / HIGH) |
| **Data Brokers** | Every broker site scanned — with status colour-coded (red = found, green = submitted/cleared, orange = manual required, yellow = pending email verification, grey = not found), opt-out URL, and submission date |
| **Breaches (HIBP)** | Every known data breach your email address appeared in — breach name, date, what data types were exposed, and a link to the HIBP entry |
| **Social Platforms** | Social media profiles that are publicly exposing personal information — platform, profile URL, and what fields are visible |
| **Search Engine Removals** | Search engine removal requests that were submitted, with status and submission date |

---

## Getting a HIBP API Key

Have I Been Pwned (HIBP) is a free service that tells you whether your email address appeared in a known data breach. Checking programmatically requires an API key.

**Cost:** approximately **$3.50 USD per month** (billed monthly, cancel any time).

**Why it is worth it:** HIBP tracks over 14 billion compromised accounts across 800+ breaches. Without an API key, PrivGuard cannot check whether your passwords or personal data have been leaked.

**How to get a key:**

1. Go to [https://haveibeenpwned.com/API/Key](https://haveibeenpwned.com/API/Key)
2. Enter your email address and complete the payment form
3. You will receive your API key by email within a few minutes
4. When you run `privguard user add`, you will be prompted to enter your HIBP API key — paste it there.

PrivGuard stores the key in your encrypted vault — it is never written to a plain-text file.

**Note:** HIBP requires a 6-second wait between API calls (rate limiting). PrivGuard handles this automatically — the breach scan will just take a bit longer if you have many email addresses.

---

## Updating the Broker Database

PrivGuard's list of broker sites lives in `data/brokers.json`. You can edit this file to add new sites, remove sites, or change how submissions work.

### Broker entry schema

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
| `name` | string | Display name shown in reports and terminal output |
| `category` | string | Always `"data_broker"` for broker entries |
| `opt_out_url` | string | URL of the opt-out or removal request page |
| `submission_method` | string | `"playwright"` for automated, `"manual"` for manual-only |
| `form_fields` | object | Maps HTML form field names to profile placeholders |
| `requires_email_verification` | boolean | `true` if the site sends a confirmation email |
| `requires_id_verification` | boolean | `true` if the site requires a photo ID |
| `manual_instructions` | string or null | Step-by-step instructions shown when `submission_method` is `"manual"` |

### Available profile placeholders for `form_fields`

| Placeholder | Value |
|---|---|
| `{first_name}` | User's first name |
| `{last_name}` | User's last name |
| `{full_name}` | First and last name joined with a space |
| `{city}` | City |
| `{state}` | Two-letter state abbreviation |
| `{zip}` | ZIP code |
| `{dob}` | Date of birth (YYYY-MM-DD) |
| `{primary_email}` | First email address in the user's profile |

---

## Runtime Files

PrivGuard stores all data under `~/.privguard/` (your home directory).

```
~/.privguard/
├── vault.enc          # Encrypted vault — contains ALL personal info (AES-256)
├── privguard.db       # SQLite database — scan results, statuses, URLs (NOT encrypted)
└── screenshots/       # Browser screenshots saved during opt-out submissions
    └── alice_johnson_whitepages_20260615_143022_123456.png
```

| File / Folder | Description |
|---|---|
| `vault.enc` | AES-256 encrypted file holding all user PII (names, emails, phone numbers, DOB, address). Protected by your master password. |
| `privguard.db` | SQLite database holding scan findings: which sites were checked, their opt-out URLs, submission statuses, and dates. Contains no raw personal information. |
| `screenshots/` | PNG screenshots captured by the Playwright browser when forms are submitted. Stored locally only — never uploaded anywhere. |

---

## Troubleshooting

### "Playwright browser not found" error

You need to install the Chromium browser that Playwright uses:

```bash
playwright install chromium
```

If you are on Linux and see a missing shared-library error, also run:

```bash
playwright install-deps chromium
```

---

### "Invalid master password" error

PrivGuard cannot recover a forgotten master password — this is by design, because your password is the only key to your encrypted vault.

If you have forgotten your master password, you must delete the vault and start over:

```bash
rm ~/.privguard/vault.enc
rm ~/.privguard/privguard.db
privguard init
```

**This permanently deletes all stored profiles and scan history.**

---

### "Rate limited" or slow HIBP scans

The Have I Been Pwned API requires a 6-second delay between requests. PrivGuard enforces this automatically, so breach scans are intentionally slow if you have many email addresses. This is normal — do not interrupt the scan.

If you receive an HTTP 429 (Too Many Requests) error despite the delay, wait 10 minutes and try again.

---

### Playwright form submission failing for a specific site

Some broker sites change their opt-out forms without notice, which can break automated submission. To work around this, switch that site to manual mode in `data/brokers.json`:

1. Open `data/brokers.json` in a text editor
2. Find the entry for the problem site
3. Change `"submission_method": "playwright"` to `"submission_method": "manual"`
4. Add step-by-step instructions in the `"manual_instructions"` field:

```json
{
  "id": "example-broker",
  "name": "Example Broker",
  "submission_method": "manual",
  "manual_instructions": "Go to https://example.com/remove, search for your name, click the listing, then click 'Request Removal'.",
  ...
}
```

5. Save the file — the change takes effect on the next scan.

If you find a fix, please open an issue or pull request so others benefit.

---

## Security Notes

### What IS encrypted

- **`~/.privguard/vault.enc`** — AES-256 encryption, key derived from your master password using PBKDF2-HMAC-SHA256 (600,000 iterations). Contains all PII: names, emails, phone numbers, date of birth, address.

### What is NOT encrypted

- **`~/.privguard/privguard.db`** — Plain SQLite database. Contains broker site names, opt-out URLs, submission statuses, and scan timestamps. Contains **no raw personal information** — it is safe to back up or inspect with any SQLite viewer (e.g. [DBeaver Community](https://dbeaver.io/)).

### What leaves your machine

| Action | Data sent externally | Destination |
|---|---|---|
| Broker opt-out submission | Your name, address, and/or email (as required by each broker's form) | The broker's website |
| HIBP breach scan | Your email address(es) | `haveibeenpwned.com` |
| Everything else | Nothing | — |

PrivGuard never sends data to Anthropic, GitHub, or any other third party. There is no telemetry, no analytics, and no update check.

### Screenshots

Screenshots taken during opt-out submissions are saved in `~/.privguard/screenshots/` and stored locally only. They may contain your personal information as it appeared on a broker's website. Do not share these files.
