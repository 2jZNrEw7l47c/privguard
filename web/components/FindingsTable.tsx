"use client";

import { useState } from "react";
import type { Finding, FindingStatus } from "@/lib/types";

interface Props {
  findings: Finding[];
  filter?: { source?: string; status?: FindingStatus };
  onStatusChange: (findingId: number, newStatus: FindingStatus) => void;
}

const SOURCES = ["all", "brokers", "hibp", "social", "search_engines", "ad_networks"] as const;

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
            {s.replace(/_/g, " ")}
          </button>
        ))}
      </div>

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
            <tr className="bg-panel text-muted">
              <th className="px-4 py-2.5 font-medium text-xs">Site</th>
              <th className="px-4 py-2.5 font-medium text-xs">Detection</th>
              <th className="px-4 py-2.5 font-medium text-xs border-l border-border">Removal</th>
              <th className="px-4 py-2.5 font-medium text-xs">View Listing</th>
              <th className="px-4 py-2.5 font-medium text-xs">Opt-Out Link</th>
              <th className="px-4 py-2.5 font-medium text-xs">Actions</th>
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
                      <div className="mt-1 text-xs text-muted">
                        {new Date(f.last_checked).toLocaleDateString()}
                      </div>
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
