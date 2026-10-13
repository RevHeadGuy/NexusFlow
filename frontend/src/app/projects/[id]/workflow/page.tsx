"use client";

import { useState } from "react";
import { useParams } from "next/navigation";
import { useWorkflow, useStartWorkflow } from "@/lib/hooks/useWorkflow";
import { useViolations } from "@/lib/hooks/useDashboard";
import { WorkflowStepper } from "@/components/workflow/WorkflowStepper";
import { ApprovalPanel } from "@/components/workflow/ApprovalPanel";
import { ViolationBadge } from "@/components/guardrails/ViolationBadge";
import { Button } from "@/components/ui/Button";
import { Card, CardContent } from "@/components/ui/Card";
import { dashboardApi } from "@/lib/api/dashboard";
import { useQueryClient } from "@tanstack/react-query";
import { STATUS_STYLES, cn, formatDate } from "@/lib/utils";
import Link from "next/link";
import { FileText, GitBranch, Zap, ArrowRight } from "lucide-react";
import { WORKFLOW_STAGES } from "@/lib/utils";
import { ApiError } from "@/lib/api/client";
import { WORKFLOW_TEMPLATES } from "@/lib/templates";

export default function WorkflowPage() {
  const { id } = useParams<{ id: string }>();
  const { data: workflow, isLoading, isError, error, refetch } = useWorkflow(id);
  const startMutation = useStartWorkflow(id);
  const [templateKey, setTemplateKey] = useState<string>(WORKFLOW_TEMPLATES[0].key);
  const [selectedStages, setSelectedStages] = useState<string[]>([...WORKFLOW_TEMPLATES[0].stagePlan]);
  const { data: violations } = useViolations(id);
  const qc = useQueryClient();
  const currentStage = workflow && WORKFLOW_STAGES.find((stage) => stage.key === workflow.current_stage);
  const orderedSelectedStages = WORKFLOW_STAGES.filter((stage) => selectedStages.includes(stage.key)).map((stage) => stage.key);

  function handleOverride(violationId: string) {
    const note = prompt("Override note:");
    if (!note) return;
    dashboardApi
      .overrideViolation(id, violationId, { override_note: note, overridden_by: "reviewer" })
      .then(() => qc.invalidateQueries({ queryKey: ["violations", id, false] }));
  }

  if (isLoading) return (
    <div className="flex h-40 items-center justify-center text-sm text-[var(--text-muted)]">Loading…</div>
  );

  const workflowNotStarted = isError && error instanceof ApiError && error.status === 404;
  if (isError && !workflowNotStarted) {
    return (
      <div className="p-4 sm:p-6 lg:p-8">
        <div role="alert" className="rounded-xl border border-red-400/20 bg-red-400/[0.05] p-5">
          <p className="text-sm font-medium text-red-200">Saved workflow could not be loaded</p>
          <p className="mt-1 text-xs text-[var(--text-secondary)]">Your saved progress stays in the database. Check the API connection and retry.</p>
          <Button className="mt-4" size="sm" variant="secondary" onClick={() => refetch()}>Retry</Button>
        </div>
      </div>
    );
  }

  return (
    <div className="p-4 sm:p-6 lg:p-8 space-y-6 animate-fade-in-up">
      {!workflow ? (
        <div className="mx-auto flex max-w-xl flex-col items-center gap-4 rounded-2xl border border-white/[0.08] bg-white/[0.02] px-6 py-14 text-center">
          <div className="rounded-xl bg-indigo-500/10 p-3"><GitBranch className="h-6 w-6 text-indigo-300" /></div>
          <div>
            <h2 className="text-base font-semibold text-[var(--text-primary)]">Start the review workflow</h2>
            <p className="mt-1 text-sm leading-relaxed text-[var(--text-secondary)]">Choose a workflow template, tailor its stages, and save the plan with this project.</p>
          </div>
          <div className="w-full space-y-4 text-left">
            <label className="block space-y-1.5 text-xs font-medium text-[var(--text-secondary)]">
              Workflow template
              <select
                value={templateKey}
                onChange={(event) => {
                  const nextKey = event.target.value;
                  setTemplateKey(nextKey);
                  const template = WORKFLOW_TEMPLATES.find((item) => item.key === nextKey);
                  if (template) setSelectedStages([...template.stagePlan]);
                }}
                className="w-full rounded-lg border border-white/10 bg-[#111119] px-3 py-2.5 text-sm text-[var(--text-primary)] focus:outline-none focus:ring-2 focus:ring-indigo-500/40"
              >
                {WORKFLOW_TEMPLATES.map((template) => <option key={template.key} value={template.key}>{template.label}</option>)}
                <option value="custom">Custom sequence</option>
              </select>
            </label>
            <p className="text-xs text-[var(--text-muted)]">{WORKFLOW_TEMPLATES.find((item) => item.key === templateKey)?.description ?? "Choose the stages that match this project."}</p>
            <fieldset className="grid gap-2 sm:grid-cols-2">
              <legend className="mb-2 text-xs font-medium text-[var(--text-secondary)]">Included stages, in project order</legend>
              {WORKFLOW_STAGES.map((stage) => (
                <label key={stage.key} className="flex items-start gap-2 rounded-lg border border-white/[0.06] bg-white/[0.02] p-3 text-xs text-[var(--text-secondary)]">
                  <input
                    type="checkbox"
                    checked={selectedStages.includes(stage.key)}
                    onChange={(event) => {
                      setTemplateKey("custom");
                      setSelectedStages((current) => event.target.checked
                        ? [...current, stage.key]
                        : current.filter((key) => key !== stage.key));
                    }}
                    className="mt-0.5 accent-indigo-500"
                  />
                  <span><span className="block font-medium text-[var(--text-primary)]">{stage.label}</span><span className="mt-1 block text-[11px] leading-relaxed text-[var(--text-muted)]">{stage.description}</span></span>
                </label>
              ))}
            </fieldset>
          </div>
          <Button
            onClick={() => startMutation.mutate({ template_key: templateKey, stage_plan: orderedSelectedStages })}
            loading={startMutation.isPending}
            disabled={startMutation.isPending || orderedSelectedStages.length === 0}
          >
            <Zap className="h-3.5 w-3.5" /> Start workflow
          </Button>
          {orderedSelectedStages.length === 0 && <p className="text-xs text-amber-200">Select at least one stage to continue.</p>}
          {startMutation.isError && <p className="text-xs text-red-300">{String(startMutation.error)}</p>}
        </div>
      ) : (
        <>
          <Card><CardContent><WorkflowStepper workflow={workflow} /></CardContent></Card>
          <div className="rounded-lg border border-white/[0.06] bg-white/[0.02] px-4 py-3 text-xs leading-relaxed text-[var(--text-secondary)]">
            {workflow.status === "revision_requested"
              ? "Changes were requested for this stage. Save a new version of every required draft in Artifacts, then return here for another review."
              : "Your workflow stage, decisions, and artifact versions are saved locally. Reopen this page any time to continue."}
          </div>

          {currentStage && (
            <Card>
              <CardContent className="flex flex-col gap-4 sm:flex-row sm:items-center sm:justify-between">
                <div className="flex items-start gap-3">
                  <div className="rounded-lg bg-indigo-500/10 p-2"><FileText className="h-4 w-4 text-indigo-300" /></div>
                  <div>
                    <p className="text-[10px] font-semibold uppercase tracking-[0.14em] text-indigo-300">Current stage</p>
                    <h2 className="mt-1 text-base font-semibold text-[var(--text-primary)]">{currentStage.label}</h2>
                    <p className="mt-1 max-w-2xl text-sm leading-relaxed text-[var(--text-secondary)]">{currentStage.description}</p>
                  </div>
                </div>
                <div className="flex shrink-0 items-center gap-2 rounded-lg border border-white/[0.08] bg-white/[0.02] px-3 py-2 text-xs text-[var(--text-secondary)]">
                  <span className="text-[var(--text-muted)]">Deliverable</span>
                  <span className="font-medium text-[var(--text-primary)]">{currentStage.output}</span>
                </div>
              </CardContent>
            </Card>
          )}

          <div className="grid gap-4 lg:grid-cols-2">
            {/* Status */}
            <Card>
              <div className="px-5 pt-5 pb-4 border-b border-white/[0.05]">
                <p className="text-xs font-semibold text-[var(--text-muted)] uppercase tracking-widest">Status</p>
              </div>
              <CardContent className="space-y-3 text-sm">
                {[
                  ["Stage", <span key="stage" className="capitalize text-indigo-200">{workflow.current_stage.replace(/_/g, " ")}</span>],
                  ["Status", <span key="status" className={cn("inline-flex items-center gap-1 rounded-full px-2 py-0.5 text-[10px] font-medium", STATUS_STYLES[workflow.status] ?? "")}><span className="h-1 w-1 rounded-full bg-current" />{workflow.status}</span>],
                  ["Last Decision", <span key="decision" className="text-[var(--text-secondary)]">{workflow.last_decision ?? "—"}</span>],
                  ["Updated", <span key="updated" className="text-[var(--text-muted)] text-xs">{formatDate(workflow.updated_at)}</span>],
                ].map(([label, val]) => (
                  <div key={String(label)} className="flex items-center justify-between gap-4">
                    <span className="text-[var(--text-muted)] text-xs">{label}</span>
                    {val}
                  </div>
                ))}
              </CardContent>
            </Card>

            <ApprovalPanel projectId={id} workflow={workflow} />
          </div>

          {/* Decision history */}
          {workflow.decisions.length > 0 && (
            <Card>
              <div className="px-5 pt-5 pb-4 border-b border-white/[0.05]">
                <p className="text-xs font-semibold text-[var(--text-muted)] uppercase tracking-widest">Decision History</p>
              </div>
              <CardContent className="space-y-0">
                {workflow.decisions.map((d) => (
                  <div key={d.id} className="flex items-start justify-between py-3 border-b border-white/[0.04] last:border-0">
                    <div>
                      <div className="flex items-center gap-2">
                        <span className="text-sm font-medium capitalize text-[var(--text-primary)]">{d.action}</span>
                        <span className="text-xs text-[var(--text-muted)] capitalize">{d.stage.replace(/_/g, " ")}</span>
                      </div>
                      {d.notes && <p className="text-xs text-[var(--text-muted)] mt-0.5 italic">{d.notes}</p>}
                    </div>
                    <span className="text-[10px] text-[var(--text-muted)] shrink-0 ml-4">{formatDate(d.created_at)}</span>
                  </div>
                ))}
              </CardContent>
            </Card>
          )}

          {workflow.status === "completed" && (
            <div className="flex flex-col gap-3 rounded-xl border border-emerald-400/20 bg-emerald-400/[0.06] p-4 sm:flex-row sm:items-center sm:justify-between">
              <div>
                <p className="text-sm font-semibold text-emerald-100">All workflow stages are approved</p>
                <p className="mt-1 text-xs text-[var(--text-secondary)]">Export the saved project artifacts as a package.</p>
              </div>
              <Link href={`/projects/${id}/artifacts`}><Button size="sm" variant="secondary">Open artifacts <ArrowRight className="h-3.5 w-3.5" /></Button></Link>
            </div>
          )}

          {/* Violations */}
          {violations && violations.length > 0 && (
            <div className="space-y-2">
              <p className="text-xs font-semibold text-[var(--text-muted)] uppercase tracking-widest">Guardrail Violations</p>
              {violations.map((v) => (
                <ViolationBadge key={v.id} violation={v} onOverride={!v.resolved_at ? handleOverride : undefined} />
              ))}
            </div>
          )}
        </>
      )}
    </div>
  );
}
