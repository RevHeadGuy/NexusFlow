"use client";

import Link from "next/link";
import { usePathname } from "next/navigation";
import { Brain, FileText, FlaskConical, GitBranch, ListChecks, Radio, Search } from "lucide-react";
import { cn } from "@/lib/utils";

const TABS = [
  { label: "Overview",    suffix: "",              icon: Brain },
  { label: "Workflow",    suffix: "/workflow",     icon: GitBranch },
  { label: "Research",    suffix: "/research",     icon: Search },
  { label: "Artifacts",   suffix: "/artifacts",   icon: FileText },
  { label: "Evaluations", suffix: "/evaluations", icon: FlaskConical },
  { label: "Checkpoints", suffix: "/checkpoints", icon: ListChecks },
  { label: "Traces",      suffix: "/traces",      icon: Radio },
];

export function ProjectTabs({ projectId }: { projectId: string }) {
  const pathname = usePathname();
  const base = `/projects/${projectId}`;

  return (
    <div className="-mx-1 overflow-x-auto border-b border-white/[0.06] px-1">
      <div className="flex min-w-max gap-0.5">
      {TABS.map(({ label, suffix, icon: Icon }) => {
        const href = `${base}${suffix}`;
        const active = suffix === "" ? pathname === base : pathname.startsWith(href);
        return (
          <Link
            key={label}
            href={href}
            className={cn(
              "flex min-h-11 items-center gap-2 px-3 sm:px-4 py-3 text-xs font-medium border-b-2 transition-all duration-150 -mb-px",
              active
                ? "border-indigo-500 text-indigo-300"
                : "border-transparent text-[var(--text-muted)] hover:text-[var(--text-secondary)]"
            )}
          >
            <Icon className="h-3.5 w-3.5" />
            {label}
          </Link>
        );
      })}
      </div>
    </div>
  );
}
