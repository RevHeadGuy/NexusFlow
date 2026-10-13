"use client";

import { useState } from "react";
import { useParams } from "next/navigation";
import Link from "next/link";
import { Brain, Loader2, GitBranch, ArrowRight, Pencil, Save, X } from "lucide-react";
import { useProject, useProjectBrief, useAnalyzeIdea, useSaveProjectBrief } from "@/lib/hooks/useProjects";
import { useWorkflow } from "@/lib/hooks/useWorkflow";
import { Button } from "@/components/ui/Button";
import { Card, CardContent, GlassCard } from "@/components/ui/Card";
import type { ProjectBrief } from "@/lib/types/api";

type BriefDraft = {
  problem_statement: string;
  target_users: string;
  goals: string;
  constraints: string;
  success_criteria: string;
  clarifying_questions: string;
};

const briefTextareaClass = "w-full resize-y rounded-lg border border-white/[0.08] bg-white/[0.03] px-3 py-2.5 text-sm text-[var(--text-primary)] focus:outline-none focus:ring-2 focus:ring-indigo-500/40";

function BriefTag({ label }: { label: string }) {
  return (
    <span className="inline-flex items-center rounded-lg bg-white/[0.04] border border-white/[0.08] px-2.5 py-1 text-xs text-[var(--text-secondary)]">
      {label}
    </span>
  );
}

function BriefSection({ label, items, accent }: { label: string; items: string[]; accent?: string }) {
  return (
    <div className="space-y-2">
      <p className={`text-[10px] font-semibold uppercase tracking-widest ${accent ?? "text-[var(--text-muted)]"}`}>
        {label}
      </p>
      <div className="flex flex-wrap gap-1.5">
        {items.map((item, i) => <BriefTag key={i} label={item} />)}
      </div>
    </div>
  );
}

export default function ProjectPage() {
  const { id } = useParams<{ id: string }>();
  const { data: project, isLoading: projectLoading, error: projectError, refetch: refetchProject } = useProject(id);
  const { data: brief, isLoading: briefLoading } = useProjectBrief(id);
  const analyzeMutation = useAnalyzeIdea(id);
  const saveBriefMutation = useSaveProjectBrief(id);
  const [editingBrief, setEditingBrief] = useState(false);
  const [briefDraft, setBriefDraft] = useState<BriefDraft | null>(null);
  const [briefEditError, setBriefEditError] = useState<string | null>(null);
  const { data: workflow, isLoading: workflowLoading } = useWorkflow(id);

  if (projectLoading) {
    return (
      <div className="flex h-40 items-center justify-center">
        <Loader2 className="h-5 w-5 animate-spin text-[var(--text-muted)]" />
      </div>
    );
  }

  if (projectError || !project) {
    return (
      <div className="mx-auto max-w-xl p-6 sm:p-10">
        <div className="rounded-xl border border-red-400/20 bg-red-400/[0.06] p-5">
          <p className="font-medium text-red-200">Project could not be loaded</p>
          <p className="mt-1 text-sm text-[var(--text-secondary)]">Check the API connection and try again.</p>
          <Button className="mt-4" variant="secondary" size="sm" onClick={() => refetchProject()}>Try again</Button>
        </div>
      </div>
    );
  }

  function beginBriefEdit() {
    if (!brief) return;
    setBriefDraft({
      problem_statement: brief.problem_statement,
      target_users: brief.target_users.join("\n"),
      goals: brief.goals.join("\n"),
      constraints: brief.constraints.join("\n"),
      success_criteria: brief.success_criteria.join("\n"),
      clarifying_questions: brief.clarifying_questions.join("\n"),
    });
    setBriefEditError(null);
    setEditingBrief(true);
  }

  function saveBrief() {
    if (!briefDraft) return;
    const toList = (value: string) => value.split("\n").map((item) => item.trim()).filter(Boolean);
    const data: Omit<ProjectBrief, "id" | "project_id" | "created_at" | "updated_at"> = {
      problem_statement: briefDraft.problem_statement.trim(),
      target_users: toList(briefDraft.target_users),
      goals: toList(briefDraft.goals),
      constraints: toList(briefDraft.constraints),
      success_criteria: toList(briefDraft.success_criteria),
      clarifying_questions: toList(briefDraft.clarifying_questions),
    };
    if (data.problem_statement.length < 10 || !data.target_users.length || !data.goals.length || !data.constraints.length || !data.success_criteria.length) {
      setBriefEditError("Add a problem statement and at least one item for users, goals, constraints, and success criteria.");
      return;
    }
    setBriefEditError(null);
    saveBriefMutation.mutate(data, { onSuccess: () => setEditingBrief(false) });
  }

  return (
    <div className="mx-auto w-full max-w-6xl p-4 sm:p-6 lg:p-8 space-y-6 animate-fade-in-up">
      <GlassCard className="flex flex-col gap-4 p-5 sm:flex-row sm:items-center sm:justify-between">
        <div className="flex items-start gap-3">
          <div className="rounded-lg bg-indigo-500/10 p-2"><GitBranch className="h-4 w-4 text-indigo-400" /></div>
          <div>
            <p className="text-sm font-semibold text-[var(--text-primary)]">
              {workflow?.status === "completed" ? "Project workflow complete" : workflow?.status === "rejected" ? "Workflow review required" : workflow ? "Continue project workflow" : brief ? "Your idea brief is ready" : "Start with an idea brief"}
            </p>
            <p className="mt-1 text-sm leading-relaxed text-[var(--text-secondary)]">
              {workflow?.status === "completed" ? "All approvals are recorded. Review and export the saved project artifacts." : workflow?.status === "rejected" ? "Review the decision history and project artifacts." : workflow ? `Current stage: ${workflow.current_stage.replace(/_/g, " ")}. Prepare the draft, review it, then record your decision.` : workflowLoading ? "Checking workflow status…" : briefLoading ? "Checking whether an idea brief is ready…" : brief ? "Start the staged review workflow. You control every approval." : "Generate a structured brief, then move through the workflow one review at a time."}
            </p>
          </div>
        </div>
        {workflow?.status === "completed" ? (
          <Link href={`/projects/${id}/artifacts`}><Button variant="secondary" size="sm">View final package <ArrowRight className="h-3.5 w-3.5" /></Button></Link>
        ) : workflow ? (
          <Link href={`/projects/${id}/workflow`}><Button variant="secondary" size="sm">Open workflow <ArrowRight className="h-3.5 w-3.5" /></Button></Link>
        ) : workflowLoading || briefLoading ? (
          <Button size="sm" disabled loading>Loading project status</Button>
        ) : brief ? (
          <Link href={`/projects/${id}/workflow`}><Button size="sm">Configure workflow <ArrowRight className="h-3.5 w-3.5" /></Button></Link>
        ) : (
          <Button size="sm" onClick={() => analyzeMutation.mutate()} loading={analyzeMutation.isPending}><Brain className="h-3.5 w-3.5" /> Generate Brief</Button>
        )}
      </GlassCard>
      <Card>
        <div className="flex items-center justify-between border-b border-white/[0.05] px-5 py-4">
          <span className="text-xs font-semibold uppercase tracking-widest text-indigo-300">Project idea</span>
          <span className="text-xs text-[var(--text-muted)]">Submitted {new Date(project.created_at).toLocaleDateString()}</span>
        </div>
        <CardContent>
          <p className="whitespace-pre-wrap text-sm leading-7 text-[var(--text-secondary)]">{project.idea}</p>
        </CardContent>
      </Card>

      {/* Brief */}
      {brief ? (
        <div className="space-y-4">
          <div className="flex flex-col gap-3 sm:flex-row sm:items-center sm:justify-between">
            <div className="flex items-center gap-2">
              <Brain className="h-4 w-4 text-indigo-400" />
              <h2 className="text-sm font-semibold text-[var(--text-primary)]">Idea Brief</h2>
              <span className="text-xs text-emerald-400 bg-emerald-400/10 border border-emerald-400/20 px-2 py-0.5 rounded-full">
                Generated brief
              </span>
            </div>
            <div className="flex flex-wrap gap-2">
              {editingBrief ? (
                <>
                  <Button size="sm" variant="ghost" onClick={() => { setEditingBrief(false); setBriefEditError(null); }} disabled={saveBriefMutation.isPending}>
                    <X className="h-3.5 w-3.5" /> Cancel
                  </Button>
                  <Button size="sm" onClick={saveBrief} loading={saveBriefMutation.isPending} disabled={saveBriefMutation.isPending}>
                    <Save className="h-3.5 w-3.5" /> Save brief
                  </Button>
                </>
              ) : (
                <>
                  <Button size="sm" variant="secondary" onClick={beginBriefEdit}>
                    <Pencil className="h-3.5 w-3.5" /> Edit brief
                  </Button>
                  <Button size="sm" variant="ghost" onClick={() => analyzeMutation.mutate()} loading={analyzeMutation.isPending}>
                    Regenerate
                  </Button>
                </>
              )}
            </div>
          </div>
          {analyzeMutation.isError && <p role="alert" className="text-xs text-red-300">Brief could not be regenerated: {String(analyzeMutation.error)}</p>}
          {analyzeMutation.data?.token_usage && (
            <p className="text-xs text-[var(--text-muted)]">
              Generated with {analyzeMutation.data.token_usage.provider} · {analyzeMutation.data.token_usage.model} · {analyzeMutation.data.token_usage.input_tokens ?? "—"} input + {analyzeMutation.data.token_usage.output_tokens ?? "—"} output tokens
            </p>
          )}
          {saveBriefMutation.isError && <p role="alert" className="text-xs text-red-300">Brief could not be saved: {String(saveBriefMutation.error)}</p>}

          {editingBrief && briefDraft ? (
            <Card>
              <CardContent className="space-y-4">
                <p className="text-xs text-[var(--text-muted)]">Enter one list item per line. Saving also updates the saved Idea Brief artifact as a new version, if one exists.</p>
                <label className="block space-y-1.5 text-xs font-medium text-[var(--text-secondary)]">Problem statement
                  <textarea rows={3} value={briefDraft.problem_statement} onChange={(event) => setBriefDraft({ ...briefDraft, problem_statement: event.target.value })} className={briefTextareaClass} />
                </label>
                {([
                  ["target_users", "Target users"],
                  ["goals", "Goals"],
                  ["constraints", "Constraints"],
                  ["success_criteria", "Success criteria"],
                  ["clarifying_questions", "Open questions"],
                ] as const).map(([key, label]) => (
                  <label key={key} className="block space-y-1.5 text-xs font-medium text-[var(--text-secondary)]">{label}
                    <textarea rows={3} value={briefDraft[key]} onChange={(event) => setBriefDraft({ ...briefDraft, [key]: event.target.value })} className={briefTextareaClass} placeholder="One item per line" />
                  </label>
                ))}
                {briefEditError && <p role="alert" className="text-xs text-red-300">{briefEditError}</p>}
              </CardContent>
            </Card>
          ) : (
            <>
          {/* Problem statement — featured */}
          <GlassCard className="p-5">
            <p className="text-[10px] font-semibold uppercase tracking-widest text-indigo-400 mb-2">
              Problem Statement
            </p>
            <p className="text-sm text-[var(--text-primary)] leading-relaxed">{brief.problem_statement}</p>
          </GlassCard>

          <div className="grid gap-4 sm:grid-cols-2">
            <Card>
              <CardContent className="space-y-4">
                <BriefSection label="Target Users" items={brief.target_users} accent="text-purple-400" />
                <BriefSection label="Goals" items={brief.goals} accent="text-emerald-400" />
              </CardContent>
            </Card>
            <Card>
              <CardContent className="space-y-4">
                <BriefSection label="Constraints" items={brief.constraints} accent="text-amber-400" />
                <BriefSection label="Success Criteria" items={brief.success_criteria} accent="text-teal-400" />
              </CardContent>
            </Card>
          </div>

          {brief.clarifying_questions.length > 0 && (
            <Card>
              <CardContent>
                <p className="text-[10px] font-semibold uppercase tracking-widest text-amber-400 mb-3">
                  Clarifying Questions
                </p>
                <ul className="space-y-2">
                  {brief.clarifying_questions.map((q, i) => (
                    <li key={i} className="flex items-start gap-2.5 text-sm text-[var(--text-secondary)]">
                      <span className="mt-0.5 text-xs text-amber-400 font-mono shrink-0">Q{i + 1}</span>
                      {q}
                    </li>
                  ))}
                </ul>
              </CardContent>
            </Card>
          )}
            </>
          )}
        </div>
      ) : (
        <div className="rounded-xl border border-dashed border-white/[0.08] py-16 flex flex-col items-center gap-4">
          <div className="p-3 rounded-xl bg-indigo-500/10">
            <Brain className="h-6 w-6 text-indigo-400" />
          </div>
          <div className="text-center">
            <p className="text-sm font-medium text-[var(--text-primary)]">No idea brief yet</p>
            <p className="text-xs text-[var(--text-muted)] mt-1">
              Run AI analysis to generate a structured brief from your idea
            </p>
          </div>
          <Button onClick={() => analyzeMutation.mutate()} loading={analyzeMutation.isPending}>
            <Brain className="h-3.5 w-3.5" />
            Analyze with AI
          </Button>
          {analyzeMutation.isError && (
            <p className="text-xs text-red-400 max-w-sm text-center">{String(analyzeMutation.error)}</p>
          )}
        </div>
      )}
    </div>
  );
}
