"use client";

import { useParams } from "next/navigation";
import { useQuery } from "@tanstack/react-query";
import { api } from "@/lib/api/client";
import type { ProjectTrace } from "@/lib/types/api";
import { formatDate, cn } from "@/lib/utils";
import { Radio } from "lucide-react";

const DOT: Record<string, string> = {
  agent_start:    "bg-blue-400",
  agent_complete: "bg-emerald-400",
  agent_error:    "bg-red-400",
  decision:       "bg-amber-400",
  guardrail:      "bg-orange-400",
};

export default function TracesPage() {
  const { id } = useParams<{ id: string }>();
  const { data: traces, isLoading } = useQuery({
    queryKey: ["traces", id],
    queryFn: () => api.get<ProjectTrace[]>(`/projects/${id}/traces`),
    enabled: !!id,
  });

  if (isLoading) return (
    <div className="flex h-40 items-center justify-center text-sm text-[var(--text-muted)]">Loading…</div>
  );

  return (
    <div className="p-4 sm:p-6 lg:p-8 space-y-5 animate-fade-in-up">
      <h2 className="text-sm font-semibold text-[var(--text-primary)]">
        Event Traces <span className="text-[var(--text-muted)] font-normal ml-1">{traces?.length ?? 0}</span>
      </h2>

      {!traces || traces.length === 0 ? (
        <div className="flex flex-col items-center gap-3 py-20">
          <div className="p-3 rounded-xl bg-white/[0.03] border border-white/[0.06]"><Radio className="h-6 w-6 text-[var(--text-muted)]" /></div>
          <p className="text-sm text-[var(--text-muted)]">No traces recorded yet</p>
        </div>
      ) : (
        <div className="relative pl-6">
          <div className="absolute left-2.5 top-0 bottom-0 w-px bg-white/[0.06]" />
          <div className="space-y-3">
            {traces.map((trace) => (
              <div key={trace.id} className="relative group">
                <div className={cn(
                  "absolute -left-[17px] top-2.5 h-2.5 w-2.5 rounded-full ring-2 ring-[var(--bg-base)] transition-transform group-hover:scale-110",
                  DOT[trace.event] ?? "bg-zinc-500"
                )} />
                <div className="rounded-xl border border-white/[0.06] bg-white/[0.02] px-4 py-3 hover:bg-white/[0.04] hover:border-white/[0.10] transition-all">
                  <div className="flex items-start justify-between gap-3">
                    <div>
                      <div className="flex items-center gap-2">
                        <span className="text-xs font-semibold text-[var(--text-primary)] uppercase tracking-wide">{trace.event}</span>
                        <span className="text-[10px] text-[var(--text-muted)] capitalize bg-white/[0.04] px-2 py-0.5 rounded">{trace.stage.replace(/_/g, " ")}</span>
                      </div>
                      <p className="text-sm text-[var(--text-secondary)] mt-1">{trace.message}</p>
                    </div>
                    <span className="shrink-0 text-[10px] text-[var(--text-muted)]">{formatDate(trace.created_at)}</span>
                  </div>
                </div>
              </div>
            ))}
          </div>
        </div>
      )}
    </div>
  );
}
