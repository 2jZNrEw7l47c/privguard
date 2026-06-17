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
