"use client";

import { useState, useMemo } from "react";
import type { Finding, FindingStatus } from "@/lib/types";

interface Props {
  findings: Finding[];
  filter?: { source?: string; status?: FindingStatus };
  onStatusChange: (findingId: number, newStatus: FindingStatus) => void;
}

const SOURCES = ["all", "brokers", "hibp", "social", "search_engines", "ad_networks"] as const;
const STATUS_FILTERS = [
  { value: "all",                  label: "All" },
  { value: "exposed",              label: "Exposed" },
  { value: "found",                label: "No Action Yet" },
  { value: "submitted",            label: "Submitted" },
  { value: "pending_verification", label: "Awaiting Email" },
  { value: "manual_required",      label: "Manual Required" },
  { value: "cleared",              label: "Cleared" },
  { value: "not_found",            label: "Not Found" },
] as const;

type SortKey = "site" | "detection" | "removal" | "date";
type SortDir = "asc" | "desc";

const REMOVAL_ORDER: Record<string, number> = {
  manual_required: 0, found: 1, pending_verification: 2,
  submitted: 3, cleared: 4, not_found: 5,
};

// Was the user's data detected on this site?
function DetectionBadge({ status }: { status: string }) {
  const exposed = status !== "not_found";
  return exposed ? (
    <span className="inline-flex items-center gap-1.5 rounded-full bg-red-900/60 px-2.5 py-1 text-xs font-medium text-red-300">
      <span className="h-1.5 w-1.5 rounded-full bg-red-400" />
      Exposed
    </span>
  ) : (
    <span className="inline-flex items-center gap-1.5 rounded-full bg-zinc-800 px-2.5 py-1 text-xs font-medium text-zinc-400">
      <span className="h-1.5 w-1.5 rounded-full bg-zinc-500" />
      Not Found
    </span>
  );
}

// What removal action has been taken?
function RemovalBadge({ status }: { status: string }) {
  if (status === "not_found" || status === "found") return <span className="text-xs text-muted">—</span>;
  const map: Record<string, { label: string; cls: string }> = {
    submitted:           { label: "Submitted",        cls: "bg-blue-900/60 text-blue-300" },
    pending_verification:{ label: "Awaiting Email",   cls: "bg-yellow-900/60 text-yellow-300" },
    manual_required:     { label: "Manual Required",  cls: "bg-orange-900/60 text-orange-300" },
    cleared:             { label: "Cleared ✓",        cls: "bg-green-900/60 text-green-300" },
  };
  const m = map[status];
  if (!m) return null;
  return (
    <span className={`inline-flex rounded-full px-2.5 py-1 text-xs font-medium ${m.cls}`}>
      {m.label}
    </span>
  );
}

function SortButton({ col, current, dir, onClick }: {
  col: SortKey; current: SortKey; dir: SortDir; onClick: () => void;
}) {
  const active = col === current;
  return (
    <button onClick={onClick} className="inline-flex items-center gap-1 hover:text-gray-100 transition-colors">
      {col === "site" ? "Site" : col === "detection" ? "Detection" : col === "removal" ? "Removal" : "Date"}
      <span className={active ? "text-accent" : "text-muted/40"}>
        {active ? (dir === "asc" ? "↑" : "↓") : "↕"}
      </span>
    </button>
  );
}

export function FindingsTable({ findings, filter, onStatusChange }: Props) {
  const [sourceFilter, setSourceFilter] = useState<string>(filter?.source ?? "all");
  const [statusFilter, setStatusFilter] = useState<string>("all");
  const [search, setSearch]             = useState("");
  const [sortKey, setSortKey]           = useState<SortKey>("detection");
  const [sortDir, setSortDir]           = useState<SortDir>("asc");

  function toggleSort(key: SortKey) {
    if (sortKey === key) setSortDir(d => d === "asc" ? "desc" : "asc");
    else { setSortKey(key); setSortDir("asc"); }
  }

  const visible = useMemo(() => {
    let rows = findings.filter((f) => {
      if (sourceFilter !== "all" && f.source !== sourceFilter) return false;
      if (filter?.status && f.status !== filter.status) return false;
      if (statusFilter === "exposed" && f.status === "not_found") return false;
      else if (statusFilter !== "all" && statusFilter !== "exposed" && f.status !== statusFilter) return false;
      if (search && !f.site_name.toLowerCase().includes(search.toLowerCase())) return false;
      return true;
    });

    rows = [...rows].sort((a, b) => {
      let cmp = 0;
      if (sortKey === "site")      cmp = a.site_name.localeCompare(b.site_name);
      if (sortKey === "detection") cmp = (a.status === "not_found" ? 1 : 0) - (b.status === "not_found" ? 1 : 0);
      if (sortKey === "removal")   cmp = (REMOVAL_ORDER[a.status] ?? 9) - (REMOVAL_ORDER[b.status] ?? 9);
      if (sortKey === "date")      cmp = (a.last_checked ?? "").localeCompare(b.last_checked ?? "");
      return sortDir === "asc" ? cmp : -cmp;
    });

    return rows;
  }, [findings, sourceFilter, statusFilter, search, sortKey, sortDir, filter]);

  if (findings.length === 0) {
    return (
      <div className="rounded-lg border border-border bg-panel p-8 text-center text-muted">
        No findings to display.
      </div>
    );
  }

  return (
    <div className="space-y-3">
      {/* Search + status filter row */}
      <div className="flex flex-wrap gap-3 items-center">
        <input
          type="text"
          value={search}
          onChange={e => setSearch(e.target.value)}
          placeholder="Search sites…"
          className="rounded-md border border-border bg-panel px-3 py-1.5 text-sm text-gray-100 placeholder:text-muted focus:border-accent focus:outline-none w-44 transition-colors"
        />
        <div className="flex gap-1.5 flex-wrap">
          {STATUS_FILTERS.map(sf => (
            <button
              key={sf.value}
              onClick={() => setStatusFilter(sf.value)}
              className={`rounded px-2.5 py-1 text-xs transition-colors ${
                statusFilter === sf.value
                  ? "bg-accent text-white"
                  : "bg-panel text-muted hover:text-gray-100 border border-border"
              }`}
            >
              {sf.label}
              {sf.value !== "all" && (
                <span className="ml-1 opacity-60">
                  ({sf.value === "exposed"
                    ? findings.filter(f => f.status !== "not_found").length
                    : findings.filter(f => f.status === sf.value).length})
                </span>
              )}
            </button>
          ))}
        </div>
      </div>

      {/* Source tabs */}
      <div className="flex gap-2 flex-wrap">
        {SOURCES.map((s) => (
          <button
            key={s}
            onClick={() => setSourceFilter(s)}
            className={`rounded px-3 py-1 text-xs capitalize transition-colors ${
              sourceFilter === s
                ? "bg-surface text-gray-100 border border-accent"
                : "bg-panel text-muted hover:text-gray-100 border border-border"
            }`}
          >
            {s.replace(/_/g, " ")}
          </button>
        ))}
      </div>

      {visible.length === 0 ? (
        <div className="rounded-lg border border-border bg-panel p-6 text-center text-muted text-sm">
          No results match your filters.{" "}
          <button onClick={() => { setSearch(""); setStatusFilter("all"); setSourceFilter("all"); }}
            className="text-accent hover:underline">Clear filters</button>
        </div>
      ) : (
      <div className="overflow-x-auto rounded-lg border border-border">
        <table className="w-full text-sm">
          <thead className="text-left">
            <tr>
              <th colSpan={2} className="bg-red-950/40 px-4 py-2 text-xs font-semibold uppercase tracking-wider text-red-400 border-b border-border">
                Scan Results — what was detected
              </th>
              <th colSpan={3} className="bg-blue-950/40 px-4 py-2 text-xs font-semibold uppercase tracking-wider text-blue-400 border-b border-border">
                Removal Status — what's been done
              </th>
              <th className="bg-panel px-4 py-2 border-b border-border" />
            </tr>
            <tr className="bg-panel text-muted text-xs">
              <th className="px-4 py-2.5 font-medium">
                <SortButton col="site" current={sortKey} dir={sortDir} onClick={() => toggleSort("site")} />
              </th>
              <th className="px-4 py-2.5 font-medium">
                <SortButton col="detection" current={sortKey} dir={sortDir} onClick={() => toggleSort("detection")} />
              </th>
              <th className="px-4 py-2.5 font-medium border-l border-border">
                <SortButton col="removal" current={sortKey} dir={sortDir} onClick={() => toggleSort("removal")} />
              </th>
              <th className="px-4 py-2.5 font-medium">View Listing</th>
              <th className="px-4 py-2.5 font-medium">Opt-Out Link</th>
              <th className="px-4 py-2.5 font-medium">Actions</th>
            </tr>
          </thead>
          <tbody className="divide-y divide-border">
            {visible.map((f) => {
              const exposed = f.status !== "not_found";
              let listingOrigin: string | null = null;
              try { if (f.opt_out_url) listingOrigin = new URL(f.opt_out_url).origin; } catch {}

              return (
                <tr
                  key={f.id}
                  className={`transition-colors ${exposed ? "hover:bg-red-950/20" : "hover:bg-panel/60 opacity-60"}`}
                >
                  <td className="px-4 py-3 font-medium text-gray-100 whitespace-nowrap">
                    {f.site_name}
                    <div className="text-xs text-muted font-normal capitalize">
                      {f.source.replace(/_/g, " ")}
                    </div>
                  </td>
                  <td className="px-4 py-3">
                    <DetectionBadge status={f.status} />
                    {f.last_checked && (
                      <button
                        onClick={() => toggleSort("date")}
                        className="mt-1 text-xs text-muted hover:text-gray-300 transition-colors"
                        title="Sort by date"
                      >
                        {new Date(f.last_checked).toLocaleDateString()}
                      </button>
                    )}
                  </td>
                  <td className="px-4 py-3 border-l border-border">
                    <RemovalBadge status={f.status} />
                  </td>
                  <td className="px-4 py-3">
                    {f.listing_url ? (
                      <a href={f.listing_url} target="_blank" rel="noopener noreferrer"
                         className="text-blue-400 hover:text-blue-300 text-xs font-medium">
                        View Listing ↗
                      </a>
                    ) : listingOrigin ? (
                      <a href={listingOrigin} target="_blank" rel="noopener noreferrer"
                         className="text-blue-400/50 hover:text-blue-300 text-xs">
                        Visit Site ↗
                      </a>
                    ) : (
                      <span className="text-muted text-xs">—</span>
                    )}
                  </td>
                  <td className="px-4 py-3">
                    {f.opt_out_url ? (
                      <a href={f.opt_out_url} target="_blank" rel="noopener noreferrer"
                         className="text-accent hover:text-accent/80 text-xs font-medium">
                        Opt-Out Form ↗
                      </a>
                    ) : (
                      <span className="text-muted text-xs">—</span>
                    )}
                  </td>
                  <td className="px-4 py-3">
                    {exposed && f.status !== "cleared" && (
                      <button
                        onClick={() => onStatusChange(f.id, "cleared")}
                        className="rounded border border-green-800 px-2 py-1 text-xs text-green-400 hover:bg-green-900/30 transition-colors"
                      >
                        Mark Cleared
                      </button>
                    )}
                  </td>
                </tr>
              );
            })}
          </tbody>
        </table>
      </div>

      )}

      {visible.some((f) => f.manual_instructions) && (
        <details className="rounded-lg border border-orange-900/50 bg-orange-950/20 p-4">
          <summary className="cursor-pointer text-sm font-medium text-orange-300">
            Manual steps required for {visible.filter((f) => f.manual_instructions).length} site(s) — click to expand
          </summary>
          <div className="mt-4 space-y-5">
            {visible.filter((f) => f.manual_instructions).map((f) => (
              <div key={f.id} className="border-l-2 border-orange-700 pl-4">
                <p className="text-sm font-semibold text-gray-100">{f.site_name}</p>
                <pre className="mt-1 whitespace-pre-wrap text-xs text-muted leading-relaxed">
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
