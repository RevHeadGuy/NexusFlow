"use client";

import { Check, CircleAlert } from "lucide-react";
import { WORKFLOW_STAGES, cn } from "@/lib/utils";
import type { Workflow } from "@/lib/types/api";

export function WorkflowStepper({ workflow }: { workflow: Workflow }) {
  const stagePlan = (workflow.stage_plan?.length ? workflow.stage_plan : WORKFLOW_STAGES.map((stage) => stage.key))
    .map((key) => WORKFLOW_STAGES.find((stage) => stage.key === key))
    .filter((stage): stage is (typeof WORKFLOW_STAGES)[number] => Boolean(stage));
  const currentIndex = stagePlan.findIndex((stage) => stage.key === workflow.current_stage);
  const isBlocked = workflow.status === "revision_requested" || workflow.status === "rejected";
  const isComplete = workflow.status === "completed";

  return (
    <div className="space-y-4">
      <div className="flex items-center justify-between gap-4">
        <div>
          <p className="text-sm font-semibold text-[var(--text-primary)]">Workflow progress</p>
          <p className="mt-1 text-xs text-[var(--text-secondary)]">
            {isComplete ? "All stages have been reviewed." : `${Math.max(currentIndex + 1, 1)} of ${stagePlan.length} stages · approvals are recorded in project history.`}
          </p>
        </div>
        <span className={cn(
          "shrink-0 rounded-full border px-2.5 py-1 text-[10px] font-medium capitalize",
          isComplete ? "border-emerald-400/20 bg-emerald-400/10 text-emerald-300" :
            isBlocked ? "border-amber-400/20 bg-amber-400/10 text-amber-300" :
              "border-indigo-400/20 bg-indigo-400/10 text-indigo-200"
        )}>{workflow.status.replace(/_/g, " ")}</span>
      </div>

      <div className="overflow-x-auto pb-1" aria-label="Workflow stages">
        <ol className="flex min-w-[700px] items-start">
          {stagePlan.map((stage, index) => {
            const done = index < currentIndex || isComplete;
            const active = index === currentIndex && !isComplete;
            const blocked = active && isBlocked;
            const future = index > currentIndex && !isComplete;
            return (
              <li key={stage.key} className="flex min-w-0 flex-1 items-start last:flex-none">
                <div className="flex w-[104px] shrink-0 flex-col items-center text-center">
                  <div className={cn(
                    "relative flex h-9 w-9 items-center justify-center rounded-full border transition-colors",
                    done && "border-emerald-400/30 bg-emerald-400/15 text-emerald-300",
                    active && !blocked && "border-indigo-400/40 bg-indigo-500/20 text-indigo-200 ring-4 ring-indigo-500/10",
                    blocked && "border-amber-400/40 bg-amber-400/10 text-amber-300",
                    future && "border-white/[0.12] bg-white/[0.03] text-[var(--text-muted)]"
                  )}>
                    {done ? <Check className="h-4 w-4" aria-hidden="true" /> : blocked ? <CircleAlert className="h-4 w-4" aria-hidden="true" /> : <span className="text-xs font-semibold" aria-hidden="true">{index + 1}</span>}
                    <span className="sr-only">{done ? "Complete" : active ? "Current stage" : "Upcoming"}</span>
                  </div>
                  <span className={cn(
                    "mt-2 text-[11px] font-medium leading-tight",
                    done ? "text-emerald-200" : active && !blocked ? "text-indigo-200" : blocked ? "text-amber-200" : "text-[var(--text-muted)]"
                  )}>{stage.short}</span>
                </div>
                {index < stagePlan.length - 1 && (
                  <div className="mt-[18px] h-px min-w-3 flex-1 bg-white/[0.1]">
                    <div className={cn("h-full", index < currentIndex && "bg-emerald-400/70")} />
                  </div>
                )}
              </li>
            );
          })}
        </ol>
      </div>
    </div>
  );
}
