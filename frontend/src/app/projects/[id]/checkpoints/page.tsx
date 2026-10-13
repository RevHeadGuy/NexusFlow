"use client";

import { useParams } from "next/navigation";
import { useCheckpoints } from "@/lib/hooks/useCheckpoints";
import { CheckpointCard } from "@/components/hitl/CheckpointCard";
import { ListChecks } from "lucide-react";

export default function CheckpointsPage() {
  const { id } = useParams<{ id: string }>();
  const { data: checkpoints, isLoading } = useCheckpoints(id);
  const pending = checkpoints?.filter((c) => c.status === "pending").length ?? 0;

  if (isLoading) return (
    <div className="flex h-40 items-center justify-center text-sm text-[var(--text-muted)]">Loading…</div>
  );

  return (
    <div className="p-4 sm:p-6 lg:p-8 space-y-5 animate-fade-in-up">
      <div className="flex items-center justify-between">
        <h2 className="text-sm font-semibold text-[var(--text-primary)]">Checkpoints</h2>
        {pending > 0 && (
          <span className="text-xs bg-amber-500/10 text-amber-400 border border-amber-500/20 px-2.5 py-0.5 rounded-full">
            {pending} pending
          </span>
        )}
      </div>

      {!checkpoints || checkpoints.length === 0 ? (
        <div className="flex flex-col items-center gap-3 py-20">
          <div className="p-3 rounded-xl bg-white/[0.03] border border-white/[0.06]"><ListChecks className="h-6 w-6 text-[var(--text-muted)]" /></div>
          <p className="text-sm text-[var(--text-muted)]">No checkpoints yet</p>
        </div>
      ) : (
        <div className="space-y-3">
          {checkpoints.map((cp) => (
            <CheckpointCard key={cp.id} checkpoint={cp} projectId={id} />
          ))}
        </div>
      )}
    </div>
  );
}
