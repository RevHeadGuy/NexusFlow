"use client";

import { useParams } from "next/navigation";
import { useQuery, useMutation, useQueryClient } from "@tanstack/react-query";
import { api } from "@/lib/api/client";
import type { EvaluationReport } from "@/lib/types/api";
import { Button } from "@/components/ui/Button";
import { Card, CardContent } from "@/components/ui/Card";
import { SEVERITY_STYLES, cn, formatDate } from "@/lib/utils";
import { ShieldCheck, Swords, FlaskConical } from "lucide-react";

export default function EvaluationsPage() {
  const { id } = useParams<{ id: string }>();
  const qc = useQueryClient();

  const { data: reports, isLoading } = useQuery({
    queryKey: ["evaluations", id],
    queryFn: () => api.get<EvaluationReport[]>(`/projects/${id}/evaluations`),
    enabled: !!id,
  });

  const consistencyMutation = useMutation({
    mutationFn: () => api.post<EvaluationReport>(`/projects/${id}/evaluations/consistency-check`),
    onSuccess: () => qc.invalidateQueries({ queryKey: ["evaluations", id] }),
  });
  const devilMutation = useMutation({
    mutationFn: () => api.post<EvaluationReport>(`/projects/${id}/evaluations/devils-advocate`),
    onSuccess: () => qc.invalidateQueries({ queryKey: ["evaluations", id] }),
  });

  if (isLoading) return (
    <div className="flex h-40 items-center justify-center text-sm text-[var(--text-muted)]">Loading…</div>
  );

  return (
    <div className="p-4 sm:p-6 lg:p-8 space-y-5 animate-fade-in-up">
      <div className="flex items-center justify-between">
        <h2 className="text-sm font-semibold text-[var(--text-primary)]">Evaluations</h2>
        <div className="flex gap-2">
          <Button size="sm" variant="secondary" onClick={() => consistencyMutation.mutate()} loading={consistencyMutation.isPending}>
            <ShieldCheck className="h-3.5 w-3.5" /> Consistency Check
          </Button>
          <Button size="sm" variant="secondary" onClick={() => devilMutation.mutate()} loading={devilMutation.isPending}>
            <Swords className="h-3.5 w-3.5" /> Devil&apos;s Advocate
          </Button>
        </div>
      </div>

      {!reports || reports.length === 0 ? (
        <div className="flex flex-col items-center gap-3 py-20">
          <div className="p-3 rounded-xl bg-white/[0.03] border border-white/[0.06]"><FlaskConical className="h-6 w-6 text-[var(--text-muted)]" /></div>
          <p className="text-sm text-[var(--text-muted)]">No evaluations yet — run one above</p>
        </div>
      ) : (
        <div className="space-y-4">
          {reports.map((report) => (
            <Card key={report.id}>
              <div className="px-5 pt-5 pb-3 border-b border-white/[0.05] flex items-center justify-between">
                <p className="text-sm font-semibold text-[var(--text-primary)] capitalize">
                  {report.report_type.replace(/_/g, " ")}
                </p>
                <span className="text-[10px] text-[var(--text-muted)]">{formatDate(report.created_at)}</span>
              </div>
              {report.summary && (
                <div className="px-5 py-3 border-b border-white/[0.04]">
                  <p className="text-xs text-[var(--text-secondary)]">{report.summary}</p>
                </div>
              )}
              {report.findings && report.findings.length > 0 && (
                <CardContent className="space-y-2 pt-4">
                  {report.findings.map((f) => {
                    const styles = SEVERITY_STYLES[f.severity] ?? SEVERITY_STYLES.medium;
                    return (
                      <div key={f.id} className="rounded-lg border border-white/[0.06] bg-white/[0.02] p-3 space-y-1.5">
                        <div className="flex items-center gap-2">
                          <span className={cn("inline-flex items-center rounded-full px-2 py-0.5 text-[10px] font-semibold", styles.badge)}>
                            {f.severity}
                          </span>
                          <span className="text-[10px] text-[var(--text-muted)]">{f.category}</span>
                        </div>
                        <p className="text-xs font-semibold text-[var(--text-primary)]">{f.title}</p>
                        <p className="text-xs text-[var(--text-secondary)]">{f.description}</p>
                        {f.recommendation && (
                          <p className="text-xs text-indigo-400">↗ {f.recommendation}</p>
                        )}
                      </div>
                    );
                  })}
                </CardContent>
              )}
            </Card>
          ))}
        </div>
      )}
    </div>
  );
}
