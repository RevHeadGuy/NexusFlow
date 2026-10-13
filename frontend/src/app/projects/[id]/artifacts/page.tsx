"use client";

import { useState } from "react";
import { useParams } from "next/navigation";
import { useQuery } from "@tanstack/react-query";
import { Plus, FileText, Download } from "lucide-react";
import { artifactsApi } from "@/lib/api/artifacts";
import { ArtifactViewer } from "@/components/artifacts/ArtifactViewer";
import { Button } from "@/components/ui/Button";
import { Card, CardContent } from "@/components/ui/Card";
import { cn, formatRelative } from "@/lib/utils";
import { API_URL } from "@/lib/api/client";
import Link from "next/link";

export default function ArtifactsPage() {
  const { id } = useParams<{ id: string }>();
  const [selectedId, setSelectedId] = useState<string | null>(null);
  const [creating, setCreating] = useState(false);
  const [newName, setNewName] = useState("");
  const [newContent, setNewContent] = useState("");
  const [createError, setCreateError] = useState<string | null>(null);

  const { data: artifacts, isLoading, isError, refetch } = useQuery({
    queryKey: ["artifacts", id],
    queryFn: () => artifactsApi.list(id),
    enabled: !!id,
  });

  const active = artifacts?.find((a) => a.id === selectedId) ?? artifacts?.[0] ?? null;

  const { data: versions } = useQuery({
    queryKey: ["artifact-versions", active?.id],
    queryFn: () => artifactsApi.versions(id, active!.id),
    enabled: !!active,
  });

  async function handleCreate() {
    if (!newName.trim()) return;
    setCreateError(null);
    try {
      await artifactsApi.create(id, { name: newName, type: "markdown", content: newContent });
      setCreating(false); setNewName(""); setNewContent("");
      await refetch();
    } catch (error) {
      setCreateError(error instanceof Error ? error.message : "Could not save this artifact.");
    }
  }

  if (isLoading) return (
    <div className="flex h-40 items-center justify-center text-sm text-[var(--text-muted)]">Loading…</div>
  );

  const inputCls = "w-full rounded-lg bg-white/[0.04] border border-white/[0.08] px-3 py-2 text-sm text-[var(--text-primary)] placeholder:text-[var(--text-muted)] focus:outline-none focus:ring-2 focus:ring-indigo-500/30 transition-all";

  return (
    <div className="p-4 sm:p-6 lg:p-8 space-y-5 animate-fade-in-up">
      <div className="flex flex-col gap-3 sm:flex-row sm:items-center sm:justify-between">
        <div>
          <h2 className="text-base font-semibold text-[var(--text-primary)]">Project artifacts</h2>
          <p className="mt-1 text-xs text-[var(--text-secondary)]">Versioned drafts and approved project documents · {artifacts?.length ?? 0} saved</p>
        </div>
        <div className="flex flex-wrap gap-2">
          <a href={`${API_URL}/projects/${id}/package/export`} className="inline-flex">
            <Button size="sm" variant="secondary"><Download className="h-3.5 w-3.5" /> Export package</Button>
          </a>
          <Button size="sm" onClick={() => { setCreateError(null); setCreating(true); }}>
            <Plus className="h-3.5 w-3.5" /> New artifact
          </Button>
        </div>
      </div>

      {creating && (
        <Card>
          <CardContent className="space-y-3">
            <label className="block space-y-1.5 text-xs font-medium text-[var(--text-secondary)]">
              Artifact name
              <input className={inputCls} placeholder="e.g. Product requirements" value={newName} onChange={(e) => setNewName(e.target.value)} />
            </label>
            <label className="block space-y-1.5 text-xs font-medium text-[var(--text-secondary)]">
              Markdown content
              <textarea className={cn(inputCls, "font-mono resize-y")} rows={8} placeholder="# Document title" value={newContent} onChange={(e) => setNewContent(e.target.value)} />
            </label>
            {createError && <p role="alert" className="text-xs text-red-300">{createError}</p>}
            <div className="flex gap-2">
              <Button size="sm" onClick={handleCreate} disabled={!newName.trim()}>Save artifact</Button>
              <Button size="sm" variant="ghost" onClick={() => setCreating(false)}>Cancel</Button>
            </div>
          </CardContent>
        </Card>
      )}

      {isError ? (
        <div role="alert" className="rounded-xl border border-red-400/20 bg-red-400/[0.05] p-5">
          <p className="text-sm font-medium text-red-200">Artifacts could not be loaded</p>
          <Button className="mt-3" size="sm" variant="secondary" onClick={() => refetch()}>Try again</Button>
        </div>
      ) : !artifacts || artifacts.length === 0 ? (
        <div className="flex flex-col items-center gap-3 rounded-xl border border-dashed border-white/[0.12] py-16 text-center">
          <div className="rounded-xl border border-white/[0.08] bg-white/[0.03] p-3"><FileText className="h-6 w-6 text-indigo-300" /></div>
          <div>
            <p className="text-sm font-semibold text-[var(--text-primary)]">No artifacts saved yet</p>
            <p className="mt-1 text-xs text-[var(--text-secondary)]">Prepare a workflow draft or create a document to start the project package.</p>
          </div>
          <Link href={`/projects/${id}/workflow`}><Button size="sm" variant="secondary">Open workflow</Button></Link>
        </div>
      ) : (
        <div className="flex min-h-[360px] h-[calc(100dvh-300px)] flex-col gap-4 md:flex-row">
          {/* List */}
          <div className="flex max-h-28 w-full shrink-0 gap-1 overflow-x-auto md:max-h-none md:w-52 md:flex-col md:overflow-x-hidden md:overflow-y-auto">
            {artifacts.map((a) => {
              const isActive = (selectedId ?? artifacts[0]?.id) === a.id;
              return (
                <button key={a.id} onClick={() => setSelectedId(a.id)} aria-current={isActive ? "true" : undefined} className={cn(
                  "w-44 shrink-0 rounded-lg border px-3 py-2.5 text-left text-xs transition-colors md:w-full",
                  isActive ? "border-indigo-400/25 bg-indigo-500/10 text-indigo-100" : "border-transparent text-[var(--text-secondary)] hover:bg-white/[0.04]"
                )}>
                  <p className="font-medium truncate">{a.name}</p>
                  <p className="mt-1 text-[11px] text-[var(--text-muted)]">v{a.current_version} · {formatRelative(a.updated_at)}</p>
                </button>
              );
            })}
          </div>

          {/* Viewer */}
          <div className="flex-1 min-w-0">
            {active && versions && <ArtifactViewer artifact={active} versions={versions} />}
          </div>
        </div>
      )}
    </div>
  );
}
