"use client";

import { useState } from "react";
import { useQueryClient } from "@tanstack/react-query";
import ReactMarkdown from "react-markdown";
import remarkGfm from "remark-gfm";
import { Download, ChevronDown, Clock, Pencil, Save, X } from "lucide-react";
import { Button } from "@/components/ui/Button";
import { artifactsApi } from "@/lib/api/artifacts";
import { ArtifactReviewComments } from "@/components/artifacts/ArtifactReviewComments";
import { formatRelative, cn } from "@/lib/utils";
import type { Artifact, ArtifactVersion } from "@/lib/types/api";

export function ArtifactViewer({ artifact, versions }: { artifact: Artifact; versions: ArtifactVersion[] }) {
  const [selectedVersion, setSelectedVersion] = useState<ArtifactVersion | null>(null);
  const [showVersions, setShowVersions] = useState(false);
  const [editing, setEditing] = useState(false);
  const [draftContent, setDraftContent] = useState("");
  const [saving, setSaving] = useState(false);
  const [saveError, setSaveError] = useState<string | null>(null);
  // Reset view/edit state when switching to a different artifact. Adjusting
  // state during render (the React-recommended pattern) avoids the cascading
  // render that an effect-based reset triggers.
  const [lastArtifactId, setLastArtifactId] = useState(artifact.id);
  const queryClient = useQueryClient();

  if (artifact.id !== lastArtifactId) {
    setLastArtifactId(artifact.id);
    setSelectedVersion(null);
    setEditing(false);
    setSaveError(null);
  }

  const current = selectedVersion ?? versions.find((v) => v.version === artifact.current_version) ?? versions[0];
  const content = current?.content ?? artifact.content;
  const isLatestVersion = current?.version === artifact.current_version;
  const exportUrl = artifactsApi.exportUrl(artifact.project_id, artifact.id);

  async function saveDraft() {
    if (draftContent === content || saving) return;
    setSaving(true);
    setSaveError(null);
    try {
      await artifactsApi.addVersion(artifact.project_id, artifact.id, {
        content: draftContent,
        summary: "Edited by project reviewer",
      });
      setSelectedVersion(null);
      setEditing(false);
      await Promise.all([
        queryClient.invalidateQueries({ queryKey: ["artifacts", artifact.project_id] }),
        queryClient.invalidateQueries({ queryKey: ["artifact-versions", artifact.id] }),
        queryClient.invalidateQueries({ queryKey: ["workflow", artifact.project_id] }),
        queryClient.invalidateQueries({ queryKey: ["workflow-review-queue"] }),
      ]);
    } catch (error) {
      setSaveError(error instanceof Error ? error.message : "Could not save this version.");
    } finally {
      setSaving(false);
    }
  }

  return (
    <div className="flex flex-col gap-3">
      {/* Toolbar */}
      <div className="flex items-center justify-between gap-3">
        {/* Version picker */}
        <div className="relative">
          <button
            onClick={() => setShowVersions((v) => !v)}
            disabled={editing}
            className="flex items-center gap-2 rounded-lg bg-white/[0.04] border border-white/[0.08] px-3 py-1.5 text-xs text-[var(--text-secondary)] hover:bg-white/[0.07] hover:border-white/[0.14] transition-all"
          >
            <Clock className="h-3 w-3 text-[var(--text-muted)]" />
            v{current?.version ?? artifact.current_version}
            {current?.summary && <span className="text-[var(--text-muted)]"> — {current.summary}</span>}
            <ChevronDown className={cn("h-3 w-3 text-[var(--text-muted)] transition-transform", showVersions && "rotate-180")} />
          </button>

          {showVersions && !editing && (
            <div className="absolute top-full left-0 mt-1 w-64 rounded-xl border border-white/[0.08] bg-[#1a1a24] shadow-2xl z-10 overflow-hidden">
              {versions.map((v) => (
                <button
                  key={v.id}
                  onClick={() => { setSelectedVersion(v); setShowVersions(false); }}
                  className={cn(
                    "w-full flex items-center justify-between px-3 py-2.5 text-xs text-left hover:bg-white/[0.04] transition-colors",
                    current?.version === v.version && "bg-indigo-500/10 text-indigo-300"
                  )}
                >
                  <span className="font-medium">v{v.version}</span>
                  <div className="text-right">
                    {v.summary && <p className="text-[var(--text-muted)] truncate max-w-[140px]">{v.summary}</p>}
                    <p className="text-[var(--text-muted)]">{formatRelative(v.created_at)}</p>
                  </div>
                </button>
              ))}
            </div>
          )}
        </div>

        <div className="flex items-center gap-2">
          {!editing && isLatestVersion && (
            <Button size="sm" variant="secondary" onClick={() => { setDraftContent(content); setSaveError(null); setShowVersions(false); setEditing(true); }}>
              <Pencil className="h-3.5 w-3.5" /> Edit draft
            </Button>
          )}
          <a href={exportUrl} download>
            <Button size="sm" variant="secondary">
              <Download className="h-3.5 w-3.5" />
              Export ZIP
            </Button>
          </a>
        </div>
      </div>

      {/* Content */}
      <div className="min-h-[320px] rounded-xl border border-white/[0.06] bg-[var(--bg-surface)]">
        {editing ? (
          <div className="flex h-full min-h-80 flex-col gap-3 p-4 sm:p-6">
            <label htmlFor="artifact-draft-editor" className="text-xs font-medium text-[var(--text-secondary)]">
              Edit {artifact.name} · changes are saved as a new version
            </label>
            <textarea
              id="artifact-draft-editor"
              aria-label={`Edit ${artifact.name} Markdown`}
              className="min-h-80 flex-1 resize-y rounded-lg border border-white/[0.08] bg-black/20 p-4 font-mono text-xs leading-relaxed text-[var(--text-primary)] focus:outline-none focus:ring-2 focus:ring-indigo-500/40"
              value={draftContent}
              onChange={(event) => setDraftContent(event.target.value)}
              spellCheck={false}
            />
            {saveError && <p role="alert" className="text-xs text-red-300">{saveError}</p>}
            <div className="flex flex-wrap justify-end gap-2">
              <Button size="sm" variant="ghost" onClick={() => { setEditing(false); setSaveError(null); }} disabled={saving}>
                <X className="h-3.5 w-3.5" /> Cancel
              </Button>
              <Button size="sm" onClick={saveDraft} loading={saving} disabled={saving || draftContent === content}>
                <Save className="h-3.5 w-3.5" /> Save version
              </Button>
            </div>
          </div>
        ) : (
          <div className="p-6 prose prose-sm max-w-none">
            <ReactMarkdown remarkPlugins={[remarkGfm]}>{content}</ReactMarkdown>
          </div>
        )}
      </div>
      <ArtifactReviewComments artifact={artifact} versionNumber={current?.version ?? artifact.current_version} />
    </div>
  );
}
