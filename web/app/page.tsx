"use client";

import { useEffect, useState } from "react";
import { useRouter } from "next/navigation";
import { unlock } from "@/lib/api";

type Mode = "loading" | "unlock" | "create";

async function initVault(password: string) {
  const res = await fetch("/api/auth/init", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    credentials: "include",
    body: JSON.stringify({ password }),
  });
  if (!res.ok) {
    const data = await res.json().catch(() => ({}));
    throw new Error(data.detail ?? "Failed to create vault.");
  }
}

export default function LoginPage() {
  const router = useRouter();
  const [mode, setMode] = useState<Mode>("loading");
  const [password, setPassword] = useState("");
  const [confirm, setConfirm] = useState("");
  const [error, setError] = useState("");
  const [loading, setLoading] = useState(false);

  useEffect(() => {
    fetch("/api/auth/status")
      .then((r) => r.json())
      .then((data) => setMode(data.vault_exists ? "unlock" : "create"))
      .catch(() => setMode("unlock"));
  }, []);

  async function handleSubmit(e: React.FormEvent) {
    e.preventDefault();
    setError("");

    if (mode === "create") {
      if (password !== confirm) {
        setError("Passwords do not match.");
        return;
      }
      if (password.length < 8) {
        setError("Password must be at least 8 characters.");
        return;
      }
    }

    setLoading(true);
    try {
      if (mode === "create") {
        await initVault(password);
      } else {
        await unlock(password);
      }
      router.push("/dashboard");
    } catch (err) {
      setError(err instanceof Error ? err.message : "Incorrect password.");
    } finally {
      setLoading(false);
    }
  }

  if (mode === "loading") {
    return (
      <div className="flex min-h-screen items-center justify-center bg-surface">
        <p className="text-muted text-sm">Loading…</p>
      </div>
    );
  }

  const isCreate = mode === "create";

  return (
    <div className="flex min-h-screen items-center justify-center bg-surface px-4">
      <div className="w-full max-w-sm">
        <div className="mb-8 text-center">
          <div className="mx-auto mb-4 flex h-14 w-14 items-center justify-center rounded-full bg-accent/20">
            <span className="text-2xl">{isCreate ? "🔐" : "🔒"}</span>
          </div>
          <h1 className="text-2xl font-bold text-gray-100">PrivGuard</h1>
          <p className="mt-1 text-sm text-muted">
            {isCreate
              ? "No vault found. Set a master password to get started."
              : "Enter your master password to unlock the vault."}
          </p>
        </div>

        <form onSubmit={handleSubmit} className="space-y-4">
          <input
            type="password"
            value={password}
            onChange={(e) => setPassword(e.target.value)}
            placeholder={isCreate ? "Choose a master password" : "Master password"}
            autoFocus
            className="w-full rounded-lg border border-border bg-panel px-4 py-3 text-gray-100 placeholder:text-muted focus:border-accent focus:outline-none transition-colors"
          />

          {isCreate && (
            <input
              type="password"
              value={confirm}
              onChange={(e) => setConfirm(e.target.value)}
              placeholder="Confirm password"
              className="w-full rounded-lg border border-border bg-panel px-4 py-3 text-gray-100 placeholder:text-muted focus:border-accent focus:outline-none transition-colors"
            />
          )}

          {error && <p className="text-sm text-red-400">{error}</p>}

          <button
            type="submit"
            disabled={loading || !password || (isCreate && !confirm)}
            className="w-full rounded-lg bg-accent py-3 font-medium text-white hover:bg-accent/80 disabled:opacity-50 transition-colors"
          >
            {loading
              ? isCreate ? "Creating vault…" : "Unlocking…"
              : isCreate ? "Create Vault" : "Unlock Vault"}
          </button>
        </form>
      </div>
    </div>
  );
}
