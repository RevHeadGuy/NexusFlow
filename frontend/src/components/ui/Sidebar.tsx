"use client";

import { useState } from "react";
import Link from "next/link";
import { usePathname } from "next/navigation";
import { useQuery } from "@tanstack/react-query";
import {
  Activity,
  BarChart2,
  Cable,
  CheckSquare,
  FlaskConical,
  FolderKanban,
  LayoutDashboard,
  LogOut,
  Menu,
  Sparkles,
  X,
  Zap,
} from "lucide-react";
import { cn } from "@/lib/utils";
import { api } from "@/lib/api/client";
import { useAuth } from "@/app/providers";

const GROUPS = [
  {
    label: "Workspace",
    links: [
      { href: "/", label: "Dashboard", icon: LayoutDashboard },
      { href: "/projects", label: "Projects", icon: FolderKanban },
      { href: "/review-queue", label: "Review Queue", icon: CheckSquare },
    ],
  },
  {
    label: "Integrations",
    links: [{ href: "/tools", label: "MCP Tool Access", icon: Cable }],
  },
  {
    label: "Operations",
    links: [
      { href: "/mlops/runs", label: "Agent Runs", icon: Zap },
      { href: "/mlops/prompts", label: "Prompts", icon: FlaskConical },
      { href: "/mlops/metrics", label: "Metrics", icon: BarChart2 },
    ],
  },
] as const;

function ApiStatus() {
  const { data, isPending, isError } = useQuery({
    queryKey: ["api-health"],
    queryFn: () => api.get<{ status: string }>("/health"),
    retry: false,
    refetchInterval: 20_000,
  });
  const connected = data?.status === "healthy";
  const label = connected ? "API connected" : isPending ? "Connecting to API" : isError ? "API unavailable" : "API status unknown";

  return (
    <div className="flex items-center gap-2" aria-live="polite" title={label}>
      <span className={cn(
        "h-2 w-2 rounded-full",
        connected ? "bg-emerald-400" : isPending ? "bg-amber-400 animate-pulse" : "bg-red-400"
      )} />
      <span className="text-xs text-[var(--text-secondary)]">{label}</span>
    </div>
  );
}

function Brand() {
  return (
    <div className="flex h-16 items-center gap-2.5 border-b border-white/[0.06] px-5">
      <div className="flex h-8 w-8 items-center justify-center rounded-lg bg-gradient-to-br from-indigo-500 to-purple-600 shadow-lg shadow-indigo-500/20">
        <Sparkles className="h-4 w-4 text-white" />
      </div>
      <div>
        <span className="block text-sm font-semibold tracking-tight text-white">NexusFlow</span>
        <span className="block text-[10px] text-[var(--text-muted)]">Product workspace</span>
      </div>
    </div>
  );
}

function Navigation({ onNavigate }: { onNavigate?: () => void }) {
  const pathname = usePathname();
  const isActive = (href: string) => href === "/" ? pathname === "/" : pathname.startsWith(href);

  return (
    <nav className="flex-1 space-y-5 overflow-y-auto px-3 py-5" aria-label="Main navigation">
      {GROUPS.map(({ label, links }) => (
        <div key={label}>
          <p className="mb-2 px-3 text-[10px] font-semibold uppercase tracking-[0.14em] text-[var(--text-muted)]">{label}</p>
          <div className="space-y-1">
            {links.map(({ href, label: linkLabel, icon: Icon }) => {
              const active = isActive(href);
              return (
                <Link
                  key={href}
                  href={href}
                  onClick={onNavigate}
                  aria-current={active ? "page" : undefined}
                  className={cn(
                    "group flex min-h-10 items-center gap-3 rounded-lg border px-3 text-sm transition-colors focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-indigo-400/70",
                    active
                      ? "border-indigo-400/15 bg-indigo-500/10 font-medium text-indigo-200"
                      : "border-transparent text-[var(--text-secondary)] hover:bg-white/[0.04] hover:text-[var(--text-primary)]"
                  )}
                >
                  <Icon className={cn("h-4 w-4 shrink-0", active ? "text-indigo-300" : "text-[var(--text-muted)] group-hover:text-[var(--text-secondary)]")} />
                  <span className="min-w-0 flex-1 truncate">{linkLabel}</span>
                  {active && <span className="h-1.5 w-1.5 rounded-full bg-indigo-300" />}
                </Link>
              );
            })}
          </div>
        </div>
      ))}
    </nav>
  );
}

function SidebarFooter() {
  const { user, logout } = useAuth();
  return (
    <div className="space-y-3 border-t border-white/[0.06] px-5 py-4">
      {user && <div className="flex items-center gap-3">
        <div className="flex h-8 w-8 shrink-0 items-center justify-center rounded-full bg-indigo-500/15 text-xs font-semibold text-indigo-200">{user.display_name.slice(0, 1).toUpperCase()}</div>
        <div className="min-w-0 flex-1"><p className="truncate text-xs font-medium text-[var(--text-primary)]">{user.display_name}</p><p className="truncate text-[10px] text-[var(--text-muted)]">{user.email}</p></div>
        <button type="button" onClick={logout} aria-label="Sign out" title="Sign out" className="rounded-md p-2 text-[var(--text-muted)] hover:bg-white/[0.05] hover:text-white"><LogOut className="h-4 w-4" /></button>
      </div>}
      <ApiStatus />
      <div className="flex items-center gap-2 text-[10px] text-[var(--text-muted)]">
        <Activity className="h-3 w-3" /> NexusFlow API · v0.2.0
      </div>
    </div>
  );
}

export function Sidebar() {
  const [menuOpen, setMenuOpen] = useState(false);

  return (
    <>
      <aside className="hidden h-dvh w-[236px] shrink-0 flex-col border-r border-white/[0.06] bg-[#0d0d14] md:flex">
        <Brand />
        <Navigation />
        <SidebarFooter />
      </aside>

      <header className="sticky top-0 z-40 flex h-14 shrink-0 items-center justify-between border-b border-white/[0.08] bg-[#0d0d14]/95 px-4 backdrop-blur md:hidden">
        <div className="flex items-center gap-2.5">
          <div className="flex h-7 w-7 items-center justify-center rounded-lg bg-gradient-to-br from-indigo-500 to-purple-600">
            <Sparkles className="h-3.5 w-3.5 text-white" />
          </div>
          <span className="text-sm font-semibold text-white">NexusFlow</span>
        </div>
        <button
          type="button"
          onClick={() => setMenuOpen((open) => !open)}
          aria-expanded={menuOpen}
          aria-label={menuOpen ? "Close navigation" : "Open navigation"}
          className="flex h-10 w-10 items-center justify-center rounded-lg text-[var(--text-secondary)] hover:bg-white/[0.06] hover:text-white focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-indigo-400/70"
        >
          {menuOpen ? <X className="h-5 w-5" /> : <Menu className="h-5 w-5" />}
        </button>
      </header>

      {menuOpen && (
        <>
          <button type="button" aria-label="Close navigation" className="fixed inset-0 z-50 cursor-default bg-black/60 md:hidden" onClick={() => setMenuOpen(false)} />
          <aside
            className="fixed inset-y-0 left-0 z-[51] flex h-dvh w-[min(86vw,320px)] flex-col border-r border-white/[0.08] bg-[#0d0d14] shadow-2xl md:hidden"
            aria-label="Navigation menu"
          >
            <div className="flex items-center justify-between">
              <Brand />
              <button className="mr-3 rounded-lg p-2 text-[var(--text-secondary)] hover:bg-white/[0.06]" onClick={() => setMenuOpen(false)} aria-label="Close navigation">
                <X className="h-4 w-4" />
              </button>
            </div>
            <Navigation onNavigate={() => setMenuOpen(false)} />
            <SidebarFooter />
          </aside>
        </>
      )}
    </>
  );
}
