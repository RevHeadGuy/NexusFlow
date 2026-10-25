"use client";

import Link from "next/link";
import { Plus, Trash2, ArrowRight, FolderKanban } from "lucide-react";
import { useProjects, useDeleteProject } from "@/lib/hooks/useProjects";
import { Button } from "@/components/ui/Button";
import { STATUS_STYLES, cn, formatRelative } from "@/lib/utils";

export default function ProjectsPage() {
  const { data: projects, isLoading, isError, refetch } = useProjects();
  const deleteMutation = useDeleteProject();

  if (isLoading) {
    return (
      <div className="flex h-full items-center justify-center">
        <div className="flex items-center gap-3 text-[var(--text-muted)]">
          <svg className="h-4 w-4 animate-spin" fill="none" viewBox="0 0 24 24">
            <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4"/>
            <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8v8H4z"/>
          </svg>
          <span className="text-sm">Loading projects…</span>
        </div>
      </div>
    );
  }

  return (
    <div className="p-4 sm:p-6 lg:p-8 space-y-6 animate-fade-in-up">
      <div className="mx-auto max-w-7xl">
      <div className="flex flex-col gap-4 sm:flex-row sm:items-center sm:justify-between">
        <div>
          <h1 className="text-2xl font-bold text-[var(--text-primary)] tracking-tight">Projects</h1>
          <p className="text-sm text-[var(--text-muted)] mt-1">
            {projects?.length ?? 0} project{projects?.length !== 1 ? "s" : ""}
          </p>
        </div>
        <Link href="/projects/new">
          <Button><Plus className="h-3.5 w-3.5" />New Project</Button>
        </Link>
      </div>

      {isError ? (
        <div role="alert" className="rounded-xl border border-red-400/20 bg-red-400/[0.05] p-5">
          <p className="text-sm font-medium text-red-200">Projects could not be loaded</p>
          <p className="mt-1 text-xs text-[var(--text-secondary)]">Check the API connection and try again.</p>
          <Button className="mt-4" size="sm" variant="secondary" onClick={() => refetch()}>Try again</Button>
        </div>
      ) : !projects || projects.length === 0 ? (
        <div className="flex flex-col items-center justify-center py-24 space-y-4">
          <div className="p-4 rounded-2xl bg-white/[0.03] border border-white/[0.06]">
            <FolderKanban className="h-8 w-8 text-[var(--text-muted)]" />
          </div>
          <p className="text-sm text-[var(--text-muted)]">No projects yet</p>
          <Link href="/projects/new">
            <Button variant="secondary" size="sm">Create your first project</Button>
          </Link>
        </div>
      ) : (
        <div className="grid gap-4 sm:grid-cols-2 lg:grid-cols-3">
          {projects.map((project, i) => (
            <div
              key={project.id}
              className="group stagger-item surface-interactive relative rounded-xl overflow-hidden"
              style={{ "--i": i } as React.CSSProperties}
            >
              {/* Top accent line */}
              <div className="absolute inset-x-0 top-0 h-px bg-gradient-to-r from-transparent via-indigo-500/40 to-transparent opacity-0 group-hover:opacity-100 transition-opacity" />

              <div className="p-5">
                <div className="flex items-start justify-between mb-3">
                  <Link href={`/projects/${project.id}`} className="flex-1 min-w-0">
                    <h3 className="font-semibold text-[var(--text-primary)] group-hover:text-indigo-300 transition-colors truncate text-sm">
                      {project.name}
                    </h3>
                  </Link>
                  <button
                    onClick={() => {
                      if (confirm("Delete this project?")) deleteMutation.mutate(project.id);
                    }}
                    className="ml-2 flex h-8 w-8 items-center justify-center rounded text-[var(--text-secondary)] hover:text-red-300 hover:bg-red-500/10 focus-visible:opacity-100 sm:opacity-0 sm:group-hover:opacity-100 transition-all"
                    aria-label={`Delete ${project.name}`}
                  >
                    <Trash2 className="h-3.5 w-3.5" />
                  </button>
                </div>

                {project.description && (
                  <p className="text-xs text-[var(--text-secondary)] line-clamp-2 mb-4 leading-relaxed">
                    {project.description}
                  </p>
                )}

                <div className="flex items-center justify-between">
                  <span className={cn(
                    "inline-flex items-center rounded-full px-2.5 py-0.5 text-[10px] font-medium",
                    STATUS_STYLES[project.status] ?? "bg-zinc-500/10 text-zinc-400"
                  )}>
                    <span className="h-1.5 w-1.5 rounded-full bg-current opacity-70 mr-1.5" />
                    {project.status.replace(/_/g, " ")}
                  </span>
                  <span className="text-[10px] text-[var(--text-muted)]">
                    {formatRelative(project.updated_at)}
                  </span>
                </div>
              </div>

              <Link href={`/projects/${project.id}`}>
                <div className="px-5 py-3 border-t border-white/[0.06] flex items-center justify-between transition-colors group-hover:bg-white/[0.02]">
                  <span className="text-xs font-medium text-indigo-200">Open project</span>
                  <ArrowRight className="h-3.5 w-3.5 text-indigo-400" />
                </div>
              </Link>
            </div>
          ))}
        </div>
      )}
      </div>
    </div>
  );
}
