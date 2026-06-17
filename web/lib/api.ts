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
    throw new Error((body as { detail?: string }).detail ?? "Incorrect password.");
  }
}

export async function lock(): Promise<void> {
  await fetch("/api/auth/lock", { method: "POST", credentials: "include" });
}

export async function getUsers(): Promise<Profile[]> {
  return fetcher("/api/users");
}

export async function addUser(profile: Profile): Promise<Profile> {
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
