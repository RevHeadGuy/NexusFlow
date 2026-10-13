import { ShieldAlert, ShieldCheck } from "lucide-react";
import { SEVERITY_STYLES, cn } from "@/lib/utils";
import type { GuardrailViolation } from "@/lib/types/api";

interface Props {
  violation: GuardrailViolation;
  onOverride?: (id: string) => void;
}

export function ViolationBadge({ violation, onOverride }: Props) {
  const resolved = !!violation.resolved_at;
  const styles = SEVERITY_STYLES[violation.severity] ?? SEVERITY_STYLES.medium;

  return (
    <div className={cn(
      "flex items-start gap-3 rounded-xl border p-4 transition-all duration-200",
      resolved
        ? "border-white/[0.06] bg-white/[0.02] opacity-50"
        : violation.severity === "critical" || violation.severity === "high"
          ? "border-red-500/20 bg-red-500/[0.04]"
          : "border-amber-500/20 bg-amber-500/[0.04]"
    )}>
      <div className={cn(
        "mt-0.5 p-1.5 rounded-lg shrink-0",
        resolved ? "bg-emerald-500/10 text-emerald-400" : "bg-red-500/10 text-red-400"
      )}>
        {resolved
          ? <ShieldCheck className="h-3.5 w-3.5" />
          : <ShieldAlert className="h-3.5 w-3.5" />
        }
      </div>

      <div className="flex-1 min-w-0 space-y-1.5">
        <div className="flex items-center gap-2 flex-wrap">
          <span className={cn(
            "inline-flex items-center rounded-full px-2 py-0.5 text-[10px] font-semibold",
            styles.badge
          )}>
            {violation.severity}
          </span>
          <span className="text-[10px] font-mono text-[var(--text-muted)] bg-white/[0.04] px-2 py-0.5 rounded">
            {violation.rule_name}
          </span>
          <span className="text-[10px] text-[var(--text-muted)]">
            {violation.stage.replace(/_/g, " ")} · {violation.agent_name}
          </span>
        </div>
        <p className="text-sm text-[var(--text-secondary)]">{violation.message}</p>
        {resolved && violation.overridden_by && (
          <div className="flex items-center gap-1.5">
            <ShieldCheck className="h-3 w-3 text-emerald-400" />
            <p className="text-xs text-emerald-400">
              Overridden by {violation.overridden_by}
              {violation.override_note && ` — "${violation.override_note}"`}
            </p>
          </div>
        )}
      </div>

      {!resolved && onOverride && (
        <button
          onClick={() => onOverride(violation.id)}
          className="shrink-0 text-xs text-indigo-400 hover:text-indigo-300 bg-indigo-500/10 hover:bg-indigo-500/20 border border-indigo-500/20 px-2.5 py-1 rounded-lg transition-all"
        >
          Override
        </button>
      )}
    </div>
  );
}
