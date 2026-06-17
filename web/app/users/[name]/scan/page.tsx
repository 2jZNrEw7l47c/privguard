"use client";

import Link from "next/link";
import { useParams, useRouter, useSearchParams } from "next/navigation";
import { useCallback, useState, Suspense } from "react";
import { ScanProgress } from "@/components/ScanProgress";

function ScanPageInner() {
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
        No job ID provided.{" "}
        <Link href="/dashboard" className="underline">
          ← Dashboard
        </Link>
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

export default function ScanPage() {
  return (
    <Suspense fallback={<div className="text-muted text-sm pt-12">Loading…</div>}>
      <ScanPageInner />
    </Suspense>
  );
}
