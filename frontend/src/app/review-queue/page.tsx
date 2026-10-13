"use client";

import Link from "next/link";
import { useReviewQueue } from "@/lib/hooks/useCheckpoints";
import { CheckpointCard } from "@/components/hitl/CheckpointCard";
import { useWorkflowReviewQueue } from "@/lib/hooks/useWorkflow";
import { ArrowRight, ShieldAlert, MessageSquareWarning, CheckSquare } from "lucide-react";
import { Card, CardContent } from "@/components/ui/Card";
import { formatRelative } from "@/lib/utils";

export default function ReviewQueuePage() {
  const { data: queue, isLoading, isError: checkpointError } = useReviewQueue();
  const { data: workflowQueue, isLoading: workflowLoading, isError: workflowError } = useWorkflowReviewQueue();

  if (isLoading && workflowLoading) return (
    <div className="flex h-full items-center justify-center text-sm text-[var(--text-muted)]">Loading…</div>
  );

  return (
    <div className="p-4 sm:p-6 lg:p-8 space-y-6 animate-fade-in-up">
      <div>
        <h1 className="text-2xl font-bold text-[var(--text-primary)] tracking-tight">Review Queue</h1>
        <p className="text-sm text-[var(--text-muted)] mt-1">Workflow stages and HITL checkpoints that need human attention</p>
      </div>

      <section className="space-y-3">
        <div className="flex items-end justify-between gap-3">
          <div>
            <h2 className="text-sm font-semibold text-[var(--text-primary)]">Project workflow reviews</h2>
            <p className="mt-1 text-xs text-[var(--text-muted)]">Current stage, approval checks, and unresolved feedback</p>
          </div>
          <span className="text-xs text-[var(--text-muted)]">{workflowQueue?.length ?? 0} active</span>
        </div>
        {workflowError && <p role="alert" className="rounded-lg border border-red-400/20 bg-red-400/[0.05] p-3 text-xs text-red-200">Workflow reviews could not be loaded. Check the API connection and refresh.</p>}
        {!workflowLoading && !workflowError && workflowQueue?.length === 0 && (
          <p className="rounded-xl border border-dashed border-white/[0.08] px-4 py-8 text-center text-xs text-[var(--text-muted)]">No active workflow stages need review.</p>
        )}
        <div className="grid gap-3 lg:grid-cols-2">
          {workflowQueue?.map((item) => (
            <Card key={item.workflow_id}>
              <CardContent className="space-y-3">
                <div className="flex items-start justify-between gap-3">
                  <div className="min-w-0">
                    <p className="truncate text-sm font-semibold text-[var(--text-primary)]">{item.project_name}</p>
                    <p className="mt-1 text-xs capitalize text-indigo-200">{item.current_stage.replace(/_/g, " ")}</p>
                  </div>
                  <span className={`shrink-0 rounded-full px-2.5 py-1 text-[10px] ${item.ready_for_approval ? "bg-emerald-400/10 text-emerald-200" : "bg-amber-400/10 text-amber-200"}`}>
                    {item.ready_for_approval ? "Ready for decision" : "Needs attention"}
                  </span>
                </div>
                <div className="flex flex-wrap gap-3 text-[11px] text-[var(--text-muted)]">
                  <span className="inline-flex items-center gap-1"><MessageSquareWarning className="h-3 w-3" />{item.unresolved_comment_count} open comments</span>
                  <span className="inline-flex items-center gap-1"><ShieldAlert className="h-3 w-3" />{item.blocking_guardrail_count} blocking findings</span>
                  <span className="capitalize">{item.status.replace(/_/g, " ")}</span>
                  <span>Updated {formatRelative(item.updated_at)}</span>
                </div>
                {item.review_issues.length > 0 && (
                  <ul className="space-y-1 rounded-lg border border-amber-400/10 bg-amber-400/[0.03] p-3 text-[11px] leading-relaxed text-amber-100/80">
                    {item.review_issues.slice(0, 3).map((issue) => <li key={issue}>• {issue}</li>)}
                    {item.review_issues.length > 3 && <li>+ {item.review_issues.length - 3} more checks</li>}
                  </ul>
                )}
                <Link href={`/projects/${item.project_id}/workflow`}>
                  <span className="inline-flex w-full items-center justify-center gap-2 rounded-lg border border-white/10 bg-white/[0.05] px-3 py-2 text-xs font-medium text-[var(--text-primary)] transition-colors hover:bg-white/[0.09]">Open review <ArrowRight className="h-3.5 w-3.5" /></span>
                </Link>
              </CardContent>
            </Card>
          ))}
        </div>
      </section>

      <section className="space-y-3">
        <div>
          <h2 className="text-sm font-semibold text-[var(--text-primary)]">HITL checkpoints</h2>
          <p className="mt-1 text-xs text-[var(--text-muted)]">Standalone checkpoints awaiting a reviewer decision</p>
        </div>
      {checkpointError ? (
        <p role="alert" className="rounded-lg border border-red-400/20 bg-red-400/[0.05] p-3 text-xs text-red-200">HITL checkpoints could not be loaded. Check the API connection and refresh.</p>
      ) : !queue || queue.length === 0 ? (
        <div className="flex flex-col items-center gap-3 py-24">
          <div className="p-4 rounded-2xl bg-emerald-500/10 border border-emerald-500/20">
            <CheckSquare className="h-7 w-7 text-emerald-400" />
          </div>
          <p className="text-sm font-medium text-emerald-400">Queue is empty</p>
          <p className="text-xs text-[var(--text-muted)]">Nothing awaiting review right now.</p>
        </div>
      ) : (
        <div className="space-y-4">
          {queue.map((cp) => (
            <div key={cp.id}>
              <div className="mb-1.5 flex items-center gap-2">
                <span className="text-[10px] text-[var(--text-muted)] uppercase tracking-wider">Project</span>
                <Link href={`/projects/${cp.project_id}/checkpoints`} className="text-xs text-indigo-400 hover:text-indigo-300 transition-colors font-mono">
                  {cp.project_id.slice(0, 8)}…
                </Link>
              </div>
              <CheckpointCard checkpoint={cp} projectId={cp.project_id} />
            </div>
          ))}
        </div>
      )}
      </section>
    </div>
  );
}
