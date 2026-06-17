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
            {s.replace(/_/g, " ")}
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
              <th className="px-4 py-3 font-medium">Links</th>
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
                  {f.source.replace(/_/g, " ")}
                </td>
                <td className="px-4 py-3">
                  <StatusBadge status={f.status} />
                </td>
                <td className="px-4 py-3">
                  <div className="flex flex-col gap-1">
                    {f.listing_url ? (
                      <a href={f.listing_url} target="_blank" rel="noopener noreferrer"
                         className="text-blue-400 hover:text-blue-300 text-xs">
                        View Listing ↗
                      </a>
                    ) : f.opt_out_url && (() => {
                      let origin: string | null = null;
                      try { origin = new URL(f.opt_out_url).origin; } catch {}
                      return origin ? (
                        <a href={origin} target="_blank" rel="noopener noreferrer"
                           className="text-blue-400 hover:text-blue-300 text-xs opacity-60">
                          Visit Site ↗
                        </a>
                      ) : null;
                    })()}
                    {f.opt_out_url && (
                      <a href={f.opt_out_url} target="_blank" rel="noopener noreferrer"
                         className="text-accent hover:text-accent-hover text-xs">
                        Opt-Out ↗
                      </a>
                    )}
                  </div>
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
