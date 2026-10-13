"use client";

import { useAgentRuns } from "@/lib/hooks/useMlops";
import { RunTable } from "@/components/mlops/RunTable";
import { Zap } from "lucide-react";

export default function RunsPage() {
  const { data: runs, isLoading } = useAgentRuns({ limit: 100 });

  return (
    <div className="p-4 sm:p-6 lg:p-8 space-y-6 animate-fade-in-up">
      <div className="flex items-center gap-3">
        <div className="p-2 rounded-lg bg-purple-500/10"><Zap className="h-4 w-4 text-purple-400" /></div>
        <div>
          <h1 className="text-2xl font-bold text-[var(--text-primary)] tracking-tight">Agent Runs</h1>
          <p className="text-sm text-[var(--text-muted)] mt-0.5">Full execution history with latency and quality scores</p>
        </div>
      </div>
      {isLoading ? (
        <div className="py-16 text-center text-sm text-[var(--text-muted)]">Loading…</div>
      ) : (
        <RunTable runs={runs ?? []} />
      )}
    </div>
  );
}
