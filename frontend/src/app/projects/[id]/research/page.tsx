"use client";

import { type FormEvent, useState } from "react";
import { useParams } from "next/navigation";
import Link from "next/link";
import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { ExternalLink, FilePlus2, RefreshCw, ShieldCheck, Trash2 } from "lucide-react";
import { Button } from "@/components/ui/Button";
import { Card, CardContent } from "@/components/ui/Card";
import { researchApi } from "@/lib/api/research";
import { formatDate } from "@/lib/utils";

const inputClass = "w-full rounded-lg border border-white/10 bg-white/[0.04] px-3 py-2.5 text-sm text-[var(--text-primary)] placeholder:text-[var(--text-muted)] focus:outline-none focus:ring-2 focus:ring-indigo-500/40";

export default function ResearchPage() {
  const { id } = useParams<{ id: string }>();
  const queryClient = useQueryClient();
  const [title, setTitle] = useState("");
  const [url, setUrl] = useState("");
  const [finding, setFinding] = useState("");
  const [notes, setNotes] = useState("");
  const [reviewer, setReviewer] = useState("Reviewer");
  const [formError, setFormError] = useState<string | null>(null);
  const sourceKey = ["research-sources", id] as const;

  const { data: sources, isLoading, isError, refetch } = useQuery({
    queryKey: sourceKey,
    queryFn: () => researchApi.list(id),
    enabled: !!id,
  });

  const addSource = useMutation({
    mutationFn: () => researchApi.add(id, { title, url, finding, notes: notes || undefined, added_by: reviewer }),
    onSuccess: async () => {
      setTitle(""); setUrl(""); setFinding(""); setNotes(""); setFormError(null);
      await queryClient.invalidateQueries({ queryKey: sourceKey });
    },
    onError: (error) => setFormError(error instanceof Error ? error.message : "Could not save the source."),
  });

  const updateReview = useMutation({
    mutationFn: ({ sourceId, reviewed }: { sourceId: string; reviewed: boolean }) => researchApi.review(id, sourceId, reviewed),
    onSuccess: () => queryClient.invalidateQueries({ queryKey: sourceKey }),
  });

  const removeSource = useMutation({
    mutationFn: (sourceId: string) => researchApi.remove(id, sourceId),
    onSuccess: () => queryClient.invalidateQueries({ queryKey: sourceKey }),
  });

  const refreshPlan = useMutation({
    mutationFn: () => researchApi.refreshPlan(id),
    onSuccess: () => Promise.all([
      queryClient.invalidateQueries({ queryKey: ["artifacts", id] }),
      queryClient.invalidateQueries({ queryKey: ["research-sources", id] }),
      queryClient.invalidateQueries({ queryKey: ["workflow", id] }),
      queryClient.invalidateQueries({ queryKey: ["workflow-review-queue"] }),
    ]),
  });

  function submitSource(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    setFormError(null);
    addSource.mutate();
  }

  return (
    <div className="mx-auto w-full max-w-6xl space-y-6 p-4 sm:p-6 lg:p-8 animate-fade-in-up">
      <div className="flex flex-col gap-3 sm:flex-row sm:items-end sm:justify-between">
        <div>
          <p className="text-xs font-semibold uppercase tracking-widest text-indigo-300">Project evidence</p>
          <h2 className="mt-1 text-xl font-semibold text-[var(--text-primary)]">Research sources</h2>
          <p className="mt-2 max-w-2xl text-sm leading-relaxed text-[var(--text-secondary)]">Collect citations and findings from your own research. NexusFlow stores what you add; it does not fetch or independently verify source content.</p>
        </div>
        <Button
          size="sm"
          variant="secondary"
          onClick={() => refreshPlan.mutate()}
          loading={refreshPlan.isPending}
          disabled={refreshPlan.isPending}
        >
          <RefreshCw className="h-3.5 w-3.5" /> Update research plan
        </Button>
      </div>

      {refreshPlan.isSuccess && (
        <p role="status" className="text-xs text-emerald-300">Research Plan updated as version {refreshPlan.data.current_version}. <Link className="underline hover:text-emerald-100" href={`/projects/${id}/artifacts`}>Review it in Artifacts</Link>.</p>
      )}
      {refreshPlan.isError && <p role="alert" className="text-xs text-red-300">{String(refreshPlan.error)}</p>}
          {updateReview.isError && <p role="alert" className="text-xs text-red-300">Source review status could not be updated: {String(updateReview.error)}</p>}
          {removeSource.isError && <p role="alert" className="text-xs text-red-300">Source could not be removed: {String(removeSource.error)}</p>}

      <div className="grid items-start gap-5 lg:grid-cols-[minmax(0,1.1fr)_minmax(0,0.9fr)]">
        <Card>
          <CardContent>
            <form onSubmit={submitSource} className="space-y-4">
              <div>
                <h3 className="text-sm font-semibold text-[var(--text-primary)]">Add a source</h3>
                <p className="mt-1 text-xs text-[var(--text-muted)]">Record a useful claim and where it came from.</p>
              </div>
              <label className="block space-y-1.5 text-xs font-medium text-[var(--text-secondary)]">
                Source title
                <input required minLength={2} maxLength={255} value={title} onChange={(event) => setTitle(event.target.value)} className={inputClass} placeholder="Report, article, interview, or dataset" />
              </label>
              <label className="block space-y-1.5 text-xs font-medium text-[var(--text-secondary)]">
                URL
                <input required type="url" value={url} onChange={(event) => setUrl(event.target.value)} className={inputClass} placeholder="https://example.org/source" />
              </label>
              <label className="block space-y-1.5 text-xs font-medium text-[var(--text-secondary)]">
                Finding or claim
                <textarea required minLength={5} maxLength={10000} rows={3} value={finding} onChange={(event) => setFinding(event.target.value)} className={inputClass} placeholder="What did this source contribute to your understanding?" />
              </label>
              <label className="block space-y-1.5 text-xs font-medium text-[var(--text-secondary)]">
                Context or caveats <span className="font-normal text-[var(--text-muted)]">(optional)</span>
                <textarea maxLength={10000} rows={2} value={notes} onChange={(event) => setNotes(event.target.value)} className={inputClass} placeholder="Limitations, date checked, or follow-up needed" />
              </label>
              <label className="block space-y-1.5 text-xs font-medium text-[var(--text-secondary)]">
                Added by
                <input required maxLength={100} value={reviewer} onChange={(event) => setReviewer(event.target.value)} className={inputClass} />
              </label>
              {formError && <p role="alert" className="text-xs text-red-300">{formError}</p>}
              <Button type="submit" loading={addSource.isPending} disabled={addSource.isPending || !title.trim() || !url.trim() || !finding.trim()}>
                <FilePlus2 className="h-3.5 w-3.5" /> Save source
              </Button>
            </form>
          </CardContent>
        </Card>

        <div className="space-y-3">
          <div className="flex items-center justify-between">
            <h3 className="text-sm font-semibold text-[var(--text-primary)]">Evidence log</h3>
            <span className="text-xs text-[var(--text-muted)]">{sources?.length ?? 0} sources</span>
          </div>
          {isLoading ? <p className="py-10 text-center text-sm text-[var(--text-muted)]">Loading sources…</p> : null}
          {isError ? (
            <div role="alert" className="rounded-xl border border-red-400/20 bg-red-400/[0.05] p-4">
              <p className="text-sm text-red-200">Could not load project sources.</p>
              <Button className="mt-3" size="sm" variant="secondary" onClick={() => refetch()}>Retry</Button>
            </div>
          ) : null}
          {!isLoading && !isError && sources?.length === 0 ? (
            <div className="rounded-xl border border-dashed border-white/[0.1] px-5 py-10 text-center">
              <p className="text-sm font-medium text-[var(--text-primary)]">No sources added yet</p>
              <p className="mt-1 text-xs text-[var(--text-muted)]">Save a citation and a concise finding to begin the evidence log.</p>
            </div>
          ) : null}
          {sources?.map((source) => (
            <Card key={source.id}>
              <CardContent className="space-y-3">
                <div className="flex items-start justify-between gap-3">
                  <div className="min-w-0">
                    <a href={source.url} target="_blank" rel="noreferrer" className="inline-flex items-center gap-1.5 text-sm font-semibold text-indigo-200 hover:text-indigo-100">
                      <span className="break-words">{source.title}</span><ExternalLink className="h-3 w-3 shrink-0" />
                    </a>
                    <p className="mt-1 break-all text-[11px] text-[var(--text-muted)]">{source.url}</p>
                  </div>
                  <button type="button" onClick={() => removeSource.mutate(source.id)} disabled={removeSource.isPending} aria-label={`Remove ${source.title}`} className="rounded-md p-2 text-[var(--text-muted)] hover:bg-red-500/10 hover:text-red-300 disabled:opacity-50">
                    <Trash2 className="h-3.5 w-3.5" />
                  </button>
                </div>
                <p className="whitespace-pre-wrap text-sm leading-relaxed text-[var(--text-secondary)]">{source.finding}</p>
                {source.notes && <p className="whitespace-pre-wrap rounded-lg bg-white/[0.03] p-3 text-xs leading-relaxed text-[var(--text-muted)]">{source.notes}</p>}
                <div className="flex flex-wrap items-center justify-between gap-2 border-t border-white/[0.06] pt-3">
                  <span className="text-[11px] text-[var(--text-muted)]">Added by {source.added_by} · {formatDate(source.created_at)}</span>
                  <button
                    type="button"
                    onClick={() => updateReview.mutate({ sourceId: source.id, reviewed: !source.reviewed })}
                    disabled={updateReview.isPending}
                    className={`inline-flex items-center gap-1.5 rounded-full border px-2.5 py-1 text-[10px] font-medium ${source.reviewed ? "border-emerald-400/20 bg-emerald-400/10 text-emerald-200" : "border-amber-400/20 bg-amber-400/10 text-amber-200"}`}
                  >
                    <ShieldCheck className="h-3 w-3" /> {source.reviewed ? "Marked reviewed" : "Mark reviewed"}
                  </button>
                </div>
              </CardContent>
            </Card>
          ))}
        </div>
      </div>
    </div>
  );
}
