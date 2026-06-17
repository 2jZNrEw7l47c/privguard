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

  function update<K extends keyof typeof form>(key: K, value: (typeof form)[K]) {
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
      await addUser({
        ...form,
        emails: form.emails.filter(Boolean),
        phone_numbers: form.phone_numbers.filter(Boolean),
      });
      router.push("/dashboard");
    } catch (err) {
      setError(err instanceof Error ? err.message : "Failed to save profile.");
    } finally {
      setLoading(false);
    }
  }

  const fieldCls =
    "rounded-lg border border-border bg-panel px-3 py-2 text-sm text-gray-100 placeholder:text-muted focus:border-accent focus:outline-none w-full transition-colors";
  const labelCls = "block text-xs text-muted mb-1";

  return (
    <div className="mx-auto max-w-xl space-y-6">
      <h1 className="text-xl font-bold text-gray-100">Add Profile</h1>

      <form onSubmit={handleSubmit} className="space-y-5">
        <div>
          <label className={labelCls}>Display Name *</label>
          <input
            className={fieldCls}
            required
            value={form.display_name}
            onChange={(e) => update("display_name", e.target.value)}
            placeholder="Alice Johnson"
          />
        </div>

        <div>
          <label className={labelCls}>Full Name</label>
          <input
            className={fieldCls}
            value={form.full_name}
            onChange={(e) => update("full_name", e.target.value)}
            placeholder="Alice Marie Johnson"
          />
        </div>

        <div>
          <label className={labelCls}>Date of Birth (YYYY-MM-DD)</label>
          <input
            className={fieldCls}
            value={form.date_of_birth}
            onChange={(e) => update("date_of_birth", e.target.value)}
            placeholder="1985-03-22"
          />
        </div>

        <div className="grid grid-cols-2 gap-4">
          <div>
            <label className={labelCls}>City</label>
            <input
              className={fieldCls}
              value={form.addresses[0].city}
              onChange={(e) =>
                update("addresses", [{ ...form.addresses[0], city: e.target.value }])
              }
              placeholder="Portland"
            />
          </div>
          <div>
            <label className={labelCls}>State</label>
            <input
              className={fieldCls}
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
          <label className={labelCls}>Email Addresses</label>
          <div className="space-y-2">
            {form.emails.map((email, i) => (
              <input
                key={i}
                className={fieldCls}
                type="email"
                value={email}
                onChange={(e) => updateEmail(i, e.target.value)}
                placeholder={i === 0 ? "alice@gmail.com *" : "Additional email"}
              />
            ))}
          </div>
        </div>

        <div>
          <label className={labelCls}>Phone Numbers</label>
          <div className="space-y-2">
            {form.phone_numbers.map((phone, i) => (
              <input
                key={i}
                className={fieldCls}
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
