"use client";

import { useState } from "react";
import { CheckCircle, XCircle, GitBranch, Clock } from "lucide-react";
import { Button } from "@/components/ui/Button";
import { STATUS_STYLES, cn, formatRelative } from "@/lib/utils";
import { useReviewCheckpoint } from "@/lib/hooks/useCheckpoints";
import type { Checkpoint } from "@/lib/types/api";

export function CheckpointCard({ checkpoint, projectId }: { checkpoint: Checkpoint; projectId: string }) {
  const [notes, setNotes] = useState("");
  const mutation = useReviewCheckpoint(projectId, checkpoint.id);
  const isPending = checkpoint.status === "pending";

  function submit(action: "approve" | "approve_with_edits" | "reject") {
    mutation.mutate({ action, reviewer_notes: notes || undefined });
  }

  return (
    <div className={cn(
      "rounded-xl border transition-all duration-200",
      isPending
        ? "border-amber-500/20 bg-amber-500/[0.03] hover:border-amber-500/30"
        : "border-white/[0.06] bg-white/[0.02]"
    )}>
      {/* Header */}
      <div className="flex items-start justify-between px-4 pt-4 pb-3">
        <div className="flex items-center gap-2.5">
          <div className={cn(
            "p-1.5 rounded-lg",
            isPending ? "bg-amber-500/10 text-amber-400" : "bg-white/[0.04] text-[var(--text-muted)]"
          )}>
            {isPending ? <Clock className="h-3.5 w-3.5" /> : <GitBranch className="h-3.5 w-3.5" />}
          </div>
          <div>
            <p className="text-sm font-medium text-[var(--text-primary)] capitalize">
              {checkpoint.stage.replace(/_/g, " ")}
            </p>
            <p className="text-[10px] text-[var(--text-muted)] mt-0.5">
              {checkpoint.checkpoint_type.replace(/_/g, " ")} · {formatRelative(checkpoint.created_at)}
            </p>
          </div>
        </div>
        <span className={cn(
          "inline-flex items-center gap-1.5 rounded-full px-2.5 py-0.5 text-[10px] font-medium",
          STATUS_STYLES[checkpoint.status] ?? "bg-zinc-500/10 text-zinc-400"
        )}>
          <span className="h-1 w-1 rounded-full bg-current" />
          {checkpoint.status.replace(/_/g, " ")}
        </span>
      </div>

      {/* Reviewed note */}
      {!isPending && checkpoint.reviewer_notes && (
        <div className="mx-4 mb-3 rounded-lg bg-white/[0.03] border border-white/[0.06] px-3 py-2">
          <p className="text-xs text-[var(--text-muted)] italic">
            &ldquo;{checkpoint.reviewer_notes}&rdquo;
          </p>
          {checkpoint.reviewed_by && (
            <p className="text-[10px] text-[var(--text-muted)] mt-1">— {checkpoint.reviewed_by}</p>
          )}
        </div>
      )}

      {/* Review controls */}
      {isPending && (
        <div className="px-4 pb-4 space-y-3 border-t border-white/[0.05] pt-3">
          <textarea
            className="w-full rounded-lg bg-white/[0.03] border border-white/[0.08] px-3 py-2 text-xs text-[var(--text-secondary)] placeholder:text-[var(--text-muted)] focus:outline-none focus:ring-2 focus:ring-indigo-500/30 resize-none transition-all"
            rows={2}
            placeholder="Reviewer notes (optional)…"
            value={notes}
            onChange={(e) => setNotes(e.target.value)}
          />
          <div className="flex gap-2">
            <Button size="sm" onClick={() => submit("approve")} loading={mutation.isPending}>
              <CheckCircle className="h-3.5 w-3.5" /> Approve
            </Button>
            <Button size="sm" variant="secondary" onClick={() => submit("approve_with_edits")} disabled={mutation.isPending}>
              Approve w/ Edits
            </Button>
            <Button size="sm" variant="destructive" onClick={() => submit("reject")} disabled={mutation.isPending}>
              <XCircle className="h-3.5 w-3.5" /> Reject
            </Button>
          </div>
          {mutation.isError && (
            <p className="text-xs text-red-400">{String(mutation.error)}</p>
          )}
        </div>
      )}
    </div>
  );
}
