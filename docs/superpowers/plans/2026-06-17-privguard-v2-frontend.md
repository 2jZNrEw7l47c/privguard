# PrivGuard v2.0.0 — Frontend Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Build the Next.js 14 web dashboard that talks to the FastAPI backend (from the backend plan) and replaces all CLI output with a visual interface.

**Architecture:** Next.js 14 App Router with TypeScript and Tailwind CSS. All data fetching uses `swr` for automatic revalidation. The session cookie is httpOnly (set by the backend) — the frontend never touches it directly. SWR config uses `credentials: "include"` globally. Pwned Passwords check runs entirely in the browser (Web Crypto API for SHA-1, k-anonymity request to HIBP). Dark theme only.

**Tech Stack:** Next.js 14 (App Router), TypeScript 5, Tailwind CSS 3, SWR 2, vitest, @testing-library/react, @testing-library/jest-dom

**Prerequisite:** Backend plan must be complete and `privguard serve` must start successfully before running the dev server.

---

## File Map

| File | Action | Purpose |
|------|---------|---------|
| `web/package.json` | Create | Next.js project manifest |
| `web/tsconfig.json` | Create | TypeScript configuration |
| `web/next.config.ts` | Create | API proxy rewrites for dev mode |
| `web/tailwind.config.ts` | Create | Dark theme Tailwind config |
| `web/vitest.config.ts` | Create | Vitest + JSDOM test runner config |
| `web/vitest.setup.ts` | Create | @testing-library/jest-dom matchers |
| `web/lib/types.ts` | Create | Shared TypeScript interfaces |
| `web/lib/api.ts` | Create | SWR fetcher + typed API helpers |
| `web/lib/hibp.ts` | Create | k-anonymity Pwned Passwords logic |
| `web/components/StatusBadge.tsx` | Create | Colour-coded status pill |
| `web/components/StatCards.tsx` | Create | Four summary count cards |
| `web/components/FindingsTable.tsx` | Create | Sortable findings grid |
| `web/components/BreachList.tsx` | Create | Breach cards with HIBP enrichment |
| `web/components/ScanProgress.tsx` | Create | SSE progress bar |
| `web/components/PasswordChecker.tsx` | Create | Client-side Pwned Passwords widget |
| `web/app/layout.tsx` | Create | Root layout with sidebar nav |
| `web/app/globals.css` | Create | Tailwind directives + dark base |
| `web/app/page.tsx` | Create | Login / unlock page |
| `web/app/dashboard/page.tsx` | Create | All-users overview |
| `web/app/users/[name]/page.tsx` | Create | User detail with tabs |
| `web/app/users/[name]/scan/page.tsx` | Create | Scan-in-progress with SSE |
| `web/app/users/add/page.tsx` | Create | Add-profile form |
| `web/app/tools/password-check/page.tsx` | Create | Pwned Passwords tool page |
| `web/__tests__/StatusBadge.test.tsx` | Create | Component unit tests |
| `web/__tests__/hibp.test.ts` | Create | k-anonymity logic unit tests |
| `web/__tests__/FindingsTable.test.tsx` | Create | Table render + sort tests |

---

## Task 1: Scaffold Next.js project

**Files:**
- Create: `web/package.json`
- Create: `web/tsconfig.json`
- Create: `web/next.config.ts`
- Create: `web/tailwind.config.ts`
- Create: `web/vitest.config.ts`
- Create: `web/vitest.setup.ts`
- Create: `web/app/globals.css`

No tests in this task — scaffold only.

- [ ] **Step 1: Create `web/package.json`**

```json
{
  "name": "privguard-web",
  "version": "2.0.0",
  "private": true,
  "scripts": {
    "dev": "next dev --port 3000",
    "build": "next build",
    "start": "next start --port 3000",
    "test": "vitest run",
    "test:watch": "vitest"
  },
  "dependencies": {
    "next": "14.2.3",
    "react": "^18.3.0",
    "react-dom": "^18.3.0",
    "swr": "^2.2.5"
  },
  "devDependencies": {
    "@testing-library/jest-dom": "^6.4.2",
    "@testing-library/react": "^15.0.6",
    "@testing-library/user-event": "^14.5.2",
    "@types/node": "^20.12.7",
    "@types/react": "^18.3.1",
    "@types/react-dom": "^18.3.0",
    "@vitejs/plugin-react": "^4.2.1",
    "autoprefixer": "^10.4.19",
    "jsdom": "^24.0.0",
    "postcss": "^8.4.38",
    "tailwindcss": "^3.4.3",
    "typescript": "^5.4.5",
    "vitest": "^1.5.0"
  }
}
```

- [ ] **Step 2: Create `web/tsconfig.json`**

```json
{
  "compilerOptions": {
    "lib": ["dom", "dom.iterable", "esnext"],
    "allowJs": true,
    "skipLibCheck": true,
    "strict": true,
    "noEmit": true,
    "esModuleInterop": true,
    "module": "esnext",
    "moduleResolution": "bundler",
    "resolveJsonModule": true,
    "isolatedModules": true,
    "jsx": "preserve",
    "incremental": true,
    "plugins": [{ "name": "next" }],
    "paths": { "@/*": ["./*"] }
  },
  "include": ["next-env.d.ts", "**/*.ts", "**/*.tsx", ".next/types/**/*.ts"],
  "exclude": ["node_modules"]
}
```

- [ ] **Step 3: Create `web/next.config.ts`**

```ts
import type { NextConfig } from "next";

const nextConfig: NextConfig = {
  async rewrites() {
    return [
      {
        source: "/api/:path*",
        destination: "http://localhost:8000/api/:path*",
      },
    ];
  },
};

export default nextConfig;
```

- [ ] **Step 4: Create `web/tailwind.config.ts`**

```ts
import type { Config } from "tailwindcss";

const config: Config = {
  darkMode: "class",
  content: [
    "./app/**/*.{ts,tsx}",
    "./components/**/*.{ts,tsx}",
    "./lib/**/*.{ts,tsx}",
  ],
  theme: {
    extend: {
      colors: {
        surface: "#0f1117",
        panel: "#1a1d27",
        border: "#2a2d3a",
        accent: "#6366f1",
        "accent-hover": "#818cf8",
        muted: "#6b7280",
        danger: "#ef4444",
        warning: "#f59e0b",
        success: "#22c55e",
      },
    },
  },
  plugins: [],
};

export default config;
```

- [ ] **Step 5: Create `web/vitest.config.ts`**

```ts
import { defineConfig } from "vitest/config";
import react from "@vitejs/plugin-react";
import path from "path";

export default defineConfig({
  plugins: [react()],
  test: {
    environment: "jsdom",
    setupFiles: ["./vitest.setup.ts"],
    globals: true,
  },
  resolve: {
    alias: { "@": path.resolve(__dirname, ".") },
  },
});
```

- [ ] **Step 6: Create `web/vitest.setup.ts`**

```ts
import "@testing-library/jest-dom";
```

- [ ] **Step 7: Create `web/app/globals.css`**

```css
@tailwind base;
@tailwind components;
@tailwind utilities;

:root {
  color-scheme: dark;
}

body {
  @apply bg-surface text-gray-100 antialiased;
}
```

- [ ] **Step 8: Create `web/postcss.config.js`**

```js
module.exports = {
  plugins: {
    tailwindcss: {},
    autoprefixer: {},
  },
};
```

- [ ] **Step 9: Install dependencies**

```bash
cd web && npm install
```

Expected: `node_modules/` created, no errors.

- [ ] **Step 10: Verify TypeScript compiles**

```bash
cd web && npx tsc --noEmit
```

Expected: no errors (only the empty project, so no TS files to check yet).

- [ ] **Step 11: Commit**

```bash
git add web/
git commit -m "chore: scaffold Next.js 14 project with TypeScript, Tailwind, Vitest"
```

---

## Task 2: Shared types and API layer — `web/lib/types.ts` + `web/lib/api.ts`

**Files:**
- Create: `web/lib/types.ts`
- Create: `web/lib/api.ts`

- [ ] **Step 1: Create `web/lib/types.ts`**

```ts
export interface Profile {
  display_name: string;
  full_name: string;
  date_of_birth: string;
  emails: string[];
  phone_numbers: string[];
  addresses: Address[];
  aliases: string[];
  ssn_last4: string;
}

export interface Address {
  street: string;
  city: string;
  state: string;
  zip: string;
  current: boolean;
}

export interface Finding {
  id: number;
  user_display_name: string;
  source: string;
  site_id: string;
  site_name: string;
  status: FindingStatus;
  opt_out_url: string | null;
  manual_instructions: string | null;
  last_checked: string | null;
  submitted_at: string | null;
}

export type FindingStatus =
  | "found"
  | "not_found"
  | "submitted"
  | "pending_verification"
  | "manual_required"
  | "cleared";

export interface Breach {
  id: number;
  user_display_name: string;
  email: string;
  breach_name: string;
  breach_date: string | null;
  exposed_fields: string;
  hibp_url: string | null;
  catalogue?: HibpBreachRecord | null;
}

export interface HibpBreachRecord {
  Name: string;
  Title: string;
  Domain: string;
  BreachDate: string;
  AddedDate: string;
  ModifiedDate: string;
  PwnCount: number;
  Description: string;
  LogoPath: string;
  DataClasses: string[];
  IsVerified: boolean;
  IsFabricated: boolean;
  IsSensitive: boolean;
  IsRetired: boolean;
  IsSpamList: boolean;
  IsMalware: boolean;
}

export interface ScanProgressEvent {
  type: "progress" | "done" | "error";
  source?: string;
  site?: string;
  status?: string;
  count?: number;
  total?: number;
  message?: string;
}
```

- [ ] **Step 2: Create `web/lib/api.ts`**

```ts
import type { Breach, Finding, FindingStatus, Profile } from "./types";

export const fetcher = (url: string) =>
  fetch(url, { credentials: "include" }).then((r) => {
    if (!r.ok) throw new Error(`${r.status} ${r.statusText}`);
    return r.json();
  });

export async function unlock(password: string): Promise<void> {
  const r = await fetch("/api/auth/unlock", {
    method: "POST",
    credentials: "include",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ password }),
  });
  if (!r.ok) {
    const body = await r.json().catch(() => ({}));
    throw new Error(body.detail ?? "Incorrect password.");
  }
}

export async function lock(): Promise<void> {
  await fetch("/api/auth/lock", { method: "POST", credentials: "include" });
}

export async function getUsers(): Promise<Profile[]> {
  return fetcher("/api/users");
}

export async function addUser(profile: Omit<Profile, never>): Promise<Profile> {
  const r = await fetch("/api/users", {
    method: "POST",
    credentials: "include",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(profile),
  });
  if (!r.ok) throw new Error(`Failed to add user: ${r.status}`);
  return r.json();
}

export async function removeUser(displayName: string): Promise<void> {
  const r = await fetch(`/api/users/${encodeURIComponent(displayName)}`, {
    method: "DELETE",
    credentials: "include",
  });
  if (!r.ok) throw new Error(`Failed to remove user: ${r.status}`);
}

export async function startScan(
  displayName: string,
  source?: string
): Promise<{ job_id: string }> {
  const r = await fetch(
    `/api/users/${encodeURIComponent(displayName)}/scan`,
    {
      method: "POST",
      credentials: "include",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ source: source ?? null }),
    }
  );
  if (!r.ok) throw new Error(`Failed to start scan: ${r.status}`);
  return r.json();
}

export async function startSubmit(
  displayName: string
): Promise<{ job_id: string }> {
  const r = await fetch(
    `/api/users/${encodeURIComponent(displayName)}/submit`,
    {
      method: "POST",
      credentials: "include",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({}),
    }
  );
  if (!r.ok) throw new Error(`Failed to start submit: ${r.status}`);
  return r.json();
}

export async function getFindings(displayName: string): Promise<Finding[]> {
  return fetcher(`/api/users/${encodeURIComponent(displayName)}/findings`);
}

export async function getBreaches(displayName: string): Promise<Breach[]> {
  return fetcher(`/api/users/${encodeURIComponent(displayName)}/breaches`);
}

export async function updateFindingStatus(
  findingId: number,
  status: FindingStatus
): Promise<void> {
  const r = await fetch(`/api/findings/${findingId}/status`, {
    method: "PATCH",
    credentials: "include",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ status }),
  });
  if (!r.ok) throw new Error(`Failed to update status: ${r.status}`);
}
```

- [ ] **Step 3: Commit**

```bash
git add web/lib/types.ts web/lib/api.ts
git commit -m "feat: add shared TypeScript types and API helper layer"
```

---

## Task 3: Pwned Passwords logic — `web/lib/hibp.ts`

**Files:**
- Create: `web/lib/hibp.ts`
- Create: `web/__tests__/hibp.test.ts`

- [ ] **Step 1: Write failing tests at `web/__tests__/hibp.test.ts`**

```ts
import { describe, it, expect, vi, beforeEach } from "vitest";
import { sha1Hex, checkPwnedPassword } from "../lib/hibp";

describe("sha1Hex", () => {
  it("hashes 'password' to known SHA-1", async () => {
    const hash = await sha1Hex("password");
    expect(hash.toUpperCase()).toBe(
      "5BAA61E4C9B93F3F0682250B6CF8331B7EE68FD8"
    );
  });

  it("hashes empty string to known SHA-1", async () => {
    const hash = await sha1Hex("");
    expect(hash.toUpperCase()).toBe(
      "DA39A3EE5E6B4B0D3255BFEF95601890AFD80709"
    );
  });
});

describe("checkPwnedPassword", () => {
  beforeEach(() => {
    vi.resetAllMocks();
  });

  it("returns count > 0 when suffix found in response", async () => {
    const hashOfPassword = "5BAA61E4C9B93F3F0682250B6CF8331B7EE68FD8";
    const prefix = hashOfPassword.slice(0, 5); // 5BAA6
    const suffix = hashOfPassword.slice(5);     // 1E4C9B93F3F0682250B6CF8331B7EE68FD8

    vi.stubGlobal(
      "fetch",
      vi.fn().mockResolvedValue({
        ok: true,
        text: async () => `${suffix}:42\r\nABCDE12345678901234567890123456789:1`,
      })
    );

    const count = await checkPwnedPassword("password");
    expect(count).toBe(42);
  });

  it("returns 0 when suffix not in response", async () => {
    vi.stubGlobal(
      "fetch",
      vi.fn().mockResolvedValue({
        ok: true,
        text: async () => "ABCDE12345678901234567890123456789:1",
      })
    );

    const count = await checkPwnedPassword("password");
    expect(count).toBe(0);
  });

  it("throws when HIBP API is unreachable", async () => {
    vi.stubGlobal(
      "fetch",
      vi.fn().mockRejectedValue(new Error("network error"))
    );

    await expect(checkPwnedPassword("password")).rejects.toThrow();
  });
});
```

- [ ] **Step 2: Run tests to verify they fail**

```bash
cd web && npm test
```

Expected: FAIL — `sha1Hex` and `checkPwnedPassword` not found.

- [ ] **Step 3: Create `web/lib/hibp.ts`**

```ts
const HIBP_RANGE_URL = "https://api.pwnedpasswords.com/range/";

export async function sha1Hex(text: string): Promise<string> {
  const encoder = new TextEncoder();
  const data = encoder.encode(text);
  const hashBuffer = await crypto.subtle.digest("SHA-1", data);
  const hashArray = Array.from(new Uint8Array(hashBuffer));
  return hashArray.map((b) => b.toString(16).padStart(2, "0")).join("");
}

export async function checkPwnedPassword(password: string): Promise<number> {
  const hash = (await sha1Hex(password)).toUpperCase();
  const prefix = hash.slice(0, 5);
  const suffix = hash.slice(5);

  const resp = await fetch(`${HIBP_RANGE_URL}${prefix}`, {
    headers: { "Add-Padding": "true" },
  });

  if (!resp.ok) {
    throw new Error(`HIBP API error: ${resp.status}`);
  }

  const body = await resp.text();
  const lines = body.split("\r\n");

  for (const line of lines) {
    const [lineSuffix, countStr] = line.split(":");
    if (lineSuffix === suffix) {
      return parseInt(countStr, 10);
    }
  }

  return 0;
}
```

- [ ] **Step 4: Run tests**

```bash
cd web && npm test
```

Expected: all PASSED

- [ ] **Step 5: Commit**

```bash
git add web/lib/hibp.ts web/__tests__/hibp.test.ts
git commit -m "feat: add k-anonymity Pwned Passwords checker (client-side SHA-1)"
```

---

## Task 4: StatusBadge component

**Files:**
- Create: `web/components/StatusBadge.tsx`
- Create: `web/__tests__/StatusBadge.test.tsx`

- [ ] **Step 1: Write failing tests at `web/__tests__/StatusBadge.test.tsx`**

```tsx
import { render, screen } from "@testing-library/react";
import { describe, it, expect } from "vitest";
import { StatusBadge } from "../components/StatusBadge";

describe("StatusBadge", () => {
  it("renders 'Found' label for found status", () => {
    render(<StatusBadge status="found" />);
    expect(screen.getByText("Found")).toBeInTheDocument();
  });

  it("renders 'Submitted' label for submitted status", () => {
    render(<StatusBadge status="submitted" />);
    expect(screen.getByText("Submitted")).toBeInTheDocument();
  });

  it("renders 'Cleared' label for cleared status", () => {
    render(<StatusBadge status="cleared" />);
    expect(screen.getByText("Cleared")).toBeInTheDocument();
  });

  it("renders 'Manual Required' for manual_required", () => {
    render(<StatusBadge status="manual_required" />);
    expect(screen.getByText("Manual Required")).toBeInTheDocument();
  });

  it("renders 'Pending Verification' for pending_verification", () => {
    render(<StatusBadge status="pending_verification" />);
    expect(screen.getByText("Pending Verification")).toBeInTheDocument();
  });

  it("renders 'Not Found' for not_found", () => {
    render(<StatusBadge status="not_found" />);
    expect(screen.getByText("Not Found")).toBeInTheDocument();
  });

  it("applies danger colour class for found status", () => {
    const { container } = render(<StatusBadge status="found" />);
    expect(container.firstChild).toHaveClass("bg-red-900");
  });

  it("applies success colour class for cleared status", () => {
    const { container } = render(<StatusBadge status="cleared" />);
    expect(container.firstChild).toHaveClass("bg-green-900");
  });
});
```

- [ ] **Step 2: Run tests to verify they fail**

```bash
cd web && npm test
```

Expected: FAIL — StatusBadge not found.

- [ ] **Step 3: Create `web/components/StatusBadge.tsx`**

```tsx
import type { FindingStatus } from "@/lib/types";

const LABELS: Record<FindingStatus, string> = {
  found: "Found",
  not_found: "Not Found",
  submitted: "Submitted",
  pending_verification: "Pending Verification",
  manual_required: "Manual Required",
  cleared: "Cleared",
};

const CLASSES: Record<FindingStatus, string> = {
  found: "bg-red-900 text-red-200",
  not_found: "bg-gray-800 text-gray-400",
  submitted: "bg-indigo-900 text-indigo-200",
  pending_verification: "bg-yellow-900 text-yellow-200",
  manual_required: "bg-orange-900 text-orange-200",
  cleared: "bg-green-900 text-green-200",
};

interface Props {
  status: FindingStatus;
}

export function StatusBadge({ status }: Props) {
  return (
    <span
      className={`inline-flex items-center rounded-full px-2.5 py-0.5 text-xs font-medium ${CLASSES[status]}`}
    >
      {LABELS[status]}
    </span>
  );
}
```

- [ ] **Step 4: Run tests**

```bash
cd web && npm test
```

Expected: all PASSED

- [ ] **Step 5: Commit**

```bash
git add web/components/StatusBadge.tsx web/__tests__/StatusBadge.test.tsx
git commit -m "feat: add StatusBadge component with colour-coded finding statuses"
```

---

## Task 5: StatCards component

**Files:**
- Create: `web/components/StatCards.tsx`

No separate tests — StatCards is pure presentational (4 cards, prop-driven). The dashboard page tests cover it indirectly.

- [ ] **Step 1: Create `web/components/StatCards.tsx`**

```tsx
interface Stat {
  label: string;
  value: number;
  accent?: "danger" | "warning" | "success" | "default";
}

const ACCENT_CLASSES = {
  danger: "text-red-400",
  warning: "text-yellow-400",
  success: "text-green-400",
  default: "text-indigo-400",
};

interface Props {
  stats: Stat[];
}

export function StatCards({ stats }: Props) {
  return (
    <div className="grid grid-cols-2 gap-4 sm:grid-cols-4">
      {stats.map((s) => (
        <div
          key={s.label}
          className="rounded-lg border border-border bg-panel p-4"
        >
          <p className="text-sm text-muted">{s.label}</p>
          <p
            className={`mt-1 text-3xl font-bold ${
              ACCENT_CLASSES[s.accent ?? "default"]
            }`}
          >
            {s.value}
          </p>
        </div>
      ))}
    </div>
  );
}
```

- [ ] **Step 2: Commit**

```bash
git add web/components/StatCards.tsx
git commit -m "feat: add StatCards summary component"
```

---

## Task 6: FindingsTable component

**Files:**
- Create: `web/components/FindingsTable.tsx`
- Create: `web/__tests__/FindingsTable.test.tsx`

- [ ] **Step 1: Write failing tests at `web/__tests__/FindingsTable.test.tsx`**

```tsx
import { render, screen, fireEvent } from "@testing-library/react";
import { describe, it, expect, vi } from "vitest";
import { FindingsTable } from "../components/FindingsTable";
import type { Finding } from "../lib/types";

const FINDINGS: Finding[] = [
  {
    id: 1,
    user_display_name: "Alice",
    source: "brokers",
    site_id: "whitepages",
    site_name: "Whitepages",
    status: "found",
    opt_out_url: "https://whitepages.com/opt-out",
    manual_instructions: null,
    last_checked: "2026-06-17T10:00:00",
    submitted_at: null,
  },
  {
    id: 2,
    user_display_name: "Alice",
    source: "brokers",
    site_id: "spokeo",
    site_name: "Spokeo",
    status: "cleared",
    opt_out_url: "https://spokeo.com/opt-out",
    manual_instructions: null,
    last_checked: "2026-06-17T10:00:00",
    submitted_at: "2026-06-17T10:05:00",
  },
];

describe("FindingsTable", () => {
  it("renders site names", () => {
    render(<FindingsTable findings={FINDINGS} onStatusChange={vi.fn()} />);
    expect(screen.getByText("Whitepages")).toBeInTheDocument();
    expect(screen.getByText("Spokeo")).toBeInTheDocument();
  });

  it("renders status badges", () => {
    render(<FindingsTable findings={FINDINGS} onStatusChange={vi.fn()} />);
    expect(screen.getByText("Found")).toBeInTheDocument();
    expect(screen.getByText("Cleared")).toBeInTheDocument();
  });

  it("renders opt-out links", () => {
    render(<FindingsTable findings={FINDINGS} onStatusChange={vi.fn()} />);
    const links = screen.getAllByRole("link");
    expect(links.some((l) => l.getAttribute("href")?.includes("whitepages"))).toBe(true);
  });

  it("filters by source", () => {
    render(
      <FindingsTable
        findings={FINDINGS}
        filter={{ source: "brokers" }}
        onStatusChange={vi.fn()}
      />
    );
    expect(screen.getByText("Whitepages")).toBeInTheDocument();
  });

  it("calls onStatusChange when status button clicked", () => {
    const onStatusChange = vi.fn();
    render(<FindingsTable findings={FINDINGS} onStatusChange={onStatusChange} />);
    const clearButtons = screen.getAllByTitle("Mark as cleared");
    fireEvent.click(clearButtons[0]);
    expect(onStatusChange).toHaveBeenCalledWith(1, "cleared");
  });

  it("shows empty state message when no findings", () => {
    render(<FindingsTable findings={[]} onStatusChange={vi.fn()} />);
    expect(screen.getByText(/no findings/i)).toBeInTheDocument();
  });
});
```

- [ ] **Step 2: Run tests to verify they fail**

```bash
cd web && npm test
```

Expected: FAIL — FindingsTable not found.

- [ ] **Step 3: Create `web/components/FindingsTable.tsx`**

```tsx
"use client";

import { useState } from "react";
import { StatusBadge } from "./StatusBadge";
import type { Finding, FindingStatus } from "@/lib/types";

interface Props {
  findings: Finding[];
  filter?: { source?: string; status?: FindingStatus };
  onStatusChange: (findingId: number, newStatus: FindingStatus) => void;
}

const SOURCES = ["all", "brokers", "hibp", "social", "search_engines", "ad_networks"] as const;

export function FindingsTable({ findings, filter, onStatusChange }: Props) {
  const [sourceFilter, setSourceFilter] = useState<string>(filter?.source ?? "all");

  const visible = findings.filter((f) => {
    if (sourceFilter !== "all" && f.source !== sourceFilter) return false;
    if (filter?.status && f.status !== filter.status) return false;
    return true;
  });

  if (visible.length === 0) {
    return (
      <div className="rounded-lg border border-border bg-panel p-8 text-center text-muted">
        No findings to display.
      </div>
    );
  }

  return (
    <div className="space-y-3">
      <div className="flex gap-2 flex-wrap">
        {SOURCES.map((s) => (
          <button
            key={s}
            onClick={() => setSourceFilter(s)}
            className={`rounded px-3 py-1 text-xs capitalize transition-colors ${
              sourceFilter === s
                ? "bg-accent text-white"
                : "bg-panel text-muted hover:text-gray-100 border border-border"
            }`}
          >
            {s.replace("_", " ")}
          </button>
        ))}
      </div>

      <div className="overflow-x-auto rounded-lg border border-border">
        <table className="w-full text-sm">
          <thead className="bg-panel text-muted text-left">
            <tr>
              <th className="px-4 py-3 font-medium">Site</th>
              <th className="px-4 py-3 font-medium">Source</th>
              <th className="px-4 py-3 font-medium">Status</th>
              <th className="px-4 py-3 font-medium">Opt-Out</th>
              <th className="px-4 py-3 font-medium">Last Checked</th>
              <th className="px-4 py-3 font-medium">Actions</th>
            </tr>
          </thead>
          <tbody className="divide-y divide-border">
            {visible.map((f) => (
              <tr key={f.id} className="hover:bg-panel/60 transition-colors">
                <td className="px-4 py-3 font-medium text-gray-100">
                  {f.site_name}
                </td>
                <td className="px-4 py-3 text-muted capitalize">
                  {f.source.replace("_", " ")}
                </td>
                <td className="px-4 py-3">
                  <StatusBadge status={f.status} />
                </td>
                <td className="px-4 py-3">
                  {f.opt_out_url ? (
                    <a
                      href={f.opt_out_url}
                      target="_blank"
                      rel="noopener noreferrer"
                      className="text-accent hover:text-accent-hover text-xs"
                    >
                      Opt-Out ↗
                    </a>
                  ) : (
                    <span className="text-muted text-xs">—</span>
                  )}
                </td>
                <td className="px-4 py-3 text-muted text-xs">
                  {f.last_checked
                    ? new Date(f.last_checked).toLocaleDateString()
                    : "—"}
                </td>
                <td className="px-4 py-3">
                  {f.status !== "cleared" && (
                    <button
                      title="Mark as cleared"
                      onClick={() => onStatusChange(f.id, "cleared")}
                      className="text-xs text-green-400 hover:text-green-300"
                    >
                      Clear
                    </button>
                  )}
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>

      {visible.some((f) => f.manual_instructions) && (
        <details className="rounded-lg border border-border bg-panel p-4">
          <summary className="cursor-pointer text-sm text-muted">
            Manual steps required for {visible.filter((f) => f.manual_instructions).length} site(s)
          </summary>
          <div className="mt-3 space-y-4">
            {visible
              .filter((f) => f.manual_instructions)
              .map((f) => (
                <div key={f.id}>
                  <p className="text-sm font-medium text-gray-100">{f.site_name}</p>
                  <pre className="mt-1 whitespace-pre-wrap text-xs text-muted">
                    {f.manual_instructions}
                  </pre>
                </div>
              ))}
          </div>
        </details>
      )}
    </div>
  );
}
```

- [ ] **Step 4: Run tests**

```bash
cd web && npm test
```

Expected: all PASSED

- [ ] **Step 5: Commit**

```bash
git add web/components/FindingsTable.tsx web/__tests__/FindingsTable.test.tsx
git commit -m "feat: add FindingsTable with source filter, status badge, manual instructions"
```

---

## Task 7: BreachList component

**Files:**
- Create: `web/components/BreachList.tsx`

- [ ] **Step 1: Create `web/components/BreachList.tsx`**

```tsx
import type { Breach } from "@/lib/types";

interface Props {
  breaches: Breach[];
}

export function BreachList({ breaches }: Props) {
  if (breaches.length === 0) {
    return (
      <div className="rounded-lg border border-border bg-panel p-8 text-center text-muted">
        No known breaches found for this user's email addresses.
      </div>
    );
  }

  return (
    <div className="space-y-3">
      {breaches.map((b) => {
        const fields: string[] = (() => {
          try {
            return JSON.parse(b.exposed_fields);
          } catch {
            return [];
          }
        })();

        return (
          <div
            key={b.id}
            className="flex items-start gap-4 rounded-lg border border-border bg-panel p-4"
          >
            {b.catalogue?.LogoPath && (
              <img
                src={b.catalogue.LogoPath}
                alt={b.catalogue.Title}
                className="h-10 w-10 rounded object-contain flex-shrink-0 bg-gray-800"
              />
            )}
            <div className="flex-1 min-w-0">
              <div className="flex items-center justify-between gap-2">
                <h3 className="font-semibold text-gray-100">
                  {b.catalogue?.Title ?? b.breach_name}
                </h3>
                {b.breach_date && (
                  <span className="text-xs text-muted flex-shrink-0">
                    {new Date(b.breach_date).toLocaleDateString("en-US", {
                      year: "numeric",
                      month: "short",
                    })}
                  </span>
                )}
              </div>
              <p className="text-xs text-muted mt-0.5">{b.email}</p>
              {b.catalogue?.Description && (
                <p
                  className="mt-1 text-xs text-gray-400 line-clamp-2"
                  dangerouslySetInnerHTML={{ __html: b.catalogue.Description }}
                />
              )}
              {fields.length > 0 && (
                <div className="mt-2 flex flex-wrap gap-1">
                  {fields.map((field) => (
                    <span
                      key={field}
                      className="rounded bg-gray-800 px-2 py-0.5 text-xs text-gray-400"
                    >
                      {field}
                    </span>
                  ))}
                </div>
              )}
            </div>
            {b.hibp_url && (
              <a
                href={b.hibp_url}
                target="_blank"
                rel="noopener noreferrer"
                className="text-xs text-accent hover:text-accent-hover flex-shrink-0"
              >
                Details ↗
              </a>
            )}
          </div>
        );
      })}
    </div>
  );
}
```

- [ ] **Step 2: Commit**

```bash
git add web/components/BreachList.tsx
git commit -m "feat: add BreachList component with HIBP catalogue enrichment"
```

---

## Task 8: ScanProgress component (SSE hook)

**Files:**
- Create: `web/components/ScanProgress.tsx`

- [ ] **Step 1: Create `web/components/ScanProgress.tsx`**

```tsx
"use client";

import { useEffect, useRef, useState } from "react";
import type { ScanProgressEvent } from "@/lib/types";

interface Props {
  jobId: string;
  onComplete: () => void;
}

export function ScanProgress({ jobId, onComplete }: Props) {
  const [events, setEvents] = useState<ScanProgressEvent[]>([]);
  const [current, setCurrent] = useState<ScanProgressEvent | null>(null);
  const [done, setDone] = useState(false);
  const containerRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    const es = new EventSource(`/api/jobs/${jobId}/stream`, {
      withCredentials: true,
    });

    es.onmessage = (e: MessageEvent) => {
      const event: ScanProgressEvent = JSON.parse(e.data);
      if (event.type === "done") {
        setDone(true);
        es.close();
        onComplete();
        return;
      }
      setCurrent(event);
      setEvents((prev) => [...prev.slice(-49), event]);
    };

    es.onerror = () => {
      es.close();
      setDone(true);
      onComplete();
    };

    return () => es.close();
  }, [jobId, onComplete]);

  useEffect(() => {
    if (containerRef.current) {
      containerRef.current.scrollTop = containerRef.current.scrollHeight;
    }
  }, [events]);

  const progressPercent =
    current?.count && current?.total
      ? Math.round((current.count / current.total) * 100)
      : null;

  return (
    <div className="space-y-4">
      <div className="flex items-center gap-3">
        {!done ? (
          <span className="inline-block h-3 w-3 animate-spin rounded-full border-2 border-accent border-t-transparent" />
        ) : (
          <span className="inline-block h-3 w-3 rounded-full bg-green-400" />
        )}
        <span className="text-sm text-gray-300">
          {done ? "Scan complete." : current?.site ? `Checking ${current.site}…` : "Starting…"}
        </span>
        {progressPercent !== null && !done && (
          <span className="ml-auto text-xs text-muted">
            {current?.count} / {current?.total}
          </span>
        )}
      </div>

      {progressPercent !== null && !done && (
        <div className="h-1.5 w-full rounded-full bg-gray-800">
          <div
            className="h-1.5 rounded-full bg-accent transition-all duration-300"
            style={{ width: `${progressPercent}%` }}
          />
        </div>
      )}

      <div
        ref={containerRef}
        className="h-48 overflow-y-auto rounded-lg border border-border bg-panel p-3 font-mono text-xs text-gray-400 space-y-0.5"
      >
        {events.map((e, i) => (
          <div key={i} className="flex gap-2">
            <span className="text-muted">{e.source}</span>
            <span className="text-gray-300">{e.site}</span>
            <span
              className={
                e.status === "found"
                  ? "text-red-400"
                  : e.status === "not_found"
                  ? "text-gray-500"
                  : "text-yellow-400"
              }
            >
              {e.status}
            </span>
          </div>
        ))}
        {done && (
          <div className="text-green-400 mt-1">— scan finished —</div>
        )}
      </div>
    </div>
  );
}
```

- [ ] **Step 2: Commit**

```bash
git add web/components/ScanProgress.tsx
git commit -m "feat: add ScanProgress component with SSE event stream and progress bar"
```

---

## Task 9: PasswordChecker component

**Files:**
- Create: `web/components/PasswordChecker.tsx`

- [ ] **Step 1: Create `web/components/PasswordChecker.tsx`**

```tsx
"use client";

import { useState } from "react";
import { checkPwnedPassword } from "@/lib/hibp";

type CheckState = "idle" | "checking" | "safe" | "pwned" | "error";

export function PasswordChecker() {
  const [password, setPassword] = useState("");
  const [state, setState] = useState<CheckState>("idle");
  const [count, setCount] = useState(0);
  const [error, setError] = useState("");

  async function handleCheck() {
    if (!password) return;
    setState("checking");
    setError("");
    try {
      const n = await checkPwnedPassword(password);
      setCount(n);
      setState(n > 0 ? "pwned" : "safe");
    } catch (e) {
      setError(e instanceof Error ? e.message : "Unknown error");
      setState("error");
    }
  }

  return (
    <div className="space-y-4">
      <p className="text-sm text-muted">
        Check if a password has appeared in a known data breach. Your password
        never leaves your browser — only an anonymised partial hash is sent to
        the{" "}
        <a
          href="https://haveibeenpwned.com/API/v3#PwnedPasswords"
          target="_blank"
          rel="noopener noreferrer"
          className="text-accent hover:underline"
        >
          HIBP Pwned Passwords API
        </a>
        .
      </p>

      <div className="flex gap-2">
        <input
          type="password"
          value={password}
          onChange={(e) => {
            setPassword(e.target.value);
            setState("idle");
          }}
          onKeyDown={(e) => e.key === "Enter" && handleCheck()}
          placeholder="Enter a password to check…"
          className="flex-1 rounded-lg border border-border bg-panel px-3 py-2 text-sm text-gray-100 placeholder:text-muted focus:border-accent focus:outline-none"
        />
        <button
          onClick={handleCheck}
          disabled={!password || state === "checking"}
          className="rounded-lg bg-accent px-4 py-2 text-sm font-medium text-white hover:bg-accent-hover disabled:opacity-50 transition-colors"
        >
          {state === "checking" ? "Checking…" : "Check"}
        </button>
      </div>

      {state === "pwned" && (
        <div className="rounded-lg border border-red-700 bg-red-950 p-4">
          <p className="font-semibold text-red-300">
            ⚠ This password has been seen {count.toLocaleString()} time
            {count !== 1 ? "s" : ""} in data breaches.
          </p>
          <p className="mt-1 text-sm text-red-400">
            You should not use this password anywhere. Change it immediately
            wherever it is in use.
          </p>
        </div>
      )}

      {state === "safe" && (
        <div className="rounded-lg border border-green-700 bg-green-950 p-4">
          <p className="font-semibold text-green-300">
            ✓ This password has not been found in any known breach.
          </p>
          <p className="mt-1 text-sm text-green-400">
            That's a good sign — but still use a unique password for every
            account.
          </p>
        </div>
      )}

      {state === "error" && (
        <div className="rounded-lg border border-yellow-700 bg-yellow-950 p-4">
          <p className="text-sm text-yellow-300">
            Could not reach HIBP API: {error}
          </p>
        </div>
      )}
    </div>
  );
}
```

- [ ] **Step 2: Commit**

```bash
git add web/components/PasswordChecker.tsx
git commit -m "feat: add PasswordChecker component (client-side k-anonymity check)"
```

---

## Task 10: Root layout and Login page

**Files:**
- Create: `web/app/layout.tsx`
- Create: `web/app/page.tsx`

- [ ] **Step 1: Create `web/app/layout.tsx`**

```tsx
import type { Metadata } from "next";
import "./globals.css";

export const metadata: Metadata = {
  title: "PrivGuard",
  description: "Personal data exposure tracker and opt-out manager.",
};

export default function RootLayout({
  children,
}: {
  children: React.ReactNode;
}) {
  return (
    <html lang="en" className="dark">
      <body>{children}</body>
    </html>
  );
}
```

- [ ] **Step 2: Create `web/app/page.tsx`** (login / unlock screen)

```tsx
"use client";

import { useState } from "react";
import { useRouter } from "next/navigation";
import { unlock } from "@/lib/api";

export default function LoginPage() {
  const router = useRouter();
  const [password, setPassword] = useState("");
  const [error, setError] = useState("");
  const [loading, setLoading] = useState(false);

  async function handleSubmit(e: React.FormEvent) {
    e.preventDefault();
    setLoading(true);
    setError("");
    try {
      await unlock(password);
      router.push("/dashboard");
    } catch (err) {
      setError(err instanceof Error ? err.message : "Incorrect password.");
    } finally {
      setLoading(false);
    }
  }

  return (
    <div className="flex min-h-screen items-center justify-center bg-surface px-4">
      <div className="w-full max-w-sm">
        <div className="mb-8 text-center">
          <div className="mx-auto mb-4 flex h-14 w-14 items-center justify-center rounded-full bg-accent/20">
            <span className="text-2xl">🔒</span>
          </div>
          <h1 className="text-2xl font-bold text-gray-100">PrivGuard</h1>
          <p className="mt-1 text-sm text-muted">
            Enter your master password to unlock the vault.
          </p>
        </div>

        <form onSubmit={handleSubmit} className="space-y-4">
          <input
            type="password"
            value={password}
            onChange={(e) => setPassword(e.target.value)}
            placeholder="Master password"
            autoFocus
            className="w-full rounded-lg border border-border bg-panel px-4 py-3 text-gray-100 placeholder:text-muted focus:border-accent focus:outline-none transition-colors"
          />

          {error && (
            <p className="text-sm text-red-400">{error}</p>
          )}

          <button
            type="submit"
            disabled={loading || !password}
            className="w-full rounded-lg bg-accent py-3 font-medium text-white hover:bg-accent-hover disabled:opacity-50 transition-colors"
          >
            {loading ? "Unlocking…" : "Unlock Vault"}
          </button>
        </form>
      </div>
    </div>
  );
}
```

- [ ] **Step 3: Commit**

```bash
git add web/app/layout.tsx web/app/page.tsx
git commit -m "feat: add root layout and login/unlock page"
```

---

## Task 11: Dashboard page

**Files:**
- Create: `web/app/dashboard/page.tsx`

- [ ] **Step 1: Create `web/app/dashboard/layout.tsx`** (shared sidebar for all authenticated pages)

```tsx
"use client";

import Link from "next/link";
import { useRouter } from "next/navigation";
import { lock } from "@/lib/api";

const NAV = [
  { href: "/dashboard", label: "Dashboard" },
  { href: "/users/add", label: "Add Profile" },
  { href: "/tools/password-check", label: "Password Check" },
];

export default function DashboardLayout({
  children,
}: {
  children: React.ReactNode;
}) {
  const router = useRouter();

  async function handleLock() {
    await lock();
    router.push("/");
  }

  return (
    <div className="flex min-h-screen">
      <aside className="w-56 shrink-0 border-r border-border bg-panel flex flex-col">
        <div className="px-5 py-6">
          <span className="text-lg font-bold text-gray-100">PrivGuard</span>
        </div>
        <nav className="flex-1 space-y-1 px-3">
          {NAV.map((item) => (
            <Link
              key={item.href}
              href={item.href}
              className="block rounded-md px-3 py-2 text-sm text-muted hover:bg-surface hover:text-gray-100 transition-colors"
            >
              {item.label}
            </Link>
          ))}
        </nav>
        <div className="p-4">
          <button
            onClick={handleLock}
            className="w-full rounded-md border border-border px-3 py-2 text-xs text-muted hover:text-gray-100 hover:border-gray-500 transition-colors"
          >
            Lock Vault
          </button>
        </div>
      </aside>
      <main className="flex-1 overflow-y-auto p-6">{children}</main>
    </div>
  );
}
```

- [ ] **Step 2: Create `web/app/dashboard/page.tsx`**

```tsx
"use client";

import Link from "next/link";
import useSWR from "swr";
import { StatCards } from "@/components/StatCards";
import { fetcher } from "@/lib/api";
import type { Finding, Profile } from "@/lib/types";

export default function DashboardPage() {
  const { data: users, error: usersError } = useSWR<Profile[]>("/api/users", fetcher);

  if (usersError) {
    return (
      <div className="text-red-400 text-sm">
        Failed to load profiles. Is the vault unlocked?
      </div>
    );
  }

  if (!users) {
    return <div className="text-muted text-sm">Loading…</div>;
  }

  if (users.length === 0) {
    return (
      <div className="flex flex-col items-center justify-center py-24 text-center">
        <p className="text-muted mb-4">No profiles added yet.</p>
        <Link
          href="/users/add"
          className="rounded-lg bg-accent px-5 py-2.5 text-sm font-medium text-white hover:bg-accent-hover"
        >
          Add First Profile
        </Link>
      </div>
    );
  }

  return (
    <div className="space-y-8">
      <h1 className="text-xl font-bold text-gray-100">Dashboard</h1>

      {users.map((user) => (
        <UserCard key={user.display_name} user={user} />
      ))}
    </div>
  );
}

function UserCard({ user }: { user: Profile }) {
  const { data: findings } = useSWR<Finding[]>(
    `/api/users/${encodeURIComponent(user.display_name)}/findings`,
    fetcher
  );

  const found = findings?.filter((f) => f.status === "found").length ?? 0;
  const submitted = findings?.filter((f) => f.status === "submitted").length ?? 0;
  const cleared = findings?.filter((f) => f.status === "cleared").length ?? 0;
  const manual = findings?.filter((f) => f.status === "manual_required").length ?? 0;

  return (
    <div className="rounded-lg border border-border bg-panel p-5 space-y-4">
      <div className="flex items-center justify-between">
        <div>
          <h2 className="font-semibold text-gray-100">{user.display_name}</h2>
          <p className="text-xs text-muted">{user.emails.join(", ")}</p>
        </div>
        <Link
          href={`/users/${encodeURIComponent(user.display_name)}`}
          className="text-sm text-accent hover:text-accent-hover"
        >
          View →
        </Link>
      </div>

      <StatCards
        stats={[
          { label: "Exposed", value: found, accent: "danger" },
          { label: "Submitted", value: submitted, accent: "default" },
          { label: "Manual", value: manual, accent: "warning" },
          { label: "Cleared", value: cleared, accent: "success" },
        ]}
      />
    </div>
  );
}
```

- [ ] **Step 3: Commit**

```bash
git add web/app/dashboard/layout.tsx web/app/dashboard/page.tsx
git commit -m "feat: add dashboard page with per-user stat cards"
```

---

## Task 12: User detail page with tabs

**Files:**
- Create: `web/app/users/[name]/page.tsx`

- [ ] **Step 1: Create `web/app/users/[name]/page.tsx`**

```tsx
"use client";

import Link from "next/link";
import { useParams, useRouter } from "next/navigation";
import { useState } from "react";
import useSWR, { mutate } from "swr";
import { BreachList } from "@/components/BreachList";
import { FindingsTable } from "@/components/FindingsTable";
import { fetcher, startScan, startSubmit, updateFindingStatus } from "@/lib/api";
import type { Breach, Finding, FindingStatus } from "@/lib/types";

const TABS = ["All", "Brokers", "Social", "Ad Networks", "Breaches"] as const;
type Tab = (typeof TABS)[number];

export default function UserDetailPage() {
  const params = useParams();
  const router = useRouter();
  const name = decodeURIComponent(params.name as string);

  const [activeTab, setActiveTab] = useState<Tab>("All");
  const [scanLoading, setScanLoading] = useState(false);
  const [submitLoading, setSubmitLoading] = useState(false);

  const findingsKey = `/api/users/${encodeURIComponent(name)}/findings`;
  const breachesKey = `/api/users/${encodeURIComponent(name)}/breaches`;

  const { data: findings } = useSWR<Finding[]>(findingsKey, fetcher);
  const { data: breaches } = useSWR<Breach[]>(breachesKey, fetcher);

  async function handleScan() {
    setScanLoading(true);
    try {
      const { job_id } = await startScan(name);
      router.push(`/users/${encodeURIComponent(name)}/scan?job=${job_id}`);
    } catch {
      setScanLoading(false);
    }
  }

  async function handleSubmit() {
    setSubmitLoading(true);
    try {
      const { job_id } = await startSubmit(name);
      router.push(`/users/${encodeURIComponent(name)}/scan?job=${job_id}&mode=submit`);
    } catch {
      setSubmitLoading(false);
    }
  }

  async function handleStatusChange(findingId: number, status: FindingStatus) {
    await updateFindingStatus(findingId, status);
    mutate(findingsKey);
  }

  const tabFindings = (() => {
    if (!findings) return [];
    if (activeTab === "Brokers") return findings.filter((f) => f.source === "brokers");
    if (activeTab === "Social") return findings.filter((f) => f.source === "social");
    if (activeTab === "Ad Networks") return findings.filter((f) => f.source === "ad_networks");
    return findings;
  })();

  return (
    <div className="space-y-6">
      <div className="flex items-start justify-between">
        <div>
          <h1 className="text-xl font-bold text-gray-100">{name}</h1>
          <Link
            href="/dashboard"
            className="text-xs text-muted hover:text-gray-300"
          >
            ← Dashboard
          </Link>
        </div>
        <div className="flex gap-2">
          <button
            onClick={handleScan}
            disabled={scanLoading}
            className="rounded-lg bg-accent px-4 py-2 text-sm font-medium text-white hover:bg-accent-hover disabled:opacity-50"
          >
            {scanLoading ? "Starting…" : "Scan"}
          </button>
          <button
            onClick={handleSubmit}
            disabled={submitLoading}
            className="rounded-lg border border-border px-4 py-2 text-sm text-muted hover:text-gray-100 disabled:opacity-50"
          >
            {submitLoading ? "Starting…" : "Submit Opt-Outs"}
          </button>
        </div>
      </div>

      <div className="flex gap-1 border-b border-border">
        {TABS.map((tab) => (
          <button
            key={tab}
            onClick={() => setActiveTab(tab)}
            className={`px-4 py-2 text-sm transition-colors ${
              activeTab === tab
                ? "border-b-2 border-accent text-gray-100"
                : "text-muted hover:text-gray-300"
            }`}
          >
            {tab}
            {tab === "Breaches" && breaches && breaches.length > 0 && (
              <span className="ml-1.5 rounded-full bg-red-900 px-1.5 py-0.5 text-xs text-red-300">
                {breaches.length}
              </span>
            )}
          </button>
        ))}
      </div>

      {activeTab === "Breaches" ? (
        <BreachList breaches={breaches ?? []} />
      ) : (
        <FindingsTable
          findings={tabFindings}
          onStatusChange={handleStatusChange}
        />
      )}
    </div>
  );
}
```

- [ ] **Step 2: Commit**

```bash
git add web/app/users/
git commit -m "feat: add user detail page with findings tabs and scan/submit buttons"
```

---

## Task 13: Scan-in-progress page

**Files:**
- Create: `web/app/users/[name]/scan/page.tsx`

- [ ] **Step 1: Create `web/app/users/[name]/scan/page.tsx`**

```tsx
"use client";

import Link from "next/link";
import { useParams, useRouter, useSearchParams } from "next/navigation";
import { useCallback, useState } from "react";
import { ScanProgress } from "@/components/ScanProgress";

export default function ScanPage() {
  const params = useParams();
  const searchParams = useSearchParams();
  const router = useRouter();
  const name = decodeURIComponent(params.name as string);
  const jobId = searchParams.get("job") ?? "";
  const mode = searchParams.get("mode") ?? "scan";

  const [done, setDone] = useState(false);

  const handleComplete = useCallback(() => {
    setDone(true);
  }, []);

  if (!jobId) {
    return (
      <div className="text-red-400 text-sm">
        No job ID provided. <Link href="/dashboard">← Dashboard</Link>
      </div>
    );
  }

  return (
    <div className="mx-auto max-w-xl space-y-6 pt-12">
      <h1 className="text-xl font-bold text-gray-100">
        {mode === "submit" ? "Submitting Opt-Outs" : "Scanning"} — {name}
      </h1>

      <ScanProgress jobId={jobId} onComplete={handleComplete} />

      {done && (
        <div className="flex gap-3">
          <Link
            href={`/users/${encodeURIComponent(name)}`}
            className="rounded-lg bg-accent px-5 py-2.5 text-sm font-medium text-white hover:bg-accent-hover"
          >
            View Results →
          </Link>
          <Link
            href="/dashboard"
            className="rounded-lg border border-border px-5 py-2.5 text-sm text-muted hover:text-gray-100"
          >
            Dashboard
          </Link>
        </div>
      )}
    </div>
  );
}
```

- [ ] **Step 2: Commit**

```bash
git add web/app/users/
git commit -m "feat: add scan-in-progress page with SSE live feed"
```

---

## Task 14: Add-profile page

**Files:**
- Create: `web/app/users/add/page.tsx`

- [ ] **Step 1: Create `web/app/users/add/page.tsx`**

```tsx
"use client";

import { useState } from "react";
import { useRouter } from "next/navigation";
import { addUser } from "@/lib/api";

export default function AddProfilePage() {
  const router = useRouter();
  const [error, setError] = useState("");
  const [loading, setLoading] = useState(false);

  const [form, setForm] = useState({
    display_name: "",
    full_name: "",
    date_of_birth: "",
    emails: [""],
    phone_numbers: [""],
    aliases: [] as string[],
    ssn_last4: "",
    addresses: [{ street: "", city: "", state: "", zip: "", current: true }],
  });

  function update(key: string, value: unknown) {
    setForm((prev) => ({ ...prev, [key]: value }));
  }

  function updateEmail(i: number, val: string) {
    const emails = [...form.emails];
    emails[i] = val;
    if (i === emails.length - 1 && val) emails.push("");
    update("emails", emails);
  }

  function updatePhone(i: number, val: string) {
    const phones = [...form.phone_numbers];
    phones[i] = val;
    if (i === phones.length - 1 && val) phones.push("");
    update("phone_numbers", phones);
  }

  async function handleSubmit(e: React.FormEvent) {
    e.preventDefault();
    setLoading(true);
    setError("");
    try {
      const payload = {
        ...form,
        emails: form.emails.filter(Boolean),
        phone_numbers: form.phone_numbers.filter(Boolean),
      };
      await addUser(payload);
      router.push("/dashboard");
    } catch (err) {
      setError(err instanceof Error ? err.message : "Failed to save profile.");
    } finally {
      setLoading(false);
    }
  }

  const field = "rounded-lg border border-border bg-panel px-3 py-2 text-sm text-gray-100 placeholder:text-muted focus:border-accent focus:outline-none w-full transition-colors";
  const label = "block text-xs text-muted mb-1";

  return (
    <div className="mx-auto max-w-xl space-y-6">
      <h1 className="text-xl font-bold text-gray-100">Add Profile</h1>

      <form onSubmit={handleSubmit} className="space-y-5">
        <div>
          <label className={label}>Display Name *</label>
          <input
            className={field}
            required
            value={form.display_name}
            onChange={(e) => update("display_name", e.target.value)}
            placeholder="Alice Johnson"
          />
        </div>

        <div>
          <label className={label}>Full Name</label>
          <input
            className={field}
            value={form.full_name}
            onChange={(e) => update("full_name", e.target.value)}
            placeholder="Alice Marie Johnson"
          />
        </div>

        <div>
          <label className={label}>Date of Birth (YYYY-MM-DD)</label>
          <input
            className={field}
            value={form.date_of_birth}
            onChange={(e) => update("date_of_birth", e.target.value)}
            placeholder="1985-03-22"
          />
        </div>

        <div className="grid grid-cols-2 gap-4">
          <div>
            <label className={label}>City</label>
            <input
              className={field}
              value={form.addresses[0].city}
              onChange={(e) =>
                update("addresses", [
                  { ...form.addresses[0], city: e.target.value },
                ])
              }
              placeholder="Portland"
            />
          </div>
          <div>
            <label className={label}>State</label>
            <input
              className={field}
              value={form.addresses[0].state}
              onChange={(e) =>
                update("addresses", [
                  { ...form.addresses[0], state: e.target.value.toUpperCase() },
                ])
              }
              placeholder="OR"
              maxLength={2}
            />
          </div>
        </div>

        <div>
          <label className={label}>Email Addresses</label>
          <div className="space-y-2">
            {form.emails.map((email, i) => (
              <input
                key={i}
                className={field}
                type="email"
                value={email}
                onChange={(e) => updateEmail(i, e.target.value)}
                placeholder={i === 0 ? "alice@gmail.com *" : "Additional email"}
              />
            ))}
          </div>
        </div>

        <div>
          <label className={label}>Phone Numbers</label>
          <div className="space-y-2">
            {form.phone_numbers.map((phone, i) => (
              <input
                key={i}
                className={field}
                type="tel"
                value={phone}
                onChange={(e) => updatePhone(i, e.target.value)}
                placeholder={i === 0 ? "503-555-0100" : "Additional phone"}
              />
            ))}
          </div>
        </div>

        {error && <p className="text-sm text-red-400">{error}</p>}

        <div className="flex gap-3 pt-2">
          <button
            type="submit"
            disabled={loading || !form.display_name}
            className="rounded-lg bg-accent px-5 py-2.5 text-sm font-medium text-white hover:bg-accent-hover disabled:opacity-50"
          >
            {loading ? "Saving…" : "Save Profile"}
          </button>
          <button
            type="button"
            onClick={() => router.back()}
            className="rounded-lg border border-border px-5 py-2.5 text-sm text-muted hover:text-gray-100"
          >
            Cancel
          </button>
        </div>
      </form>
    </div>
  );
}
```

- [ ] **Step 2: Commit**

```bash
git add web/app/users/add/page.tsx
git commit -m "feat: add profile creation form page"
```

---

## Task 15: Password check tool page + update README

**Files:**
- Create: `web/app/tools/password-check/page.tsx`
- Modify: `README.md`

- [ ] **Step 1: Create `web/app/tools/password-check/page.tsx`**

```tsx
import { PasswordChecker } from "@/components/PasswordChecker";

export default function PasswordCheckPage() {
  return (
    <div className="mx-auto max-w-lg space-y-6">
      <div>
        <h1 className="text-xl font-bold text-gray-100">Password Breach Check</h1>
        <p className="mt-1 text-sm text-muted">
          Powered by{" "}
          <a
            href="https://haveibeenpwned.com/Passwords"
            target="_blank"
            rel="noopener noreferrer"
            className="text-accent hover:underline"
          >
            Have I Been Pwned Pwned Passwords
          </a>
          . Free to use, no API key required.
        </p>
      </div>

      <PasswordChecker />

      <div className="rounded-lg border border-border bg-panel p-4 text-xs text-muted space-y-2">
        <p>
          <strong className="text-gray-400">How it works:</strong> Your
          password is hashed (SHA-1) in your browser. Only the first 5
          characters of the hash are sent to HIBP. The rest is compared
          locally — your full password never leaves your device.
        </p>
        <p>
          This technique is called{" "}
          <a
            href="https://en.wikipedia.org/wiki/K-anonymity"
            target="_blank"
            rel="noopener noreferrer"
            className="text-accent hover:underline"
          >
            k-anonymity
          </a>
          . It was designed by Troy Hunt and Cloudflare.
        </p>
      </div>
    </div>
  );
}
```

- [ ] **Step 2: Update `README.md`**

Replace the version header (first 3 lines) with:

```markdown
# PrivGuard

**v2.0.0 — Web Dashboard** · [Changelog](CHANGELOG.md)

**Take back control of your personal information.**

PrivGuard is a local web dashboard that automatically searches data broker websites, people-search engines, social platforms, and known data breach databases to find where your personal information is exposed. When it finds your data on a broker site, it can auto-submit opt-out / removal requests on your behalf. Everything stays on your machine — no cloud accounts required.

## Quick Start

```bash
pip install -e .
npm install --prefix web
playwright install chromium
privguard serve
```

Open http://localhost:3000. Enter your master password to unlock the vault.
```

- [ ] **Step 3: Commit**

```bash
git add web/app/tools/ README.md
git commit -m "feat: add password check tool page, update README for v2"
```

---

## Task 16: Smoke test — run the full app

**Files:** None (integration verification only)

- [ ] **Step 1: Start the FastAPI backend**

```bash
uvicorn api.app:app --port 8000 --reload &
```

Expected: starts without error, HIBP catalogue fetch completes (or silently falls back).

- [ ] **Step 2: Start the Next.js dev server**

```bash
cd web && npm run dev
```

Expected: starts on port 3000, no build errors.

- [ ] **Step 3: Run frontend tests**

```bash
cd web && npm test
```

Expected: all tests PASS (hibp tests + StatusBadge + FindingsTable)

- [ ] **Step 4: TypeScript check**

```bash
cd web && npx tsc --noEmit
```

Expected: no errors.

- [ ] **Step 5: Manual walkthrough**

Open `http://localhost:3000` and verify:

1. Login page loads with password input
2. Entering a wrong password shows an error message
3. Entering the correct master password redirects to `/dashboard`
4. Dashboard shows user cards (or "no profiles" prompt)
5. Click "Add Profile" → form renders → submit creates a profile → back to dashboard
6. Click a user card → tabs render (All / Brokers / Social / Ad Networks / Breaches)
7. Click "Scan" → redirects to `/users/{name}/scan?job={id}` → SSE progress scrolls
8. After scan completes, "View Results" button appears
9. Click "View Results" → findings table populated
10. Click "Password Check" in sidebar → PasswordChecker widget renders
11. Enter "password" into the checker → "has been seen N times" shown
12. Click "Lock Vault" → redirects back to login

- [ ] **Step 6: Tag v2.0.0**

```bash
git tag -a v2.0.0 -m "PrivGuard v2.0.0 — web dashboard (FastAPI + Next.js)"
git push origin main --tags
```

Expected: tag visible in git log.

---

## Self-Review Checklist

**Spec coverage:**
- [x] Next.js 14 App Router with TypeScript — Task 1
- [x] Tailwind CSS dark theme — Tasks 1, 4–14
- [x] SWR for data fetching with `credentials: "include"` — Task 2 (`fetcher`)
- [x] Session cookie is httpOnly (backend sets it, frontend never reads it) — Task 2
- [x] Login / unlock page — Task 10
- [x] Dashboard with per-user stat cards — Task 11
- [x] User detail page with findings tabs — Task 12
- [x] Scan progress via SSE — Tasks 8, 13
- [x] Submit opt-outs — Task 12 (button wired to `/api/users/{name}/submit`)
- [x] Breaches tab with HIBP enrichment (logo, description, data classes) — Tasks 7, 12
- [x] Manual opt-out instructions displayed in FindingsTable — Task 6
- [x] Status override (Clear button → PATCH) — Tasks 6, 12
- [x] Add profile form — Task 14
- [x] Pwned Passwords tool page (client-side, k-anonymity) — Tasks 3, 9, 15
- [x] Source filter tabs in findings table — Task 6
- [x] Lock vault button in sidebar — Task 11
- [x] `privguard serve` opens browser automatically — Backend Task 10

**Placeholder scan:** None found.

**Type consistency:**
- `fetcher(url)` returns `r.json()` — matches SWR usage throughout
- `ScanProgressEvent.type` is `"progress" | "done" | "error"` — matches backend `{"type": "done"}` sentinel
- `Breach.exposed_fields` is `string` (JSON-encoded list) — `JSON.parse()` applied in BreachList
- `FindingStatus` union matches the 6 statuses sent by the backend

---

*Run both plans' tests together before tagging: `pytest tests/ -v && cd web && npm test`*
