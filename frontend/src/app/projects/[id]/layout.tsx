"use client";

import { useParams } from "next/navigation";
import { useProject } from "@/lib/hooks/useProjects";
import { ProjectTabs } from "@/components/ui/ProjectTabs";
import { STATUS_STYLES, cn, formatDate } from "@/lib/utils";

export default function ProjectLayout({ children }: { children: React.ReactNode }) {
  const { id } = useParams<{ id: string }>();
  const { data: project } = useProject(id);

  return (
    <div className="flex flex-col h-full" style={{ background: "var(--bg-base)" }}>
      {/* Project header */}
      <div className="px-4 pt-5 sm:px-6 sm:pt-7 lg:px-8 lg:pt-8">
        <div className="flex items-start justify-between">
          <div className="min-w-0">
            <div className="flex flex-wrap items-center gap-x-3 gap-y-2">
              <h1 className="max-w-full break-words text-xl font-bold tracking-tight text-[var(--text-primary)] sm:text-2xl">
                {project?.name ?? "Loading…"}
              </h1>
              {project && (
                <span className={cn(
                  "inline-flex items-center gap-1.5 rounded-full px-2.5 py-0.5 text-[10px] font-medium",
                  STATUS_STYLES[project.status] ?? "bg-zinc-500/10 text-zinc-400"
                )}>
                  <span className="h-1 w-1 rounded-full bg-current" />
                  {project.status.replace(/_/g, " ")}
                </span>
              )}
            </div>
            {project?.description && (
              <p className="mt-1 max-w-3xl text-sm leading-relaxed text-[var(--text-secondary)]">{project.description}</p>
            )}
            {project && (
              <p className="mt-2 text-xs text-[var(--text-muted)]">
                Created {formatDate(project.created_at)}
              </p>
            )}
          </div>
        </div>
        <div className="mt-4"><ProjectTabs projectId={id} /></div>
      </div>

      {/* Page content */}
      <div className="flex-1 overflow-y-auto">
        {children}
      </div>
    </div>
  );
}
