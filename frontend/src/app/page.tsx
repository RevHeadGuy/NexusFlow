"use client";

import Link from "next/link";
import { useRouter } from "next/navigation";
import { ArrowRight, Plus, AlertTriangle, Clock, CheckCircle, TrendingUp, Activity, Layers, Sparkles } from "lucide-react";
import { useDashboardStats } from "@/lib/hooks/useDashboard";
import { useCreateProject } from "@/lib/hooks/useProjects";
import { Card, CardContent, GlassCard } from "@/components/ui/Card";
import { Button } from "@/components/ui/Button";
import { STATUS_STYLES, cn, formatRelative, WORKFLOW_STAGES } from "@/lib/utils";

function StatCard({
  label, value, sub, icon: Icon, accent,
}: {
  label: string; value: string | number; sub?: string;
  icon: React.ElementType; accent: string;
}) {
  return (
    <div className={cn(
      "relative rounded-xl p-5 overflow-hidden surface transition-all duration-200 hover:border-white/[0.12] group"
    )}>
      {/* Glow accent */}
      <div className={cn(
        "absolute inset-0 opacity-0 group-hover:opacity-100 transition-opacity duration-300",
        accent === "blue" && "bg-gradient-to-br from-indigo-600/5 to-transparent",
        accent === "amber" && "bg-gradient-to-br from-amber-500/5 to-transparent",
        accent === "red"   && "bg-gradient-to-br from-red-500/5 to-transparent",
        accent === "green" && "bg-gradient-to-br from-emerald-500/5 to-transparent",
      )} />
      <div className="relative flex items-start justify-between">
        <div>
          <p className="text-xs text-[var(--text-muted)] font-medium uppercase tracking-wider">{label}</p>
          <p className={cn(
            "mt-2 text-3xl font-bold tracking-tight",
            accent === "blue"  && "text-indigo-300",
            accent === "amber" && "text-amber-300",
            accent === "red"   && "text-red-400",
            accent === "green" && "text-emerald-300",
          )}>
            {value}
          </p>
          {sub && <p className="mt-1 text-xs text-[var(--text-muted)]">{sub}</p>}
        </div>
        <div className={cn(
          "p-2.5 rounded-lg",
          accent === "blue"  && "bg-indigo-500/10 text-indigo-400",
          accent === "amber" && "bg-amber-500/10 text-amber-400",
          accent === "red"   && "bg-red-500/10 text-red-400",
          accent === "green" && "bg-emerald-500/10 text-emerald-400",
        )}>
          <Icon className="h-5 w-5" />
        </div>
      </div>
    </div>
  );
}

export default function DashboardPage() {
  const router = useRouter();
  const createProject = useCreateProject();
  const { data: stats, isLoading, error, refetch } = useDashboardStats();

  if (isLoading) {
    return (
      <div className="flex h-full items-center justify-center">
        <div className="flex items-center gap-3 text-[var(--text-muted)]">
          <svg className="h-4 w-4 animate-spin" fill="none" viewBox="0 0 24 24">
            <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4"/>
            <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8v8H4z"/>
          </svg>
          <span className="text-sm">Loading dashboard…</span>
        </div>
      </div>
    );
  }

  if (error || !stats) {
    return (
      <div className="p-4 sm:p-6 lg:p-8">
        <div role="alert" className="rounded-xl border border-red-400/20 bg-red-400/[0.05] p-5">
          <p className="text-sm font-medium text-red-200">Dashboard data is unavailable</p>
          <p className="mt-1 text-xs text-[var(--text-secondary)]">Check that the NexusFlow API is running, then try again.</p>
          <Button className="mt-4" size="sm" variant="secondary" onClick={() => refetch()}>Retry connection</Button>
        </div>
      </div>
    );
  }

  return (
    <div className="mx-auto w-full max-w-7xl space-y-7 p-4 sm:p-6 lg:p-8 animate-fade-in-up">
      {/* Header */}
      <div className="flex flex-col gap-4 sm:flex-row sm:items-center sm:justify-between">
        <div>
          <h1 className="text-2xl font-bold text-[var(--text-primary)] tracking-tight">Dashboard</h1>
          <p className="text-sm text-[var(--text-muted)] mt-1">
            Projects, approvals, and recent agent activity
          </p>
        </div>
        <Link href="/projects/new">
          <Button>
            <Plus className="h-3.5 w-3.5" />
            New Project
          </Button>
        </Link>
      </div>

      {/* Stats */}
      <div className="grid grid-cols-2 gap-4 lg:grid-cols-4">
        <StatCard label="Total Projects"   value={stats.total_projects}       icon={Layers}        accent="blue" />
        <StatCard label="Pending Reviews"  value={stats.pending_checkpoints}  icon={Clock}         accent="amber"
          sub={stats.pending_checkpoints === 0 ? "All clear" : "Awaiting review"} />
        <StatCard label="Active Violations" value={stats.blocking_violations} icon={AlertTriangle}  accent="red"
          sub={stats.blocking_violations === 0 ? "No blockers" : "Need override"} />
        <StatCard label="Completed"        value={stats.projects_by_status?.completed ?? 0} icon={CheckCircle} accent="green" />
      </div>

      {stats.total_projects === 0 && (
        <GlassCard className="overflow-hidden p-5 sm:p-7">
          <div className="grid gap-6 lg:grid-cols-[1fr_auto] lg:items-center">
            <div className="max-w-2xl">
              <div className="mb-3 inline-flex items-center gap-2 rounded-full border border-indigo-400/20 bg-indigo-400/[0.08] px-3 py-1 text-xs font-medium text-indigo-200">
                <Sparkles className="h-3.5 w-3.5" /> Start here
              </div>
              <h2 className="text-lg font-semibold tracking-tight text-[var(--text-primary)]">Turn a project idea into a reviewable plan</h2>
              <p className="mt-2 text-sm leading-relaxed text-[var(--text-secondary)]">NexusFlow structures your idea, prepares stage drafts, and keeps you in control of every workflow decision. Try a sample project or bring your own.</p>
              <p className="mt-3 text-xs text-[var(--text-muted)]">The sample uses your local backend and is saved like any other project. No external AI account is needed with the mock provider.</p>
              {createProject.isError && (
                <p role="alert" className="mt-3 text-xs text-red-300">Could not create the sample project. Check the API connection and try again.</p>
              )}
            </div>
            <div className="flex flex-col gap-3 sm:flex-row lg:flex-col">
              <Button
                loading={createProject.isPending}
                disabled={createProject.isPending}
                onClick={() => createProject.mutate({
                  name: "Community Pantry Network",
                  description: "Coordinate local food donations and pantry inventory.",
                  idea: "Build a simple platform that helps neighborhood food pantries coordinate donations, track inventory, and share current needs with nearby residents and local businesses. Pantry volunteers need a low-friction way to update stock, while donors need to know which items are most useful and where to drop them off. The first version should work well on mobile, protect volunteer contact details, and remain usable for people with limited technical experience. Start with one neighborhood and make it easy to measure whether the platform reduces stockouts and wasted donations.",
                }, { onSuccess: (project) => router.push(`/projects/${project.id}`) })}
              >
                <Sparkles className="h-3.5 w-3.5" /> Explore with a sample
              </Button>
              <Button variant="secondary" className="w-full" onClick={() => router.push("/projects/new")}>
                <Plus className="h-3.5 w-3.5" /> Start your own <ArrowRight className="h-3.5 w-3.5" />
              </Button>
            </div>
          </div>
        </GlassCard>
      )}

      <div className="grid grid-cols-1 gap-6 lg:grid-cols-3">
        {/* Workflow funnel */}
        <div className="lg:col-span-2">
          <Card>
            <div className="px-5 pt-5 pb-4 flex items-center justify-between">
              <div className="flex items-center gap-2">
                <TrendingUp className="h-4 w-4 text-indigo-400" />
                <h3 className="text-sm font-semibold text-[var(--text-primary)]">Workflow Pipeline</h3>
              </div>
              <span className="text-xs text-[var(--text-muted)]">Active projects by stage</span>
            </div>
            <div className="h-px bg-white/[0.05] mx-5" />
            <CardContent className="space-y-3 pt-4">
              {WORKFLOW_STAGES.map(({ key, label }, i) => {
                const count = stats.workflows_by_stage[key] ?? 0;
                const max = Math.max(...WORKFLOW_STAGES.map((s) => stats.workflows_by_stage[s.key] ?? 0), 1);
                const pct = (count / max) * 100;
                return (
                  <div key={key} className="flex items-center gap-3">
                    <div className="w-4 text-right text-[10px] text-[var(--text-muted)] font-mono shrink-0">
                      {i + 1}
                    </div>
                    <div className="w-28 shrink-0">
                      <span className="text-xs text-[var(--text-secondary)]">{label}</span>
                    </div>
                    <div className="flex-1 h-1.5 bg-white/5 rounded-full overflow-hidden">
                      <div
                        className="h-full rounded-full bg-gradient-to-r from-indigo-500 to-purple-500 transition-all duration-500"
                        style={{ width: `${pct}%` }}
                      />
                    </div>
                    <span className="w-5 text-right text-xs font-medium text-[var(--text-secondary)] shrink-0">
                      {count}
                    </span>
                  </div>
                );
              })}
            </CardContent>
          </Card>
        </div>

        {/* Recent agent runs */}
        <Card>
          <div className="px-5 pt-5 pb-4 flex items-center gap-2">
            <Activity className="h-4 w-4 text-purple-400" />
            <h3 className="text-sm font-semibold text-[var(--text-primary)]">Recent Runs</h3>
          </div>
          <div className="h-px bg-white/[0.05] mx-5" />
          <CardContent className="pt-3 space-y-0.5">
            {stats.recent_agent_runs.length === 0 ? (
              <p className="text-sm text-[var(--text-muted)] py-4 text-center">No runs yet</p>
            ) : (
              stats.recent_agent_runs.map((run) => (
                <div
                  key={run.id}
                  className="flex items-center justify-between py-2.5 px-2 rounded-lg hover:bg-white/[0.03] transition-colors group"
                >
                  <div className="min-w-0">
                    <p className="text-xs font-medium text-[var(--text-primary)] truncate">
                      {run.agent_name.replace(/_/g, " ")}
                    </p>
                    <p className="text-[10px] text-[var(--text-muted)] capitalize mt-0.5">
                      {run.stage.replace(/_/g, " ")}
                    </p>
                  </div>
                  <div className="flex items-center gap-2 shrink-0 ml-2">
                    <span
                      className={cn(
                        "inline-flex items-center rounded-full px-2 py-0.5 text-[10px] font-medium",
                        STATUS_STYLES[run.status] ?? "bg-zinc-500/10 text-zinc-400"
                      )}
                    >
                      {run.status}
                    </span>
                    <span className="text-[10px] text-[var(--text-muted)]">
                      {formatRelative(run.started_at)}
                    </span>
                  </div>
                </div>
              ))
            )}
          </CardContent>
        </Card>
      </div>

      {/* Quick links */}
      {stats.pending_checkpoints > 0 && (
        <GlassCard className="p-5">
          <div className="flex items-center justify-between">
            <div className="flex items-center gap-3">
              <div className="p-2 rounded-lg bg-amber-500/10">
                <Clock className="h-4 w-4 text-amber-400" />
              </div>
              <div>
                <p className="text-sm font-medium text-[var(--text-primary)]">
                  {stats.pending_checkpoints} checkpoint{stats.pending_checkpoints > 1 ? "s" : ""} awaiting review
                </p>
                <p className="text-xs text-[var(--text-muted)]">Human-in-the-loop reviews are blocking workflow progress</p>
              </div>
            </div>
            <Link href="/review-queue">
              <Button variant="secondary" size="sm">
                Go to Queue
              </Button>
            </Link>
          </div>
        </GlassCard>
      )}
    </div>
  );
}
