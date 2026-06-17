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
          <Link href="/dashboard" className="text-xs text-muted hover:text-gray-300">
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
        <FindingsTable findings={tabFindings} onStatusChange={handleStatusChange} />
      )}
    </div>
  );
}
