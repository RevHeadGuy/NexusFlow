"use client";

import { type FormEvent, useState } from "react";
import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { Check, MessageSquarePlus } from "lucide-react";
import { Button } from "@/components/ui/Button";
import { Card, CardContent } from "@/components/ui/Card";
import { reviewsApi } from "@/lib/api/reviews";
import type { Artifact } from "@/lib/types/api";
import { formatDate } from "@/lib/utils";

export function ArtifactReviewComments({ artifact, versionNumber }: { artifact: Artifact; versionNumber: number }) {
  const queryClient = useQueryClient();
  const queryKey = ["artifact-review-comments", artifact.project_id, artifact.id] as const;
  const [reviewerName, setReviewerName] = useState("Reviewer");
  const [sectionKey, setSectionKey] = useState("Document");
  const [commentText, setCommentText] = useState("");
  const [suggestedEdit, setSuggestedEdit] = useState("");
  const [formError, setFormError] = useState<string | null>(null);
  const { data: comments, isLoading, isError, refetch } = useQuery({
    queryKey,
    queryFn: () => reviewsApi.list(artifact.project_id, artifact.id),
  });

  const addComment = useMutation({
    mutationFn: () => reviewsApi.add(artifact.project_id, artifact.id, {
      version_number: versionNumber,
      reviewer_name: reviewerName,
      section_key: sectionKey,
      comment: commentText,
      suggested_edit: suggestedEdit || undefined,
    }),
    onSuccess: async () => {
      setCommentText(""); setSuggestedEdit(""); setFormError(null);
      await Promise.all([
        queryClient.invalidateQueries({ queryKey }),
        queryClient.invalidateQueries({ queryKey: ["workflow", artifact.project_id] }),
        queryClient.invalidateQueries({ queryKey: ["workflow-review-queue"] }),
      ]);
    },
    onError: (error) => setFormError(error instanceof Error ? error.message : "Could not add the review comment."),
  });

  const resolveComment = useMutation({
    mutationFn: (commentId: string) => reviewsApi.resolve(artifact.project_id, artifact.id, commentId),
    onSuccess: () => Promise.all([
      queryClient.invalidateQueries({ queryKey }),
      queryClient.invalidateQueries({ queryKey: ["workflow", artifact.project_id] }),
      queryClient.invalidateQueries({ queryKey: ["workflow-review-queue"] }),
    ]),
  });

  function submit(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    setFormError(null);
    addComment.mutate();
  }

  return (
    <Card>
      <CardContent className="space-y-4">
        <div className="flex items-start justify-between gap-3">
          <div>
            <div className="flex items-center gap-2">
              <MessageSquarePlus className="h-4 w-4 text-indigo-300" />
              <h3 className="text-sm font-semibold text-[var(--text-primary)]">Review feedback</h3>
            </div>
            <p className="mt-1 text-xs text-[var(--text-muted)]">Comments attach to v{versionNumber} and can be resolved after edits.</p>
          </div>
          <span className="shrink-0 rounded-full border border-amber-400/15 bg-amber-400/[0.06] px-2.5 py-1 text-[10px] text-amber-200">Local reviewer labels</span>
        </div>

        <form onSubmit={submit} className="grid gap-3 sm:grid-cols-2">
          <label className="space-y-1.5 text-xs font-medium text-[var(--text-secondary)]">
            Reviewer name
            <input required maxLength={100} value={reviewerName} onChange={(event) => setReviewerName(event.target.value)} className="w-full rounded-lg border border-white/[0.08] bg-white/[0.03] px-3 py-2 text-sm text-[var(--text-primary)] focus:outline-none focus:ring-2 focus:ring-indigo-500/40" />
          </label>
          <label className="space-y-1.5 text-xs font-medium text-[var(--text-secondary)]">
            Section or heading
            <input maxLength={255} value={sectionKey} onChange={(event) => setSectionKey(event.target.value)} className="w-full rounded-lg border border-white/[0.08] bg-white/[0.03] px-3 py-2 text-sm text-[var(--text-primary)] focus:outline-none focus:ring-2 focus:ring-indigo-500/40" placeholder="Document" />
          </label>
          <label className="space-y-1.5 text-xs font-medium text-[var(--text-secondary)] sm:col-span-2">
            Feedback
            <textarea required minLength={2} maxLength={5000} rows={2} value={commentText} onChange={(event) => setCommentText(event.target.value)} className="w-full resize-y rounded-lg border border-white/[0.08] bg-white/[0.03] px-3 py-2 text-sm text-[var(--text-primary)] focus:outline-none focus:ring-2 focus:ring-indigo-500/40" placeholder="What needs clarification or revision?" />
          </label>
          <label className="space-y-1.5 text-xs font-medium text-[var(--text-secondary)] sm:col-span-2">
            Suggested edit <span className="font-normal text-[var(--text-muted)]">(optional)</span>
            <textarea maxLength={10000} rows={2} value={suggestedEdit} onChange={(event) => setSuggestedEdit(event.target.value)} className="w-full resize-y rounded-lg border border-white/[0.08] bg-white/[0.03] px-3 py-2 text-sm text-[var(--text-primary)] focus:outline-none focus:ring-2 focus:ring-indigo-500/40" placeholder="Proposed wording or change" />
          </label>
          {formError && <p role="alert" className="text-xs text-red-300 sm:col-span-2">{formError}</p>}
          <div className="sm:col-span-2">
            <Button size="sm" type="submit" loading={addComment.isPending} disabled={addComment.isPending || !commentText.trim() || !reviewerName.trim()}>
              <MessageSquarePlus className="h-3.5 w-3.5" /> Add feedback
            </Button>
          </div>
        </form>

        <div className="space-y-2 border-t border-white/[0.06] pt-4">
          {isLoading && <p className="text-xs text-[var(--text-muted)]">Loading feedback…</p>}
          {isError && <div role="alert" className="text-xs text-red-300">Feedback could not be loaded. <button type="button" onClick={() => refetch()} className="underline">Retry</button></div>}
          {comments?.length === 0 && <p className="text-xs text-[var(--text-muted)]">No feedback on this artifact yet.</p>}
          {comments?.map((item) => (
            <div key={item.id} className={`rounded-lg border p-3 ${item.resolved ? "border-emerald-400/10 bg-emerald-400/[0.03]" : "border-white/[0.07] bg-white/[0.02]"}`}>
              <div className="flex flex-wrap items-center justify-between gap-2">
                <div className="flex flex-wrap items-center gap-2 text-[11px]">
                  <span className="font-semibold text-[var(--text-primary)]">{item.reviewer_name}</span>
                  <span className="text-[var(--text-muted)]">{item.section_key}</span>
                  <span className="text-[var(--text-muted)]">v{item.version_number} · {formatDate(item.created_at)}</span>
                </div>
                {item.resolved ? (
                  <span className="inline-flex items-center gap-1 text-[10px] text-emerald-300"><Check className="h-3 w-3" /> Resolved</span>
                ) : (
                  <button type="button" onClick={() => resolveComment.mutate(item.id)} disabled={resolveComment.isPending} className="text-[10px] text-indigo-200 hover:text-white">Mark resolved</button>
                )}
              </div>
              <p className="mt-2 whitespace-pre-wrap text-xs leading-relaxed text-[var(--text-secondary)]">{item.comment}</p>
              {item.suggested_edit && <p className="mt-2 whitespace-pre-wrap rounded-md border-l-2 border-indigo-400/40 bg-indigo-400/[0.04] px-3 py-2 text-xs leading-relaxed text-indigo-100">Suggested edit: {item.suggested_edit}</p>}
            </div>
          ))}
        </div>
      </CardContent>
    </Card>
  );
}
