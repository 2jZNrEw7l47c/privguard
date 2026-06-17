"use client";

import Link from "next/link";
import { usePathname, useRouter } from "next/navigation";
import { lock } from "@/lib/api";

const NAV = [
  { href: "/dashboard", label: "Dashboard", icon: "⊞", match: (p: string) => p === "/dashboard" },
  { href: "/users/add", label: "Add Profile", icon: "+", match: (p: string) => p === "/users/add" },
  { href: "/tools/password-check", label: "Password Check", icon: "🔑", match: (p: string) => p.startsWith("/tools") },
];

export default function DashboardLayout({
  children,
}: {
  children: React.ReactNode;
}) {
  const router = useRouter();
  const pathname = usePathname();

  async function handleLock() {
    await lock();
    router.push("/");
  }

  // Breadcrumb: show profile name when on a user detail page
  const profileMatch = pathname.match(/^\/users\/([^/]+)/);
  const profileName = profileMatch ? decodeURIComponent(profileMatch[1]) : null;
  const isOnScanPage = pathname.includes("/scan");

  return (
    <div className="flex min-h-screen bg-surface">
      <aside className="w-60 shrink-0 border-r border-border bg-panel flex flex-col">
        <div className="px-5 py-5 border-b border-border">
          <span className="text-base font-bold text-gray-100 tracking-tight">PrivGuard</span>
          <div className="text-xs text-muted mt-0.5">v2.0.0</div>
        </div>

        <nav className="flex-1 py-4 space-y-0.5 px-2">
          {NAV.map((item) => {
            const active = item.match(pathname);
            return (
              <Link
                key={item.href}
                href={item.href}
                className={`flex items-center gap-3 rounded-md px-3 py-2.5 text-sm font-medium transition-colors ${
                  active
                    ? "bg-accent/15 text-accent border-l-2 border-accent pl-[10px]"
                    : "text-muted hover:bg-surface hover:text-gray-100 border-l-2 border-transparent pl-[10px]"
                }`}
              >
                <span className="text-base leading-none">{item.icon}</span>
                {item.label}
              </Link>
            );
          })}

          {/* Dynamic entry for current profile */}
          {profileName && profileName !== "add" && (
            <>
              <div className="pt-4 pb-1 px-3">
                <span className="text-xs font-semibold uppercase tracking-wider text-muted/60">Current Profile</span>
              </div>
              <Link
                href={`/users/${encodeURIComponent(profileName)}`}
                className={`flex items-center gap-3 rounded-md px-3 py-2.5 text-sm font-medium transition-colors border-l-2 pl-[10px] ${
                  !isOnScanPage
                    ? "bg-accent/15 text-accent border-accent"
                    : "text-muted hover:bg-surface hover:text-gray-100 border-transparent"
                }`}
              >
                <span className="text-base leading-none">👤</span>
                <span className="truncate">{profileName}</span>
              </Link>
              {isOnScanPage && (
                <div className="flex items-center gap-3 rounded-md px-3 py-2.5 text-sm font-medium border-l-2 border-accent pl-[10px] bg-accent/15 text-accent">
                  <span className="text-base leading-none">⟳</span>
                  Scanning…
                </div>
              )}
            </>
          )}
        </nav>

        <div className="p-3 border-t border-border">
          <button
            onClick={handleLock}
            className="w-full rounded-md bg-surface border border-border px-3 py-2.5 text-sm font-medium text-muted hover:text-gray-100 hover:border-gray-500 transition-colors flex items-center justify-center gap-2"
          >
            <span>🔒</span> Lock Vault
          </button>
        </div>
      </aside>

      <main className="flex-1 overflow-y-auto p-8">{children}</main>
    </div>
  );
}
