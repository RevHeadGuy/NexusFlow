import Link from "next/link";
import { STATUS_STYLES, cn, formatRelative } from "@/lib/utils";
import type { AgentRun } from "@/lib/types/api";

export function RunTable({ runs }: { runs: AgentRun[] }) {
  if (runs.length === 0) {
    return (
      <div className="py-16 text-center text-sm text-[var(--text-muted)]">
        No agent runs recorded yet.
      </div>
    );
  }

  return (
    <div className="overflow-x-auto rounded-xl border border-white/[0.06]">
      <table className="min-w-full text-sm">
        <thead>
          <tr className="border-b border-white/[0.06]">
            {["Agent", "Stage", "Status", "Latency", "Tokens", "Score", "Started"].map((h) => (
              <th key={h} className="px-4 py-3 text-left text-[10px] font-semibold uppercase tracking-wider text-[var(--text-muted)]">
                {h}
              </th>
            ))}
          </tr>
        </thead>
        <tbody className="divide-y divide-white/[0.04]">
          {runs.map((run) => (
            <tr key={run.id} className="hover:bg-white/[0.02] transition-colors group">
              <td className="px-4 py-3">
                <Link href={`/mlops/runs/${run.id}`} className="font-medium text-[var(--text-primary)] group-hover:text-indigo-300 transition-colors">
                  {run.agent_name.replace(/_/g, " ")}
                </Link>
              </td>
              <td className="px-4 py-3 text-[var(--text-muted)] text-xs capitalize">
                {run.stage.replace(/_/g, " ")}
              </td>
              <td className="px-4 py-3">
                <span className={cn(
                  "inline-flex items-center gap-1.5 rounded-full px-2 py-0.5 text-[10px] font-medium",
                  STATUS_STYLES[run.status] ?? "bg-zinc-500/10 text-zinc-400"
                )}>
                  <span className="h-1 w-1 rounded-full bg-current" />
                  {run.status}
                </span>
              </td>
              <td className="px-4 py-3 text-xs text-[var(--text-muted)] font-mono">
                {run.latency_ms != null ? `${(run.latency_ms / 1000).toFixed(1)}s` : "—"}
              </td>
              <td className="px-4 py-3 text-xs text-[var(--text-muted)] font-mono">
                {run.input_tokens != null
                  ? ((run.input_tokens + (run.output_tokens ?? 0)) / 1000).toFixed(1) + "k"
                  : "—"}
              </td>
              <td className="px-4 py-3">
                {run.evaluation_score != null ? (
                  <div className="flex items-center gap-2">
                    <div className="w-12 h-1 rounded-full bg-white/[0.06] overflow-hidden">
                      <div
                        className="h-full rounded-full bg-gradient-to-r from-indigo-500 to-emerald-500"
                        style={{ width: `${run.evaluation_score * 100}%` }}
                      />
                    </div>
                    <span className="text-xs text-[var(--text-muted)] font-mono">
                      {(run.evaluation_score * 100).toFixed(0)}%
                    </span>
                  </div>
                ) : (
                  <span className="text-xs text-[var(--text-muted)]">—</span>
                )}
              </td>
              <td className="px-4 py-3 text-[10px] text-[var(--text-muted)]">
                {formatRelative(run.started_at)}
              </td>
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  );
}
