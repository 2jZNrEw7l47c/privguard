"use client";

import Link from "next/link";
import { useRouter } from "next/navigation";
import { lock } from "@/lib/api";

const NAV = [
  { href: "/dashboard", label: "Dashboard" },
  { href: "/users/add", label: "Add Profile" },
  { href: "/tools/password-check", label: "Password Check" },
];

export default function DashboardLayout({
  children,
}: {
  children: React.ReactNode;
}) {
  const router = useRouter();

  async function handleLock() {
    await lock();
    router.push("/");
  }

  return (
    <div className="flex min-h-screen">
      <aside className="w-56 shrink-0 border-r border-border bg-panel flex flex-col">
        <div className="px-5 py-6">
          <span className="text-lg font-bold text-gray-100">PrivGuard</span>
        </div>
        <nav className="flex-1 space-y-1 px-3">
          {NAV.map((item) => (
            <Link
              key={item.href}
              href={item.href}
              className="block rounded-md px-3 py-2 text-sm text-muted hover:bg-surface hover:text-gray-100 transition-colors"
            >
              {item.label}
            </Link>
          ))}
        </nav>
        <div className="p-4">
          <button
            onClick={handleLock}
            className="w-full rounded-md border border-border px-3 py-2 text-xs text-muted hover:text-gray-100 hover:border-gray-500 transition-colors"
          >
            Lock Vault
          </button>
        </div>
      </aside>
      <main className="flex-1 overflow-y-auto p-6">{children}</main>
    </div>
  );
}
