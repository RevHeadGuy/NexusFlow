"use client";

import { useEffect } from "react";
import { usePathname, useRouter } from "next/navigation";
import { Sidebar } from "@/components/ui/Sidebar";
import { useAuth } from "./providers";

export function AppShell({ children }: { children: React.ReactNode }) {
  const pathname = usePathname();
  const router = useRouter();
  const { user, ready } = useAuth();
  const isLogin = pathname === "/login";

  useEffect(() => {
    if (ready && !user && !isLogin) {
      const next = `${pathname}${window.location.search}`;
      router.replace(`/login?next=${encodeURIComponent(next)}`);
    }
    if (ready && user && isLogin) {
      const next = new URLSearchParams(window.location.search).get("next");
      const safeNext = next?.startsWith("/") && !next.startsWith("//") ? next : "/";
      router.replace(safeNext);
    }
  }, [isLogin, pathname, ready, router, user]);

  if (isLogin) return <main className="min-h-dvh">{children}</main>;
  if (!ready || !user) {
    return <div className="flex min-h-dvh items-center justify-center text-sm text-[var(--text-secondary)]">Loading your workspace…</div>;
  }

  return (
    <div className="flex min-h-dvh flex-col md:h-dvh md:flex-row" style={{ background: "var(--bg-base)" }}>
      <Sidebar />
      <main className="min-h-0 min-w-0 flex-1 overflow-y-auto">{children}</main>
    </div>
  );
}
