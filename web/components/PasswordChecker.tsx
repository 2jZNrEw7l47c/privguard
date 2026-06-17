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
            That&#39;s a good sign — but still use a unique password for every
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
