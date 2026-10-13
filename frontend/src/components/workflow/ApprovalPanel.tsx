"use client";

import { useState } from "react";
import Link from "next/link";
import { CheckCircle, XCircle, RefreshCw, MessageSquare, FileText, ArrowUpRight, ShieldAlert } from "lucide-react";
import { Button } from "@/components/ui/Button";
import { usePrepareWorkflowStage, useWorkflowDecision } from "@/lib/hooks/useWorkflow";
import type { Workflow } from "@/lib/types/api";

export function ApprovalPanel({ projectId, workflow }: { projectId: string; workflow: Workflow }) {
  const [notes, setNotes] = useState("");
  const [notesError, setNotesError] = useState<string | null>(null);
  const mutation = useWorkflowDecision(projectId);
  const prepareMutation = usePrepareWorkflowStage(projectId);
  const isTerminal = workflow.status === "completed" || workflow.status === "rejected";

  function decide(action: string) {
    if (action === "request_changes" && !notes.trim()) {
      setNotesError("Add reviewer notes describing the changes needed.");
      return;
    }
    setNotesError(null);
    mutation.mutate(
      { stage: workflow.current_stage, action, notes: notes || undefined },
      { onSuccess: () => setNotes("") }
    );
  }

  if (isTerminal) {
    return (
      <div className="rounded-xl border border-white/[0.08] bg-white/[0.02] p-5 text-center">
        {workflow.status === "completed" ? <CheckCircle className="mx-auto h-6 w-6 text-emerald-300" /> : <XCircle className="mx-auto h-6 w-6 text-red-300" />}
        <p className="mt-2 text-sm font-semibold text-[var(--text-primary)]">{workflow.status === "completed" ? "Workflow complete" : "Workflow rejected"}</p>
        <p className="mt-1 text-xs text-[var(--text-secondary)]">Your decisions and project artifacts are saved.</p>
        <Link href={`/projects/${projectId}/artifacts`} className="mt-3 inline-flex items-center gap-1 text-xs font-medium text-indigo-300 hover:text-indigo-200">
          View artifacts <ArrowUpRight className="h-3 w-3" />
        </Link>
      </div>
    );
  }

  return (
    <div className="rounded-xl surface p-4 space-y-3">
      <div className="flex items-center gap-2">
        <MessageSquare className="h-4 w-4 text-[var(--text-muted)]" />
        <p className="text-sm font-medium text-[var(--text-primary)]">
          Review decision
          <span className="ml-2 text-xs font-normal text-indigo-200 capitalize">
            {workflow.current_stage.replace(/_/g, " ")}
          </span>
        </p>
      </div>

      <div className="rounded-lg border border-indigo-500/15 bg-indigo-500/[0.04] p-3 space-y-2">
        <div className="flex items-start gap-2">
          <FileText className="mt-0.5 h-3.5 w-3.5 shrink-0 text-indigo-400" />
          <p className="text-xs leading-relaxed text-[var(--text-muted)]">
            Prepare a draft, then review or edit it in Artifacts. Saved edits are preserved when you return. Resolve open comments before approval; research plans do not claim outside sources were checked.
          </p>
        </div>
        <Button
          size="sm"
          variant="secondary"
          onClick={() => prepareMutation.mutate()}
          loading={prepareMutation.isPending}
          disabled={prepareMutation.isPending}
          className="w-full"
        >
          <FileText className="h-3.5 w-3.5" /> Prepare stage deliverable
        </Button>
        {prepareMutation.isSuccess && (
          <div className="flex items-center justify-between gap-2 text-xs text-emerald-300">
            <span>Saved draft: {prepareMutation.data.artifacts.join(", ")}</span>
            <Link href={`/projects/${projectId}/artifacts`} className="inline-flex shrink-0 items-center gap-1 hover:text-white">
              Review or edit <ArrowUpRight className="h-3 w-3" />
            </Link>
          </div>
        )}
        {prepareMutation.isError && (
          <p className="text-xs text-red-400">{String(prepareMutation.error)}</p>
        )}
      </div>

      <div className={`rounded-lg border p-3 ${workflow.ready_for_approval ? "border-emerald-400/15 bg-emerald-400/[0.04]" : "border-amber-400/15 bg-amber-400/[0.04]"}`}>
        <div className="flex items-center gap-2 text-xs font-medium">
          {workflow.ready_for_approval ? <CheckCircle className="h-3.5 w-3.5 text-emerald-300" /> : <ShieldAlert className="h-3.5 w-3.5 text-amber-300" />}
          <span className={workflow.ready_for_approval ? "text-emerald-100" : "text-amber-100"}>{workflow.ready_for_approval ? "Approval checks passed" : "Approval checks need attention"}</span>
        </div>
        {!workflow.ready_for_approval && (
          <ul className="mt-2 space-y-1 text-[11px] leading-relaxed text-[var(--text-secondary)]">
            {workflow.review_issues.map((issue) => <li key={issue}>• {issue}</li>)}
          </ul>
        )}
        {!workflow.ready_for_approval && <Link href={`/projects/${projectId}/artifacts`} className="mt-2 inline-flex items-center gap-1 text-[11px] text-indigo-200 hover:text-white">Review project artifacts <ArrowUpRight className="h-3 w-3" /></Link>}
      </div>

      <textarea
        aria-label="Reviewer notes"
        className="w-full rounded-lg bg-white/[0.03] border border-white/[0.08] px-3 py-2 text-xs text-[var(--text-secondary)] placeholder:text-[var(--text-muted)] focus:outline-none focus:ring-2 focus:ring-indigo-500/30 focus:border-indigo-500/30 resize-none transition-all"
        rows={2}
        placeholder="Notes for the decision. Required when requesting changes."
        value={notes}
        onChange={(e) => { setNotes(e.target.value); setNotesError(null); }}
      />
      {notesError && <p role="alert" className="text-xs text-red-300">{notesError}</p>}

      <div className="grid grid-cols-1 gap-2 sm:grid-cols-2">
        <Button size="sm" onClick={() => decide("approve")} loading={mutation.isPending} disabled={mutation.isPending || !workflow.ready_for_approval}>
          <CheckCircle className="h-3.5 w-3.5" /> Approve and continue
        </Button>
        <Button size="sm" variant="outline" onClick={() => decide("request_changes")} disabled={mutation.isPending}>
          <RefreshCw className="h-3.5 w-3.5" /> Request changes
        </Button>
      </div>

      <Button size="sm" variant="ghost" className="text-red-300 hover:bg-red-500/10 hover:text-red-200" onClick={() => decide("reject")} disabled={mutation.isPending}>
        <XCircle className="h-3.5 w-3.5" /> Reject project
      </Button>

      {mutation.isError && (
        <p className="text-xs text-red-400">{String(mutation.error)}</p>
      )}
    </div>
  );
}
